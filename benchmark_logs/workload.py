# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import asyncio
import logging
import re
import time

from osbenchmark import exceptions
from osbenchmark.client import RequestContextHolder
from osbenchmark.worker_coordinator.runner import Runner

request_context_holder = RequestContextHolder()

# Same 1024-based units ISM uses when parsing rollover "min_size".
_BYTE_UNITS = {"b": 1, "kb": 1024, "mb": 1024 ** 2, "gb": 1024 ** 3, "tb": 1024 ** 4, "pb": 1024 ** 5}
# Keep explain URLs well below the default 4KB HTTP initial line limit.
_EXPLAIN_BATCH_SIZE = 50


def parse_byte_size(value):
    if value is None or value == "":
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kmgtp]?b|[kmgtp])\s*", str(value).lower())
    if not match:
        raise exceptions.InvalidSyntax(f"Cannot parse byte size [{value}]; expected a value like '2gb' or '500mb'.")
    unit = match.group(2) if match.group(2).endswith("b") else match.group(2) + "b"
    return int(float(match.group(1)) * _BYTE_UNITS[unit])


class WaitForIsmWarmMigration(Runner):
    """
    Waits until ISM has finished managing a data stream after ingestion:

    * every backing index except the write index has completed its ISM policy
      (rolled over and migrated to UltraWarm), and
    * the write index is below every configured rollover threshold, so ISM will
      not roll it over later while queries are running.

    Fails if ISM reports a failed action on any backing index, or if the
    timeout expires.
    """

    RUNNER_NAME = "wait-for-ism-warm-migration"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    async def _request(self, opensearch, method, path):
        request_context_holder.on_client_request_start()
        try:
            return await opensearch.transport.perform_request(method, path)
        finally:
            request_context_holder.on_client_request_end()

    async def _explain(self, opensearch, indices):
        explained = {}
        for i in range(0, len(indices), _EXPLAIN_BATCH_SIZE):
            batch = ",".join(indices[i:i + _EXPLAIN_BATCH_SIZE])
            response = await self._request(opensearch, "GET", f"/_plugins/_ism/explain/{batch}")
            explained.update({k: v for k, v in response.items() if isinstance(v, dict)})
        return explained

    async def _write_index_over_threshold(self, opensearch, write_index, min_size, min_doc_count):
        stats = await self._request(opensearch, "GET", f"/{write_index}/_stats/docs,store")
        primaries = stats["indices"][write_index]["primaries"]
        size = primaries["store"]["size_in_bytes"]
        docs = primaries["docs"]["count"]
        over = (min_size is not None and size >= min_size) or (min_doc_count is not None and docs >= min_doc_count)
        return over, size, docs

    async def __call__(self, opensearch, params):
        data_stream = params["data-stream"]
        min_size = parse_byte_size(params.get("rollover-min-size"))
        min_doc_count = params.get("rollover-min-doc-count")
        min_doc_count = int(min_doc_count) if min_doc_count not in (None, "") else None
        timeout = float(params.get("timeout", 14400))
        poll_interval = float(params.get("poll-interval", 30))

        deadline = time.monotonic() + timeout
        polls = 0
        while True:
            polls += 1
            ds = await self._request(opensearch, "GET", f"/_data_stream/{data_stream}")
            backing = [i["index_name"] for i in ds["data_streams"][0]["indices"]]
            write_index = backing[-1]
            rolled_over = backing[:-1]

            explained = await self._explain(opensearch, rolled_over) if rolled_over else {}
            failed = {idx: e.get("info", {}).get("message") for idx, e in explained.items()
                      if e.get("action", {}).get("failed")}
            if failed:
                raise exceptions.BenchmarkError(f"ISM action failed for backing indices of [{data_stream}]: {failed}")

            pending = [idx for idx in rolled_over if not explained.get(idx, {}).get("policy_completed")]
            over, size, docs = await self._write_index_over_threshold(opensearch, write_index, min_size, min_doc_count)

            if not pending and not over:
                self.logger.info("ISM done for [%s]: %d backing indices migrated, write index [%s] at %d bytes / %d docs.",
                                 data_stream, len(rolled_over), write_index, size, docs)
                return {
                    "weight": polls,
                    "unit": "ops",
                    "success": True,
                    "migrated-indices": len(rolled_over),
                }

            if time.monotonic() >= deadline:
                raise exceptions.BenchmarkError(
                    f"Timed out after {timeout}s waiting for ISM on [{data_stream}]: {len(pending)} backing indices "
                    f"still migrating {pending[:10]}, write index [{write_index}] at {size} bytes / {docs} docs "
                    f"({'over' if over else 'under'} rollover threshold).")

            self.logger.info("Waiting for ISM on [%s]: %d of %d rolled-over indices pending, write index [%s] "
                             "at %d bytes / %d docs (over threshold: %s).",
                             data_stream, len(pending), len(rolled_over), write_index, size, docs, over)
            await asyncio.sleep(poll_interval)

    def __repr__(self, *args, **kwargs):
        return self.RUNNER_NAME


def register(registry):
    registry.register_runner(WaitForIsmWarmMigration.RUNNER_NAME, WaitForIsmWarmMigration(), async_runner=True)

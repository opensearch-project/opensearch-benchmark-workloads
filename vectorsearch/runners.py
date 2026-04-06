# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import logging

from opensearchpy.exceptions import ConnectionTimeout
from osbenchmark.worker_coordinator.runner import Retry, Runner
from osbenchmark.client import RequestContextHolder

from osbenchmark.utils.parse import parse_int_parameter, parse_string_parameter


def register(registry):
    # Warm up api is idempotent, so we can safely retry until complete. This is required
    # so that search can perform without any initial load penalties
    registry.register_runner(
        WarmupIndicesRunner.RUNNER_NAME, Retry(WarmupIndicesRunner(), retry_until_success=True), async_runner=True
    )

request_context_holder = RequestContextHolder()

class WarmupIndicesRunner(Runner):
    """
    WarmupIndicesRunner loads all the native library files for all of the
    shards (primaries and replicas) of all the indexes.
    """
    RUNNER_NAME = "warmup-knn-indices"

    async def __call__(self, opensearch, params):
        index = parse_string_parameter("index", params)
        method = "GET"
        warmup_url = "/_plugins/_knn/warmup/{}".format(index)
        result = {'success': False}
        request_context_holder.on_client_request_start()
        response = await opensearch.transport.perform_request(method, warmup_url)
        request_context_holder.on_client_request_end()
        if response is None or response['_shards'] is None:
            return result
        status = response['_shards']['failed'] == 0
        result['success'] = status
        return result

    def __repr__(self, *args, **kwargs):
        return self.RUNNER_NAME

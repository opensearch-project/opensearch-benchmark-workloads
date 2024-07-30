# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

from osbenchmark.worker_coordinator.runner import Retry, Runner
from osbenchmark.client import RequestContextHolder

# This runner class and registration is a temporary workaround while the next version of OSB is pending release
def register(registry):
    registry.register_runner(
        UpdateConcurrentSegmentSearchSettings.RUNNER_NAME,
                    Retry(UpdateConcurrentSegmentSearchSettings()), async_runner=True
    )

request_context_holder = RequestContextHolder()

class UpdateConcurrentSegmentSearchSettings(Runner):

    RUNNER_NAME = "update-concurrent-segment-search-settings"

    async def __call__(self, opensearch, params):
        enable_setting = params.get("enable", "false")
        max_slice_count = params.get("max_slice_count", None)
        body = {
            "persistent": {
                "search.concurrent_segment_search.enabled": enable_setting
            }
        }
        if max_slice_count is not None:
            body["persistent"]["search.concurrent.max_slice_count"] = max_slice_count
        request_context_holder.on_client_request_start()
        await opensearch.cluster.put_settings(body=body)
        request_context_holder.on_client_request_end()

    def __repr__(self, *args, **kwargs):
        return self.RUNNER_NAME

from copy import copy
import re

from esrally import exceptions
from esrally.workload import loader


def reindex(es, params):
    result = es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))
    return result["total"], "docs"


async def reindex_async(es, params):
    result = await es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))
    return result["total"], "docs"


class RuntimeFieldResolver(loader.WorkloadProcessor):
    PATTERN = re.compile('.+-from-(.+)-using-(.+)')

    def on_after_load_workload(self, t):
        for test_procedure in t.test_procedures:
            for task in test_procedure.schedule:
                m = self.PATTERN.match(task.name)
                if m is not None:
                    source = m[1]
                    impl = m[2].replace('-', '_')
                    task.operation = copy(task.operation)
                    task.operation.params = self._replace_field(f"{impl}.from_{source}.", task.operation.params)

    def on_prepare_workload(self, workload, data_root_dir):
        # TODO remove this backwards compatibility hatch after several Rally releases
        # ref: https://github.com/elastic/rally/pull/1228 and https://github.com/elastic/rally/issues/1166
        class EmptyTrueList(list):
            def __bool__(self):
                return True

            def __eq__(self, other):
                if isinstance(other, bool):
                    return True

        return EmptyTrueList()

    def _replace_field(self, field, t):
        if t == 'path' or t == 'status':
            return field + t
        if isinstance(t, list):
            return [self._replace_field(field, v) for v in t]
        if isinstance(t, dict):
            return {
                self._replace_field(field, k): self._replace_field(field, v)
                for k, v in t.items()
            }
        return t


def register(registry):
    async_runner = registry.meta_data.get("async_runner", False)
    if async_runner:
        registry.register_runner("reindex", reindex_async, async_runner=True)
    else:
        registry.register_runner("reindex", reindex)
    registry.register_workload_processor(RuntimeFieldResolver())
    # TODO change this based on https://github.com/elastic/rally/issues/1257
    try:
        registry.register_workload_processor(loader.DefaultWorkloadPreparator())
    except TypeError as e:
        if e == "__init__() missing 1 required positional argument: 'cfg'":
            pass

# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

from .runners import register as register_runners
from osbenchmark.workload.params import ParamSource
import random
import numpy as np
import logging


def register(registry):
    register_runners(registry)
    # Register random-vector param-sources
    registry.register_param_source("random-vector-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("random-vector-search-param-source", RandomSearchParamSource)


class RandomBulkParamSource(ParamSource):
    def __init__(self, workload, params, **kwargs):
        super().__init__(workload, params, **kwargs)
        logging.getLogger(__name__).info("Workload: [%s], params: [%s]", workload, params)
        self._bulk_size = params.get("bulk-size", 100)
        self._index_name = params.get('index_name','target_index')
        self._field = params.get("field", "target_field")
        self._dims = params.get("dims", 768)
        self._partitions = params.get("partitions", 1000)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        bulk_data = []
        for _ in range(self._bulk_size):
            vec = np.random.rand(self._dims)
            partition_id = random.randint(0, self._partitions)
            metadata = {"_index": self._index_name}
            bulk_data.append({"create": metadata})
            bulk_data.append({"partition_id": partition_id, self._field: vec.tolist()})

        return {
            "body": bulk_data,
            "bulk-size": self._bulk_size,
            "action-metadata-present": True,
            "unit": "docs",
            "index": self._index_name,
            "type": "",
        }

class RandomSearchParamSource(ParamSource):
    def __init__(self, workload, params, **kwargs):
        super().__init__(workload, params, **kwargs)
        logging.getLogger(__name__).info("Workload: [%s], params: [%s]", workload, params)
        self._index_name = params.get('index_name', 'target_index')
        self._dims = params.get("dims", 768)
        self._cache = params.get("cache", False)
        self._top_k = params.get("k", 100)
        self._field = params.get("field", "target_field")
        self._query_body = params.get("body", {})
        self._detailed_results = params.get("detailed-results", False)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query_vec = np.random.rand(self._dims).tolist()
        query = self.generate_knn_query(query_vec)
        query.update(self._query_body)
        return {"index": self._index_name, "cache": self._cache, "size": self._top_k, "body": query, "detailed-results": self._detailed_results}

    def generate_knn_query(self, query_vector):
        return {
            "query": {
                "knn": {
                    self._field: {
                        "vector": query_vector,
                        "k": self._top_k
                    }
                }
            }
        }

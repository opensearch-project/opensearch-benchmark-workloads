# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

from .runners import register as register_runners
from osbenchmark.workload.params import ParamSource
import random
import numpy as np
from sklearn.datasets import make_blobs
import logging


def register(registry):
    register_runners(registry)
    # Register random-vector param-sources
    registry.register_param_source("random-vector-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("random-vector-search-param-source", RandomSearchParamSource)


# Shared cluster centers generated once and reused across all param source instances.
#
# Why make_blobs instead of uniform random?
# Uniform random vectors are approximately equidistant from each other in high-dimensional
# space, meaning there are no natural neighborhoods. Graph-based ANN algorithms like HNSW
# rely on neighborhood structure to build efficient navigable graphs. With uniform data,
# the greedy search cannot prune candidates effectively, resulting in worst-case build times
# and recall numbers that are not representative of real-world workloads.
#
# Why 2000 centers (default)?
# - For 1B vectors: ~500K vectors per cluster — strong density per neighborhood
# - For per-segment graphs (~800K-1.5M docs): 400-750 vectors per cluster per segment,
#   well above HNSW's M parameter (16), ensuring meaningful intra-cluster edges
# - For 1M vectors (default workload): ~500 vectors per cluster — still meaningful structure
# - Real-world embeddings (text, image) naturally cluster by semantic similarity, typically
#   into thousands of distinct topics/categories
#
# Why cluster_std=0.5 (default)?
# - Controls the standard deviation (spread) of points around each cluster center.
#   Smaller values = tighter clusters with more separation between them.
#   Larger values = more spread/overlap between clusters (approaches uniform at very high values).
# - At 0.5 in 768D space with centers spread over [0, 100]:
#   * Points within a cluster are close together (intra-cluster distance is small)
#   * Clusters have slight overlap at boundaries, creating realistic transitions
#   * HNSW can efficiently navigate between clusters via upper-layer long-range edges
#   * Avoids overly isolated clusters that could degrade greedy search between clusters
# - Produces neighborhoods representative of real embedding spaces (text, image, etc.)
#
# Why fixed seed (42)?
# - Ensures all parallel processes/clients generate vectors from the same cluster structure
# - Critical when running with multiple indexing clients (e.g., 200 processes for 1B docs)
_cluster_centers = None


def _get_cluster_centers(dims, num_centers, seed=42):
    """Generate and cache cluster centers so all processes use the same centers."""
    global _cluster_centers
    if _cluster_centers is None or _cluster_centers.shape != (num_centers, dims):
        rng = np.random.RandomState(seed)
        _cluster_centers = rng.rand(num_centers, dims).astype('float32') * 100
    return _cluster_centers


class RandomBulkParamSource(ParamSource):
    def __init__(self, workload, params, **kwargs):
        super().__init__(workload, params, **kwargs)
        logging.getLogger(__name__).info("Workload: [%s], params: [%s]", workload, params)
        self._bulk_size = params.get("bulk-size", 100)
        self._index_name = params.get('index_name', 'target_index')
        self._field = params.get("field", "target_field")
        self._dims = params.get("dims", 768)
        self._partitions = params.get("partitions", 1000)
        self._num_centers = params.get("num_centers", 2000)
        self._cluster_std = params.get("cluster_std", 0.5)
        self._centers = _get_cluster_centers(self._dims, self._num_centers)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        bulk_data = []
        vectors, _ = make_blobs(
            n_samples=self._bulk_size,
            n_features=self._dims,
            centers=self._centers,
            cluster_std=self._cluster_std
        )
        for i in range(self._bulk_size):
            partition_id = random.randint(0, self._partitions)
            metadata = {"_index": self._index_name}
            bulk_data.append({"create": metadata})
            bulk_data.append({"partition_id": partition_id, self._field: vectors[i].tolist()})

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
        self._num_centers = params.get("num_centers", 2000)
        self._cluster_std = params.get("cluster_std", 0.5)
        self._centers = _get_cluster_centers(self._dims, self._num_centers)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        # Generate query vector from the same cluster distribution
        query_vec, _ = make_blobs(
            n_samples=1,
            n_features=self._dims,
            centers=self._centers,
            cluster_std=self._cluster_std
        )
        query_vec = query_vec[0].tolist()
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

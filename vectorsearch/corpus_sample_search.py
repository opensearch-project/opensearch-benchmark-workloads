# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Vector search with query vectors sampled from a data set, without ground truth.

Used by the ``corpus-search`` test procedure. It needs no query set and no
neighbors: when ``query_data_set_path`` and ``query_data_set_corpus`` are both
blank, the queries come from the vectors that were indexed (the ``train`` key of
``target_index_bulk_index_data_set_*``). When a query data set is given, its
``test`` key is used instead. Recall is not calculated.

* ``query_count`` vectors (default 10000) are picked once, uniformly and without
  replacement, as the query pool. The pick is seeded with ``query_seed``, so
  every client and every run with the same seed uses the same pool.
* With a ``time_period``, each client picks pool vectors at random, with
  replacement, until the time is up. Each client has its own seeded sequence.
* Without one, the pool is shuffled and split across the clients (shares differ
  by at most one vector), and each vector is sent once per repetition (``repetitions``, default 1), so the step
  sends exactly ``query_count * repetitions`` queries.
* ``query_noise`` (default 0) adds Gaussian noise to each query: per component
  ``sigma = query_noise * |v| / sqrt(d)``, so the noise vector's expected norm is
  ``query_noise`` times the query's norm. For ``cosinesimil`` and
  ``innerproduct`` the noisy vector is scaled back to ``|v|``. Integer vectors are
  rounded and clipped to their type's range. Noise is refused for ``hamming``.

A ``query_body`` that contains a ``query`` is sent as written, with the vector
placed into every ``knn`` clause on the operation's field (as in
``raw_search_body.py``). Otherwise the stock k-NN query is built.
"""

import copy
import logging
import math

import numpy as np

from osbenchmark import exceptions
from osbenchmark.utils.dataset import Context, get_data_set
from osbenchmark.workload.params import SearchParamSource, VectorSearchPartitionParamSource

from .raw_search_body import _get, validate_search_body

DEFAULT_POOL_SIZE = 10000
NORM_PRESERVING_SPACES = ("cosinesimil", "innerproduct")

# One pool per (file, key, size, seed) per worker process, shared by that process's clients.
_POOLS = {}


def resolve_query_source(params):
    """Return (params, context) with data_set_* naming the file the queries come from.

    A blank query data set means the indexed vectors: the corpus_data_set_* params
    (the bulk index data set) under the ``train`` key."""
    params = dict(params)
    if params.get("data_set_path") or params.get("data_set_corpus"):
        return params, Context.QUERY
    for key in ("format", "path", "corpus"):
        params[f"data_set_{key}"] = params.get(f"corpus_data_set_{key}") or (
            "hdf5" if key == "format" else "")
    if not params["data_set_path"] and not params["data_set_corpus"]:
        raise exceptions.ConfigurationError(
            "corpus-search needs a data set to sample queries from: set "
            "target_index_bulk_index_data_set_path or _corpus (or query_data_set_path or _corpus).")
    return params, Context.INDEX


def pick_pool_indices(size, pool_size, seed):
    """Sorted, distinct row numbers of the pool; all rows when pool_size is < 0 or >= size."""
    if pool_size < 0 or pool_size >= size:
        return np.arange(size)
    return np.sort(np.random.default_rng(seed).choice(size, size=pool_size, replace=False))


def load_pool(data_set_format, path, context, pool_size, seed):
    key = (data_set_format, path, context, pool_size, seed)
    if key not in _POOLS:
        data_set = get_data_set(data_set_format, path, context)
        indices = pick_pool_indices(data_set.size(), pool_size, seed)
        data = getattr(data_set, "data", None)
        if data is not None and hasattr(data, "id"):   # h5py: one read of the sorted rows
            pool = np.asarray(data[:] if len(indices) == data_set.size() else data[indices])
        else:
            rows = []
            for i in indices:
                data_set.seek(int(i))
                rows.append(data_set.read(1)[0])
            pool = np.asarray(rows)
        logging.getLogger(__name__).info(
            "corpus-search pool: %d of %d vectors from [%s] (%s), seed %d, first rows %s",
            len(pool), data_set.size(), path, context.name, seed, indices[:5].tolist())
        _POOLS[key] = pool
    return _POOLS[key]


def add_noise(vector, noise, rng, keep_norm):
    """vector plus N(0, sigma) per component, sigma = noise * |vector| / sqrt(d)."""
    v = np.asarray(vector, dtype=np.float32)
    if noise <= 0:
        return vector
    norm = float(np.linalg.norm(v))
    if norm == 0:
        return vector
    out = v + rng.normal(0.0, noise * norm / math.sqrt(v.shape[0]), v.shape[0]).astype(np.float32)
    if keep_norm:
        out_norm = float(np.linalg.norm(out))
        if out_norm > 0:
            out *= norm / out_norm
    dtype = np.asarray(vector).dtype
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        out = np.clip(np.rint(out), info.min, info.max).astype(dtype)
    return out


class CorpusSampleVectorSearchParamSource(SearchParamSource):
    """``vector-search`` operation whose queries are sampled from a data set, without recall."""

    def __init__(self, workload, params, **kwargs):
        super().__init__(workload, params, **kwargs)
        self.delegate_param_source = CorpusSamplePartitionParamSource(workload, params, self.query_params, **kwargs)
        self.corpora = self.delegate_param_source.corpora

    def partition(self, partition_index, total_partitions):
        return self.delegate_param_source.partition(partition_index, total_partitions)

    def params(self):
        raise exceptions.WorkloadConfigError("Do not use a CorpusSampleVectorSearchParamSource without partitioning")


class CorpusSamplePartitionParamSource(VectorSearchPartitionParamSource):
    def __init__(self, workload, params, query_params, **kwargs):
        params, context = resolve_query_source(params)
        for key in ("neighbors_data_set_path", "neighbors_data_set_corpus"):
            params.pop(key, None)                      # no ground truth: recall is off
        if params.get("num_vectors") is None:
            params["num_vectors"] = DEFAULT_POOL_SIZE
        body = params.get(self.PARAMS_NAME_BODY)
        self._raw_body = None
        if isinstance(body, dict) and "query" in body:
            if not params.get("field"):
                raise exceptions.InvalidSyntax("'field' is mandatory with 'query_body'.")
            self._vector_paths, clause_k = validate_search_body(body, params["field"])
            if self.PARAMS_NAME_K not in params:
                if clause_k is None:
                    raise exceptions.InvalidSyntax("No 'k' in the knn clause or on the operation.")
                params[self.PARAMS_NAME_K] = clause_k
            elif clause_k is not None and int(params[self.PARAMS_NAME_K]) != int(clause_k):
                raise exceptions.InvalidSyntax(
                    f"Operation k={params[self.PARAMS_NAME_K]} (query_k) differs from the knn clause's "
                    f"k={clause_k}; set query_k to {clause_k} or drop it.")
            self._raw_body = copy.deepcopy(body)
        super().__init__(workload, params, query_params, **kwargs)
        self.context = context
        self.timed = bool(params.get("timed", False))
        self.seed = int(params.get("query_seed", 1))
        try:
            self.noise = float(params.get("query_noise", 0) or 0)
        except (TypeError, ValueError):
            raise exceptions.InvalidSyntax(f"query_noise must be a number >= 0, got {params.get('query_noise')!r}")
        if self.noise < 0 or math.isnan(self.noise):
            raise exceptions.InvalidSyntax(f"query_noise must be a number >= 0, got {params.get('query_noise')!r}")
        space_type = str(params.get("space_type") or "").lower()
        if self.noise > 0 and space_type == "hamming":
            raise exceptions.InvalidSyntax("query_noise is not supported for binary (hamming) vectors; set it to 0.")
        self.keep_norm = space_type in NORM_PRESERVING_SPACES
        self.query_params["calculate-recall"] = False
        self.query_params.pop("neighbors", None)

        self._pool = None
        self._rng = None
        self._order = None
        self._pos = 0

    @property
    def infinite(self):
        return self.timed

    def partition(self, partition_index, total_partitions):
        if self.data_set_corpus and not self.data_set_path:
            paths = self._get_corpora_file_paths(self.data_set_corpus, self.data_set_format)
            self._validate_data_set_corpus(paths)
            self.data_set_path = paths[0]
        pool = load_pool(self.data_set_format, self.data_set_path, self.context, self.total_num_vectors, self.seed)

        p = copy.copy(self)
        p._pool = pool
        p._rng = np.random.default_rng([self.seed, partition_index + 1])
        p.current = 0
        p.current_rep = 1
        if not self.timed:
            order = np.random.default_rng([self.seed, 0]).permutation(len(pool))
            # near-equal shares: the first len(pool) % total_partitions clients get one vector more
            base, extra = divmod(len(pool), total_partitions)
            start = partition_index * base + min(partition_index, extra)
            end = start + base + (1 if partition_index < extra else 0)
            p._order = order[start:end].copy()
            p._pos = 0
            p.total = len(p._order) * self.repetitions
        return p

    def _next_index(self):
        if self.timed:
            return int(self._rng.integers(len(self._pool)))
        if self._pos >= len(self._order):
            if self.current_rep >= self.repetitions or len(self._order) == 0:
                raise StopIteration
            self.current_rep += 1
            self._rng.shuffle(self._order)
            self._pos = 0
        i = int(self._order[self._pos])
        self._pos += 1
        return i

    def params(self):
        vector = add_noise(self._pool[self._next_index()], self.noise, self._rng, self.keep_norm)
        self._update_request_params()
        if self._raw_body is not None:
            body = copy.deepcopy(self._raw_body)
            for path in self._vector_paths:
                _get(body, path)["vector"] = vector
            self.query_params.update({self.PARAMS_NAME_BODY: body})
        else:
            self._update_body_params(vector)
        self.current += 1
        if not self.timed and self.total:
            self.task_progress = (self.current / self.total, '%')
        return self.query_params

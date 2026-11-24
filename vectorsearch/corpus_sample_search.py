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
  by at most one vector), and each vector is sent once per repetition
  (``repetitions``, default 1), so the step sends exactly
  ``query_count * repetitions`` queries.

A ``query_body`` that contains a ``query`` is sent as written, with the vector
placed into every ``knn`` clause on the operation's field (as in
``raw_search_body.py``). Otherwise the stock k-NN query is built.

``query_profile`` picks how the queries are made (``query_profile.py``):

* ``prod`` (default): traffic shaped like real users. Up to 1,000 topics from the
  test queries (the query data set's, else the bulk data set's ``test`` key, filled
  from the indexed vectors), popular topics picked far more often, each query
  nudged slightly. Without a ``time_period`` the step sends ``query_count`` such
  queries, split across the clients as above; with one, each client makes its own.
* ``uniform``: the pool described above, every vector equally likely: the worst
  case for memory.
"""

import copy
import logging
import time

import numpy as np

from osbenchmark import exceptions
from osbenchmark.utils.dataset import Context, get_data_set
from osbenchmark.workload.params import SearchParamSource, VectorSearchPartitionParamSource

from . import query_profile as qp
from .raw_search_body import _get, validate_search_body

DEFAULT_POOL_SIZE = 10000

# One pool per (file, key, size, seed) per worker process, shared by that process's clients.
_POOLS = {}
# One prod profile per (files, seed, exponent, space) per worker process, and its fixed-count query sets.
_PROFILES = {}
_PROD_POOLS = {}


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


def read_rows(data_set, indices):
    """The rows at ``indices`` (sorted, distinct) of a data set."""
    data = getattr(data_set, "data", None)
    if data is not None and hasattr(data, "id"):       # h5py: one read of the sorted rows
        return np.asarray(data[:] if len(indices) == data_set.size() else data[indices])
    rows = []
    for i in indices:
        data_set.seek(int(i))
        rows.append(data_set.read(1)[0])
    return np.asarray(rows)


def open_data_set(data_set_format, path, context):
    """The data set, or None when the file has no such key (a data set without test queries or neighbors)."""
    try:
        data_set = get_data_set(data_set_format, path, context)
        return data_set if data_set.size() > 0 else None
    except Exception:                                  # noqa: BLE001 - a missing key surfaces as different errors
        return None


def load_prod(query_file, train_file, seed, exponent, space_type):
    """The prod profile for these files: topics from ``query_file``'s test key (filled from ``train_file``'s
    train key), d10 from its neighbors, else estimated on a sample of the indexed vectors. Each is
    (format, path)."""
    key = (query_file, train_file, seed, exponent, space_type)
    if key in _PROFILES:
        return _PROFILES[key]
    log = logging.getLogger(__name__)
    rng = np.random.default_rng([seed, 5])
    test = open_data_set(*query_file, Context.QUERY)
    train = open_data_set(*train_file, Context.INDEX)
    topics, rows, source = [], np.array([], dtype=np.int64), []
    if test is not None:
        rows = np.sort(rng.choice(test.size(), size=min(qp.TOPICS, test.size()), replace=False))
        topics.append(read_rows(test, rows))
        source.append("test")
    if len(rows) < qp.TOPICS and train is not None:
        fill = np.sort(rng.choice(train.size(), size=min(qp.TOPICS - len(rows), train.size()), replace=False))
        topics.append(read_rows(train, fill))
        source.append("train")
    if not topics:
        raise exceptions.ConfigurationError(
            f"query_profile prod: no test queries in [{query_file[1]}] and no indexed vectors in [{train_file[1]}]")
    topics = np.concatenate(topics).astype(np.float32)

    d10, d10_source = None, None
    neighbors = open_data_set(*query_file, Context.NEIGHBORS) if test is not None else None
    if neighbors is not None and train is not None and neighbors.size() == test.size():
        sel = rows[:qp.D10_QUERIES]
        tenth_ids = read_rows(neighbors, sel)[:, 9].astype(np.int64)
        ok = (tenth_ids >= 0) & (tenth_ids < train.size())
        if ok.any():
            order = np.argsort(tenth_ids[ok])
            uniq, inv = np.unique(tenth_ids[ok][order], return_inverse=True)
            vec = read_rows(train, uniq)[inv]
            tenth = np.empty_like(vec)
            tenth[order] = vec
            d10, d10_source = qp.d10_from_neighbors(topics[:len(sel)][ok], tenth), "neighbors"
    if d10 is None:
        if train is None:
            raise exceptions.ConfigurationError(
                f"query_profile prod: no neighbors in [{query_file[1]}] and no indexed vectors to estimate d10")
        sample = np.sort(rng.choice(train.size(), size=min(qp.D10_SAMPLE, train.size()), replace=False))
        d10, d10_source = qp.d10_estimate(topics[:qp.D10_QUERIES], read_rows(train, sample)), "sample"
    prof = qp.Prod(topics, d10, seed, exponent, space_type)
    settings = dict(prof.settings(), topic_source="+".join(source), d10_source=d10_source, space_type=space_type)
    log.info("corpus-search query profile: %s", settings)
    _PROFILES[key] = prof
    return prof


def load_prod_pool(prof, count):
    """``count`` prod queries for a step without a time_period: the same for every client and run."""
    key = (id(prof), count)
    if key not in _PROD_POOLS:
        _PROD_POOLS[key] = prof.queries(np.random.default_rng([prof.seed, 0]), count)
    return _PROD_POOLS[key]


def load_pool(data_set_format, path, context, pool_size, seed):
    key = (data_set_format, path, context, pool_size, seed)
    if key not in _POOLS:
        data_set = get_data_set(data_set_format, path, context)
        indices = pick_pool_indices(data_set.size(), pool_size, seed)
        pool = read_rows(data_set, indices)
        logging.getLogger(__name__).info(
            "corpus-search pool: %d of %d vectors from [%s] (%s), seed %d, first rows %s",
            len(pool), data_set.size(), path, context.name, seed, indices[:5].tolist())
        _POOLS[key] = pool
    return _POOLS[key]


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
        self.has_query_set = bool(params.get("data_set_path") or params.get("data_set_corpus"))
        corpus = (params.get("corpus_data_set_format") or "hdf5", params.get("corpus_data_set_path") or "",
                  params.get("corpus_data_set_corpus") or "")
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
        if self.seed < 0:
            raise exceptions.InvalidSyntax(f"query_seed must be a whole number >= 0, got {self.seed}")
        self.query_params["calculate-recall"] = False
        self.query_params.pop("neighbors", None)

        self.profile = str(params.get("query_profile") or qp.DEFAULT_PROFILE).lower()
        if self.profile not in qp.PROFILES:
            raise exceptions.InvalidSyntax(
                f"query_profile must be one of {', '.join(qp.PROFILES)}, got {params.get('query_profile')!r}")
        try:
            self.exponent = qp.exponent(params.get("query_concentration"))
        except ValueError as e:
            raise exceptions.InvalidSyntax(str(e))
        self.space_type = str(params.get("query_space_type") or "l2")
        self.time_period = float(params.get("time_period") or 0)
        if self.profile == "prod" and self.total_num_vectors < 0:
            raise exceptions.InvalidSyntax("query_count -1 (the whole data set) is for query_profile uniform; "
                                           "set a number of queries for prod")
        self.corpus = corpus
        if self.profile == "prod" and self.has_query_set and corpus[2] and not corpus[1]:
            # the indexed vectors fill topics and estimate d10: make the named corpus available too
            extra = self.extract_corpora(corpus[2], corpus[0])
            self.corpora.extend(c for c in extra if c not in self.corpora)

        self._pool = None
        self._prod = None
        self._buf = None
        self._t0 = None
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
        prof = None
        if self.profile == "prod":
            train = (self.corpus[0], self.corpus[1])
            if not self.has_query_set:
                train = (self.data_set_format, self.data_set_path)    # the bulk data set: test and train keys
            elif not train[1] and self.corpus[2]:
                paths = self._get_corpora_file_paths(self.corpus[2], self.corpus[0])
                train = (self.corpus[0], paths[0] if paths else "")
            prof = load_prod((self.data_set_format, self.data_set_path), train, self.seed, self.exponent,
                             self.space_type)
            pool = None if self.timed else load_prod_pool(prof, self.total_num_vectors)
        else:
            pool = load_pool(self.data_set_format, self.data_set_path, self.context, self.total_num_vectors, self.seed)

        p = copy.copy(self)
        p._prod = prof
        p._buf = None
        p._t0 = None
        p.partition_index = partition_index           # the client's index in the task (read by shape_scheduler.py)
        p._pool = pool
        p._rng = np.random.default_rng([self.seed, partition_index + 1])
        p.current = 0
        p.current_rep = 1
        if not self.timed:
            order = np.random.default_rng([self.seed, 0]).permutation(len(pool))   # prod: already random
            # near-equal shares: the first len(pool) % total_partitions clients get one vector more
            base, extra = divmod(len(pool), total_partitions)
            start = partition_index * base + min(partition_index, extra)
            end = start + base + (1 if partition_index < extra else 0)
            p._order = order[start:end].copy()
            p._pos = 0
            p.total = len(p._order) * self.repetitions
        return p

    def _next_prod(self):
        """A timed step's next prod query: made in batches by this client, the batch's drift period from the
        time since the client's first query."""
        if not self._buf:
            now = time.monotonic()
            self._t0 = self._t0 or now
            epoch = qp.drift_epoch(now - self._t0, self.time_period)
            self._buf = list(self._prod.queries(self._rng, 64, epoch))
        return self._buf.pop(0)

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
        vector = self._next_prod() if (self.timed and self._prod is not None) else self._pool[self._next_index()]
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

# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Vector search with the whole ``_search`` body supplied as ``body`` (``query_body``).

The stock ``vector-search`` param source rebuilds the knn clause from a fixed
set of params (``k``, ``oversample_factor``, filter params, ...), so any query
option without a param of its own (``rescore: false``, ``expand_nested_docs``,
``method_parameters`` other than what the index template sets, extra clauses)
cannot be benchmarked without a code change.

When ``query_body`` contains a ``query``, the search schedules switch to
``RawBodyVectorSearchParamSource``, which sends that body exactly as written.
A ``query_body`` without ``query`` (only ``size``, ``_source``, ...) keeps the
stock behaviour. The only change per request is the query vector:
it replaces ``vector`` in every ``knn`` clause on the operation's ``field``.
Ground-truth neighbors and recall work as in the stock source; ``k`` for
recall is read from the knn clause unless the operation sets it explicitly.
"""

import copy

from osbenchmark import exceptions
from osbenchmark.workload.params import VectorSearchParamSource, VectorSearchPartitionParamSource

PARAM_BODY = "body"
PARAM_FIELD = "field"
PARAM_K = "k"
_RADIAL_KEYS = ("max_distance", "min_score")


def find_knn_vector_paths(node, field_name, path=()):
    """Return the key paths of every ``knn.<field_name>`` clause in ``node``."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "knn" and isinstance(value, dict) and isinstance(value.get(field_name), dict):
                found.append(path + (key, field_name))
            found.extend(find_knn_vector_paths(value, field_name, path + (key,)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(find_knn_vector_paths(value, field_name, path + (index,)))
    return found


def _get(node, path):
    for key in path:
        node = node[key]
    return node


def validate_search_body(search_body, field_name):
    """Check the body can be benchmarked and return (knn clause paths, k)."""
    if not isinstance(search_body, dict):
        raise exceptions.InvalidSyntax(
            f"'query_body' must be a JSON object, got {type(search_body).__name__}.")
    paths = find_knn_vector_paths(search_body, field_name)
    if not paths:
        raise exceptions.InvalidSyntax(
            f"'query_body' has no knn clause on field '{field_name}'.")
    k_values = set()
    for path in paths:
        clause = _get(search_body, path)
        if "vector" not in clause:
            raise exceptions.InvalidSyntax(
                f"knn clause at '{'.'.join(map(str, path))}' has no 'vector' to replace.")
        radial = [key for key in _RADIAL_KEYS if key in clause]
        if radial:
            raise exceptions.InvalidSyntax(
                f"knn clause at '{'.'.join(map(str, path))}' uses {radial}; radial search is not "
                f"supported with 'query_body' yet. Use the stock params instead.")
        if "k" in clause:
            k_values.add(clause["k"])
    if len(k_values) > 1:
        raise exceptions.InvalidSyntax(
            f"knn clauses on '{field_name}' use different k values {sorted(k_values)}; set 'k' on the "
            f"operation to say which one recall is computed at.")
    return paths, (k_values.pop() if k_values else None)


class RawBodyVectorSearchParamSource(VectorSearchParamSource):
    """``vector-search`` operation whose request body is ``query_body`` verbatim."""

    def __init__(self, workload, params, **kwargs):
        field_name = params.get(PARAM_FIELD)
        if not field_name:
            raise exceptions.InvalidSyntax(f"'{PARAM_FIELD}' is mandatory with 'query_body'.")
        if PARAM_BODY not in params:
            raise exceptions.InvalidSyntax(f"'query_body' is mandatory for this param source.")
        for conflicting in ("filter_type", "filter_body", "oversample_factor", "radial_search_type",
                            "max_distance", "min_score"):
            if params.get(conflicting):
                raise exceptions.InvalidSyntax(
                    f"'{conflicting}' cannot be combined with 'query_body'; "
                    f"put it in the body instead.")
        search_body = params[PARAM_BODY]
        paths, clause_k = validate_search_body(search_body, field_name)
        params = dict(params)
        if PARAM_K not in params:
            if clause_k is None:
                raise exceptions.InvalidSyntax(
                    "No 'k' in the knn clause or on the operation; recall needs one.")
            params[PARAM_K] = clause_k
        elif clause_k is not None and int(params[PARAM_K]) != int(clause_k):
            raise exceptions.InvalidSyntax(
                f"Operation k={params[PARAM_K]} (query_k) differs from the knn clause's k={clause_k}; "
                f"recall would be computed at the wrong depth. Set query_k to {clause_k} or drop it.")
        super().__init__(workload, params, **kwargs)
        self.delegate_param_source = RawBodyVectorSearchPartitionParamSource(
            workload, params, self.query_params, search_body=search_body, vector_paths=paths, **kwargs)
        self.corpora = self.delegate_param_source.corpora


class RawBodyVectorSearchPartitionParamSource(VectorSearchPartitionParamSource):
    def __init__(self, workloads, params, query_params, search_body, vector_paths, **kwargs):
        super().__init__(workloads, params, query_params, **kwargs)
        self._search_body = copy.deepcopy(search_body)
        self._vector_paths = vector_paths

    def _update_body_params(self, vector):
        body = copy.deepcopy(self._search_body)
        for path in self._vector_paths:
            # Same value type the stock source sends, so request serialization cost is unchanged.
            _get(body, path)["vector"] = vector
        self.query_params.update({self.PARAMS_NAME_BODY: body})


class FullBodyUnsupportedParamSource:
    """Fails fast on search operations that build their own query from params.

    The filter-percentage sweep generates a different filter per operation and the
    gRPC operation encodes the query as protobuf, so a full ``query_body`` would be
    replaced without notice. The schedules select this source only when
    ``query_body`` contains a ``query``.
    """

    def __init__(self, workload, params, **kwargs):
        raise exceptions.InvalidSyntax(
            f"Operation '{params.get('name', kwargs.get('operation_name'))}' builds its own query and cannot "
            f"send a full 'query_body' (one containing 'query'). Use the stock query params, or run the "
            f"search-only / no-train-test procedures.")

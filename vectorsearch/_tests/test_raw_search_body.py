# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Unit tests for vectorsearch/raw_search_body.py.

Lives in _tests/ because OSB imports every module under the workload directory except
directories starting with '_', and this file needs pytest.

Run from the repository root:  pip install opensearch-benchmark h5py pytest && pytest vectorsearch/_tests
"""
import importlib.util
import json
import os
import tempfile

import h5py
import numpy as np
import pytest

from osbenchmark import exceptions

WL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw_search_body.py")
spec = importlib.util.spec_from_file_location("raw_search_body", WL)
rsb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rsb)


class FakeWorkload:
    corpora = []
    indices = []
    data_streams = []


@pytest.fixture(scope="module")
def dataset():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "ds.hdf5")
    rng = np.random.default_rng(0)
    with h5py.File(p, "w") as f:
        f["train"] = rng.random((20, 4), dtype=np.float32)
        f["test"] = rng.random((5, 4), dtype=np.float32)
        f["neighbors"] = np.tile(np.arange(10), (5, 1)).astype(np.int64)
    return p


BODY = {
    "size": 100,
    "docvalue_fields": ["_id"],
    "stored_fields": "_none_",
    "_source": False,
    "query": {"knn": {"target_field": {"vector": [0], "k": 3, "rescore": False,
                                       "method_parameters": {"ef_search": 256}}}},
}


def params_for(ds, search_body, **extra):
    p = {"index": "target_index", "field": "target_field", "data_set_format": "hdf5",
         "data_set_path": ds, "neighbors_data_set_path": ds, "neighbors_data_set_format": "hdf5",
         "num_vectors": -1, "id-field-name": "_id", "filter_body": {}, "filter_type": {},
         "repetitions": 1, "detailed-results": True, "body": search_body}
    p.update(extra)
    return p


def make(ds, search_body, **extra):
    return rsb.RawBodyVectorSearchParamSource(FakeWorkload(), params_for(ds, search_body, **extra),
                                              operation_name="prod-queries")


def test_body_sent_verbatim_except_vector(dataset):
    src = make(dataset, BODY).partition(0, 1)
    with h5py.File(dataset) as f:
        queries = f["test"][:]
    for i in range(5):
        out = src.params()
        body = out["body"]
        clause = body["query"]["knn"]["target_field"]
        np.testing.assert_array_equal(np.asarray(clause["vector"]), queries[i])
        # everything else identical to the input, including rescore: false
        expected = json.loads(json.dumps(BODY))
        got = dict(body)
        got["query"] = {"knn": {"target_field": {k: v for k, v in clause.items() if k != "vector"}}}
        del expected["query"]["knn"]["target_field"]["vector"]
        assert got == expected
        assert out["k"] == 3
        assert out["neighbors"] == ["0", "1", "2"]
    with pytest.raises(StopIteration):
        src.params()
    # template not mutated across requests
    assert BODY["query"]["knn"]["target_field"]["vector"] == [0]


def test_multiple_clauses_all_substituted(dataset):
    body = {"size": 3, "query": {"bool": {"should": [
        {"knn": {"target_field": {"vector": [0], "k": 3}}},
        {"knn": {"target_field": {"vector": [0], "k": 3, "filter": {"term": {"a": 1}}}}}]}}}
    out = make(dataset, body).partition(0, 1).params()
    for clause in out["body"]["query"]["bool"]["should"]:
        assert len(clause["knn"]["target_field"]["vector"]) == 4
    assert out["body"]["query"]["bool"]["should"][1]["knn"]["target_field"]["filter"] == {"term": {"a": 1}}


def test_explicit_k_matching(dataset):
    assert make(dataset, BODY, k=3).partition(0, 1).params()["k"] == 3


@pytest.mark.parametrize("body,extra,msg", [
    ({"query": {"match_all": {}}}, {}, "no knn clause"),
    ({"query": {"knn": {"target_field": {"k": 3}}}}, {}, "no 'vector'"),
    ({"query": {"knn": {"target_field": {"vector": [0]}}}}, {}, "No 'k'"),
    ({"query": {"knn": {"target_field": {"vector": [0], "max_distance": 1.0}}}}, {}, "radial"),
    (BODY, {"k": 100}, "differs"),
    (BODY, {"oversample_factor": 2}, "cannot be combined"),
    ("not-a-dict", {}, "JSON object"),
])
def test_rejections(dataset, body, extra, msg):
    with pytest.raises(exceptions.InvalidSyntax, match=msg):
        make(dataset, body, **extra)


def test_full_body_unsupported_source_fails():
    with pytest.raises(exceptions.InvalidSyntax, match="builds its own query"):
        rsb.FullBodyUnsupportedParamSource(FakeWorkload(), {"name": "grpc-prod-queries"})

# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Query profiles (prod, uniform) for corpus-search and shaped-search.

Run from the repository root: python -m unittest vectorsearch._tests.test_query_profile
"""
import os
import tempfile
import unittest
from types import SimpleNamespace

import h5py
import numpy as np

from osbenchmark import exceptions
from vectorsearch import corpus_sample_search as css
from vectorsearch import query_profile as qp


class Popularity(unittest.TestCase):
    def test_shares_of_1000_topics(self):
        self.assertAlmostEqual(qp.top_share(1000, 1.0, 0.1), 0.693, places=3)    # top 10%: about 70%
        self.assertAlmostEqual(qp.top_share(1000, 1.0, 0.01), 0.391, places=3)   # top 10 topics
        self.assertAlmostEqual(qp.top_share(1000, 1.0, 0.001), 0.134, places=3)  # the most popular one
        self.assertAlmostEqual(qp.top_share(1000, 0.7, 0.1), 0.44, places=2)
        self.assertAlmostEqual(qp.top_share(1000, 1.3, 0.1), 0.88, places=2)

    def test_concentration(self):
        self.assertEqual([qp.exponent(c) for c in (None, "low", "medium", "HIGH")], [1.0, 0.7, 1.0, 1.3])
        with self.assertRaises(ValueError):
            qp.exponent("extreme")

    def test_sampled_ranks_follow_the_shares(self):
        prof = qp.Prod(np.zeros((1000, 4)), 1.0, seed=1)
        ranks = prof.ranks(np.random.default_rng(3), 200000)
        self.assertAlmostEqual(float((ranks < 100).mean()), 0.693, delta=0.01)
        self.assertEqual((int(ranks.min()), int(ranks.max()) < 1000), (0, True))


class Queries(unittest.TestCase):
    def setUp(self):
        self.topics = np.random.default_rng(0).normal(size=(1000, 64)).astype(np.float32)

    def test_same_seed_same_queries(self):
        a = qp.Prod(self.topics, 2.0, seed=1).queries(np.random.default_rng([1, 1]), 500)
        b = qp.Prod(self.topics, 2.0, seed=1).queries(np.random.default_rng([1, 1]), 500)
        c = qp.Prod(self.topics, 2.0, seed=2).queries(np.random.default_rng([2, 1]), 500)
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, c))

    def test_noise_is_about_three_tenths_of_d10(self):
        prof = qp.Prod(self.topics, 2.0, seed=1)
        rng = np.random.default_rng(5)
        ranks = prof.ranks(np.random.default_rng(5), 2000)
        q = prof.queries(rng, 2000)
        base = self.topics[prof.order[ranks]]
        self.assertAlmostEqual(float(np.median(np.linalg.norm(q - base, axis=1))), 0.3 * 2.0, delta=0.05)
        self.assertEqual(q.dtype, np.float32)

    def test_cosine_queries_are_unit_length(self):
        q = qp.Prod(self.topics, 2.0, seed=1, space_type="cosinesimil").queries(np.random.default_rng(1), 100)
        np.testing.assert_allclose(np.linalg.norm(q, axis=1), 1.0, rtol=1e-5)

    def test_drift_rotates_a_tenth_of_the_topics(self):
        self.assertEqual([qp.drift_epoch(t, 3600) for t in (0, 1800, 5000)], [0, 0, 0])   # not over an hour
        self.assertEqual([qp.drift_epoch(t, 7200) for t in (0, 1799, 1800, 5400)], [0, 0, 1, 3])
        prof = qp.Prod(np.arange(1000, dtype=np.float32)[:, None] * np.ones((1, 4), np.float32), 0.0, seed=1)
        top = lambda epoch: prof.queries(np.random.default_rng(9), 1, epoch)[0][0]
        self.assertEqual(top(0), prof.order[prof.ranks(np.random.default_rng(9), 1)[0]])
        self.assertEqual(top(1), np.roll(prof.order, -100)[prof.ranks(np.random.default_rng(9), 1)[0]])

    def test_d10_estimate_on_a_line(self):
        # points 0, 1, ..., 99 on a line: the 10th nearest of point 50 (itself first) is 5 away
        x = np.arange(100, dtype=np.float32)[:, None]
        self.assertAlmostEqual(qp.d10_estimate(np.array([[50.0]]), x), 5.0)
        self.assertAlmostEqual(qp.d10_from_neighbors([[0, 0]], [[3, 4]]), 5.0)


def data_set(path, n_train=5000, n_test=300, dim=16, neighbors=True):
    rng = np.random.default_rng(0)
    train = rng.normal(size=(n_train, dim)).astype(np.float32)
    with h5py.File(path, "w") as f:
        f.create_dataset("train", data=train)
        if n_test:
            test = rng.normal(size=(n_test, dim)).astype(np.float32)
            f.create_dataset("test", data=test)
            if neighbors:
                d = ((test[:, None, :] - train[None, :, :]) ** 2).sum(-1)
                f.create_dataset("neighbors", data=np.argsort(d, axis=1)[:, :20].astype(np.int32))
    return train


class ParamSource(unittest.TestCase):
    """The operation params as corpus-search-schedule.json renders them, on a small HDF5 data set."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "ds.hdf5")
        css._POOLS.clear()
        css._PROFILES.clear()
        css._PROD_POOLS.clear()

    def tearDown(self):
        for f in os.listdir(self.dir):
            os.unlink(os.path.join(self.dir, f))
        os.rmdir(self.dir)

    def source(self, **kw):
        params = {"index": "target_index", "field": "target_field", "k": 10, "data_set_format": "hdf5",
                  "data_set_path": "", "data_set_corpus": "", "corpus_data_set_format": "hdf5",
                  "corpus_data_set_path": self.path, "corpus_data_set_corpus": "", "num_vectors": 1000,
                  "repetitions": 1, "query_seed": 1, "body": {}}
        params.update(kw)
        return css.CorpusSampleVectorSearchParamSource(SimpleNamespace(corpora=[], indices=[], data_streams=[]), params)

    def vectors(self, src, clients=1, n=None):
        out = []
        for i in range(clients):
            p = src.partition(i, clients)
            for _ in range(n or 10 ** 9):
                try:
                    out.append(np.asarray(p.params()["body"]["query"]["knn"]["target_field"]["vector"]))
                except StopIteration:
                    break
        return np.array(out)

    def test_prod_is_the_default_and_sends_query_count_queries(self):
        data_set(self.path)
        q = self.vectors(self.source(), clients=3)
        self.assertEqual(len(q), 1000)
        prof = next(iter(css._PROFILES.values()))
        self.assertEqual(prof.k, 1000)                 # all 300 test queries, filled with 700 indexed vectors
        train, test = h5py.File(self.path)["train"][:], h5py.File(self.path)["test"][:]
        tenth = h5py.File(self.path)["neighbors"][:, 9]
        rows = np.sort(np.random.default_rng([1, 5]).choice(300, size=300, replace=False))[:200]
        want = float(np.median(np.linalg.norm(test[rows] - train[tenth[rows]], axis=1)))
        self.assertAlmostEqual(prof.d10, want, places=5)               # from the data set's neighbors
        np.testing.assert_array_equal(q, self.vectors(self.source(), clients=3))   # repeatable

    def test_prod_topics_are_filled_from_the_index_without_neighbors(self):
        data_set(self.path, neighbors=False)
        self.vectors(self.source(num_vectors=50))
        prof = next(iter(css._PROFILES.values()))
        self.assertEqual(prof.k, 1000)                                 # 300 test + 700 indexed vectors
        self.assertGreater(prof.d10, 0)                                # estimated on a sample

    def test_prod_timed_runs_until_stopped(self):
        data_set(self.path)
        self.assertEqual(len(self.vectors(self.source(timed=True, time_period=600), n=200)), 200)

    def test_uniform_is_the_old_pool(self):
        train = data_set(self.path)
        q = self.vectors(self.source(query_profile="uniform", num_vectors=100))
        self.assertEqual(len(q), 100)
        rows = {tuple(r) for r in train}
        self.assertTrue(all(tuple(v) in rows for v in q))             # every query is an indexed vector

    def test_bad_settings_are_refused(self):
        data_set(self.path)
        with self.assertRaises(exceptions.InvalidSyntax):
            self.source(query_profile="zipf")
        with self.assertRaises(exceptions.InvalidSyntax):
            self.source(query_concentration="extreme")
        with self.assertRaises(exceptions.InvalidSyntax):
            self.source(num_vectors=-1)


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

"""Query profiles for corpus-search and shaped-search: ``prod`` (traffic shaped like real users) and
``uniform`` (every vector of the pool equally likely: a worst case).

``prod`` builds its queries from a fixed set of topics:

* **Topics.** Up to ``TOPICS`` query vectors (the data set's test queries, filled from the indexed vectors
  when there are fewer). They are shuffled once with the seed; the order after the shuffle is the popularity
  order.
* **Popularity.** The topic at position r (1 = most popular) is picked with probability proportional to
  1 / r^s (a Zipf distribution). With 1,000 topics and s = 1.0 the top 10% of topics get about 70% of the
  queries. ``query_concentration`` low / medium / high sets s to 0.7 / 1.0 / 1.3.
* **Variation.** Each query is its topic plus Gaussian noise with standard deviation
  ``NUDGE * d10 / sqrt(dim)`` per coordinate, where d10 is the median distance from a test query to its
  10th nearest neighbour, so the noise is about 0.3 x d10 long: the query lands in the same area of the
  index, but no two queries are the same. ``cosinesimil`` queries are renormalised to unit length.
* **Drift.** A timed step longer than ``DRIFT_AFTER_S`` rotates the popularity order by a tenth of the topics
  every ``DRIFT_EVERY_S``.

Everything is driven by one seed, so the same parameters send the same queries. numpy only: no OSB imports.
"""

import numpy as np

PROFILES = ("prod", "uniform")
DEFAULT_PROFILE = "prod"
CONCENTRATION = {"low": 0.7, "medium": 1.0, "high": 1.3}
TOPICS = 1000
NUDGE = 0.3
DRIFT_AFTER_S = 3600
DRIFT_EVERY_S = 1800
D10_SAMPLE = 100000      # indexed vectors searched to estimate d10 when the data set has no neighbors
D10_QUERIES = 200        # topics whose 10th neighbour is measured


def exponent(concentration):
    """Zipf exponent s for a ``query_concentration`` (low, medium, high; default medium)."""
    c = (concentration or "medium").lower()
    if c not in CONCENTRATION:
        raise ValueError(f"query_concentration must be one of {', '.join(CONCENTRATION)}, got {concentration!r}")
    return CONCENTRATION[c]


def popularity(k, s):
    """Cumulative pick probabilities of positions 1..k (position r has weight 1 / r^s)."""
    w = 1.0 / np.arange(1, k + 1, dtype=np.float64) ** s
    c = np.cumsum(w / w.sum())
    c[-1] = 1.0
    return c


def top_share(k, s, fraction):
    """Share of the queries that go to the top ``fraction`` of the k topics."""
    w = 1.0 / np.arange(1, k + 1, dtype=np.float64) ** s
    return float(w[: max(1, int(k * fraction))].sum() / w.sum())


def d10_from_neighbors(queries, tenth):
    """Median L2 distance between each query and its 10th true neighbour (rows aligned)."""
    return float(np.median(np.linalg.norm(np.asarray(queries, np.float32) - np.asarray(tenth, np.float32), axis=1)))


def d10_estimate(queries, sample):
    """d10 when there is no ground truth: each query's 10th nearest (L2) vector within ``sample``. A sample
    of the index is sparser than the index, so this overestimates d10 a little (the noise is a bit larger)."""
    q = np.asarray(queries, np.float32)
    x = np.asarray(sample, np.float32)
    if len(x) < 10:
        raise ValueError(f"need at least 10 vectors to estimate d10, got {len(x)}")
    xx = (x * x).sum(axis=1)
    out = []
    for i in range(0, len(q), 64):                       # bounded memory: 64 x len(sample) distances at a time
        b = q[i:i + 64]
        d2 = (b * b).sum(axis=1)[:, None] - 2.0 * b @ x.T + xx[None, :]
        out.append(np.sqrt(np.maximum(np.partition(d2, 9, axis=1)[:, 9], 0.0)))
    return float(np.median(np.concatenate(out)))


class Prod:
    """The prod profile over a fixed set of topics. ``topics`` (k x dim) is in the order it was read; the
    popularity order comes from the seed."""

    def __init__(self, topics, d10, seed, s=1.0, space_type="l2"):
        self.topics = np.asarray(topics, np.float32)
        if self.topics.ndim != 2 or len(self.topics) == 0:
            raise ValueError("prod needs at least one topic vector")
        self.k, self.dim = self.topics.shape
        self.s, self.seed, self.d10 = float(s), int(seed), float(d10)
        self.cosine = space_type == "cosinesimil"
        self.order = np.random.default_rng([self.seed, 7]).permutation(self.k)   # order[0]: the most popular
        self.cum = popularity(self.k, self.s)
        self.sigma = NUDGE * self.d10 / np.sqrt(self.dim)
        self.rotate_by = max(1, self.k // 10)

    def settings(self):
        """The resolved settings, for the benchmark log."""
        return {"query_profile": "prod", "topics": self.k, "exponent": self.s, "nudge": NUDGE, "d10": self.d10,
                "noise_sigma_per_dim": float(self.sigma), "top_10pct_share": round(top_share(self.k, self.s, 0.1), 3),
                "drift": f"rotate {self.rotate_by} topics every {DRIFT_EVERY_S} s on steps over {DRIFT_AFTER_S} s",
                "seed": self.seed}

    def ranks(self, rng, n):
        """n popularity positions (0 = most popular)."""
        return np.minimum(np.searchsorted(self.cum, rng.random(n), side="right"), self.k - 1)

    def queries(self, rng, n, epoch=0):
        """n queries. ``epoch`` > 0 rotates the popularity order by epoch x a tenth of the topics (drift)."""
        order = np.roll(self.order, -epoch * self.rotate_by) if epoch else self.order
        q = self.topics[order[self.ranks(rng, n)]]
        q = q + rng.normal(0.0, self.sigma, size=q.shape).astype(np.float32)
        if self.cosine:
            norms = np.linalg.norm(q, axis=1, keepdims=True)
            q = q / np.where(norms == 0, 1.0, norms)
        return q.astype(np.float32)


def drift_epoch(elapsed_s, time_period_s):
    """Which drift period a query falls in: 0 unless the step is longer than DRIFT_AFTER_S."""
    if not time_period_s or time_period_s <= DRIFT_AFTER_S or elapsed_s <= 0:
        return 0
    return int(elapsed_s // DRIFT_EVERY_S)

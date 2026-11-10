"""
Shared helpers for per-percentage filtered vector search dataset tools.

Each benchmarked filter percentage maps to one boolean keyword field named
filter<suffix> (e.g. 0.1 -> filter01pct, 25 -> filter25pct). For each field,
exactly that fraction of documents is marked 'true', chosen uniformly at
random, so a term query passes exactly that percentage of documents scattered
randomly across the HNSW graph. Used by the flat radial generator
(generate_radial_filter_percentage_ground_truth.py, docs = vectors) and the
nested generator (generate_nested_filter_percentage_ground_truth.py,
docs = parent documents).
"""

import numpy as np


def pct_suffix(pct):
    """0.1 -> '01pct', 1 -> '1pct', 25 -> '25pct'"""
    if pct < 1:
        return f"0{str(pct).replace('0.', '')}pct"
    return f"{int(pct)}pct"


def assign_attributes(num_docs, percentages, suffixes, seed):
    """For each percentage, mark exactly n_pass random docs 'true'.

    Returns the (num_docs, P) attribute matrix and per-column sorted passing ids.
    """
    rng = np.random.default_rng(seed)
    attributes = np.full((num_docs, len(percentages)), b"false", dtype="|S8")
    passing_ids = {}
    for col, pct in enumerate(percentages):
        n_pass = int(round(pct / 100.0 * num_docs))
        chosen = rng.permutation(num_docs)[:n_pass]
        attributes[chosen, col] = b"true"
        passing_ids[col] = np.sort(chosen)
        print(f"  filter{suffixes[col]}: exactly {n_pass} docs marked true")
    return attributes, passing_ids

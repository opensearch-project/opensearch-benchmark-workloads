"""
Generate a filtered radial search dataset with per-percentage ground truth.

Each document gets one boolean filter attribute field per requested percentage,
named filter<P>pct (e.g. filter1pct, filter25pct). For each field, exactly that
fraction of documents is marked 'true', chosen uniformly at random. Filtering
with a term query (e.g. {"term": {"filter25pct": "true"}}) therefore passes
exactly that percentage of documents, scattered randomly across the HNSW graph.

For each percentage, ground truth is computed by brute force over the passing
documents only: the top take_n nearest passing docs per query, plus per-query
radial search thresholds (distance to the k-th nearest passing neighbor,
converted per engine). This mirrors the unfiltered radial per-query benchmark:
at benchmark time query_k selects the ground truth depth (neighbors[:k]) and
the radial threshold (threshold[k-1]).

Usage:
    python generate_radial_filter_percentage_ground_truth.py \
        --input cohere-1m.hdf5 \
        --output cohere-1m-radial-filter-percentage.hdf5 \
        --space-type innerproduct \
        --percentages 0.1 1 5 10 25 50 75 90 99 \
        --take-n 1000

Output HDF5 layout (one set of columns per percentage, suffixed by its field
name — e.g. for percentage 10 the suffix is 10pct):
    train:                      (N, dim)     float32  — corpus vectors (copied from input)
    test:                       (Q, dim)     float32  — query vectors (copied from input)
    attributes:                 (N, P)       |S8      — 'true'/'false' per percentage field
    neighbors_<suffix>:         (Q, take_n)  int64    — top take_n passing docs, nearest first
    distances_<suffix>:         (Q, take_n)  float32  — raw distances for those neighbors
    faiss_max_distance_<suffix>, faiss_min_score_<suffix>,
    lucene_max_distance_<suffix>, lucene_min_score_<suffix>:
                                (Q, take_n)  float32  — per-engine radial thresholds

Attribute column order matches --percentages order and maps to index fields:
    percentage P -> field filter<suffix> (0.1 -> filter01pct, 25 -> filter25pct, ...)

Requires take_n <= passing docs at the smallest percentage.
"""

import argparse
import shutil
import time

import h5py
import numpy as np

from filter_percentage_utils import assign_attributes, pct_suffix
from radial_threshold_utils import (
    SUPPORTED_SPACE_TYPES,
    calculate_distances_batch,
    engine_threshold_values,
)

ENGINES = ("faiss", "lucene")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate per-percentage filtered radial ground truth for vector search benchmarks")
    parser.add_argument("--input", required=True, help="Input HDF5 with train/test")
    parser.add_argument("--output", required=True, help="Output HDF5 path")
    parser.add_argument("--space-type", required=True, choices=list(SUPPORTED_SPACE_TYPES))
    parser.add_argument("--percentages", type=float, nargs="+",
                        default=[0.1, 1, 5, 10, 25, 50, 75, 90, 99],
                        help="Filter percentages (default: 0.1 1 5 10 25 50 75 90 99)")
    parser.add_argument("--take-n", type=int, default=1000,
                        help="Neighbors stored per query per percentage (default: 1000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--query-batch-size", type=int, default=100)
    return parser.parse_args()


def load_input(path):
    """Load corpus and query vectors, failing clearly if keys are missing."""
    with h5py.File(path, "r") as f_in:
        for key in ("train", "test"):
            if key not in f_in:
                raise ValueError(f"Input {path} is missing dataset '{key}'. "
                                 f"Available keys: {sorted(f_in.keys())}")
        print("Loading dataset...")
        train = f_in["train"][:]
        test = f_in["test"][:]
    print(f"  train: {train.shape}, test: {test.shape}")
    return train, test


def validate_args(args, num_docs):
    """Validate percentages and take_n before doing any work. Returns suffixes."""
    if args.take_n <= 0:
        raise ValueError(f"--take-n must be positive, got {args.take_n}")
    suffixes = [pct_suffix(p) for p in args.percentages]
    if len(set(suffixes)) != len(suffixes):
        raise ValueError(f"Percentages {args.percentages} map to duplicate "
                         f"field suffixes {suffixes}")
    for pct in args.percentages:
        if not 0 < pct < 100:
            raise ValueError(f"Percentages must be in (0, 100), got {pct}")
        n_pass = int(round(pct / 100.0 * num_docs))
        if n_pass < args.take_n:
            raise ValueError(f"{pct}% passes only {n_pass} docs < take_n={args.take_n}. "
                             f"Reduce --take-n or raise the percentage.")
    return suffixes


def compute_ground_truth(train, test, passing_ids, suffixes, args):
    """Filter-first brute force: per percentage, top take_n passing docs per query."""
    num_queries = test.shape[0]
    out = {}
    for s in suffixes:
        out[s] = {
            "neighbors": np.empty((num_queries, args.take_n), dtype=np.int64),
            "distances": np.empty((num_queries, args.take_n), dtype=np.float32),
        }

    print(f"\nComputing ground truth for {num_queries} queries "
          f"x {len(suffixes)} percentages (take_n={args.take_n})...")
    t0 = time.time()
    for batch_start in range(0, num_queries, args.query_batch_size):
        batch_end = min(batch_start + args.query_batch_size, num_queries)
        if batch_start % 1000 == 0:
            print(f"  {batch_start}/{num_queries} ({time.time()-t0:.0f}s)")
        # One distance computation per batch, reused for all percentages
        batch_dists = calculate_distances_batch(test[batch_start:batch_end], train, args.space_type)

        for col, s in enumerate(suffixes):
            ids = passing_ids[col]
            sub = batch_dists[:, ids]                      # distances to passing docs only
            for i in range(batch_end - batch_start):
                d = sub[i]
                if args.take_n < len(d):
                    idx = np.argpartition(d, args.take_n - 1)[:args.take_n]
                    idx = idx[np.argsort(d[idx])]
                else:
                    idx = np.argsort(d)
                out[s]["neighbors"][batch_start + i] = ids[idx]
                out[s]["distances"][batch_start + i] = d[idx]
    print(f"Done in {time.time()-t0:.0f}s")
    return out


def write_output(args, attributes, out, suffixes):
    """Copy input to output and add/replace attribute + per-percentage datasets."""
    shutil.copy2(args.input, args.output)
    with h5py.File(args.output, "a") as f_out:
        def write(name, data):
            if name in f_out:
                del f_out[name]
            f_out.create_dataset(name, data=data)

        write("attributes", attributes)
        for s in suffixes:
            dist = out[s]["distances"]
            write(f"neighbors_{s}", out[s]["neighbors"])
            write(f"distances_{s}", dist)
            for engine in ENGINES:
                max_distance, min_score = engine_threshold_values(engine, args.space_type, dist)
                write(f"{engine}_max_distance_{s}", max_distance)
                write(f"{engine}_min_score_{s}", min_score)

        f_out.attrs["space_type"] = args.space_type
        f_out.attrs["percentages"] = args.percentages
        f_out.attrs["take_n"] = args.take_n
        f_out.attrs["seed"] = args.seed


def main():
    args = parse_args()
    train, test = load_input(args.input)
    num_docs, num_queries = train.shape[0], test.shape[0]

    suffixes = validate_args(args, num_docs)
    print(f"Percentages: {args.percentages} -> fields filter{{{', filter'.join(suffixes)}}}")

    attributes, passing_ids = assign_attributes(num_docs, args.percentages, suffixes, args.seed)
    out = compute_ground_truth(train, test, passing_ids, suffixes, args)
    write_output(args, attributes, out, suffixes)

    print(f"\nWritten to {args.output}")
    print(f"  attributes: {attributes.shape}")
    for s in suffixes:
        print(f"  neighbors_{s} / distances_{s} / thresholds_{s}: ({num_queries}, {args.take_n})")
    print(f"\nBenchmark filter body example: {{\"term\": {{\"filter{suffixes[-1]}\": \"true\"}}}}")


if __name__ == "__main__":
    main()

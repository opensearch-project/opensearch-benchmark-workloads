"""
Generate a nested + filtered vector search dataset with per-percentage ground truth.

Documents are parent docs holding multiple nested child vectors (as in
generate_nested_dataset.py). Each PARENT doc gets one boolean filter attribute
field per requested percentage, named filter<P>pct (e.g. filter1pct,
filter25pct). For each field, exactly that fraction of parent docs is marked
'true', chosen uniformly at random (as in
generate_radial_filter_percentage_ground_truth.py). Filtering with a term
query (e.g. {"term": {"filter25pct": "true"}}) therefore passes exactly that
percentage of parent docs.

For each percentage, ground truth is computed filter-first over parent docs:
restrict to passing parents, rank them by best child match (min distance over
the parent's nested vectors — matching OpenSearch nested knn scoring), and
keep the top take_n parent IDs. The same ground truth serves every filter
placement (efficient filter inside the knn clause, parent-level bool filter,
post_filter): the correct answer depends only on which parents pass, not on
where the query puts the filter.

Usage:
    python generate_nested_filter_percentage_ground_truth.py \
        --mode cohere --input cohere-10m.hdf5 \
        --num-docs 1000000 --distribution uniform --max-vectors-per-doc 20 \
        --num-queries 10000 --space-type innerproduct \
        --percentages 0.1 1 5 10 25 50 75 90 99 \
        --take-n 100 \
        --output cohere-10m-nested-filter-percentage.hdf5

Output HDF5 layout (one set of columns per percentage, suffixed by its field
name — e.g. for percentage 10 the suffix is 10pct):
    train:              (total_vectors, dim) float32 — all child vectors, parent-contiguous
    test:               (Q, dim)     float32 — query vectors
    parents:            (total_vectors,) int32 — 1-based parent doc ID per vector
    attributes:         (total_vectors, P) |S8 — 'true'/'false' per percentage field,
                        vector-aligned (each parent's value repeated across its
                        child vectors) so OSB can stream it in lockstep with train
    neighbors_<suffix>: (Q, take_n)  int32   — top take_n passing parent doc IDs
                                               (1-based), nearest first
    distances_<suffix>: (Q, take_n)  float32 — raw best-child distances for those parents

Attribute column order matches --percentages order and maps to index fields:
    percentage P -> field filter<suffix> (0.1 -> filter01pct, 25 -> filter25pct, ...)

Parent IDs are 1-based to match the document _id written by OSB's nested bulk
ingest (unlike the flat filter dataset, whose neighbors are 0-based row
indices). No radial threshold columns: nested+filter benchmarks are top-k.

Memory: train is held in RAM — ~32 GB for 10M x 768d float32; use a
memory-optimized instance at that scale.

Requires take_n <= passing parent docs at the smallest percentage.
"""

import argparse
import time

import h5py
import numpy as np

from nested_dataset_utils import calculate_distances, generate_parents
from filter_percentage_utils import assign_attributes, pct_suffix
from radial_threshold_utils import SUPPORTED_SPACE_TYPES, calculate_distances_batch

DEFAULT_PERCENTAGES = [0.1, 1, 5, 10, 25, 50, 75, 90, 99]
CORPUS_CHUNK_TARGET = 1_000_000  # child vectors per distance chunk (~400MB per 100-query batch)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate per-percentage filtered nested ground truth for vector search benchmarks")
    parser.add_argument("--mode", choices=["cohere", "synthetic"], default="cohere",
                        help="Vector source: 'cohere' reads train/test from --input HDF5; "
                             "'synthetic' generates random unit vectors (for testing)")
    parser.add_argument("--input", help="Input HDF5 with train/test (required for --mode cohere)")
    parser.add_argument("--dim", type=int, default=768, help="Vector dimension (synthetic mode only)")
    parser.add_argument("--output", required=True, help="Output HDF5 path")
    parser.add_argument("--space-type", required=True, choices=list(SUPPORTED_SPACE_TYPES))
    parser.add_argument("--num-docs", type=int, required=True, help="Number of parent documents")
    parser.add_argument("--distribution", choices=["fixed", "uniform", "normal"], default="uniform")
    parser.add_argument("--vectors-per-doc", type=int, default=10,
                        help="Vectors per doc (fixed distribution)")
    parser.add_argument("--max-vectors-per-doc", type=int, default=20,
                        help="Max vectors per doc (uniform/normal distributions)")
    parser.add_argument("--num-queries", type=int, default=10000)
    parser.add_argument("--percentages", type=float, nargs="+", default=DEFAULT_PERCENTAGES,
                        help="Filter percentages (default: 0.1 1 5 10 25 50 75 90 99)")
    parser.add_argument("--take-n", type=int, default=100,
                        help="Ground truth parent docs stored per query per percentage (default: 100)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--query-batch-size", type=int, default=100)
    parser.add_argument("--num-verify-queries", type=int, default=5,
                        help="Spot-check queries per percentage in the verification phase")
    return parser.parse_args()


def validate_args(args):
    if args.mode == "cohere" and not args.input:
        raise ValueError("--input is required for --mode cohere")
    suffixes = [pct_suffix(p) for p in args.percentages]
    if len(set(suffixes)) != len(suffixes):
        raise ValueError(f"Percentages {args.percentages} map to duplicate "
                         f"field suffixes {suffixes}")
    for pct in args.percentages:
        if not 0 < pct < 100:
            raise ValueError(f"Percentages must be in (0, 100), got {pct}")
        n_pass = int(round(pct / 100.0 * args.num_docs))
        if n_pass < args.take_n:
            raise ValueError(f"{pct}% passes only {n_pass} parent docs < take_n={args.take_n}. "
                             f"Reduce --take-n or raise the percentage.")
    return suffixes


def load_vectors(args, total_vectors):
    """Load child vectors + queries; synthetic mode generates both."""
    if args.mode == "synthetic":
        rng = np.random.default_rng(args.seed + 1)
        train = rng.standard_normal((total_vectors, args.dim), dtype=np.float32)
        train /= np.linalg.norm(train, axis=1, keepdims=True)
        test = rng.standard_normal((args.num_queries, args.dim), dtype=np.float32)
        test /= np.linalg.norm(test, axis=1, keepdims=True)
        return train, test
    with h5py.File(args.input, "r") as f:
        available = f["train"].shape[0]
        if total_vectors > available:
            raise ValueError(f"Need {total_vectors:,} vectors but input only has {available:,}")
        if args.num_queries > f["test"].shape[0]:
            raise ValueError(f"Need {args.num_queries:,} queries but input only has "
                             f"{f['test'].shape[0]:,}")
        print(f"Loading {total_vectors:,} train vectors and {args.num_queries:,} queries "
              f"from {args.input}...")
        train = f["train"][:total_vectors].astype(np.float32, copy=False)
        test = f["test"][:args.num_queries].astype(np.float32, copy=False)
    return train, test


def build_corpus_chunks(doc_offsets, num_docs, total_vectors):
    """Split the corpus into chunks aligned to parent boundaries.

    Returns a list of (p0, p1, v0, v1): parents [p0, p1) own vectors [v0, v1).
    Alignment keeps every parent's vectors inside one chunk so the per-parent
    min-reduction never straddles a chunk edge.
    """
    parent_starts = doc_offsets[:, 0]
    chunks = []
    p0 = 0
    while p0 < num_docs:
        v0 = int(parent_starts[p0])
        # First parent starting at or beyond the target end of this chunk
        p1 = int(np.searchsorted(parent_starts, v0 + CORPUS_CHUNK_TARGET, side="left"))
        p1 = max(p1, p0 + 1)
        v1 = int(parent_starts[p1]) if p1 < num_docs else total_vectors
        chunks.append((p0, p1, v0, v1))
        p0 = p1
    return chunks


def compute_ground_truth(train, test, doc_offsets, passing_ids, suffixes, args):
    """Filter-first brute force over parent docs.

    Per query batch: child distances once, per-parent min once (best child
    match), then each percentage is a cheap column slice of the parent-distance
    matrix followed by a top-take_n selection over passing parents only.
    """
    num_queries = test.shape[0]
    num_docs = doc_offsets.shape[0]
    parent_starts = doc_offsets[:, 0]
    chunks = build_corpus_chunks(doc_offsets, num_docs, train.shape[0])

    out = {}
    for s in suffixes:
        out[s] = {
            "neighbors": np.empty((num_queries, args.take_n), dtype=np.int32),
            "distances": np.empty((num_queries, args.take_n), dtype=np.float32),
        }

    print(f"\nComputing ground truth for {num_queries} queries x {len(suffixes)} percentages "
          f"(take_n={args.take_n}, {len(chunks)} corpus chunks)...")
    t0 = time.time()
    for batch_start in range(0, num_queries, args.query_batch_size):
        batch_end = min(batch_start + args.query_batch_size, num_queries)
        if batch_start % 1000 == 0:
            print(f"  {batch_start}/{num_queries} ({time.time()-t0:.0f}s)")
        test_batch = test[batch_start:batch_end]

        # Best child match per parent: min over each parent's child vectors.
        doc_dists = np.empty((batch_end - batch_start, num_docs), dtype=np.float32)
        for p0, p1, v0, v1 in chunks:
            child_dists = calculate_distances_batch(test_batch, train[v0:v1], args.space_type)
            doc_dists[:, p0:p1] = np.minimum.reduceat(
                child_dists, parent_starts[p0:p1] - v0, axis=1)

        # Filter-first per percentage: slice passing parents, take the top take_n.
        for col, s in enumerate(suffixes):
            ids = passing_ids[col]
            sub = doc_dists[:, ids]
            for i in range(batch_end - batch_start):
                d = sub[i]
                if args.take_n < len(d):
                    idx = np.argpartition(d, args.take_n - 1)[:args.take_n]
                    idx = idx[np.argsort(d[idx])]
                else:
                    idx = np.argsort(d)
                out[s]["neighbors"][batch_start + i] = ids[idx] + 1  # 1-based parent IDs
                out[s]["distances"][batch_start + i] = d[idx]
    print(f"Done in {time.time()-t0:.0f}s")
    return out


def verify_ground_truth(train, test, doc_offsets, passing_ids, suffixes, out, args):
    """Independent spot-check: recompute a few queries per percentage with a
    naive per-parent loop (different code path than the batched reduction) and
    require an exact match against the stored ground truth."""
    rng = np.random.default_rng(args.seed + 2)
    query_indices = rng.choice(test.shape[0], size=min(args.num_verify_queries, test.shape[0]),
                               replace=False)
    print(f"\nVerifying queries {sorted(query_indices.tolist())} at every percentage...")
    for col, s in enumerate(suffixes):
        ids = passing_ids[col]
        for q_idx in query_indices:
            dists = np.empty(len(ids), dtype=np.float32)
            for j, doc in enumerate(ids):
                start, count = doc_offsets[doc]
                child = calculate_distances(test[q_idx], train[start:start + count],
                                            args.space_type)
                dists[j] = child.min()
            order = np.argsort(dists, kind="stable")[:args.take_n]
            expected_neighbors = ids[order] + 1
            expected_distances = dists[order]
            got_neighbors = out[s]["neighbors"][q_idx]
            got_distances = out[s]["distances"][q_idx]
            if not np.allclose(expected_distances, got_distances, rtol=1e-5, atol=1e-5):
                raise AssertionError(
                    f"filter{s} query {q_idx}: stored distances diverge from recomputation")
            # Distance ties can order differently between argsort and argpartition;
            # neighbors must agree exactly wherever distances are distinct.
            mismatched = got_neighbors != expected_neighbors
            if mismatched.any():
                tied = np.isclose(got_distances[mismatched], expected_distances[mismatched],
                                  rtol=1e-6, atol=1e-7)
                if not tied.all():
                    raise AssertionError(
                        f"filter{s} query {q_idx}: neighbor mismatch beyond distance ties")
        print(f"  filter{s}: OK")


def write_output(args, train, test, parents, attributes_vec, out, suffixes):
    print(f"\nWriting {args.output}...")
    with h5py.File(args.output, "w") as f:
        f.create_dataset("train", data=train)
        f.create_dataset("test", data=test)
        f.create_dataset("parents", data=parents.astype(np.int32))
        f.create_dataset("attributes", data=attributes_vec)
        for s in suffixes:
            f.create_dataset(f"neighbors_{s}", data=out[s]["neighbors"])
            f.create_dataset(f"distances_{s}", data=out[s]["distances"])
        f.attrs["space_type"] = args.space_type
        f.attrs["percentages"] = args.percentages
        f.attrs["take_n"] = args.take_n
        f.attrs["seed"] = args.seed
        f.attrs["num_docs"] = args.num_docs
        f.attrs["distribution"] = args.distribution
        if args.distribution == "fixed":
            f.attrs["vectors_per_doc"] = args.vectors_per_doc
        else:
            f.attrs["max_vectors_per_doc"] = args.max_vectors_per_doc


def main():
    args = parse_args()
    suffixes = validate_args(args)

    print(f"Phase 1/5: parent assignment ({args.num_docs:,} docs, {args.distribution})")
    total_available = None
    if args.mode == "cohere":
        with h5py.File(args.input, "r") as f:
            total_available = f["train"].shape[0]
    else:
        # Synthetic mode generates exactly as many vectors as the distribution asks for.
        total_available = args.num_docs * max(args.vectors_per_doc, args.max_vectors_per_doc)
    parents, doc_offsets, total_vectors = generate_parents(
        args.num_docs, args.distribution, args.vectors_per_doc,
        args.max_vectors_per_doc, total_available, args.seed)
    print(f"  {total_vectors:,} child vectors across {args.num_docs:,} parents")

    print(f"\nPhase 2/5: filter attribute assignment ({len(suffixes)} percentages, per PARENT doc)")
    attributes, passing_ids = assign_attributes(args.num_docs, args.percentages, suffixes, args.seed)
    counts = doc_offsets[:, 1]
    attributes_vec = np.repeat(attributes, counts, axis=0)  # vector-aligned for OSB ingest

    print("\nPhase 3/5: loading vectors")
    train, test = load_vectors(args, total_vectors)

    print("\nPhase 4/5: ground truth")
    out = compute_ground_truth(train, test, doc_offsets, passing_ids, suffixes, args)

    print("\nPhase 5/5: verification")
    verify_ground_truth(train, test, doc_offsets, passing_ids, suffixes, out, args)

    write_output(args, train, test, parents, attributes_vec, out, suffixes)
    print("Done.")


if __name__ == "__main__":
    main()

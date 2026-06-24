"""
Generate nested vector dataset for OpenSearch Benchmark.

This script generates an HDF5 dataset file for nested vector search benchmarks.
It creates documents with multiple nested vectors per document, computes brute-force
ground truth (top-k parent docs ranked by best child distance), and writes everything
in the format OSB expects.

HDF5 output format:
    "train"     - (total_vectors, dim) all vectors flat
    "test"      - (num_queries, dim) query vectors
    "parents"   - (total_vectors,) parent doc ID for each vector (1-based)
    "neighbors" - (num_queries, k) ground truth top-k parent doc IDs per query

Distribution modes:
    --distribution fixed:   Every doc gets exactly --vectors-per-doc vectors
    --distribution uniform: Each doc gets random 1 to --max-vectors-per-doc vectors
    --distribution normal:  Each doc gets ~mean vectors (normal distribution, min=1)

Sample usage:
    # Fixed 10 vectors/doc:
    python generate_nested_dataset.py \
        --mode cohere --input cohere-10m.hdf5 \
        --num-docs 1000000 --distribution fixed --vectors-per-doc 10 \
        --num-queries 10000 --k 100 --space-type innerproduct \
        --output cohere-10m-nested-fixed10.hdf5

    # Uniform 1-20 vectors/doc:
    python generate_nested_dataset.py \
        --mode cohere --input cohere-10m.hdf5 \
        --num-docs 1000000 --distribution uniform --max-vectors-per-doc 20 \
        --num-queries 10000 --k 100 --space-type innerproduct \
        --output cohere-10m-nested-uniform.hdf5

    # Synthetic 128d, 10 docs:
    python generate_nested_dataset.py \
        --mode synthetic --dim 128 --num-docs 10 --distribution fixed --vectors-per-doc 3 \
        --num-queries 10 --k 5 \
        --output nested-10docs-128d.hdf5
"""

import argparse
import h5py
import multiprocessing as mp
import numpy as np
import os
import time
import tempfile


def calculate_distances(query, vectors, space_type):
    """Compute distances from a single query to a batch of vectors."""
    if space_type == "l2":
        return np.sum((vectors - query) ** 2, axis=1)
    elif space_type == "innerproduct":
        return -np.dot(vectors, query)
    elif space_type == "cosine":
        norm_query = np.linalg.norm(query)
        norms_vectors = np.linalg.norm(vectors, axis=1)
        return 1 - (np.dot(vectors, query) / (norms_vectors * norm_query + 1e-10))
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def generate_parents(num_docs, distribution, vectors_per_doc, max_vectors_per_doc, total_available, seed):
    """Generate parent ID array based on distribution.

    Returns:
        parents: array of parent IDs (1-based) for each vector
        doc_offsets: array of (start_idx, count) per doc for ground truth
    """
    np.random.seed(seed)

    if distribution == "fixed":
        counts = np.full(num_docs, vectors_per_doc, dtype="int32")
    elif distribution == "uniform":
        counts = np.random.randint(1, max_vectors_per_doc + 1, size=num_docs).astype("int32")
    elif distribution == "normal":
        mean = (1 + max_vectors_per_doc) / 2
        std = (max_vectors_per_doc - 1) / 4
        counts = np.random.normal(mean, std, size=num_docs).astype("int32")
        counts = np.clip(counts, 1, max_vectors_per_doc)

    total_needed = int(counts.sum())
    if total_needed > total_available:
        scale = total_available / total_needed
        counts = np.maximum(1, (counts * scale).astype("int32"))
        total_needed = int(counts.sum())
        if total_needed > total_available:
            excess = total_needed - total_available
            for i in range(excess):
                idx = num_docs - 1 - i
                if counts[idx] > 1:
                    counts[idx] -= 1

    total_vectors = int(counts.sum())

    # Build parents array (1-based doc IDs)
    parents = np.repeat(np.arange(1, num_docs + 1), counts)

    # Build doc_offsets for ground truth computation
    offsets = np.zeros(num_docs, dtype="int64")
    offsets[1:] = np.cumsum(counts[:-1])
    doc_offsets = np.column_stack([offsets, counts])

    return parents, doc_offsets, total_vectors


def generate_synthetic_vectors(total_vectors, dim):
    """Generate random unit vectors for synthetic mode."""
    print(f"Generating {total_vectors:,} synthetic vectors ({dim}d)...")
    vectors = np.random.randn(total_vectors, dim).astype("float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    return vectors


def load_vectors_from_hdf5(input_path, total_vectors):
    """Load vectors from an existing HDF5 file (expects a 'train' dataset)."""
    with h5py.File(input_path, "r") as f:
        available = f["train"].shape[0]
        dim = f["train"].shape[1]
        if total_vectors > available:
            raise ValueError(
                f"Need {total_vectors:,} vectors but input only has {available:,}."
            )
        print(f"Loading {total_vectors:,} vectors from {input_path} ({dim}d)...")
        vectors = f["train"][:total_vectors].astype("float32")
    return vectors


def _worker_compute_ground_truth(args):
    """Worker function for multiprocessing ground truth computation."""
    worker_id, start_idx, num_queries_for_worker, num_docs, k, space_type, vectors_file, queries_file, offsets_file = args

    vectors = np.load(vectors_file, mmap_mode="r")
    queries = np.load(queries_file, mmap_mode="r")
    doc_offsets = np.load(offsets_file, mmap_mode="r")
    total_vectors = len(vectors)
    corpus_chunk_size = min(total_vectors, 1_000_000)

    results = np.zeros((num_queries_for_worker, k), dtype="int32")

    for i in range(num_queries_for_worker):
        q_idx = start_idx + i
        all_distances = np.empty(total_vectors, dtype="float32")

        for chunk_start in range(0, total_vectors, corpus_chunk_size):
            chunk_end = min(chunk_start + corpus_chunk_size, total_vectors)
            chunk = vectors[chunk_start:chunk_end]
            all_distances[chunk_start:chunk_end] = calculate_distances(
                queries[q_idx], chunk, space_type
            )

        # Min distance per doc (best child match)
        doc_distances = np.empty(num_docs, dtype="float32")
        for doc_id in range(num_docs):
            offset = doc_offsets[doc_id, 0]
            count = doc_offsets[doc_id, 1]
            doc_distances[doc_id] = all_distances[offset:offset + count].min()

        # Top-k closest docs (return 1-based IDs)
        if k >= num_docs:
            top_k_indices = np.argsort(doc_distances)[:k]
        else:
            top_k_indices = np.argpartition(doc_distances, k)[:k]
            top_k_indices = top_k_indices[np.argsort(doc_distances[top_k_indices])]

        results[i] = top_k_indices + 1  # 1-based

        if (i + 1) % 100 == 0:
            print(f"  [Worker {worker_id}] {i + 1}/{num_queries_for_worker} queries done")

    print(f"  [Worker {worker_id}] finished all {num_queries_for_worker} queries")
    return worker_id, start_idx, results


def _worker_compute_ground_truth_fixed(args):
    """Optimized worker for fixed vectors-per-doc (uses reshape trick)."""
    worker_id, start_idx, num_queries_for_worker, num_docs, vectors_per_doc, k, space_type, vectors_file, queries_file = args

    vectors = np.load(vectors_file, mmap_mode="r")
    queries = np.load(queries_file, mmap_mode="r")
    total_vectors = len(vectors)
    corpus_chunk_size = min(total_vectors, 1_000_000)

    results = np.zeros((num_queries_for_worker, k), dtype="int32")

    for i in range(num_queries_for_worker):
        q_idx = start_idx + i
        all_distances = np.empty(total_vectors, dtype="float32")

        for chunk_start in range(0, total_vectors, corpus_chunk_size):
            chunk_end = min(chunk_start + corpus_chunk_size, total_vectors)
            chunk = vectors[chunk_start:chunk_end]
            all_distances[chunk_start:chunk_end] = calculate_distances(
                queries[q_idx], chunk, space_type
            )

        # Fast path: reshape since all docs have same number of vectors
        doc_distances = all_distances.reshape(num_docs, vectors_per_doc).min(axis=1)

        if k >= num_docs:
            top_k_indices = np.argsort(doc_distances)[:k]
        else:
            top_k_indices = np.argpartition(doc_distances, k)[:k]
            top_k_indices = top_k_indices[np.argsort(doc_distances[top_k_indices])]

        results[i] = top_k_indices + 1  # 1-based

        if (i + 1) % 100 == 0:
            print(f"  [Worker {worker_id}] {i + 1}/{num_queries_for_worker} queries done")

    print(f"  [Worker {worker_id}] finished all {num_queries_for_worker} queries")
    return worker_id, start_idx, results


def compute_ground_truth(vectors, queries, num_docs, k, space_type, num_workers, doc_offsets, distribution, vectors_per_doc):
    """Brute-force compute top-k parent docs for each query using multiprocessing."""
    num_queries = len(queries)
    total_vectors = len(vectors)

    print(f"\nComputing ground truth ({num_queries:,} queries, top-{k})...")
    print(f"  Corpus: {total_vectors:,} vectors across {num_docs:,} docs")
    print(f"  Space type: {space_type}")
    print(f"  Distribution: {distribution}")
    print(f"  Workers: {num_workers}")

    tmp_dir = tempfile.gettempdir()
    vectors_file = os.path.join(tmp_dir, "__nested_gt_vectors.npy")
    queries_file = os.path.join(tmp_dir, "__nested_gt_queries.npy")
    np.save(vectors_file, vectors)
    np.save(queries_file, queries)

    start_time = time.time()

    # Partition queries across workers
    partition_size = num_queries // num_workers
    worker_args = []
    start_idx = 0

    is_fixed = distribution == "fixed"

    if not is_fixed:
        offsets_file = os.path.join(tmp_dir, "__nested_gt_offsets.npy")
        np.save(offsets_file, doc_offsets)

    for wid in range(num_workers):
        qcount = partition_size
        if wid == num_workers - 1:
            qcount = num_queries - start_idx
        if is_fixed:
            worker_args.append((wid, start_idx, qcount, num_docs, vectors_per_doc, k, space_type, vectors_file, queries_file))
        else:
            worker_args.append((wid, start_idx, qcount, num_docs, k, space_type, vectors_file, queries_file, offsets_file))
        start_idx += qcount

    worker_fn = _worker_compute_ground_truth_fixed if is_fixed else _worker_compute_ground_truth

    if num_workers == 1:
        results_list = [worker_fn(worker_args[0])]
    else:
        with mp.Pool(processes=num_workers) as pool:
            results_list = pool.map(worker_fn, worker_args)

    # Assemble results in order
    results_list.sort(key=lambda x: x[0])
    neighbors = np.zeros((num_queries, k), dtype="int32")
    for worker_id, start, result_chunk in results_list:
        neighbors[start:start + len(result_chunk)] = result_chunk

    elapsed = time.time() - start_time
    print(f"  Done in {elapsed:.1f}s ({num_queries / elapsed:.1f} queries/sec)")

    # Cleanup temp files
    for tmp_file in [vectors_file, queries_file]:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
    if not is_fixed:
        if os.path.exists(offsets_file):
            os.remove(offsets_file)

    return neighbors


def verify_ground_truth(vectors, queries, neighbors, num_docs, doc_offsets, space_type):
    """Spot-check ground truth for correctness on a few queries."""
    print("\nVerifying ground truth (spot check on first 3 queries)...")
    for q_idx in range(min(3, len(queries))):
        query = queries[q_idx]
        all_distances = calculate_distances(query, vectors, space_type)

        doc_distances = np.empty(num_docs, dtype="float32")
        for doc_id in range(num_docs):
            offset = doc_offsets[doc_id, 0]
            count = doc_offsets[doc_id, 1]
            doc_distances[doc_id] = all_distances[offset:offset + count].min()

        expected_top1 = np.argmin(doc_distances) + 1  # 1-based
        actual_top1 = neighbors[q_idx, 0]

        status = "PASS" if expected_top1 == actual_top1 else "FAIL"
        print(f"  Query {q_idx}: top-1 expected={expected_top1}, got={actual_top1} [{status}]")
        if expected_top1 != actual_top1:
            print(f"    Expected dist: {doc_distances[expected_top1 - 1]:.6f}")
            print(f"    Actual dist:   {doc_distances[actual_top1 - 1]:.6f}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate nested vector dataset for OpenSearch Benchmark"
    )
    parser.add_argument("--mode", required=True, choices=["synthetic", "cohere"],
                        help="'synthetic' for random vectors, 'cohere' to reuse existing dataset")
    parser.add_argument("--input", default=None,
                        help="Input HDF5 path (required for cohere mode)")
    parser.add_argument("--output", required=True,
                        help="Output HDF5 path")
    parser.add_argument("--dim", type=int, default=128,
                        help="Vector dimensions (synthetic mode only, default: 128)")
    parser.add_argument("--num-docs", type=int, default=1_000_000,
                        help="Number of parent documents (default: 1000000)")
    parser.add_argument("--distribution", default="fixed", choices=["fixed", "uniform", "normal"],
                        help="Distribution of vectors per doc (default: fixed)")
    parser.add_argument("--vectors-per-doc", type=int, default=10,
                        help="Vectors per doc for fixed distribution (default: 10)")
    parser.add_argument("--max-vectors-per-doc", type=int, default=20,
                        help="Max vectors per doc for uniform/normal distribution (default: 20)")
    parser.add_argument("--num-queries", type=int, default=10_000,
                        help="Number of query vectors (default: 10000)")
    parser.add_argument("--k", type=int, default=100,
                        help="Top-k neighbors for ground truth (default: 100)")
    parser.add_argument("--space-type", default="innerproduct", choices=["l2", "innerproduct", "cosine"],
                        help="Distance space type (default: innerproduct)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--workers", type=int, default=0,
                        help="Number of worker processes (default: 80%% of CPU cores)")

    args = parser.parse_args()

    if args.mode == "cohere" and args.input is None:
        parser.error("--input is required for cohere mode")

    num_workers = args.workers if args.workers > 0 else int(0.8 * mp.cpu_count())
    num_workers = max(1, num_workers)

    np.random.seed(args.seed)

    # Determine total available vectors
    if args.mode == "cohere":
        with h5py.File(args.input, "r") as f:
            total_available = f["train"].shape[0]
            dim = f["train"].shape[1]
    else:
        if args.distribution == "fixed":
            total_available = args.num_docs * args.vectors_per_doc
        else:
            total_available = args.num_docs * args.max_vectors_per_doc
        dim = args.dim

    # Generate parents array based on distribution
    parents, doc_offsets, total_vectors = generate_parents(
        args.num_docs, args.distribution, args.vectors_per_doc,
        args.max_vectors_per_doc, total_available, args.seed
    )

    print(f"Mode: {args.mode}")
    print(f"Output: {args.output}")
    print(f"Distribution: {args.distribution}")
    if args.distribution == "fixed":
        print(f"Docs: {args.num_docs:,}, Vectors/doc: {args.vectors_per_doc} (total: {total_vectors:,})")
    else:
        counts = doc_offsets[:, 1]
        print(f"Docs: {args.num_docs:,}, Vectors/doc: min={counts.min()}, max={counts.max()}, "
              f"mean={counts.mean():.1f} (total: {total_vectors:,})")
    print(f"Space type: {args.space_type}, k: {args.k}")
    print(f"Workers: {num_workers} (CPUs: {mp.cpu_count()})")
    print()

    # Generate or load vectors
    if args.mode == "synthetic":
        vectors = generate_synthetic_vectors(total_vectors, dim)
    else:
        vectors = load_vectors_from_hdf5(args.input, total_vectors)

    # Generate or load query vectors
    if args.mode == "cohere" and args.input:
        with h5py.File(args.input, "r") as f:
            available_queries = f["test"].shape[0]
            num_queries = min(args.num_queries, available_queries)
            print(f"Loading {num_queries:,} queries from {args.input}")
            queries = f["test"][:num_queries].astype("float32")
    else:
        num_queries = args.num_queries
        print(f"Generating {num_queries:,} synthetic query vectors ({dim}d)")
        queries = np.random.randn(num_queries, dim).astype("float32")
        norms = np.linalg.norm(queries, axis=1, keepdims=True)
        queries = queries / norms

    # Compute ground truth
    neighbors = compute_ground_truth(
        vectors, queries, args.num_docs, args.k, args.space_type,
        num_workers, doc_offsets, args.distribution, args.vectors_per_doc
    )

    # Verify correctness
    verify_ground_truth(vectors, queries, neighbors, args.num_docs, doc_offsets, args.space_type)

    # Write HDF5
    print(f"\nWriting to {args.output}...")
    with h5py.File(args.output, "w") as f:
        f.create_dataset("train", data=vectors)
        f.create_dataset("test", data=queries)
        f.create_dataset("parents", data=parents)
        f.create_dataset("neighbors", data=neighbors)

        f.attrs["num_docs"] = args.num_docs
        f.attrs["distribution"] = args.distribution
        f.attrs["dim"] = dim
        f.attrs["space_type"] = args.space_type
        f.attrs["k"] = args.k
        f.attrs["mode"] = args.mode
        if args.distribution == "fixed":
            f.attrs["vectors_per_doc"] = args.vectors_per_doc
        else:
            f.attrs["max_vectors_per_doc"] = args.max_vectors_per_doc
            f.attrs["mean_vectors_per_doc"] = float(doc_offsets[:, 1].mean())

    file_size_mb = (total_vectors * dim * 4 + num_queries * dim * 4
                    + total_vectors * 4 + num_queries * args.k * 4) / 1e6
    print(f"  train:     ({total_vectors:,}, {dim}) float32")
    print(f"  test:      ({num_queries:,}, {dim}) float32")
    print(f"  parents:   ({total_vectors:,},) int32")
    print(f"  neighbors: ({num_queries:,}, {args.k}) int32")
    print(f"  Approx file size: {file_size_mb:.0f} MB")
    print("\nDone!")


if __name__ == "__main__":
    main()

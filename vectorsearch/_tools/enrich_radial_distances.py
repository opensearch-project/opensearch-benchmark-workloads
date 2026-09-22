"""
Enrich an HDF5 dataset with k=1000 neighbors and pre-computed radial search thresholds.

This script:
1. Brute-force computes the 1000 nearest neighbors per query 
2. Computes raw distances for all 1000 neighbors
3. Converts distances to 4 engine-specific radial search API parameters:
   - faiss_max_distance
   - faiss_min_score
   - lucene_max_distance
   - lucene_min_score

The output HDF5 can be used directly by OSB with no conversion logic at query time.
OSB reads e.g. faiss_max_distance[query_idx][k-1] and passes it as the API parameter.

Conversion logic reference (from k-NN plugin SpaceType.java, Faiss.java, Lucene.java):

  Raw distance conventions:
    l2:           ||q - c||^2        (smaller = more similar)
    innerproduct: -dot(q, c)         (more negative = more similar)
    cosine:       1 - cos(q, c)      (smaller = more similar)

  The OpenSearch API accepts max_distance or min_score. Internally, each engine
  transforms the user's parameter into an engine-specific threshold:

  For max_distance, Faiss accepts the raw distance directly. Lucene differs for
  innerproduct (takes positive dot product instead of negative):
    faiss_max_distance:  raw_distance for all space types
    lucene_max_distance: -raw_distance for innerproduct, raw_distance otherwise

  For min_score, both engines accept the same OpenSearch score value:
    Score formula: l2 -> 1/(1+d), innerproduct -> d>=0 ? 1/(1+d) : -d+1, cosine -> (2-d)/2
    faiss_min_score == lucene_min_score == OpenSearch score

Usage:
    # Full computation (brute-force k=1000 neighbors + distances + conversions):
    python enrich_radial_distances.py \\
        --input cohere-10m.hdf5 \\
        --output cohere-10m-radial-knn1000.hdf5 \\
        --space-type innerproduct

    # Only compute distances for existing neighbors (no brute-force):
    python enrich_radial_distances.py \\
        --input cohere-10m.hdf5 \\
        --output cohere-10m-radial-knn1000.hdf5 \\
        --space-type innerproduct \\
        --skip-neighbor-computation
"""

import argparse
import h5py
import numpy as np
import sys
from tqdm import tqdm


def calculate_distances_batch(queries, corpus, space_type):
    """Compute raw distances from multiple queries to all corpus vectors.

    Returns shape (num_queries, num_corpus).
    """
    if space_type == "l2":
        q_norms = np.sum(queries ** 2, axis=1, keepdims=True)
        c_norms = np.sum(corpus ** 2, axis=1, keepdims=True).T
        dots = queries @ corpus.T
        return q_norms + c_norms - 2 * dots
    elif space_type == "innerproduct":
        return -(queries @ corpus.T)
    elif space_type == "cosine":
        q_norms = np.linalg.norm(queries, axis=1, keepdims=True)
        c_norms = np.linalg.norm(corpus, axis=1, keepdims=True).T
        dots = queries @ corpus.T
        return 1 - dots / (q_norms * c_norms)
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def calculate_distance_single(query, corpus_vecs, space_type):
    """Compute raw distances from a single query to a set of corpus vectors."""
    if space_type == "l2":
        return np.sum((corpus_vecs - query) ** 2, axis=1)
    elif space_type == "innerproduct":
        return -np.dot(corpus_vecs, query)
    elif space_type == "cosine":
        norm_query = np.linalg.norm(query)
        norms_corpus = np.linalg.norm(corpus_vecs, axis=1)
        return 1 - (np.dot(corpus_vecs, query) / (norms_corpus * norm_query))
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def raw_distance_to_opensearch_score(distances, space_type):
    """Convert raw distances to OpenSearch scores (used as min_score for both engines).

    SpaceType.scoreTranslation in the k-NN plugin:
      l2:           1 / (1 + distance)
      innerproduct: distance >= 0 ? 1/(1+distance) : -distance + 1
      cosine:       (2 - distance) / 2
    """
    if space_type == "l2":
        return 1.0 / (1.0 + distances)
    elif space_type == "innerproduct":
        return np.where(distances >= 0, 1.0 / (1.0 + distances), -distances + 1.0)
    elif space_type == "cosine":
        return (2.0 - distances) / 2.0
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def compute_knn_bruteforce(f_in, space_type, k=1000, query_batch_size=100, corpus_chunk_size=1_000_000):
    """Brute-force compute k nearest neighbors for all queries.

    Returns:
        neighbors: (num_queries, k) int32 array of corpus indices, sorted nearest-first
        distances: (num_queries, k) float32 array of raw distances, sorted ascending
    """
    train = f_in["train"]
    test = f_in["test"][:]
    num_queries = test.shape[0]
    num_corpus = train.shape[0]
    dims = train.shape[1]

    print(f"Computing k={k} nearest neighbors (brute force)...")
    print(f"  Corpus: {num_corpus} vectors, {dims} dimensions")
    print(f"  Queries: {num_queries}")
    print(f"  Space type: {space_type}")
    print(f"  Query batch size: {query_batch_size}")
    print(f"  Corpus chunk size: {corpus_chunk_size}")
    print()

    neighbors = np.empty((num_queries, k), dtype=np.int32)
    distances = np.empty((num_queries, k), dtype=np.float32)

    for q_start in tqdm(range(0, num_queries, query_batch_size),
                        total=(num_queries + query_batch_size - 1) // query_batch_size,
                        desc="Brute force"):
        q_end = min(q_start + query_batch_size, num_queries)
        batch_queries = test[q_start:q_end]
        batch_size = q_end - q_start

        all_dists = np.empty((batch_size, num_corpus), dtype=np.float32)

        for chunk_start in range(0, num_corpus, corpus_chunk_size):
            chunk_end = min(chunk_start + corpus_chunk_size, num_corpus)
            corpus_chunk = train[chunk_start:chunk_end][:]
            chunk_dists = calculate_distances_batch(batch_queries, corpus_chunk, space_type)
            all_dists[:, chunk_start:chunk_end] = chunk_dists

        for i in range(batch_size):
            if k < num_corpus:
                top_k_idx = np.argpartition(all_dists[i], k - 1)[:k]
                top_k_idx = top_k_idx[np.argsort(all_dists[i][top_k_idx])]
            else:
                top_k_idx = np.argsort(all_dists[i])[:k]
            neighbors[q_start + i] = top_k_idx
            distances[q_start + i] = all_dists[i][top_k_idx]

    print("Brute force complete.")
    return neighbors, distances


def compute_distances_for_existing_neighbors(f_in, space_type):
    """Compute distances for already-stored neighbors (fast path when neighbors exist).

    Returns:
        distances: (num_queries, k) float32 array of raw distances
    """
    train = f_in["train"]
    test = f_in["test"][:]
    neighbors_ds = f_in["neighbors"][:]
    num_queries, k = neighbors_ds.shape

    print(f"Computing distances for existing {k} neighbors per query...")
    distances = np.empty((num_queries, k), dtype=np.float32)

    for i in tqdm(range(num_queries), desc="Computing distances"):
        neighbor_ids = neighbors_ds[i]
        corpus_vecs = train[neighbor_ids]
        distances[i] = calculate_distance_single(test[i], corpus_vecs, space_type)
    return distances


def main():
    parser = argparse.ArgumentParser(
        description="Enrich HDF5 dataset with k=1000 neighbors and radial search thresholds"
    )
    parser.add_argument("--input", required=True, help="Input HDF5 dataset path")
    parser.add_argument("--output", default=None,
                        help="Output HDF5 path (default: overwrites input)")
    parser.add_argument("--space-type", required=True, choices=["l2", "innerproduct", "cosine"],
                        help="Distance space type")
    parser.add_argument("--k", type=int, default=1000,
                        help="Number of neighbors to compute (default: 1000)")
    parser.add_argument("--skip-neighbor-computation", action="store_true",
                        help="Skip brute-force; only compute distances for existing neighbors")
    parser.add_argument("--query-batch-size", type=int, default=100,
                        help="Queries to process per batch during brute-force (default: 100)")
    parser.add_argument("--corpus-chunk-size", type=int, default=1_000_000,
                        help="Corpus vectors to load per chunk (default: 1M)")

    args = parser.parse_args()
    output_path = args.output or args.input

    print(f"Input: {args.input}")
    print(f"Output: {output_path}")
    print(f"Space type: {args.space_type}")
    print(f"Target k: {args.k}")
    print()

    with h5py.File(args.input, "r") as f_in:
        existing_keys = list(f_in.keys())
        print(f"Existing HDF5 keys: {existing_keys}")

        if "neighbors" in f_in:
            existing_k = f_in["neighbors"].shape[1]
            print(f"Existing neighbors shape: {f_in['neighbors'].shape} (k={existing_k})")
        else:
            existing_k = 0
            print("No existing neighbors dataset")
        print()

        if args.skip_neighbor_computation:
            if "neighbors" not in f_in:
                print("ERROR: --skip-neighbor-computation requires existing neighbors dataset")
                sys.exit(1)
            new_neighbors = f_in["neighbors"][:]
            new_distances = compute_distances_for_existing_neighbors(f_in, args.space_type)
        elif existing_k >= args.k:
            print(f"Existing neighbors already have k={existing_k} >= {args.k}, "
                  f"just computing distances.")
            new_neighbors = f_in["neighbors"][:, :args.k]
            new_distances = compute_distances_for_existing_neighbors(f_in, args.space_type)
            new_distances = new_distances[:, :args.k]
        else:
            new_neighbors, new_distances = compute_knn_bruteforce(
                f_in, args.space_type, k=args.k,
                query_batch_size=args.query_batch_size,
                corpus_chunk_size=args.corpus_chunk_size)

    print()
    print("Computing engine-specific radial thresholds...")

    # For max_distance: Faiss takes raw distance directly, but Lucene differs for IP
    faiss_max_distance = new_distances.copy()
    if args.space_type == "innerproduct":
        lucene_max_distance = -new_distances
    else:
        lucene_max_distance = new_distances.copy()

    # For min_score: both engines accept the same OpenSearch score value
    min_score = raw_distance_to_opensearch_score(new_distances, args.space_type)

    # Print stats at various k values
    k_values = [k for k in [100, 200, 500, 1000] if k <= new_distances.shape[1]]
    print(f"\nThreshold stats by k (space_type={args.space_type}):")
    for k_val in k_values:
        col_f = faiss_max_distance[:, k_val - 1]
        col_l = lucene_max_distance[:, k_val - 1]
        col_s = min_score[:, k_val - 1]
        print(f"\n  k={k_val}:")
        print(f"    faiss_max_distance:  min={col_f.min():.4f}, "
              f"median={np.median(col_f):.4f}, max={col_f.max():.4f}")
        print(f"    lucene_max_distance: min={col_l.min():.4f}, "
              f"median={np.median(col_l):.4f}, max={col_l.max():.4f}")
        print(f"    min_score:           min={col_s.min():.4f}, "
              f"median={np.median(col_s):.4f}, max={col_s.max():.4f}")

    # Write output
    print(f"\nWriting to {output_path}...")

    if output_path != args.input:
        import shutil
        shutil.copy2(args.input, output_path)

    with h5py.File(output_path, "a") as f_out:
        def write_dataset(name, data):
            if name in f_out:
                del f_out[name]
            f_out.create_dataset(name, data=data)

        write_dataset("neighbors", new_neighbors)
        write_dataset("distances", new_distances.astype(np.float32))
        write_dataset("faiss_max_distance", faiss_max_distance.astype(np.float32))
        write_dataset("faiss_min_score", min_score.astype(np.float32))
        write_dataset("lucene_max_distance", lucene_max_distance.astype(np.float32))
        write_dataset("lucene_min_score", min_score.astype(np.float32))

        f_out.attrs["space_type"] = args.space_type
        f_out.attrs["enriched_k"] = args.k

    print(f"\nDone. Output datasets:")
    print(f"  neighbors:           {new_neighbors.shape} (int32, sorted nearest-first)")
    print(f"  distances:           {new_distances.shape} (float32, raw distances)")
    print(f"  faiss_max_distance:  {faiss_max_distance.shape} (float32)")
    print(f"  faiss_min_score:     {min_score.shape} (float32)")
    print(f"  lucene_max_distance: {lucene_max_distance.shape} (float32)")
    print(f"  lucene_min_score:    {min_score.shape} (float32)")
    print()
    print("Usage: OSB reads dataset[query_idx][k-1] directly as the API parameter.")
    print("  e.g. for k=100 radial search on Faiss: faiss_max_distance[i][99]")


if __name__ == "__main__":
    main()

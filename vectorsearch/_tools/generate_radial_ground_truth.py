"""
Generate radial search ground truth for OpenSearch Benchmark.

This script computes brute-force radial neighbors for each query and writes
them to an HDF5 file for use with OSB's radial recall calculation. It generates
both max_distance_neighbors and min_score_neighbors from a single distance
threshold, along with copying the existing k-based neighbors.

Usage:
    python generate_radial_ground_truth.py \
        --input cohere-1m.hdf5 \
        --output cohere-1m-radial.hdf5 \
        --space-type innerproduct \
        --threshold -160.0

    # With auto-threshold (picks median k=100 distance):
    python generate_radial_ground_truth.py \
        --input cohere-1m.hdf5 \
        --output cohere-1m-radial.hdf5 \
        --space-type innerproduct \
        --auto-threshold

    # Optionally generate param files from a template:
    python generate_radial_ground_truth.py \
        --input cohere-1m.hdf5 \
        --output cohere-1m-radial.hdf5 \
        --space-type innerproduct \
        --threshold -160.0 \
        --template-params params/radial_search/faiss-hnsw-cohere-768-1m-inner-product.json
"""

import argparse
import json
import h5py
import numpy as np
import os
import sys


def calculate_distances(query, corpus, space_type):
    """Compute raw distances from a single query to all corpus vectors."""
    if space_type == "l2":
        return np.sum((corpus - query) ** 2, axis=1)
    elif space_type == "innerproduct":
        return -np.dot(corpus, query)
    elif space_type == "cosine":
        norm_query = np.linalg.norm(query)
        norms_corpus = np.linalg.norm(corpus, axis=1)
        return 1 - (np.dot(corpus, query) / (norms_corpus * norm_query))
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def convert_distances_to_scores(distances, space_type):
    """Convert raw distances to OpenSearch scores (higher = more similar)."""
    if space_type == "l2":
        return 1 / (1 + distances)
    elif space_type == "innerproduct":
        return np.where(distances >= 0, 1 / (1 + distances), 1 - distances)
    elif space_type == "cosine":
        return (2 - distances) / 2
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def distance_to_score(threshold, space_type):
    return float(convert_distances_to_scores(np.array([threshold]), space_type)[0])


def probe_threshold(input_path, space_type):
    """Estimate a reasonable distance threshold by looking at k=100 neighbor distances.

    Uses the median distance to the 100th nearest neighbor across queries as the
    auto-threshold. This gives ~100 neighbors per query on average.
    """
    with h5py.File(input_path, "r") as f:
        # Fast path: some ann-benchmarks datasets include precomputed k=100 distances
        if "distances" in f:
            distances_k100 = f["distances"][:]
            radii_at_k100 = distances_k100[:, -1]
            print(f"Probing distance distribution (from precomputed k=100 distances):")
            print(f"  k=100 radius: min={radii_at_k100.min():.4f}, "
                  f"median={np.median(radii_at_k100):.4f}, "
                  f"max={radii_at_k100.max():.4f}")
            return np.median(radii_at_k100)
        # Fallback: compute distance to k=100th neighbor from a sample of queries
        elif "neighbors" in f:
            print("No 'distances' key found. Computing distances from neighbors...")
            train_ds = f["train"]
            test_ds = f["test"]
            neighbors_ds = f["neighbors"]

            sample_size = min(100, test_ds.shape[0])
            radii = []
            for i in range(sample_size):
                query = test_ds[i]
                k100_idx = int(neighbors_ds[i, -1])
                corpus_vec = train_ds[k100_idx:k100_idx+1]
                dist = calculate_distances(query, corpus_vec, space_type)[0]
                radii.append(dist)

            radii = np.array(radii)
            print(f"Probing distance distribution (computed from {sample_size} sample queries):")
            print(f"  k=100 radius: min={radii.min():.4f}, "
                  f"median={np.median(radii):.4f}, "
                  f"max={radii.max():.4f}")
            return np.median(radii)
        else:
            print("Cannot probe: no 'distances' or 'neighbors' key in input file.")
            return None


def generate_ground_truth(input_path, output_path, space_type, threshold, max_length=10000):
    """Brute-force compute all neighbors within distance threshold for each query."""
    score_threshold = distance_to_score(threshold, space_type)

    with h5py.File(input_path, "r") as f_in:
        num_corpus = f_in["train"].shape[0]
        dims = f_in["train"].shape[1]
        test = f_in["test"][:]
        num_queries = len(test)

        print(f"Computing radial ground truth...")
        print(f"  Corpus: {num_corpus} vectors, {dims} dimensions")
        print(f"  Queries: {num_queries}")
        print(f"  max_distance threshold: {threshold}")
        print(f"  min_score threshold: {score_threshold}")
        print(f"  Space type: {space_type}")

        # Process corpus in chunks to avoid OOM on large datasets.
        # h5py loads entire slices into memory, so for 10M vectors (10M × 768 × float32 ≈ 29GB)
        # we read 1M at a time (~3GB per chunk) instead of all at once.
        corpus_chunk_size = min(num_corpus, 1_000_000)
        # Fixed-width array padded with -1 for HDF5 storage (variable-length not supported)
        padded_data = np.full((num_queries, max_length), -1, dtype=np.int64)
        neighbor_counts = []

        for i in range(num_queries):
            all_distances = np.empty(num_corpus, dtype=np.float32)

            # Compute distances in chunks to keep peak memory usage bounded
            for chunk_start in range(0, num_corpus, corpus_chunk_size):
                chunk_end = min(chunk_start + corpus_chunk_size, num_corpus)
                corpus_chunk = f_in["train"][chunk_start:chunk_end]
                all_distances[chunk_start:chunk_end] = calculate_distances(test[i], corpus_chunk, space_type)

            # Filter to vectors within threshold, sort by distance (closest first)
            within_threshold = np.where(all_distances <= threshold)[0]
            sorted_ids = within_threshold[np.argsort(all_distances[within_threshold])][:max_length]

            padded_data[i, :len(sorted_ids)] = sorted_ids
            neighbor_counts.append(len(sorted_ids))

            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{num_queries} queries...")

        print(f"\nGround truth stats:")
        print(f"  Mean neighbors per query: {np.mean(neighbor_counts):.1f}")
        print(f"  Median neighbors per query: {np.median(neighbor_counts):.1f}")
        print(f"  Min: {np.min(neighbor_counts)}, Max: {np.max(neighbor_counts)}")
        print(f"  Queries with 0 neighbors: {np.sum(np.array(neighbor_counts) == 0)}")

    with h5py.File(output_path, "w") as f_out:
        with h5py.File(input_path, "r") as f_in:
            copied_keys = list(f_in.keys())
            for key in copied_keys:
                f_in.copy(key, f_out)

        f_out.create_dataset("radial_neighbors", data=padded_data)

        f_out.attrs["max_distance_threshold"] = threshold
        f_out.attrs["min_score_threshold"] = score_threshold
        f_out.attrs["space_type"] = space_type

        print(f"\nWrote to {output_path}:")
        print(f"  - radial_neighbors (max_distance: {threshold}, min_score: {score_threshold})")
        print(f"  - Copied: {copied_keys}")


def generate_param_file(template_path, output_hdf5_path, threshold, query_type):
    with open(template_path, "r") as f:
        params = json.load(f)

    params["neighbors_data_set_path"] = output_hdf5_path

    if "query_max_distance" in params:
        del params["query_max_distance"]
    if "query_min_score" in params:
        del params["query_min_score"]

    if query_type == "max_distance":
        params["query_max_distance"] = threshold
    else:
        params["query_min_score"] = threshold

    output_dir = os.path.dirname(template_path)
    base_name = os.path.splitext(os.path.basename(template_path))[0]
    output_params_path = os.path.join(output_dir, f"{base_name}-{query_type.replace('_', '-')}-generated.json")

    with open(output_params_path, "w") as f:
        json.dump(params, f, indent=4)

    print(f"Generated param file: {output_params_path}")
    return output_params_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate radial search ground truth for OpenSearch Benchmark"
    )
    parser.add_argument("--input", required=True, help="Input HDF5 dataset path")
    parser.add_argument("--output", required=True, help="Output HDF5 path with ground truth")
    parser.add_argument("--space-type", required=True, choices=["l2", "innerproduct", "cosine"],
                        help="Distance space type")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Distance threshold (e.g., -160.0 for innerproduct)")
    parser.add_argument("--auto-threshold", action="store_true",
                        help="Automatically pick threshold from k=100 distance median")
    parser.add_argument("--template-params", default=None,
                        help="Path to template params JSON file to generate updated params")
    parser.add_argument("--max-length", type=int, default=10000,
                        help="Maximum neighbors per query (default: 10000)")

    args = parser.parse_args()

    if args.threshold is None and not args.auto_threshold:
        parser.error("Must specify either --threshold or --auto-threshold")


    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Space type: {args.space_type}")
    print()

    median_radius = probe_threshold(args.input, args.space_type)

    if args.auto_threshold:
        if median_radius is None:
            print("ERROR: Cannot auto-select threshold without distance data.")
            sys.exit(1)
        threshold = median_radius
        print(f"\nAuto-selected threshold: {threshold:.4f} (median of k=100 radii)")
    else:
        threshold = args.threshold
        print(f"\nUsing explicit threshold: {threshold}")
        if median_radius is not None:
            if threshold > median_radius:
                print(f"  Note: threshold is looser than median k=100 radius ({median_radius:.4f}), "
                      f"expect >100 neighbors per query")
            elif threshold < median_radius:
                print(f"  Note: threshold is tighter than median k=100 radius ({median_radius:.4f}), "
                      f"expect <100 neighbors per query")

    print()
    generate_ground_truth(args.input, args.output, args.space_type, threshold, args.max_length)

    if args.template_params:
        print()
        score_threshold = distance_to_score(threshold, args.space_type)
        generate_param_file(args.template_params, os.path.abspath(args.output), threshold, "max_distance")
        generate_param_file(args.template_params, os.path.abspath(args.output), score_threshold, "min_score")


if __name__ == "__main__":
    main()

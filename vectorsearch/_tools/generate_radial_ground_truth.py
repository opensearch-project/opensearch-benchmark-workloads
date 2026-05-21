import argparse
import json
import h5py
import numpy as np
import os
import sys


def calculate_distances(query, corpus, space_type):
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


def calculate_scores(distances, space_type):
    if space_type == "l2":
        return 1 / (1 + distances)
    elif space_type == "innerproduct":
        return np.where(distances >= 0, 1 / (1 + distances), 1 - distances)
    elif space_type == "cosine":
        return (2 - distances) / 2
    else:
        raise ValueError(f"Unsupported space type: {space_type}")


def probe_threshold(input_path, space_type):
    with h5py.File(input_path, "r") as f:
        if "distances" in f:
            distances_k100 = f["distances"][:]
            radii_at_k100 = distances_k100[:, -1]
            print(f"Probing distance distribution (from precomputed k=100 distances):")
            print(f"  k=100 radius: min={radii_at_k100.min():.4f}, "
                  f"median={np.median(radii_at_k100):.4f}, "
                  f"max={radii_at_k100.max():.4f}")
            return np.median(radii_at_k100)
        elif "neighbors" in f:
            print("No 'distances' key found. Computing distances from neighbors...")
            train = f["train"][:]
            test = f["test"][:]
            neighbors = f["neighbors"][:]

            sample_size = min(100, len(test))
            radii = []
            for i in range(sample_size):
                k100_idx = neighbors[i, -1]
                dist = calculate_distances(test[i], train[k100_idx:k100_idx+1], space_type)[0]
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


def generate_ground_truth(input_path, output_path, space_type, threshold, query_type, max_length=10000):
    with h5py.File(input_path, "r") as f_in:
        num_corpus = f_in["train"].shape[0]
        dims = f_in["train"].shape[1]
        test = f_in["test"][:]
        num_queries = len(test)

        print(f"Computing {query_type} ground truth...")
        print(f"  Corpus: {num_corpus} vectors, {dims} dimensions")
        print(f"  Queries: {num_queries}")
        print(f"  Threshold: {threshold}")
        print(f"  Space type: {space_type}")

        corpus_chunk_size = min(num_corpus, 1_000_000)
        padded_data = np.full((num_queries, max_length), -1, dtype=np.int64)
        neighbor_counts = []

        for i in range(num_queries):
            all_distances = np.empty(num_corpus, dtype=np.float32)
            for chunk_start in range(0, num_corpus, corpus_chunk_size):
                chunk_end = min(chunk_start + corpus_chunk_size, num_corpus)
                corpus_chunk = f_in["train"][chunk_start:chunk_end]
                all_distances[chunk_start:chunk_end] = calculate_distances(test[i], corpus_chunk, space_type)

            if query_type == "max_distance":
                within_threshold = np.where(all_distances <= threshold)[0]
                sorted_ids = within_threshold[np.argsort(all_distances[within_threshold])][:max_length]
            else:
                scores = calculate_scores(all_distances, space_type)
                within_threshold = np.where(scores >= threshold)[0]
                sorted_ids = within_threshold[np.argsort(-scores[within_threshold])][:max_length]

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
        dataset_name = f"{query_type}_neighbors"
        f_out.create_dataset(dataset_name, data=padded_data)
        f_out.create_dataset("test", data=test)
        print(f"\nWrote '{dataset_name}' to {output_path}")


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
    output_params_path = os.path.join(output_dir, f"{base_name}-generated.json")

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
    parser.add_argument("--query-type", required=True, choices=["max_distance", "min_score"],
                        help="Radial search query type")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Explicit threshold value")
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
    print(f"Query type: {args.query_type}")
    print()

    median_radius = probe_threshold(args.input, args.space_type)

    if args.auto_threshold:
        if median_radius is None:
            print("ERROR: Cannot auto-select threshold without distance data.")
            sys.exit(1)
        if args.query_type == "min_score":
            threshold = float(calculate_scores(np.array([median_radius]), args.space_type)[0])
            print(f"\nAuto-selected threshold: {threshold:.4f} (score converted from median k=100 distance {median_radius:.4f})")
        else:
            threshold = median_radius
            print(f"\nAuto-selected threshold: {threshold:.4f} (median of k=100 radii)")
    else:
        threshold = args.threshold
        print(f"\nUsing explicit threshold: {threshold}")
        if median_radius is not None:
            if args.query_type == "max_distance" and threshold > median_radius:
                print(f"  Note: threshold is looser than median k=100 radius ({median_radius:.4f}), "
                      f"expect >100 neighbors per query")
            elif args.query_type == "max_distance" and threshold < median_radius:
                print(f"  Note: threshold is tighter than median k=100 radius ({median_radius:.4f}), "
                      f"expect <100 neighbors per query")

    print()
    generate_ground_truth(args.input, args.output, args.space_type, threshold, args.query_type, args.max_length)

    if args.template_params:
        print()
        generate_param_file(args.template_params, os.path.abspath(args.output), threshold, args.query_type)


if __name__ == "__main__":
    main()

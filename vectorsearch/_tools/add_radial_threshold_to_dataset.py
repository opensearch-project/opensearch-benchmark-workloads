import h5py
import numpy as np
import sys
import logging


def calculate_distances(test_queries, train_docs, engine_type, distance_metric='l2_squared'):
    if distance_metric == 'l2_squared':
        distances = np.sum((train_docs - test_queries) ** 2, axis=1)
    elif distance_metric == 'cosine':
        norm_test = np.linalg.norm(test_queries)
        norms_train = np.linalg.norm(train_docs, axis=1)
        distances = 1 - (np.dot(train_docs, test_queries) / (norms_train * norm_test))
    elif distance_metric == 'inner_product':
        if engine_type == 'faiss':
            distances = -np.dot(train_docs, test_queries)
        elif engine_type == 'lucene':
            distances = np.dot(train_docs, test_queries)
    else:
        raise ValueError("Unsupported distance metric")
    return distances


def calculate_scores(test_queries, train_docs, distance_metric='l2_squared'):
    distances = calculate_distances(test_queries, train_docs, distance_metric)
    if distance_metric == 'l2_squared':
        scores = 1 / (1 + distances)
    elif distance_metric == 'cosine':
        scores = (2 - distances) / 2
    elif distance_metric == 'inner_product':
        if engine_type == 'faiss':
            scores = np.where(distances >= 0, 1 / (1 + distances), 1 - distances)
        elif engine_type == 'lucene':
            scores = np.where(distances > 0, distances + 1, 1 / (1 - distances))
        else:
            raise ValueError(f"Unsupported engine type for inner_product: {engine_type}")
    else:
        raise ValueError(f"Unsupported distance metric: {distance_metric}")
    return scores


def add_threshold_dataset(input_file_path, output_file_path, threshold_type, threshold_value, engine_type, distance_metric='l2_squared', max_length=10000):
    with h5py.File(input_file_path, 'r') as input_hdf5, h5py.File(output_file_path, 'w') as output_hdf5:
        if 'train' not in input_hdf5.keys() or 'test' not in input_hdf5.keys():
            raise ValueError("The input file must contain 'train' and 'test' datasets.")

        for key in input_hdf5.keys():
            input_hdf5.copy(key, output_hdf5)

        train_docs = input_hdf5['train'][()]
        test_queries = input_hdf5['test'][()]

        padded_data = np.full((len(test_queries), max_length), -1, dtype=int)  # Using -1 for padding

        for i, test_query in enumerate(test_queries):
            if threshold_type == 'max_distance':
                distances = calculate_distances(test_query, train_docs, engine_type, distance_metric)
                logging.info(f"Query target {i} distances calculated.")
                logging.info(f"distances: {distances}")
                within_threshold_ids = np.where(distances <= threshold_value)[0]
                sorted_ids = within_threshold_ids[np.argsort(distances[within_threshold_ids])][:max_length]
            else:
                scores = calculate_scores(test_query, train_docs, distance_metric)
                logging.info(f"Query target {i} scores calculated.")
                logging.info(f"scores: {scores}")
                within_threshold_ids = np.where(scores >= threshold_value)[0]
                sorted_ids = within_threshold_ids[np.argsort(scores[within_threshold_ids])][:max_length]

            padded_data[i, :len(sorted_ids)] = sorted_ids

        dataset_name = f"{threshold_type}_neighbors"
        output_hdf5.create_dataset(dataset_name, data=padded_data)

        logging.info(f"Dataset '{dataset_name}' added successfully to {output_file_path}.")


if __name__ == "__main__":
    if len(sys.argv) != 7:
        logging.info("Usage: python add_radial_threshold.py <threshold_type> <threshold_value> <space_type> <engine_type> "
              "<input_hdf5_file> <output_hdf5_file>")
    else:
        threshold_type = sys.argv[1]
        threshold_value = float(sys.argv[2])
        space_type = sys.argv[3]
        engine_type = sys.argv[4]
        input_file_path = sys.argv[5]
        output_file_path = sys.argv[6]
        add_threshold_dataset(input_file_path, output_file_path, threshold_type, threshold_value, engine_type, space_type)

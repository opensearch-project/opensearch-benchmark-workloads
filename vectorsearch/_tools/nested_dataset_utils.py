"""
Shared helpers for nested vector search dataset tools.

Nested datasets store multiple child vectors per parent document; the parents
array assigns each vector (contiguously) to a 1-based parent doc ID. Used by
generate_nested_dataset.py and generate_nested_filter_percentage_ground_truth.py.
"""

import numpy as np


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

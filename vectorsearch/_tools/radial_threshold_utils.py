"""
Shared distance and radial-threshold conversions for vector search dataset tools.

Radial search thresholds are engine- and space-type-specific. The conversions
here mirror the k-NN plugin so that stored thresholds match what each engine
expects at query time:

- Faiss `max_distance` takes the raw space-type distance. For innerproduct the
  plugin negates the dot product internally (larger dot product = smaller
  "distance"), so raw distances (and thresholds) are negative for well-matching
  vectors. See SpaceType.INNER_PRODUCT and FaissService in opensearch-knn.
- Lucene `max_distance` for innerproduct is the (non-negated) dot product, the
  opposite sign convention from Faiss. See LuceneEngine / VectorSimilarityFunction
  .MAXIMUM_INNER_PRODUCT in opensearch-knn and Lucene.
- `min_score` uses the plugin's distance-to-score translation, identical for
  both engines. See SpaceType#scoreTranslation in opensearch-knn:
    l2:           score = 1 / (1 + d)
    innerproduct: score = 1 / (1 + d)      if d >= 0
                  score = -d + 1           if d < 0
    cosine:       score = (2 - d) / 2

Distance functions and score translations per space type are documented at
https://docs.opensearch.org/latest/mappings/supported-field-types/knn-spaces/
"""

import numpy as np

SUPPORTED_SPACE_TYPES = ("l2", "innerproduct", "cosine")


def calculate_distances_batch(queries, corpus, space_type):
    """Raw space-type distances from each query to every corpus vector.

    Returns a (num_queries, num_corpus) float array where smaller = closer,
    matching the k-NN plugin's internal distance convention per space type
    (innerproduct is negated so it sorts ascending like l2/cosine).
    """
    if space_type == "l2":
        q_norms = np.sum(queries ** 2, axis=1, keepdims=True)
        c_norms = np.sum(corpus ** 2, axis=1, keepdims=True).T
        dots = queries @ corpus.T
        return q_norms + c_norms - 2 * dots
    if space_type == "innerproduct":
        return -(queries @ corpus.T)
    if space_type == "cosine":
        q_norms = np.linalg.norm(queries, axis=1, keepdims=True)
        c_norms = np.linalg.norm(corpus, axis=1, keepdims=True).T
        dots = queries @ corpus.T
        return 1 - dots / (q_norms * c_norms)
    raise ValueError(f"Unsupported space type: {space_type}. Supported: {SUPPORTED_SPACE_TYPES}")


def raw_distance_to_opensearch_score(distances, space_type):
    """k-NN plugin score for a raw distance (SpaceType#scoreTranslation)."""
    if space_type == "l2":
        return 1.0 / (1.0 + distances)
    if space_type == "innerproduct":
        return np.where(distances >= 0, 1.0 / (1.0 + distances), -distances + 1.0)
    if space_type == "cosine":
        return (2.0 - distances) / 2.0
    raise ValueError(f"Unsupported space type: {space_type}. Supported: {SUPPORTED_SPACE_TYPES}")


def engine_threshold_values(engine, space_type, distances):
    """Radial threshold columns for one engine: (max_distance, min_score).

    `distances` are raw space-type distances from calculate_distances_batch.
    Faiss max_distance is the raw distance. Lucene max_distance for
    innerproduct flips the sign back to a plain dot product (Lucene's
    MAXIMUM_INNER_PRODUCT convention); other space types match Faiss.
    min_score is the shared plugin score translation for both engines.
    """
    if engine not in ("faiss", "lucene"):
        raise ValueError(f"Unsupported engine: {engine}. Supported: faiss, lucene")
    if engine == "lucene" and space_type == "innerproduct":
        max_distance = -distances
    else:
        max_distance = distances.copy()
    min_score = raw_distance_to_opensearch_score(distances, space_type).astype(np.float32)
    return max_distance, min_score

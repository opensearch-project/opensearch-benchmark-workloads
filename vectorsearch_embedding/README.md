## Vector search embedding workload

This workload uses OpenSearch pretrained model and ml-common-plugin to embed vectors. It is based on the neural search tutorial https://opensearch.org/docs/latest/search-plugins/neural-search-tutorial/ 

### Workload tasks:

- cluster-settings
- delete-index
- delete-ingest-pipeline
- delete-ml-model
- register-ml-model
- deploy-ml-model
- create-ingest-pipeline
- create-index
- check-cluster-health
- index-append
- refresh-after-index
- force-merge
- refresh-after-force-merge
- wait-until-merges-finish
- default
- semantic-search

### Example document and query
```json
{
  "text":" The Manhattan Project and its atomic bomb helped bring an end to World War II. Its legacy of peaceful uses of atomic energy continues to have an impact on history and science."
}
```
```json
{
  "query": {
    "neural": {
      "passage_embedding": {
        "query_text": "What is the origin of the last name Rose?",
        "model_id": "LSmIG44BlTi78mODPYgy",
        "k": 10
      }
    }
  }
}
```

### Dataset

Documents: https://msmarco.blob.core.windows.net/msmarcoranking/collection.tar.gz  
Queries: https://msmarco.blob.core.windows.net/msmarcoranking/queries.tar.gz

### License

The MS MARCO datasets are intended for non-commercial research purposes only to promote advancement in the field of artificial intelligence and related areas, and is made available free of charge without extending any license or other intellectual property rights. The dataset is provided “as is” without warranty and usage of the data has risks since we may not own the underlying rights in the documents. We are not be liable for any damages related to use of the dataset. Feedback is voluntarily given and can be used as we see fit. Upon violation of any of these terms, your rights to use the dataset will end automatically.  
https://microsoft.github.io/msmarco/

### Parameters

This workload allows [specifying the following parameters](#specifying-workload-parameters) using the `--workload-params` option to OpenSearch Benchmark:

* `bulk_size` (default: 1000)
* `bulk_indexing_clients` (default: 1): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `query_cache_enabled` (default: false)
* `requests_cache_enabled` (default: false)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `target_throughput` (default: default values for each operation): Number of requests per second, `none` for no limit.
* `search_clients`: Number of clients that issue search requests.
* `model_name` (default: huggingface/sentence-transformers/all-mpnet-base-v2) OpenSearch-provided pretrained model name.
* `model_version` (default: 1.0.1) Model version.
* `model_format` (default: TORCH_SCRIPT) Model format.
* `dimensions` (default: 768): Vector dimensions, needed to match the model.
* `engine` (default:` lucene): The approximate k-NN library to use for indexing and search.
* `method` (default:` hnsw): K-NN search algorithm.
* `space_type` (default:` l2): The vector space used to calculate the distance between vectors.
* `k` (default: 10) Number of nearest neighbors are returned.
* `warmup_iterations` Number of Warmup iteration of each search client executes.
* `iterations`  Number of test iterations of each search client executes.
* `variable_queries` (default: 0) Number of variable queries will be used for the semantic search task, 0 means fixed query and max value is 20,000.

### Specifying Workload Parameters

Example:
```json
{
  "index_settings": {
    "index.number_of_shards": 1,
    "index.number_of_replicas": 0
  },
  "bulk_indexing_clients": 2,
  "ingest_percentage": 0.5,
  "search_clients": 10,
  "target_throughput": "none",
  "iterations": 100,
  "warmup_iterations": 100,
  "k": 100,
  "variable_queries": 100
}
 ```

Save it as `params.json` and provide it to OpenSearch Benchmark with `--workload-params="/path/to/params.json"`. The overrides for simple parameters could be specified in-place, for example `--workload-params=search_clients:2`.

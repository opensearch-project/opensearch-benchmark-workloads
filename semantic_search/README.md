## Semantic Search workload

This workload uses OpenSearch pretrained model and ml-common-plugin to embed vectors. It is based on the neural search tutorial https://opensearch.org/docs/latest/search-plugins/neural-search-tutorial/ 

### Dataset

Trec-Covid is a dataset collection of documents about COVID-19 information.
- Trec-Covid website: https://ir.nist.gov/covidSubmit/index.html
- Dataset: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip

### Example document and query
```json
{
  "_id": "2b73a28n",
  "title": "Role of endothelin-1 in lung disease",
  "text": "Endothelin-1 (ET-1) is a 21 amino acid peptide with diverse biological activity that has been implicated in numerous diseases.....",
  "metadata": {
    "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC59574/",
    "pubmed_id": "11686871"
  }
}
```
```json
{
  "query": {
    "neural": {
      "passage_embedding": {
        "query_text": "what types of rapid testing for Covid-19 have been developed?",
        "model_id": "LSmIG44BlTi78mODPYgy",
        "k": 10
      }
    }
  }
}
```

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

### Parameters

This workload allows [specifying the following parameters](#specifying-workload-parameters) using the `--workload-params` option to OpenSearch Benchmark:

* `bulk_size` (default: 100)
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
  "ingest_percentage": 20,
  "search_clients": 10,
  "target_throughput": "none",
  "iterations": 100,
  "warmup_iterations": 100,
  "k": 100,
  "variable_queries": 100
}
 ```

Save it as `params.json` and provide it to OpenSearch Benchmark with `--workload-params="/path/to/params.json"`. The overrides for simple parameters could be specified in-place, for example `--workload-params=search_clients:2`.

### License

We use the same license for the data as the original data.
```
               Apache License
           Version 2.0, January 2004
         http://www.apache.org/licenses/
```
Covid-trec [1] is part of the COVID-19 Open Research dataset [2], which is licensed under Apache 2.0.  
[1] https://arxiv.org/pdf/2005.04474v1.pdf  
[2] https://github.com/allenai/cord19/ 

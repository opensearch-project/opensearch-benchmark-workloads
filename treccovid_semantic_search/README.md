## Trec-Covid Semantic Search workload

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

### Procedures

#### Index, force-merge and search

This procedure runs all tasks of this workload. First it deletes the current index and model. Then it indexes the corpus with vector embedding. Then it does the force-merging. At the end it does the semantic search.

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
* `target_throughput` (default: default values for each operation): Number of requests per second, `""` for no limit.
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
* `num_variable_queries` (default: 0) Number of variable queries will be used for the semantic search task, 0 means fixed query and max value is 50.

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
  "target_throughput": "",
  "iterations": 100,
  "warmup_iterations": 100,
  "k": 100,
  "variable_queries": 100
}
 ```

Save it as `params.json` and provide it to OpenSearch Benchmark with `--workload-params="/path/to/params.json"`. The overrides for simple parameters could be specified in-place, for example `--workload-params=search_clients:2`.

### Sample command and output

```
./opensearch-benchmark execute-test --workload=treccovid_semantic_search \
 --target-hosts=<target-ip>:9200 --pipeline=benchmark-only --workload-params=params.json

   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] [Test Execution ID]: b6117408-73b8-4fc0-ba5d-f324cb3e1844
[INFO] Executing test with workload [treccovid_semantic_search], test_procedure [index-merge-search] and provision_config_instance ['external'] with version [2.13.0].

Running cluster-settings                                                       [100% done]
Running delete-index                                                           [100% done]
Running delete-ingest-pipeline                                                 [100% done]
Running delete-ml-model                                                        [100% done]
Running register-ml-model                                                      [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-ingest-pipeline                                                 [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running default                                                                [100% done]
Running semantic-search                                                        [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------

|                                                         Metric |                     Task |       Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                          |    0.433717 |    min |
|             Min cumulative indexing time across primary shards |                          |           0 |    min |
|          Median cumulative indexing time across primary shards |                          |     0.00015 |    min |
|             Max cumulative indexing time across primary shards |                          |       0.171 |    min |
|            Cumulative indexing throttle time of primary shards |                          |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |           0 |    min |
|                        Cumulative merge time of primary shards |                          |    0.374233 |    min |
|                       Cumulative merge count of primary shards |                          |           8 |        |
|                Min cumulative merge time across primary shards |                          |           0 |    min |
|             Median cumulative merge time across primary shards |                          |     0.00055 |    min |
|                Max cumulative merge time across primary shards |                          |    0.345033 |    min |
|               Cumulative merge throttle time of primary shards |                          |     0.33885 |    min |
|       Min cumulative merge throttle time across primary shards |                          |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |     0.33885 |    min |
|                      Cumulative refresh time of primary shards |                          |     0.10995 |    min |
|                     Cumulative refresh count of primary shards |                          |         162 |        |
|              Min cumulative refresh time across primary shards |                          |           0 |    min |
|           Median cumulative refresh time across primary shards |                          | 0.000783333 |    min |
|              Max cumulative refresh time across primary shards |                          |   0.0343667 |    min |
|                        Cumulative flush time of primary shards |                          |     0.00885 |    min |
|                       Cumulative flush count of primary shards |                          |           4 |        |
|                Min cumulative flush time across primary shards |                          |           0 |    min |
|             Median cumulative flush time across primary shards |                          |           0 |    min |
|                Max cumulative flush time across primary shards |                          |     0.00885 |    min |
|                                        Total Young Gen GC time |                          |       0.523 |      s |
|                                       Total Young Gen GC count |                          |          24 |        |
|                                          Total Old Gen GC time |                          |           0 |      s |
|                                         Total Old Gen GC count |                          |           0 |        |
|                                                     Store size |                          |     2.18146 |     GB |
|                                                  Translog size |                          |   0.0721766 |     GB |
|                                         Heap used for segments |                          |           0 |     MB |
|                                       Heap used for doc values |                          |           0 |     MB |
|                                            Heap used for terms |                          |           0 |     MB |
|                                            Heap used for norms |                          |           0 |     MB |
|                                           Heap used for points |                          |           0 |     MB |
|                                    Heap used for stored fields |                          |           0 |     MB |
|                                                  Segment count |                          |          50 |        |
|                                                 Min Throughput |             index-append |      108.82 | docs/s |
|                                                Mean Throughput |             index-append |      110.47 | docs/s |
|                                              Median Throughput |             index-append |       110.6 | docs/s |
|                                                 Max Throughput |             index-append |      111.68 | docs/s |
|                                        50th percentile latency |             index-append |     3465.01 |     ms |
|                                        90th percentile latency |             index-append |     3588.01 |     ms |
|                                       100th percentile latency |             index-append |     3764.87 |     ms |
|                                   50th percentile service time |             index-append |     3465.01 |     ms |
|                                   90th percentile service time |             index-append |     3588.01 |     ms |
|                                  100th percentile service time |             index-append |     3764.87 |     ms |
|                                                     error rate |             index-append |           0 |      % |
|                                                 Min Throughput | wait-until-merges-finish |       90.88 |  ops/s |
|                                                Mean Throughput | wait-until-merges-finish |       90.88 |  ops/s |
|                                              Median Throughput | wait-until-merges-finish |       90.88 |  ops/s |
|                                                 Max Throughput | wait-until-merges-finish |       90.88 |  ops/s |
|                                       100th percentile latency | wait-until-merges-finish |     10.6818 |     ms |
|                                  100th percentile service time | wait-until-merges-finish |     10.6818 |     ms |
|                                                     error rate | wait-until-merges-finish |           0 |      % |
|                                                 Min Throughput |                  default |     1030.78 |  ops/s |
|                                                Mean Throughput |                  default |     1030.78 |  ops/s |
|                                              Median Throughput |                  default |     1030.78 |  ops/s |
|                                                 Max Throughput |                  default |     1030.78 |  ops/s |
|                                        50th percentile latency |                  default |     8.11098 |     ms |
|                                        90th percentile latency |                  default |     10.5718 |     ms |
|                                        99th percentile latency |                  default |     12.5866 |     ms |
|                                      99.9th percentile latency |                  default |     13.8164 |     ms |
|                                       100th percentile latency |                  default |     14.1444 |     ms |
|                                   50th percentile service time |                  default |     8.11098 |     ms |
|                                   90th percentile service time |                  default |     10.5718 |     ms |
|                                   99th percentile service time |                  default |     12.5866 |     ms |
|                                 99.9th percentile service time |                  default |     13.8164 |     ms |
|                                  100th percentile service time |                  default |     14.1444 |     ms |
|                                                     error rate |                  default |           0 |      % |
|                                                 Min Throughput |          semantic-search |      110.75 |  ops/s |
|                                                Mean Throughput |          semantic-search |      112.87 |  ops/s |
|                                              Median Throughput |          semantic-search |      112.98 |  ops/s |
|                                                 Max Throughput |          semantic-search |      114.51 |  ops/s |
|                                        50th percentile latency |          semantic-search |     82.0484 |     ms |
|                                        90th percentile latency |          semantic-search |     99.8155 |     ms |
|                                        99th percentile latency |          semantic-search |     125.478 |     ms |
|                                      99.9th percentile latency |          semantic-search |     139.749 |     ms |
|                                       100th percentile latency |          semantic-search |     144.083 |     ms |
|                                   50th percentile service time |          semantic-search |     82.0484 |     ms |
|                                   90th percentile service time |          semantic-search |     99.8155 |     ms |
|                                   99th percentile service time |          semantic-search |     125.478 |     ms |
|                                 99.9th percentile service time |          semantic-search |     139.749 |     ms |
|                                  100th percentile service time |          semantic-search |     144.083 |     ms |
|                                                     error rate |          semantic-search |           0 |      % |


---------------------------------
[INFO] SUCCESS (took 266 seconds)
```

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

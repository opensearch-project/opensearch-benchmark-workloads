## Neural Search Plugin Workload

This workload is to benchmark performance of indexing and search for different search methods (Semantic, Hybrid, Sparse and multimodal) using Neural Search Plugin of OpenSearch.
### Dataset

The Quora Question Pairs (QQP) dataset, released by Quora, is a collection of over 400,000 question pairs, each labeled to indicate whether the two questions are paraphrases of each other, used for research in natural language processing and machine learning.
- Quora website: https://www.quora.com/q/quoradata/First-Quora-Dataset-Release-Question-Pairs
- Dataset: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/quora.zip

### Example document and query
```json
{
    "_id": "22",
    "title": "",
    "text": "What are some of the things technicians can tell about the durability and reliability of Laptops and its components?",
    "metadata":  {
    }
}


```
```json
"query": {
     "neural_sparse": {
       "passage_embedding": {
         "query_text": "What are some of the best science projects?",
         "model_id": ""
       }
     }
   }
```
### Running a benchmark
Before running a benchmark, ensure that the load generation host is able to access your cluster endpoint and that the appropriate dataset is available on the host.

Currently, we support 1 test procedures for the neural search workload. The default procedure is named sparse-search and does not include the steps required to train the model being used. This test procedures will index a data set of vectors into an OpenSearch cluster and then run a set of queries against the generated index.

Due to the number of parameters this workload offers, it's recommended to create a parameter file that specifies the desired workload parameters instead of listing them all on the OSB command line. Users are welcome to use the example param files, sparse_search.json, in /params, as references. Here, we named the parameter file using a format <search_method_name>.json

To run the workload, invoke the following command with the params file.
```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT=  
# Absolute file path of Workload param file
export PARAMS_FILE=

opensearch-benchmark execute-test \
    --target-hosts $ENDPOINT \
    --workload neural_search \
    --workload-params ${PARAMS_FILE} \
    --pipeline benchmark-only \
    --test-procedure=sparse-search \
    --kill-running-processes
    
```
### Procedures

#### sparse-search

This procedure runs all tasks of this sparse-search workload. First it deletes the current index and model. Then it indexes the corpus with vector embedding. Then it does the force-merging. At the end it does the sparse search.

### Workload tasks:

- delete-target-index
- delete-ingest-pipeline
- delete-ml-model-sparse
- put-cluster-settings
- register-ml-model-sparse
- deploy-ml-model
- create-ingest-pipeline-sparse
- create-target-index
- check-cluster-health
- index-append
- refresh-after-index
- force-merge
- refresh-after-force-merge
- wait-until-merges-finish
- default
- sparse-search

### Parameters

This workload allows [specifying the following parameters](#specifying-workload-parameters) using the `--workload-params` option to OpenSearch Benchmark:

* `default_ingest_pipeline` (default: nlp-default-ingest-pipeline): name of the ingest pipeline
* `prune_type` (default: max_ratio)
* `prune_ratio` (default: 0.1)
* `index_name`: : Name of the index
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
* `model_name` (default: amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill) OpenSearch-provided pretrained model name.
* `model_version` (default: 1.0.0) Model version.
* `model_format` (default: TORCH_SCRIPT) Model format.
* `dimensions` (default: 768): Vector dimensions, needed to match the model.
* `engine` (default:` lucene): The approximate k-NN library to use for indexing and search.
* `method` (default:` hnsw): K-NN search algorithm.
* `space_type` (default:` l2): The vector space used to calculate the distance between vectors.
* `k` (default: 10) Number of nearest neighbors are returned.
* `warmup_iterations` Number of Warmup iteration of each search client executes.
* `iterations`  Number of test iterations of each search client executes.
* `num_variable_queries` (default: 0) Number of variable queries will be used for the semantic search task, 0 means fixed query.

### Specifying Workload Parameters

Example:
```json
{
  "passage_embedding_type": "rank_features",
  "index_name": "quora",
  "index_body": "indices/quora.json",
  "corpora_name": "quora",
  "ingest_percentage": 1,
  "variable_queries": 0,
  "default_ingest_pipeline": "nlp-default-ingest-pipeline-sparse"
}
 ```

This is already setup as `sparse_search.json` in params directory, provide it to OpenSearch Benchmark with `--workload-params="/path/to/sparse_search.json"`. The overrides for simple parameters could be specified in-place, for example `--workload-params=search_clients:2`.

### Sample command and output

```
./opensearch-benchmark execute-test --pipeline=benchmark-only \
--workload=neural_search \
--workload-params=/path/to/opensearch-benchmark-workloads/neural_search/params/sparse_search.json \
--test-procedure=sparse-search --kill-running-processes


   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] [Test Execution ID]: 08ad495b-e63a-476a-add5-965f1bebac05
[INFO] Executing test with workload [neural_search], test_procedure [sparse-search] and provision_config_instance ['external'] with version [2.19.0].

[WARNING] merges_total_time is 100 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 461 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 125 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 104 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-target-index                                                    [100% done]
Running delete-ingest-pipeline                                                 [100% done]
Running delete-ml-model-sparse                                                 [100% done]
Running put-cluster-settings                                                   [100% done]
Running register-ml-model-sparse                                               [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-ingest-pipeline-sparse                                          [100% done]
Running create-target-index                                                    [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running default                                                                [100% done]
Running sparse-search                                                          [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------
            
|                                                         Metric |                     Task |      Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|-----------:|-------:|
|                     Cumulative indexing time of primary shards |                          |   0.272583 |    min |
|             Min cumulative indexing time across primary shards |                          |          0 |    min |
|          Median cumulative indexing time across primary shards |                          |          0 |    min |
|             Max cumulative indexing time across primary shards |                          |   0.199967 |    min |
|            Cumulative indexing throttle time of primary shards |                          |          0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |          0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |          0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |          0 |    min |
|                        Cumulative merge time of primary shards |                          |    1.94958 |    min |
|                       Cumulative merge count of primary shards |                          |         22 |        |
|                Min cumulative merge time across primary shards |                          |          0 |    min |
|             Median cumulative merge time across primary shards |                          |          0 |    min |
|                Max cumulative merge time across primary shards |                          |    1.90437 |    min |
|               Cumulative merge throttle time of primary shards |                          |     1.8385 |    min |
|       Min cumulative merge throttle time across primary shards |                          |          0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |          0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |     1.8385 |    min |
|                      Cumulative refresh time of primary shards |                          |     0.1798 |    min |
|                     Cumulative refresh count of primary shards |                          |       1383 |        |
|              Min cumulative refresh time across primary shards |                          |          0 |    min |
|           Median cumulative refresh time across primary shards |                          |          0 |    min |
|              Max cumulative refresh time across primary shards |                          |     0.0919 |    min |
|                        Cumulative flush time of primary shards |                          |     0.0114 |    min |
|                       Cumulative flush count of primary shards |                          |         78 |        |
|                Min cumulative flush time across primary shards |                          |          0 |    min |
|             Median cumulative flush time across primary shards |                          |          0 |    min |
|                Max cumulative flush time across primary shards |                          | 0.00781667 |    min |
|                                        Total Young Gen GC time |                          |       0.56 |      s |
|                                       Total Young Gen GC count |                          |        319 |        |
|                                          Total Old Gen GC time |                          |      0.059 |      s |
|                                         Total Old Gen GC count |                          |          2 |        |
|                                                     Store size |                          |    2.24142 |     GB |
|                                                  Translog size |                          |   0.670547 |     GB |
|                                         Heap used for segments |                          |          0 |     MB |
|                                       Heap used for doc values |                          |          0 |     MB |
|                                            Heap used for terms |                          |          0 |     MB |
|                                            Heap used for norms |                          |          0 |     MB |
|                                           Heap used for points |                          |          0 |     MB |
|                                    Heap used for stored fields |                          |          0 |     MB |
|                                                  Segment count |                          |        176 |        |
|                                                 Min Throughput |             index-append |    15442.9 | docs/s |
|                                                Mean Throughput |             index-append |    15959.1 | docs/s |
|                                              Median Throughput |             index-append |    16090.6 | docs/s |
|                                                 Max Throughput |             index-append |      16112 | docs/s |
|                                        50th percentile latency |             index-append |    3.60958 |     ms |
|                                        90th percentile latency |             index-append |    4.11443 |     ms |
|                                        99th percentile latency |             index-append |     6.6752 |     ms |
|                                      99.9th percentile latency |             index-append |    10.4504 |     ms |
|                                       100th percentile latency |             index-append |    15.0526 |     ms |
|                                   50th percentile service time |             index-append |    3.60958 |     ms |
|                                   90th percentile service time |             index-append |    4.11443 |     ms |
|                                   99th percentile service time |             index-append |     6.6752 |     ms |
|                                 99.9th percentile service time |             index-append |    10.4504 |     ms |
|                                  100th percentile service time |             index-append |    15.0526 |     ms |
|                                                     error rate |             index-append |          0 |      % |
|                                                 Min Throughput | wait-until-merges-finish |      21.67 |  ops/s |
|                                                Mean Throughput | wait-until-merges-finish |      21.67 |  ops/s |
|                                              Median Throughput | wait-until-merges-finish |      21.67 |  ops/s |
|                                                 Max Throughput | wait-until-merges-finish |      21.67 |  ops/s |
|                                       100th percentile latency | wait-until-merges-finish |    45.5904 |     ms |
|                                  100th percentile service time | wait-until-merges-finish |    45.5904 |     ms |
|                                                     error rate | wait-until-merges-finish |          0 |      % |
|                                                 Min Throughput |                  default |      99.89 |  ops/s |
|                                                Mean Throughput |                  default |      99.91 |  ops/s |
|                                              Median Throughput |                  default |      99.91 |  ops/s |
|                                                 Max Throughput |                  default |      99.93 |  ops/s |
|                                        50th percentile latency |                  default |    3.20208 |     ms |
|                                        90th percentile latency |                  default |    5.11781 |     ms |
|                                        99th percentile latency |                  default |    6.38286 |     ms |
|                                       100th percentile latency |                  default |    6.96813 |     ms |
|                                   50th percentile service time |                  default |    2.16298 |     ms |
|                                   90th percentile service time |                  default |    4.14619 |     ms |
|                                   99th percentile service time |                  default |    5.25284 |     ms |
|                                  100th percentile service time |                  default |     5.8795 |     ms |
|                                                     error rate |                  default |          0 |      % |
|                                                 Min Throughput |            sparse-search |       9.99 |  ops/s |
|                                                Mean Throughput |            sparse-search |       9.99 |  ops/s |
|                                              Median Throughput |            sparse-search |       9.99 |  ops/s |
|                                                 Max Throughput |            sparse-search |       9.99 |  ops/s |
|                                        50th percentile latency |            sparse-search |    47.2827 |     ms |
|                                        90th percentile latency |            sparse-search |    48.0657 |     ms |
|                                        99th percentile latency |            sparse-search |    49.2571 |     ms |
|                                       100th percentile latency |            sparse-search |    50.8855 |     ms |
|                                   50th percentile service time |            sparse-search |    45.7156 |     ms |
|                                   90th percentile service time |            sparse-search |    46.4979 |     ms |
|                                   99th percentile service time |            sparse-search |    47.5054 |     ms |
|                                  100th percentile service time |            sparse-search |    47.5916 |     ms |
|                                                     error rate |            sparse-search |          0 |      % |


---------------------------------
[INFO] SUCCESS (took 178 seconds)
---------------------------------
```

### License

- For quora dataset, we use the same license for the data as the original data: [CC-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/), also see the LICENSE.txt file within this workload for the license information

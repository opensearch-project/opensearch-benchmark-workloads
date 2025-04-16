## AI Search Workload

This workload is to benchmark performance of indexing and search for different search methods (Semantic, Hybrid, Sparse and multimodal). Check this [link](https://opensearch.org/docs/latest/vector-search/ai-search/index/) for more information about AI search. 
### Dataset

The Quora Question Pairs (QQP) dataset, released by Quora, is a collection of over 400,000 question pairs, each labeled to indicate whether the two questions are paraphrases of each other, used for research in natural language processing and machine learning.
- Quora website: https://www.quora.com/q/quoradata/First-Quora-Dataset-Release-Question-Pairs
- Dataset: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/quora.zip

### Example document and query for Quora dataset
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
Before running a benchmark, ensure that the load generation host is able to access your cluster endpoint, which can be verified by a `curl $ENDPOINT` command.

By default, we use pretrained models for the workload, so steps to train the model being used are not required. Currently, we support 1 test procedures for the AI search workload, the default procedure is named sparse-search. This test procedures will index a data set of vectors into an OpenSearch cluster and then run a set of queries against the generated index.

Due to the number of parameters this workload offers, it's recommended to create a parameter file that specifies the desired workload parameters instead of listing them all on the OSB command line. An example parameter file `sparse_search.json` is provided in the `params` directory within this workload.

To run the workload, invoke the following command with the params file.
```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT= https://search.example.com
# Absolute file path of Workload param file
export PARAMS_FILE=/path/to/params.json

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

This test procedure carries out the following steps:
 - Delete the current index and model
 - Ingests the data corpus with vector embedding
 - Runs a force-merge
 - Performs the sparse search

The full list of tasks is provided below:
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
- match-all-search
- sparse-search

### Parameters

This workload allows [specifying the following parameters](#specifying-workload-parameters) using the `--workload-params` option to OpenSearch Benchmark:

* `allow_registering_model_via_url` (default: true): Whether allows user to register models using a URL
* `bulk_indexing_clients` (default: 1): Number of clients that issue bulk indexing requests.
* `bulk_size` (default: 100): Number of documents to be ingested in the bulk request.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `corpora_name`: Name of the corpora
* `default_ingest_pipeline` (default: nlp-default-ingest-pipeline): name of the ingest pipeline
* `dimensions` (default: 768): Vector dimensions, needed to match the model.
* `engine` (default:` lucene): The approximate k-NN library to use for indexing and search.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `flush_threshold_size` (default: "1g") Size when reached to flush the translog
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `index_body`: Body of the index setting, must pass as workload parameter
* `index_knn`: Whether to create a vector index, required as parameter for all search methods EXCEPT sparse search
* `index_name`: Name of the index, must pass as workload parameter
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `iterations`  Number of test iterations of each search client executes.
* `k` (default: 10) Number of nearest neighbors are returned.
* `method` (default:` hnsw): K-NN search algorithm.
* `model_config_file` (default: "") Config file for the model
* `model_format` (default: TORCH_SCRIPT) Model format.
* `model_name` (default: amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill) OpenSearch-provided pretrained model name.
* `model_version` (default: 1.0.0) Model version.
* `native_memory_threshold` (default: 99): Sets a circuit breaker that checks all system memory usage before running an ML task. If the native memory exceeds the threshold, OpenSearch throws an exception and stops running any ML task
* `number_of_replicas` (default: 0): Number of replicas for indexes in the cluster
* `number_of_shards` (default: 1): Number of primary shards in the index
* `only_run_on_ml_node` (default: false): If true, ML Commons tasks and models run ML tasks on ML nodes only. If false, tasks and models run on ML nodes first. If no ML nodes exist, tasks and models run on data nodes
* `passage_embedding_type`: Embedding type of the passage, must pass as workload parameter for sparse search procedure
* `prune_ratio` (default: 0.1): The ratio for the pruning strategy. Required when `prune_type` is specified.
* `prune_type` (default: max_ratio): The prune strategy for sparse vectors. Valid values are max_ratio, alpha_mass, top_k, abs_value, and none. This parameter is only required for sparse search
* `query_cache_enabled` (default: false): Enables or disables the index query cache
* `refresh_interval` (default: "5s") Interval to refresh the index in seconds
* `requests_cache_enabled` (default: false): Enables or disables the index request cache
* `search_clients`: Number of clients that issue search requests.
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `space_type` (default:` l2): The vector space used to calculate the distance between vectors.
* `target_throughput` (default: default values for each operation): Number of requests per second, `""` for no limit.
* `variable_queries` (default: 0) Number of variable queries will be used for the semantic search task, 0 means fixed query.
* `warmup_iterations` Number of Warmup iteration of each search client executes.
* `warmup-time-period` (default: 120): Amount of time, in seconds, to warm up the benchmark candidate

### Specifying Workload Parameters

Example:
```json
{
  "passage_embedding_type": "rank_features",
  "index_name": "quora",
  "index_body": "indices/quora.json",
  "corpora_name": "quora",
  "ingest_percentage": 100,
  "variable_queries": 0,
  "warmup_time_period": 5,
  "default_ingest_pipeline": "nlp-default-ingest-pipeline-sparse"
}
 ```

This is already setup as `sparse_search.json` in params directory, provide it to OpenSearch Benchmark with `--workload-params="/path/to/sparse_search.json"`. If only one or two parameters need to be specified, rather than using a parameter file, they can be specified on the command line like so: --workload-params=search_clients:2.

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

[INFO] [Test Execution ID]: b8d17b2d-746b-48a6-af43-556005590efc
[INFO] Executing test with workload [neural_search], test_procedure [sparse-search] and provision_config_instance ['external'] with version [2.19.0].

[WARNING] merges_total_time is 102 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 32 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 93 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
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
Running match-all                                                              [100% done]
Running sparse-search                                                          [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------
            
|                                                         Metric |                     Task |     Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|----------:|-------:|
|                     Cumulative indexing time of primary shards |                          |  0.238333 |    min |
|             Min cumulative indexing time across primary shards |                          |         0 |    min |
|          Median cumulative indexing time across primary shards |                          |         0 |    min |
|             Max cumulative indexing time across primary shards |                          |    0.2098 |    min |
|            Cumulative indexing throttle time of primary shards |                          |         0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |         0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |         0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |         0 |    min |
|                        Cumulative merge time of primary shards |                          |   0.85035 |    min |
|                       Cumulative merge count of primary shards |                          |         7 |        |
|                Min cumulative merge time across primary shards |                          |         0 |    min |
|             Median cumulative merge time across primary shards |                          |         0 |    min |
|                Max cumulative merge time across primary shards |                          |    0.8348 |    min |
|               Cumulative merge throttle time of primary shards |                          |   0.71885 |    min |
|       Min cumulative merge throttle time across primary shards |                          |         0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |         0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |   0.71885 |    min |
|                      Cumulative refresh time of primary shards |                          |    0.0269 |    min |
|                     Cumulative refresh count of primary shards |                          |       481 |        |
|              Min cumulative refresh time across primary shards |                          |         0 |    min |
|           Median cumulative refresh time across primary shards |                          |         0 |    min |
|              Max cumulative refresh time across primary shards |                          | 0.0168333 |    min |
|                        Cumulative flush time of primary shards |                          |   0.00455 |    min |
|                       Cumulative flush count of primary shards |                          |         1 |        |
|                Min cumulative flush time across primary shards |                          |         0 |    min |
|             Median cumulative flush time across primary shards |                          |         0 |    min |
|                Max cumulative flush time across primary shards |                          |   0.00455 |    min |
|                                        Total Young Gen GC time |                          |     0.674 |      s |
|                                       Total Young Gen GC count |                          |       345 |        |
|                                          Total Old Gen GC time |                          |      0.16 |      s |
|                                         Total Old Gen GC count |                          |         3 |        |
|                                                     Store size |                          |   8.11566 |     GB |
|                                                  Translog size |                          |  0.642941 |     GB |
|                                         Heap used for segments |                          |         0 |     MB |
|                                       Heap used for doc values |                          |         0 |     MB |
|                                            Heap used for terms |                          |         0 |     MB |
|                                            Heap used for norms |                          |         0 |     MB |
|                                           Heap used for points |                          |         0 |     MB |
|                                    Heap used for stored fields |                          |         0 |     MB |
|                                                  Segment count |                          |       220 |        |
|                                                 Min Throughput |             index-append |   49997.9 | docs/s |
|                                                Mean Throughput |             index-append |   54492.8 | docs/s |
|                                              Median Throughput |             index-append |     55239 | docs/s |
|                                                 Max Throughput |             index-append |   57495.2 | docs/s |
|                                        50th percentile latency |             index-append |   8.41481 |     ms |
|                                        90th percentile latency |             index-append |   12.9676 |     ms |
|                                        99th percentile latency |             index-append |   23.6447 |     ms |
|                                      99.9th percentile latency |             index-append |   296.772 |     ms |
|                                       100th percentile latency |             index-append |   346.362 |     ms |
|                                   50th percentile service time |             index-append |   8.41481 |     ms |
|                                   90th percentile service time |             index-append |   12.9676 |     ms |
|                                   99th percentile service time |             index-append |   23.6447 |     ms |
|                                 99.9th percentile service time |             index-append |   296.772 |     ms |
|                                  100th percentile service time |             index-append |   346.362 |     ms |
|                                                     error rate |             index-append |         0 |      % |
|                                                 Min Throughput | wait-until-merges-finish |     22.75 |  ops/s |
|                                                Mean Throughput | wait-until-merges-finish |     22.75 |  ops/s |
|                                              Median Throughput | wait-until-merges-finish |     22.75 |  ops/s |
|                                                 Max Throughput | wait-until-merges-finish |     22.75 |  ops/s |
|                                       100th percentile latency | wait-until-merges-finish |   43.5016 |     ms |
|                                  100th percentile service time | wait-until-merges-finish |   43.5016 |     ms |
|                                                     error rate | wait-until-merges-finish |         0 |      % |
|                                                 Min Throughput |                match-all |     99.79 |  ops/s |
|                                                Mean Throughput |                match-all |     99.84 |  ops/s |
|                                              Median Throughput |                match-all |     99.84 |  ops/s |
|                                                 Max Throughput |                match-all |     99.87 |  ops/s |
|                                        50th percentile latency |                match-all |   3.75933 |     ms |
|                                        90th percentile latency |                match-all |   5.12179 |     ms |
|                                        99th percentile latency |                match-all |   7.12119 |     ms |
|                                       100th percentile latency |                match-all |   11.4097 |     ms |
|                                   50th percentile service time |                match-all |   2.76821 |     ms |
|                                   90th percentile service time |                match-all |   4.35323 |     ms |
|                                   99th percentile service time |                match-all |   6.15755 |     ms |
|                                  100th percentile service time |                match-all |    10.635 |     ms |
|                                                     error rate |                match-all |         0 |      % |
|                                                 Min Throughput |            sparse-search |      9.84 |  ops/s |
|                                                Mean Throughput |            sparse-search |      9.88 |  ops/s |
|                                              Median Throughput |            sparse-search |      9.88 |  ops/s |
|                                                 Max Throughput |            sparse-search |      9.91 |  ops/s |
|                                        50th percentile latency |            sparse-search |   47.7587 |     ms |
|                                        90th percentile latency |            sparse-search |   48.5417 |     ms |
|                                        99th percentile latency |            sparse-search |   50.0997 |     ms |
|                                       100th percentile latency |            sparse-search |   50.4377 |     ms |
|                                   50th percentile service time |            sparse-search |   46.2167 |     ms |
|                                   90th percentile service time |            sparse-search |   47.0693 |     ms |
|                                   99th percentile service time |            sparse-search |   48.4767 |     ms |
|                                  100th percentile service time |            sparse-search |   48.9709 |     ms |
|                                                     error rate |            sparse-search |         0 |      % |


---------------------------------
[INFO] SUCCESS (took 159 seconds)
---------------------------------
```

### License

- For quora dataset, we use the same license for the data as the original data: [CC-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/), also see the LICENSE.txt file within this workload for the license information

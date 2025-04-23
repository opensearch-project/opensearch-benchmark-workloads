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

By default, we use pretrained models for the workload, so steps to train the model being used are not required. Currently, we support 3 test procedures for the AI search workload, the default procedure is named sparse-search. This test procedures will index a data set of vectors into an OpenSearch cluster and then run a set of queries against the generated index.

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

#### sparse-search, hybrid-search, semantic-search

These test procedures carry out the following steps:
 - Delete the current index and model
 - Ingests the data corpus with vector embedding
 - Runs a force-merge
 - Performs the sparse search

The full list of tasks is provided below:
### Workload tasks:

- delete-index
- delete-normalization-search-pipeline (hybrid search only)
- delete-ingest-pipeline
- delete-ml-model
- put-cluster-settings
- register-ml-model
- deploy-ml-model
- create-ingest-pipeline
- create-normalization-search-pipeline (hybrid search only)
- create-index
- check-cluster-health
- index-append
- refresh-after-index
- force-merge
- refresh-after-force-merge
- wait-until-merges-finish
- match-all-search
- <search_method_name>-search (e.g. sparse-search, semantic-search excluding hybrid search)
- hybrid-search-with-search-pipeline (hybrid search only)
- hybrid-search-with-temporary-pipeline (hybrid search only, note that the temporary pipeline is created during search, so not necessary to explicitly create it)
 
### Parameters

This workload allows [specifying the following parameters](#specifying-workload-parameters) using the `--workload-params` option to OpenSearch Benchmark:

* `allow_registering_model_via_url` (default: true): Whether allows user to register models using a URL
* `bulk_indexing_clients` (default: 1): Number of clients that issue bulk indexing requests.
* `bulk_size` (default: 100): Number of documents to be ingested in the bulk request.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `corpora_name`: Name of the corpora
* `combination_technique` (default: arithmetic_mean): The technique for combining scores. Valid values are arithmetic_mean, geometric_mean, and harmonic_mean. Only applicable to Hybrid search with normalization-processor enabled
* `combination_parameters_weights`: Specifies the weights to use for each query. Valid values are in the [0.0, 1.0] range and signify decimal percentages. The number of values in the weights array must equal the number of queries. 
  The sum of the values in the array must equal 1.0. Optional. If not provided, all queries are given equal weight. Only applicable to Hybrid search with normalization-processor enabled
* `default_ingest_pipeline` (default: nlp-default-ingest-pipeline): name of the ingest pipeline
* `dimensions` (default: 768): Vector dimensions, needed to match the model.
* `engine` (default:` lucene): The approximate k-NN library to use for indexing and search.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `flush_threshold_size` (default: "1g"): Size when reached to flush the translog
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `hybrid_query_size` (default: 10): Size of Hybrid query
* `index_body`: Body of the index setting, must pass as workload parameter
* `index_knn`: Whether to create a vector index, required as parameter for all search methods EXCEPT sparse search
* `index_name`: Name of the index, must pass as workload parameter
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `iterations`:  Number of test iterations of each search client executes.
* `k`: The number of results returned by the k-NN search. Only one variable, either k, min_score, or max_distance, can be specified. If a variable is not specified, the default is k with a value of 10.
* `max_distance`: The maximum distance threshold for the search results. Only one variable, either k, min_score, or max_distance, can be specified. 
* `method` (default:` hnsw): K-NN search algorithm.
* `min_score`: The minimum score threshold for the search results. Only one variable, either k, min_score, or max_distance, can be specified
* `model_config_file` (default: ""): Config file for the model
* `model_format` (default: TORCH_SCRIPT): Model format.
* `model_name` (default: amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill): OpenSearch-provided pretrained model name.
* `model_version` (default: 1.0.0): Model version.
* `native_memory_threshold` (default: 99): Sets a circuit breaker that checks all system memory usage before running an ML task. If the native memory exceeds the threshold, OpenSearch throws an exception and stops running any ML task
* `normalization_technique` (default: min_max): The technique for normalizing scores. Valid values are min_max, l2 and z-score (available in OpenSearch 3.0). Only applicable to Hybrid search with normalization-processor enabled
* `number_of_replicas` (default: 0): Number of replicas for indexes in the cluster
* `number_of_shards` (default: 1): Number of primary shards in the index
* `only_run_on_ml_node` (default: false): If true, ML Commons tasks and models run ML tasks on ML nodes only. If false, tasks and models run on ML nodes first. If no ML nodes exist, tasks and models run on data nodes
* `passage_embedding_type`: Embedding type of the passage, must pass as workload parameter for sparse search procedure
* `prune_ratio` (default: 0.1): The ratio for the pruning strategy. Required when `prune_type` is specified.
* `prune_type` (default: max_ratio): The prune strategy for sparse vectors. Valid values are max_ratio, alpha_mass, top_k, abs_value, and none. This parameter is only required for sparse search
* `query_cache_enabled` (default: false): Enables or disables the index query cache
* `rank_constant` (default: 60): A constant added to each document’s rank before calculating the reciprocal score. Only applicable to Hybrid search with score-ranker-processor enabled
* `refresh_interval` (default: "5s"): Interval to refresh the index in seconds
* `requests_cache_enabled` (default: false): Enables or disables the index request cache
* `search_clients`: Number of clients that issue search requests.
* `search_pipeline_processor`: Types of processors for hybrid search, available processors are normalization-processor and score-ranker-processor, if not defined, normalization-processor will be chosen
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `space_type` (default:` l2): The vector space used to calculate the distance between vectors.
* `target_throughput` (default: default values for each operation): Number of requests per second, `""` for no limit.
* `variable_queries` (default: 0) Number of variable queries will be used for the semantic search task, 0 means fixed query.
* `warmup_iterations`: Number of Warmup iteration of each search client executes.
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
We also provide necessary parameters for Semantic and Hybrid search, check `semantic_search.json` and `hybrid_search.json` in params directory

### Sample command and output for sparse-search with 10% ingest_percentage

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

[INFO] [Test Execution ID]: f9113820-8a4a-4d77-b31a-ac8f7c75a33a
[INFO] Executing test with workload [neural_search], test_procedure [sparse-search] and provision_config_instance ['external'] with version [2.19.0].

[WARNING] merges_total_time is 154 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 281 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 197 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 104 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-index                                                           [100% done]
Running delete-ingest-pipeline                                                 [100% done]
Running delete-ml-model-sparse                                                 [100% done]
Running put-cluster-settings                                                   [100% done]
Running register-ml-model-sparse                                               [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-ingest-pipeline-sparse                                          [100% done]
Running create-index                                                           [100% done]
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
            
|                                                         Metric |                     Task |      Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|-----------:|-------:|
|                     Cumulative indexing time of primary shards |                          |   0.262283 |    min |
|             Min cumulative indexing time across primary shards |                          |          0 |    min |
|          Median cumulative indexing time across primary shards |                          |          0 |    min |
|             Max cumulative indexing time across primary shards |                          |    0.20625 |    min |
|            Cumulative indexing throttle time of primary shards |                          |          0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |          0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |          0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |          0 |    min |
|                        Cumulative merge time of primary shards |                          |   0.251083 |    min |
|                       Cumulative merge count of primary shards |                          |         13 |        |
|                Min cumulative merge time across primary shards |                          |          0 |    min |
|             Median cumulative merge time across primary shards |                          |          0 |    min |
|                Max cumulative merge time across primary shards |                          |   0.227917 |    min |
|               Cumulative merge throttle time of primary shards |                          |    0.21825 |    min |
|       Min cumulative merge throttle time across primary shards |                          |          0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |          0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |    0.21825 |    min |
|                      Cumulative refresh time of primary shards |                          |     0.0664 |    min |
|                     Cumulative refresh count of primary shards |                          |        249 |        |
|              Min cumulative refresh time across primary shards |                          |          0 |    min |
|           Median cumulative refresh time across primary shards |                          |          0 |    min |
|              Max cumulative refresh time across primary shards |                          |  0.0531833 |    min |
|                        Cumulative flush time of primary shards |                          |  0.0123833 |    min |
|                       Cumulative flush count of primary shards |                          |         19 |        |
|                Min cumulative flush time across primary shards |                          |          0 |    min |
|             Median cumulative flush time across primary shards |                          |          0 |    min |
|                Max cumulative flush time across primary shards |                          | 0.00746667 |    min |
|                                        Total Young Gen GC time |                          |      3.157 |      s |
|                                       Total Young Gen GC count |                          |        341 |        |
|                                          Total Old Gen GC time |                          |          0 |      s |
|                                         Total Old Gen GC count |                          |          0 |        |
|                                                     Store size |                          |   0.812424 |     GB |
|                                                  Translog size |                          | 0.00059478 |     GB |
|                                         Heap used for segments |                          |          0 |     MB |
|                                       Heap used for doc values |                          |          0 |     MB |
|                                            Heap used for terms |                          |          0 |     MB |
|                                            Heap used for norms |                          |          0 |     MB |
|                                           Heap used for points |                          |          0 |     MB |
|                                    Heap used for stored fields |                          |          0 |     MB |
|                                                  Segment count |                          |         50 |        |
|                                                 Min Throughput |             index-append |     135.75 | docs/s |
|                                                Mean Throughput |             index-append |     138.67 | docs/s |
|                                              Median Throughput |             index-append |      137.2 | docs/s |
|                                                 Max Throughput |             index-append |     172.01 | docs/s |
|                                        50th percentile latency |             index-append |    5862.68 |     ms |
|                                        90th percentile latency |             index-append |       6282 |     ms |
|                                        99th percentile latency |             index-append |    6810.27 |     ms |
|                                       100th percentile latency |             index-append |    7018.13 |     ms |
|                                   50th percentile service time |             index-append |    5862.68 |     ms |
|                                   90th percentile service time |             index-append |       6282 |     ms |
|                                   99th percentile service time |             index-append |    6810.27 |     ms |
|                                  100th percentile service time |             index-append |    7018.13 |     ms |
|                                                     error rate |             index-append |          0 |      % |
|                                                 Min Throughput | wait-until-merges-finish |      58.79 |  ops/s |
|                                                Mean Throughput | wait-until-merges-finish |      58.79 |  ops/s |
|                                              Median Throughput | wait-until-merges-finish |      58.79 |  ops/s |
|                                                 Max Throughput | wait-until-merges-finish |      58.79 |  ops/s |
|                                       100th percentile latency | wait-until-merges-finish |    16.5668 |     ms |
|                                  100th percentile service time | wait-until-merges-finish |    16.5668 |     ms |
|                                                     error rate | wait-until-merges-finish |          0 |      % |
|                                                 Min Throughput |                match-all |      99.86 |  ops/s |
|                                                Mean Throughput |                match-all |      99.89 |  ops/s |
|                                              Median Throughput |                match-all |       99.9 |  ops/s |
|                                                 Max Throughput |                match-all |      99.92 |  ops/s |
|                                        50th percentile latency |                match-all |      3.811 |     ms |
|                                        90th percentile latency |                match-all |    5.15052 |     ms |
|                                        99th percentile latency |                match-all |    6.75557 |     ms |
|                                       100th percentile latency |                match-all |      8.057 |     ms |
|                                   50th percentile service time |                match-all |    2.82021 |     ms |
|                                   90th percentile service time |                match-all |    4.19529 |     ms |
|                                   99th percentile service time |                match-all |    5.80084 |     ms |
|                                  100th percentile service time |                match-all |    7.61792 |     ms |
|                                                     error rate |                match-all |          0 |      % |
|                                                 Min Throughput |            sparse-search |       9.98 |  ops/s |
|                                                Mean Throughput |            sparse-search |       9.99 |  ops/s |
|                                              Median Throughput |            sparse-search |       9.99 |  ops/s |
|                                                 Max Throughput |            sparse-search |       9.99 |  ops/s |
|                                        50th percentile latency |            sparse-search |    55.6142 |     ms |
|                                        90th percentile latency |            sparse-search |    57.5806 |     ms |
|                                        99th percentile latency |            sparse-search |    69.8495 |     ms |
|                                       100th percentile latency |            sparse-search |    70.3124 |     ms |
|                                   50th percentile service time |            sparse-search |    54.0472 |     ms |
|                                   90th percentile service time |            sparse-search |    56.3233 |     ms |
|                                   99th percentile service time |            sparse-search |    68.5102 |     ms |
|                                  100th percentile service time |            sparse-search |    68.9099 |     ms |
|                                                     error rate |            sparse-search |          0 |      % |


---------------------------------
[INFO] SUCCESS (took 546 seconds)
---------------------------------
```

### Sample command and output for hybrid-search with 10% ingest_percentage
```
./opensearch-benchmark execute-test --pipeline=benchmark-only \
--workload=neural_search \
--workload-params=/path/to/opensearch-benchmark-workloads/neural_search/params/hybrid_search.json \
--test-procedure=hybrid-search --kill-running-processes



   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] [Test Execution ID]: 85db33b8-d729-401b-93a1-8f9fd85cd8f4
[INFO] Executing test with workload [neural_search], test_procedure [hybrid-search] and provision_config_instance ['external'] with version [2.19.0].

[WARNING] merges_total_time is 217412 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] merges_total_throttled_time is 185087 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 59557 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 10188 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 3546 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-index                                                           [100% done]
Running delete-search-pipeline                                                 [100% done]
Running delete-ingest-pipeline                                                 [100% done]
Running delete-ml-model-sentence-transformer                                   [100% done]
Running put-cluster-settings                                                   [100% done]
Running register-ml-model-sentence-transformer                                 [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-text-embedding-processor-ingest-pipeline                        [100% done]
Running create-search-pipeline                                                 [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running match-all                                                              [100% done]
Running hybrid-search-with-search-pipeline                                     [100% done]
Running hybrid-search-with-temporary-pipeline                                  [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------
            
|                                                         Metric |                                  Task |      Value |   Unit |
|---------------------------------------------------------------:|--------------------------------------:|-----------:|-------:|
|                     Cumulative indexing time of primary shards |                                       |    2.18425 |    min |
|             Min cumulative indexing time across primary shards |                                       |          0 |    min |
|          Median cumulative indexing time across primary shards |                                       |          0 |    min |
|             Max cumulative indexing time across primary shards |                                       |    1.35263 |    min |
|            Cumulative indexing throttle time of primary shards |                                       |          0 |    min |
|    Min cumulative indexing throttle time across primary shards |                                       |          0 |    min |
| Median cumulative indexing throttle time across primary shards |                                       |          0 |    min |
|    Max cumulative indexing throttle time across primary shards |                                       |          0 |    min |
|                        Cumulative merge time of primary shards |                                       |    7.35158 |    min |
|                       Cumulative merge count of primary shards |                                       |         40 |        |
|                Min cumulative merge time across primary shards |                                       |          0 |    min |
|             Median cumulative merge time across primary shards |                                       |          0 |    min |
|                Max cumulative merge time across primary shards |                                       |    3.63767 |    min |
|               Cumulative merge throttle time of primary shards |                                       |     4.3705 |    min |
|       Min cumulative merge throttle time across primary shards |                                       |          0 |    min |
|    Median cumulative merge throttle time across primary shards |                                       |          0 |    min |
|       Max cumulative merge throttle time across primary shards |                                       |     2.0946 |    min |
|                      Cumulative refresh time of primary shards |                                       |   0.338217 |    min |
|                     Cumulative refresh count of primary shards |                                       |        845 |        |
|              Min cumulative refresh time across primary shards |                                       |          0 |    min |
|           Median cumulative refresh time across primary shards |                                       |          0 |    min |
|              Max cumulative refresh time across primary shards |                                       |   0.186317 |    min |
|                        Cumulative flush time of primary shards |                                       |    0.07625 |    min |
|                       Cumulative flush count of primary shards |                                       |         38 |        |
|                Min cumulative flush time across primary shards |                                       |          0 |    min |
|             Median cumulative flush time across primary shards |                                       |          0 |    min |
|                Max cumulative flush time across primary shards |                                       |  0.0315167 |    min |
|                                        Total Young Gen GC time |                                       |     10.626 |      s |
|                                       Total Young Gen GC count |                                       |        661 |        |
|                                          Total Old Gen GC time |                                       |      0.031 |      s |
|                                         Total Old Gen GC count |                                       |          1 |        |
|                                                     Store size |                                       |    6.66965 |     GB |
|                                                  Translog size |                                       | 0.00104755 |     GB |
|                                         Heap used for segments |                                       |          0 |     MB |
|                                       Heap used for doc values |                                       |          0 |     MB |
|                                            Heap used for terms |                                       |          0 |     MB |
|                                            Heap used for norms |                                       |          0 |     MB |
|                                           Heap used for points |                                       |          0 |     MB |
|                                    Heap used for stored fields |                                       |          0 |     MB |
|                                                  Segment count |                                       |        134 |        |
|                                                 Min Throughput |                          index-append |      99.85 | docs/s |
|                                                Mean Throughput |                          index-append |     103.08 | docs/s |
|                                              Median Throughput |                          index-append |     101.38 | docs/s |
|                                                 Max Throughput |                          index-append |     152.67 | docs/s |
|                                        50th percentile latency |                          index-append |    7910.93 |     ms |
|                                        90th percentile latency |                          index-append |    8575.66 |     ms |
|                                        99th percentile latency |                          index-append |    9215.16 |     ms |
|                                       100th percentile latency |                          index-append |    9737.43 |     ms |
|                                   50th percentile service time |                          index-append |    7910.93 |     ms |
|                                   90th percentile service time |                          index-append |    8575.66 |     ms |
|                                   99th percentile service time |                          index-append |    9215.16 |     ms |
|                                  100th percentile service time |                          index-append |    9737.43 |     ms |
|                                                     error rate |                          index-append |          0 |      % |
|                                                 Min Throughput |              wait-until-merges-finish |      26.45 |  ops/s |
|                                                Mean Throughput |              wait-until-merges-finish |      26.45 |  ops/s |
|                                              Median Throughput |              wait-until-merges-finish |      26.45 |  ops/s |
|                                                 Max Throughput |              wait-until-merges-finish |      26.45 |  ops/s |
|                                       100th percentile latency |              wait-until-merges-finish |     37.062 |     ms |
|                                  100th percentile service time |              wait-until-merges-finish |     37.062 |     ms |
|                                                     error rate |              wait-until-merges-finish |          0 |      % |
|                                                 Min Throughput |                             match-all |      99.87 |  ops/s |
|                                                Mean Throughput |                             match-all |       99.9 |  ops/s |
|                                              Median Throughput |                             match-all |       99.9 |  ops/s |
|                                                 Max Throughput |                             match-all |      99.92 |  ops/s |
|                                        50th percentile latency |                             match-all |    5.78469 |     ms |
|                                        90th percentile latency |                             match-all |    6.39258 |     ms |
|                                        99th percentile latency |                             match-all |    6.93472 |     ms |
|                                       100th percentile latency |                             match-all |       10.2 |     ms |
|                                   50th percentile service time |                             match-all |    4.93931 |     ms |
|                                   90th percentile service time |                             match-all |    5.50767 |     ms |
|                                   99th percentile service time |                             match-all |    5.87576 |     ms |
|                                  100th percentile service time |                             match-all |    9.19983 |     ms |
|                                                     error rate |                             match-all |          0 |      % |
|                                                 Min Throughput |    hybrid-search-with-search-pipeline |       9.97 |  ops/s |
|                                                Mean Throughput |    hybrid-search-with-search-pipeline |       9.98 |  ops/s |
|                                              Median Throughput |    hybrid-search-with-search-pipeline |       9.98 |  ops/s |
|                                                 Max Throughput |    hybrid-search-with-search-pipeline |       9.98 |  ops/s |
|                                        50th percentile latency |    hybrid-search-with-search-pipeline |    59.6321 |     ms |
|                                        90th percentile latency |    hybrid-search-with-search-pipeline |    60.2887 |     ms |
|                                        99th percentile latency |    hybrid-search-with-search-pipeline |    63.8258 |     ms |
|                                       100th percentile latency |    hybrid-search-with-search-pipeline |    64.6748 |     ms |
|                                   50th percentile service time |    hybrid-search-with-search-pipeline |    57.7855 |     ms |
|                                   90th percentile service time |    hybrid-search-with-search-pipeline |    58.3824 |     ms |
|                                   99th percentile service time |    hybrid-search-with-search-pipeline |    61.7467 |     ms |
|                                  100th percentile service time |    hybrid-search-with-search-pipeline |    62.7659 |     ms |
|                                                     error rate |    hybrid-search-with-search-pipeline |          0 |      % |
|                                                 Min Throughput | hybrid-search-with-temporary-pipeline |         10 |  ops/s |
|                                                Mean Throughput | hybrid-search-with-temporary-pipeline |         10 |  ops/s |
|                                              Median Throughput | hybrid-search-with-temporary-pipeline |         10 |  ops/s |
|                                                 Max Throughput | hybrid-search-with-temporary-pipeline |         10 |  ops/s |
|                                        50th percentile latency | hybrid-search-with-temporary-pipeline |    59.4511 |     ms |
|                                        90th percentile latency | hybrid-search-with-temporary-pipeline |    60.3391 |     ms |
|                                        99th percentile latency | hybrid-search-with-temporary-pipeline |    63.0461 |     ms |
|                                       100th percentile latency | hybrid-search-with-temporary-pipeline |    81.8345 |     ms |
|                                   50th percentile service time | hybrid-search-with-temporary-pipeline |    57.8172 |     ms |
|                                   90th percentile service time | hybrid-search-with-temporary-pipeline |    58.4961 |     ms |
|                                   99th percentile service time | hybrid-search-with-temporary-pipeline |    61.5226 |     ms |
|                                  100th percentile service time | hybrid-search-with-temporary-pipeline |     80.107 |     ms |
|                                                     error rate | hybrid-search-with-temporary-pipeline |          0 |      % |


---------------------------------
[INFO] SUCCESS (took 719 seconds)
---------------------------------
```

### Sample command and output for semantic-search with 10% ingest_percentage
```
./opensearch-benchmark execute-test --pipeline=benchmark-only \
--workload=neural_search \
--workload-params=/path/to/opensearch-benchmark-workloads/neural_search/params/semantic_search.json \
--test-procedure=semantic-search --kill-running-processes



   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] [Test Execution ID]: 48a02517-0429-49fd-8d04-2494a0c0f2ef
[INFO] Executing test with workload [neural_search], test_procedure [semantic-search] and provision_config_instance ['external'] with version [2.19.0].

[WARNING] merges_total_time is 241478 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] merges_total_throttled_time is 80053 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 89015 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 12355 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 1902 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-index                                                           [100% done]
Running delete-ingest-pipeline                                                 [100% done]
Running delete-ml-model-sentence-transformer                                   [100% done]
Running put-cluster-settings                                                   [100% done]
Running register-ml-model-sentence-transformer                                 [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-text-embedding-processor-ingest-pipeline                        [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running match-all                                                              [100% done]
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
|                     Cumulative indexing time of primary shards |                          |     1.45082 |    min |
|             Min cumulative indexing time across primary shards |                          |           0 |    min |
|          Median cumulative indexing time across primary shards |                          | 1.66667e-05 |    min |
|             Max cumulative indexing time across primary shards |                          |     1.33567 |    min |
|            Cumulative indexing throttle time of primary shards |                          |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |           0 |    min |
|                        Cumulative merge time of primary shards |                          |     4.18178 |    min |
|                       Cumulative merge count of primary shards |                          |          18 |        |
|                Min cumulative merge time across primary shards |                          |           0 |    min |
|             Median cumulative merge time across primary shards |                          |           0 |    min |
|                Max cumulative merge time across primary shards |                          |     3.46207 |    min |
|               Cumulative merge throttle time of primary shards |                          |     1.57937 |    min |
|       Min cumulative merge throttle time across primary shards |                          |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |    0.884733 |    min |
|                      Cumulative refresh time of primary shards |                          |    0.196833 |    min |
|                     Cumulative refresh count of primary shards |                          |         325 |        |
|              Min cumulative refresh time across primary shards |                          |           0 |    min |
|           Median cumulative refresh time across primary shards |                          | 0.000266667 |    min |
|              Max cumulative refresh time across primary shards |                          |    0.167067 |    min |
|                        Cumulative flush time of primary shards |                          |     0.05605 |    min |
|                       Cumulative flush count of primary shards |                          |          14 |        |
|                Min cumulative flush time across primary shards |                          |           0 |    min |
|             Median cumulative flush time across primary shards |                          |           0 |    min |
|                Max cumulative flush time across primary shards |                          |   0.0244167 |    min |
|                                        Total Young Gen GC time |                          |       9.074 |      s |
|                                       Total Young Gen GC count |                          |         612 |        |
|                                          Total Old Gen GC time |                          |        0.03 |      s |
|                                         Total Old Gen GC count |                          |           1 |        |
|                                                     Store size |                          |     2.36527 |     GB |
|                                                  Translog size |                          | 9.22009e-07 |     GB |
|                                         Heap used for segments |                          |           0 |     MB |
|                                       Heap used for doc values |                          |           0 |     MB |
|                                            Heap used for terms |                          |           0 |     MB |
|                                            Heap used for norms |                          |           0 |     MB |
|                                           Heap used for points |                          |           0 |     MB |
|                                    Heap used for stored fields |                          |           0 |     MB |
|                                                  Segment count |                          |          54 |        |
|                                                 Min Throughput |             index-append |      104.38 | docs/s |
|                                                Mean Throughput |             index-append |      107.34 | docs/s |
|                                              Median Throughput |             index-append |      105.96 | docs/s |
|                                                 Max Throughput |             index-append |      133.87 | docs/s |
|                                        50th percentile latency |             index-append |     7635.14 |     ms |
|                                        90th percentile latency |             index-append |     8153.36 |     ms |
|                                        99th percentile latency |             index-append |     8733.38 |     ms |
|                                       100th percentile latency |             index-append |     8976.95 |     ms |
|                                   50th percentile service time |             index-append |     7635.14 |     ms |
|                                   90th percentile service time |             index-append |     8153.36 |     ms |
|                                   99th percentile service time |             index-append |     8733.38 |     ms |
|                                  100th percentile service time |             index-append |     8976.95 |     ms |
|                                                     error rate |             index-append |           0 |      % |
|                                                 Min Throughput | wait-until-merges-finish |       41.97 |  ops/s |
|                                                Mean Throughput | wait-until-merges-finish |       41.97 |  ops/s |
|                                              Median Throughput | wait-until-merges-finish |       41.97 |  ops/s |
|                                                 Max Throughput | wait-until-merges-finish |       41.97 |  ops/s |
|                                       100th percentile latency | wait-until-merges-finish |      23.545 |     ms |
|                                  100th percentile service time | wait-until-merges-finish |      23.545 |     ms |
|                                                     error rate | wait-until-merges-finish |           0 |      % |
|                                                 Min Throughput |                match-all |        99.8 |  ops/s |
|                                                Mean Throughput |                match-all |       99.84 |  ops/s |
|                                              Median Throughput |                match-all |       99.85 |  ops/s |
|                                                 Max Throughput |                match-all |       99.88 |  ops/s |
|                                        50th percentile latency |                match-all |     5.64821 |     ms |
|                                        90th percentile latency |                match-all |     6.29294 |     ms |
|                                        99th percentile latency |                match-all |     7.06777 |     ms |
|                                       100th percentile latency |                match-all |     9.32783 |     ms |
|                                   50th percentile service time |                match-all |     4.79592 |     ms |
|                                   90th percentile service time |                match-all |     5.39156 |     ms |
|                                   99th percentile service time |                match-all |     6.07555 |     ms |
|                                  100th percentile service time |                match-all |     8.38604 |     ms |
|                                                     error rate |                match-all |           0 |      % |
|                                                 Min Throughput |          semantic-search |        9.96 |  ops/s |
|                                                Mean Throughput |          semantic-search |        9.97 |  ops/s |
|                                              Median Throughput |          semantic-search |        9.97 |  ops/s |
|                                                 Max Throughput |          semantic-search |        9.98 |  ops/s |
|                                        50th percentile latency |          semantic-search |     55.6083 |     ms |
|                                        90th percentile latency |          semantic-search |       56.12 |     ms |
|                                        99th percentile latency |          semantic-search |     57.9657 |     ms |
|                                       100th percentile latency |          semantic-search |     62.4806 |     ms |
|                                   50th percentile service time |          semantic-search |     54.1118 |     ms |
|                                   90th percentile service time |          semantic-search |     54.5326 |     ms |
|                                   99th percentile service time |          semantic-search |     56.4637 |     ms |
|                                  100th percentile service time |          semantic-search |     60.9003 |     ms |
|                                                     error rate |          semantic-search |           0 |      % |


---------------------------------
[INFO] SUCCESS (took 671 seconds)
---------------------------------
```

### License

- For quora dataset, we use the same license for the data as the original data: [CC-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/), also see the LICENSE.txt file within this workload for the license information

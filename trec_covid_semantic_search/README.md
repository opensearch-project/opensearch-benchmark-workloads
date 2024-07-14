# Semantic Search Workload

This workload is aimed to benchmark performance of Semantic Search queries. Ingested documents will have embeddings that are generated during ingestion process by pre-trained local model. 

## Datasets

We usae processed version of trec-covid dataset. Trec-Covid is a dataset collection of documents about COVID-19 information.

- Trec-Covid website: https://ir.nist.gov/covidSubmit/index.html
- Dataset: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip

We processed the dataset by creating 6 copies of the same document and shuffle copies so they are ingested in random order. We create custom artifact for queries by extracting queries portion from original `trec-covid` dataset and generating vector embeddings for query text using 768 dimension vector, same dimensions that used for document ingestion.

### Example Document

Following is example of document that is beeing ingested during indexing:

```json
{
  "title": "Simultaneous Video-EEG-ECG Monitoring to Identify Neurocardiac Dysfunction in Mouse Models of Epilepsy.",
  "metadata": {
    "url": "https://doi.org/10.3791/57300; https://www.ncbi.nlm.nih.gov/pubmed/29443088/",
    "pubmed_id": "29443088"
  }
}
```

Following is example of query:

```json
{
  "_id": "1",
  "query": "what is the origin of COVID-19",
  "vector_embedding": [
    -0.06979332,
    0.05764826,
    ...
  ]
}

```

## Parameters

This workload allows the following parameters to be specified using `--workload-params`:

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
* `range_gte` (default: 100) Number that defines the lower bound (inclusive) for range query when it's used as elemnts in semantic search query
* `range_lte` (default: 10000000) Number that defines the upper bound (inclusive) for range query when it's used as elemnts in semantic search query

### Running a benchmark

Before running a benchmark, ensure that the load generation host is able to access your cluster endpoint and that the 
appropriate dataset is available on the host.

Currently, we support 2 test procedures for the semantic search workload. The default procedure is `create-index-ingest-data-search` and does create an index, ingest data and run a base set of search queries.

To run the default workload, invoke the following command.

```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT=  
# Absolute file path of Workload file
export WORKLOAD_PATH=

opensearch-benchmark execute-test \
 --workload-path=$WORKLOAD_PATH \
 --workload-params="/trec_covid_semantic_search/params/params.json" \
 --pipeline=benchmark-only \
 --target-host=$ENDPOINT \
 --kill-running-processes \
 --test-procedure="search"
```

## Current Procedures

### Create index with data

This procedure creates index, deploy model localy, creaes pipeline with ingest and search processors and ingest documents. At the end we ran the match_all query that returns all documents in the index.
Procedure name `create-index-ingest-data-search`.
This is a default precedure for this workload.

### Run semantic search queries

This search procedure runs semantic search queries: neural, hybrid. It deletes and deploys an ml model and creates processor and uses this model to generate search specific embeddings.
Procedure name `search`.

#### Sample Output

The output of a sample test run is provided below. Metrics are captured in the result's data store as usual, and this can be configured to be 
either in-memory, or an external OpenSearch cluster.

```

   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] [Test Execution ID]: 3ff68a05-9aa7-4375-966e-8e686a8d14d3
[INFO] Executing test with workload [trec_covid_semantic_search], test_procedure [search] and provision_config_instance ['external'] with version [2.15.0].

[WARNING] merges_total_time is 76929 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] merges_total_throttled_time is 56405 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] indexing_total_time is 1884805 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 944585 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 1674638 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-ml-model                                                        [100% done]
Running register-ml-model                                                      [100% done]
Running deploy-ml-model                                                        [100% done]
Running create-normalization-processor-no-weights-search-pipeline              [100% done]
Running semantic-search-neural                                                 [100% done]
Running semantic-search-hybrid-bm25-and-knn-search                             [100% done]
Running semantic-search-hybrid-bm25-and-neural-search                          [100% done]
Running semantic-search-hybrid-bm25-range-and-neural-search                    [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------

|                                                         Metric |                                                Task |     Value |   Unit |
|---------------------------------------------------------------:|----------------------------------------------------:|----------:|-------:|
|                     Cumulative indexing time of primary shards |                                                     |   31.5392 |    min |
|             Min cumulative indexing time across primary shards |                                                     |         0 |    min |
|          Median cumulative indexing time across primary shards |                                                     |   2.65797 |    min |
|             Max cumulative indexing time across primary shards |                                                     |   6.65067 |    min |
|            Cumulative indexing throttle time of primary shards |                                                     |         0 |    min |
|    Min cumulative indexing throttle time across primary shards |                                                     |         0 |    min |
| Median cumulative indexing throttle time across primary shards |                                                     |         0 |    min |
|    Max cumulative indexing throttle time across primary shards |                                                     |         0 |    min |
|                        Cumulative merge time of primary shards |                                                     |   1.49212 |    min |
|                       Cumulative merge count of primary shards |                                                     |        66 |        |
|                Min cumulative merge time across primary shards |                                                     |         0 |    min |
|             Median cumulative merge time across primary shards |                                                     |   0.02405 |    min |
|              Max cumulative refresh time across primary shards |                                                     |   3.16232 |    min |
|                        Cumulative flush time of primary shards |                                                     |   27.9703 |    min |
|                       Cumulative flush count of primary shards |                                                     |        43 |        |
|                Min cumulative flush time across primary shards |                                                     |         0 |    min |
|             Median cumulative flush time across primary shards |                                                     |      2.21 |    min |
|                Max cumulative flush time across primary shards |                                                     |   5.80563 |    min |
|                                        Total Young Gen GC time |                                                     |      0.26 |      s |
|                                       Total Young Gen GC count |                                                     |         9 |        |
|                                          Total Old Gen GC time |                                                     |         0 |      s |
|                                         Total Old Gen GC count |                                                     |         0 |        |
|                                                     Store size |                                                     |   30.2634 |     GB |
|                                                  Translog size |                                                     | 0.0721771 |     GB |
|                                         Heap used for segments |                                                     |         0 |     MB |
|                                       Heap used for doc values |                                                     |         0 |     MB |
|                                            Heap used for terms |                                                     |         0 |     MB |
|                                            Heap used for norms |                                                     |         0 |     MB |
|             Median cumulative flush time across primary shards |                                                     |      2.21 |    min |
|                Max cumulative flush time across primary shards |                                                     |   5.80563 |    min |
|                                        Total Young Gen GC time |                                                     |      0.26 |      s |
|                                       Total Young Gen GC count |                                                     |         9 |        |
|                                          Total Old Gen GC time |                                                     |         0 |      s |
|                                         Total Old Gen GC count |                                                     |         0 |        |
|                                                     Store size |                                                     |   30.2634 |     GB |
|                                                  Translog size |                                                     | 0.0721771 |     GB |
|                                         Heap used for segments |                                                     |         0 |     MB |
|                                       Heap used for doc values |                                                     |         0 |     MB |
|                                            Heap used for terms |                                                     |         0 |     MB |
|                                            Heap used for norms |                                                     |         0 |     MB |
|                                           Heap used for points |                                                     |         0 |     MB |
|                                    Heap used for stored fields |                                                     |         0 |     MB |
|                                                  Segment count |                                                     |       222 |        |
|                                                 Min Throughput |                              semantic-search-neural |     25.58 |  ops/s |
|                                                Mean Throughput |                              semantic-search-neural |     32.28 |  ops/s |
|                                              Median Throughput |                              semantic-search-neural |     33.23 |  ops/s |
|                                                 Max Throughput |                              semantic-search-neural |     34.79 |  ops/s |
|                                        50th percentile latency |                              semantic-search-neural |   210.864 |     ms |
|                                        90th percentile latency |                              semantic-search-neural |   232.103 |     ms |
|                                        99th percentile latency |                              semantic-search-neural |   259.537 |     ms |
|                                       100th percentile latency |                              semantic-search-neural |   287.864 |     ms |
|                                   50th percentile service time |                              semantic-search-neural |   210.864 |     ms |
|                                   90th percentile service time |                              semantic-search-neural |   232.103 |     ms |
|                                   99th percentile service time |                              semantic-search-neural |   259.537 |     ms |
|                                  100th percentile service time |                              semantic-search-neural |   287.864 |     ms |
|                                                     error rate |                              semantic-search-neural |         0 |      % |
|                                                 Min Throughput |          semantic-search-hybrid-bm25-and-knn-search |     67.79 |  ops/s |
|                                                Mean Throughput |          semantic-search-hybrid-bm25-and-knn-search |     71.87 |  ops/s |
|                                              Median Throughput |          semantic-search-hybrid-bm25-and-knn-search |     72.71 |  ops/s |
|                                                 Max Throughput |          semantic-search-hybrid-bm25-and-knn-search |     73.51 |  ops/s |
|                                        50th percentile latency |          semantic-search-hybrid-bm25-and-knn-search |   103.806 |     ms |
|                                        90th percentile latency |          semantic-search-hybrid-bm25-and-knn-search |   111.644 |     ms |
|                                        99th percentile latency |          semantic-search-hybrid-bm25-and-knn-search |   118.395 |     ms |
|                                       100th percentile latency |          semantic-search-hybrid-bm25-and-knn-search |   122.929 |     ms |
|                                   50th percentile service time |          semantic-search-hybrid-bm25-and-knn-search |   103.806 |     ms |
|                                   90th percentile service time |          semantic-search-hybrid-bm25-and-knn-search |   111.644 |     ms |
|                                   99th percentile service time |          semantic-search-hybrid-bm25-and-knn-search |   118.395 |     ms |
|                                  100th percentile service time |          semantic-search-hybrid-bm25-and-knn-search |   122.929 |     ms |
|                                                     error rate |          semantic-search-hybrid-bm25-and-knn-search |         0 |      % |
|                                                 Min Throughput |       semantic-search-hybrid-bm25-and-neural-search |     35.59 |  ops/s |
|                                                Mean Throughput |       semantic-search-hybrid-bm25-and-neural-search |     36.28 |  ops/s |
|                                              Median Throughput |       semantic-search-hybrid-bm25-and-neural-search |     36.34 |  ops/s |
|                                                 Max Throughput |       semantic-search-hybrid-bm25-and-neural-search |     36.63 |  ops/s |
|                                        50th percentile latency |       semantic-search-hybrid-bm25-and-neural-search |     213.2 |     ms |
|                                        90th percentile latency |       semantic-search-hybrid-bm25-and-neural-search |   232.455 |     ms |
|                                        99th percentile latency |       semantic-search-hybrid-bm25-and-neural-search |   265.864 |     ms |
|                                       100th percentile latency |       semantic-search-hybrid-bm25-and-neural-search |   300.295 |     ms |
|                                   50th percentile service time |       semantic-search-hybrid-bm25-and-neural-search |     213.2 |     ms |
|                                   90th percentile service time |       semantic-search-hybrid-bm25-and-neural-search |   232.455 |     ms |
|                                   99th percentile service time |       semantic-search-hybrid-bm25-and-neural-search |   265.864 |     ms |
|                                  100th percentile service time |       semantic-search-hybrid-bm25-and-neural-search |   300.295 |     ms |
|                                                     error rate |       semantic-search-hybrid-bm25-and-neural-search |         0 |      % |
|                                                 Min Throughput | semantic-search-hybrid-bm25-range-and-neural-search |     34.65 |  ops/s |
|                                                Mean Throughput | semantic-search-hybrid-bm25-range-and-neural-search |     35.98 |  ops/s |
|                                              Median Throughput | semantic-search-hybrid-bm25-range-and-neural-search |     36.22 |  ops/s |
|                                                 Max Throughput | semantic-search-hybrid-bm25-range-and-neural-search |     36.38 |  ops/s |
|                                        50th percentile latency | semantic-search-hybrid-bm25-range-and-neural-search |   214.191 |     ms |
|                                        90th percentile latency | semantic-search-hybrid-bm25-range-and-neural-search |   234.587 |     ms |
|                                        99th percentile latency | semantic-search-hybrid-bm25-range-and-neural-search |   259.207 |     ms |
|                                       100th percentile latency | semantic-search-hybrid-bm25-range-and-neural-search |   276.345 |     ms |
|                                   50th percentile service time | semantic-search-hybrid-bm25-range-and-neural-search |   214.191 |     ms |
|                                   90th percentile service time | semantic-search-hybrid-bm25-range-and-neural-search |   234.587 |     ms |
|                                   99th percentile service time | semantic-search-hybrid-bm25-range-and-neural-search |   259.207 |     ms |
|                                  100th percentile service time | semantic-search-hybrid-bm25-range-and-neural-search |   276.345 |     ms |
|                                                     error rate | semantic-search-hybrid-bm25-range-and-neural-search |         0 |      % |


---------------------------------
[INFO] SUCCESS (took 174 seconds)
---------------------------------
```

## License

Following license used by original dataset and we're using it too.
```
               Apache License
           Version 2.0, January 2004
         http://www.apache.org/licenses/
```
Covid-trec [1] is part of the COVID-19 Open Research dataset [2], which is licensed under Apache 2.0.  
[1] https://arxiv.org/pdf/2005.04474v1.pdf  
[2] https://github.com/allenai/cord19/ 

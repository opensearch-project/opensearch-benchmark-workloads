# KNN Vector Workload

This workload is to benchmark performance of indexing and search of Vector Engine of Opensearch.

## Datasets

This workload currently supports datasets  with either HDF5 format or Big-ann.
You can download datasets from [here](http://corpus-texmex.irisa.fr/) to benchmark the quality of approximate k-NN algorithm from
OpenSearch.

### Running a benchmark

Before running a benchmark, make sure you have the endpoint of your cluster and
  the machine you are running the benchmarks from, can access it. 
 Additionally, ensure that all data has been pulled to the client.

Currently, we support one test procedures for the k-NN workload: 
no-train-test that does not have steps to train a model included in the 
schedule. This test procedures will index a data set 
of vectors into an OpenSearch index and then run a set of queries against them. 

To run test procedure, open up 
[params/no-train-params.json](params/no-train-params.json) and 
fill out the mandatory parameters.
Once the parameters are set, set the URL and PORT of your cluster and run the 
command to run the test procedure. 

```
export URL=
export PORT=
export PARAMS_FILE=
export PROCEDURE="no-train-test"

opensearch-benchmark execute_test \ 
    --target-hosts $URL:$PORT \ 
    --workload-path ./workload.json \ 
    --workload-params ${PARAMS_FILE} \
    --test-procedure=${PROCEDURE} \
    --pipeline benchmark-only
```

## Current Procedures

### No Train Test

The No Train Test procedure is used to test `knn_vector` indices that do not  use an algorithm that requires training.

#### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

| Name                                    | Description                                                              |
|-----------------------------------------|--------------------------------------------------------------------------|
| target_index_name                       | Name of index to add vectors to                                          |
| target_field_name                       | Name of field to add vectors to                                          |
| target_index_body                       | Path to target index definition                                          |
| target_index_primary_shards             | Target index primary shards                                              |
| target_index_replica_shards             | Target index replica shards                                              |
| target_index_dimension                  | Dimension of target index                                                |
| target_index_space_type                 | Target index space type                                                  |
| target_index_bulk_size                  | Target index bulk size                                                   |
| target_index_bulk_index_data_set_format | Format of vector data set                                                |
| target_index_bulk_index_data_set_path   | Path to vector data set                                                  |
| target_index_bulk_index_clients         | Clients to be used for bulk ingestion (must be divisor of data set size) |
| target_index_max_num_segments           | Number of segments to merge target index down to before beginning search |
| target_index_force_merge_timeout        | Timeout for of force merge requests in seconds                           |
| hnsw_ef_search                          | HNSW ef search parameter                                                 |
| hnsw_ef_construction                    | HNSW ef construction parameter                                           |
| hnsw_m                                  | HNSW m parameter                                                         |
| query_k                                 | The number of neighbors to return for the search                         |
| query_clients                           | Number of clients to use for running queries                             |
| query_data_set_format                   | Format of vector data set for queries                                    |
| query_data_set_path                     | Path to vector data set for queries                                      |
| query_count                             | Number of queries for search operation                                   |



#### Metrics

The result metrics of this procedure will look like: 
```
------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------
            
|                                                         Metric |               Task |       Value |   Unit |
|---------------------------------------------------------------:|-------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                    |  0.00946667 |    min |
|             Min cumulative indexing time across primary shards |                    |           0 |    min |
|          Median cumulative indexing time across primary shards |                    |  0.00298333 |    min |
|             Max cumulative indexing time across primary shards |                    |  0.00336667 |    min |
|            Cumulative indexing throttle time of primary shards |                    |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                    |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                    |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                    |           0 |    min |
|                        Cumulative merge time of primary shards |                    |           0 |    min |
|                       Cumulative merge count of primary shards |                    |           0 |        |
|                Min cumulative merge time across primary shards |                    |           0 |    min |
|             Median cumulative merge time across primary shards |                    |           0 |    min |
|                Max cumulative merge time across primary shards |                    |           0 |    min |
|               Cumulative merge throttle time of primary shards |                    |           0 |    min |
|       Min cumulative merge throttle time across primary shards |                    |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                    |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                    |           0 |    min |
|                      Cumulative refresh time of primary shards |                    |  0.00861667 |    min |
|                     Cumulative refresh count of primary shards |                    |          33 |        |
|              Min cumulative refresh time across primary shards |                    |           0 |    min |
|           Median cumulative refresh time across primary shards |                    |  0.00268333 |    min |
|              Max cumulative refresh time across primary shards |                    |  0.00291667 |    min |
|                        Cumulative flush time of primary shards |                    | 0.000183333 |    min |
|                       Cumulative flush count of primary shards |                    |           2 |        |
|                Min cumulative flush time across primary shards |                    |           0 |    min |
|             Median cumulative flush time across primary shards |                    |           0 |    min |
|                Max cumulative flush time across primary shards |                    | 0.000183333 |    min |
|                                        Total Young Gen GC time |                    |       0.075 |      s |
|                                       Total Young Gen GC count |                    |          17 |        |
|                                          Total Old Gen GC time |                    |           0 |      s |
|                                         Total Old Gen GC count |                    |           0 |        |
|                                                     Store size |                    |  0.00869293 |     GB |
|                                                  Translog size |                    | 2.56114e-07 |     GB |
|                                         Heap used for segments |                    |           0 |     MB |
|                                       Heap used for doc values |                    |           0 |     MB |
|                                            Heap used for terms |                    |           0 |     MB |
|                                            Heap used for norms |                    |           0 |     MB |
|                                           Heap used for points |                    |           0 |     MB |
|                                    Heap used for stored fields |                    |           0 |     MB |
|                                                  Segment count |                    |           9 |        |
|                                                 Min Throughput | custom-vector-bulk |       25527 | docs/s |
|                                                Mean Throughput | custom-vector-bulk |       25527 | docs/s |
|                                              Median Throughput | custom-vector-bulk |       25527 | docs/s |
|                                                 Max Throughput | custom-vector-bulk |       25527 | docs/s |
|                                        50th percentile latency | custom-vector-bulk |     36.3095 |     ms |
|                                        90th percentile latency | custom-vector-bulk |     52.2662 |     ms |
|                                       100th percentile latency | custom-vector-bulk |     68.6513 |     ms |
|                                   50th percentile service time | custom-vector-bulk |     36.3095 |     ms |
|                                   90th percentile service time | custom-vector-bulk |     52.2662 |     ms |
|                                  100th percentile service time | custom-vector-bulk |     68.6513 |     ms |
|                                                     error rate | custom-vector-bulk |           0 |      % |
|                                                 Min Throughput |       prod-queries |      211.26 |  ops/s |
|                                                Mean Throughput |       prod-queries |      213.85 |  ops/s |
|                                              Median Throughput |       prod-queries |      213.48 |  ops/s |
|                                                 Max Throughput |       prod-queries |      216.49 |  ops/s |
|                                        50th percentile latency |       prod-queries |     3.43393 |     ms |
|                                        90th percentile latency |       prod-queries |     4.01881 |     ms |
|                                        99th percentile latency |       prod-queries |     5.56238 |     ms |
|                                      99.9th percentile latency |       prod-queries |     9.95666 |     ms |
|                                     99.99th percentile latency |       prod-queries |     39.7922 |     ms |
|                                       100th percentile latency |       prod-queries |      62.415 |     ms |
|                                   50th percentile service time |       prod-queries |     3.43405 |     ms |
|                                   90th percentile service time |       prod-queries |      4.0191 |     ms |
|                                   99th percentile service time |       prod-queries |     5.56316 |     ms |
|                                 99.9th percentile service time |       prod-queries |     9.95666 |     ms |
|                                99.99th percentile service time |       prod-queries |     39.7922 |     ms |
|                                  100th percentile service time |       prod-queries |      62.415 |     ms |
|                                                     error rate |       prod-queries |           0 |      % |


---------------------------------
[INFO] SUCCESS (took 119 seconds)
---------------------------------

```


### Custom Runners

Custom runners are defined in [runners.py](runners.py).

| Syntax             | Description                                         | Parameters                                                                                                   |
|--------------------|-----------------------------------------------------|:-------------------------------------------------------------------------------------------------------------|
| warmup-knn-indices | Warm up knn indices with retry until success.       | 1. index - name of index to warmup                                                                           |
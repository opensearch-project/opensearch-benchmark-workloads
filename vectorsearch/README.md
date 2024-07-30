# Vector Search Workload

This workload is to benchmark performance of indexing and search of Vector Engine of OpenSearch.

## Datasets

This workload currently supports datasets  with either HDF5 format or Big-ANN.
You can download datasets from [here](http://corpus-texmex.irisa.fr/) to benchmark the quality of approximate k-NN algorithm from
OpenSearch.

### Running a benchmark

Before running a benchmark, ensure that the load generation host is able to access your cluster endpoint and that the 
appropriate dataset is available on the host.

Currently, we support 4 test procedures for the vector search workload. The default procedure is named no-train-test and does not include the steps required to train the model being used.
This test procedures will index a data set of vectors into an OpenSearch cluster and then run a set of queries against the generated index. 

Due to the number of parameters this workload offers, it's recommended to create a parameter file that specifies the desired workload 
parameters instead of listing them all on the OSB command line. Users are welcome to use the example param files,
`faiss-sift-128-l2.json`, `nmslib-sift-128-l2.json`, or `lucene-sift-128-l2.json` in `/params`, as references. Here, we named
the parameter file using a format `<Vector Engine Type>-<Dataset Name>-<No of Dimension>-<Space Type>.json`

To run the workload, invoke the following command with the params file.

```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT=  
# Absolute file path of Workload param file
export PARAMS_FILE=

opensearch-benchmark execute-test \
    --target-hosts $ENDPOINT \
    --workload vectorsearch \
    --workload-params ${PARAMS_FILE} \
    --pipeline benchmark-only \
    --kill-running-processes
```

## Current Procedures

### No Train Test

The No Train Test procedure is used to test vector search indices which requires no training.
You can define the underlying configuration of the vector search algorithm like specific engine, space type, etc... as
method definition . Check [vector search method definitions]([https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#method-definitions)
for more details.

### No Train Test Index Only
This procedure is used to index only vector search index which requires no training. This will be useful if
you are interested in benchmarking only indexing operation.

### Force Merge Index
This procedure is used to optimize vector search indices by performing force merge on an index, up to given maximum segments.
For a large dataset, force merge is a costly operation. Hence, it is better to have separate procedure to trigger
force merge occasionally based on user's requirement.

### Search
This procedure is used to benchmark previously indexed vector search index. This will be useful if you want
to benchmark large vector search index without indexing everytime since load time is substantial for a large dataset.
This also contains warmup operation to avoid cold start problem during vector search.

### No Train Test AOSS

This is similar to no train test, except, targeted for Amazon OpenSearch Serverless Vector Search Collection. This procedure
does not contain operations like refresh and warm up since they are not supported by Vector Search Collection.



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
| target_index_bulk_index_data_set_corpus | Corpus name to vector data set                                                  |
| target_index_bulk_index_clients         | Clients to be used for bulk ingestion (must be divisor of data set size) |
| target_index_max_num_segments           | Number of segments to merge target index down to before beginning search |
| target_index_force_merge_timeout        | Timeout for of force merge requests in seconds                           |
| hnsw_ef_search                          | HNSW ef search parameter                                                 |
| hnsw_ef_construction                    | HNSW ef construction parameter                                           |
| id_field_name                           | Name of field that will be used to identify documents in an index        |
| hnsw_m                                  | HNSW m parameter                                                         |
| query_k                                 | The number of neighbors to return for the search                         |
| query_data_set_format                   | Format of vector data set for queries                                    |
| query_data_set_path                     | Path to vector data set for queries                                      |
| query_count                             | Number of queries for search operation                                   |
| query_body                              | Json properties that will be merged with search body                     |
| search_clients                          | Number of clients to use for running queries                             |
| repetitions                             | Number of repetitions until the data set is exhausted (default 1)                    |
| target_throughput                       | Target throughput for each query operation in requests per second (default 10) |
| time_period                             | The period of time dedicated for the benchmark execution in seconds (default 900)    |



#### Sample Output

The output of a sample test run is provided below. Metrics are captured in the result's data store as usual, and this can be configured to be 
either in-memory, or an external OpenSearch cluster.

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

### Train Test

This procedure benchmarks approximate k-NN search algorithms that require a training step. For example, the FAISS IVF requires a training step to cluster vectors. Then search can be performed against a smaller number of cluster centroids instead of the entire dataset.

#### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

| Name                                    | Description                                                                                  |
|-----------------------------------------|----------------------------------------------------------------------------------------------|
| target_index_name                       | Name of index to add vectors to                                                              |
| target_field_name                       | Name of field to add vectors to                                                              |
| target_index_body                       | Path to target index definition                                                              |
| target_index_primary_shards             | Target index primary shards                                                                  |
| target_index_replica_shards             | Target index replica shards                                                                  |
| target_index_dimension                  | Dimension of target index                                                                    |
| target_index_space_type                 | Target index space type                                                                      |
| target_index_bulk_size                  | Target index bulk size                                                                       |
| target_index_bulk_index_data_set_format | Format of vector data set                                                                    |
| target_index_bulk_index_data_set_path   | Path to vector data set                                                                      |
| target_index_bulk_index_data_set_corpus | Corpus name to vector data set                                                               |
| target_index_bulk_index_clients         | Clients to be used for bulk ingestion (must be divisor of data set size)                     |
| target_index_max_num_segments           | Number of segments to merge target index down to before beginning search                     |
| target_index_force_merge_timeout        | Timeout for of force merge requests in seconds                                               |
| train_index_name                        | Name of index for training                                                                   |
| train_field_name                        | Name of field for training                                                                   |
| train_method_engine                     | Engine for training (e.g "faiss")                                                            |
| train_index_body                        | Path to train index definition                                                               |
| train_index_primary_shards              | Train index primary shards                                                                   |
| train_index_replica_shards              | Train index replica shards                                                                   |
| train_index_bulk_size                   | Bulk size for train index                                                                    |
| train_index_bulk_index_data_set_format  | Format of training data set                                                                  |
| train_index_bulk_index_data_set_path    | Path to training data set                                                                    |
| train_index_bulk_indexing_clients       | Clients to be used for bulk indexing                                                         |
| train_index_num_vectors                 | Number of vectors in the training index                                                      |
| train_model_id                          | ID of the training model                                                                     |
| train_operation_retries                 | Number of retries for querying training operation to see if complete                         |
| train_operation_poll_period             | Poll period for querying training operation in seconds                                       |
| train_search_size                       | Number of results per [scroll query](http://opensearch.org/docs/latest/api-reference/scroll/)|
| encoder                                 | Encoder for quantization. One of `flat`, `sq`, `pq`. Defaults to `flat` when not specified. [See here](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#supported-faiss-encoders)
| faiss_encoder_code_size                 | PQ Encoding [code size setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#pq-parameters).
| faiss_encoder_m                         | PQ Encoding [m setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#pq-parameters)
| faiss_encoder_type                      | SQ Encoding [type setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#sq-parameters)
| faiss_encoder_clip                      | SQ Encoding [clip setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#sq-parameters)
| faiss_nprobes                           | Faiss IVF nprobes setting. [See here](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#ivf-parameters)|
| faiss_nlist                             | Faiss IVF nlist setting. [See here](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#ivf-parameters)|
| hnsw_ef_search                          | HNSW ef search parameter                                                                     |
| hnsw_ef_construction                    | HNSW ef construction parameter                                                               |
| id_field_name                           | Name of field that will be used to identify documents in an index                            |
| hnsw_m                                  | HNSW m parameter                                                                             |
| query_k                                 | The number of neighbors to return for the search                                             |
| query_data_set_format                   | Format of vector data set for queries                                                        |
| query_data_set_path                     | Path to vector data set for queries                                                          |
| query_count                             | Number of queries for search operation                                                       |
| query_body                              | Json properties that will be merged with search body                                         |
| search_clients                          | Number of clients to use for running queries                                                 |

#### Sample Output

The output of a sample test run is provided below. Metrics are captured in the result's data store as usual, and this can be configured to be 
either in-memory, or an external OpenSearch cluster.

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

Currently, there is only one custom runner defined in [runners.py](runners.py).

| Syntax             | Description                                         | Parameters                                                                                                   |
|--------------------|-----------------------------------------------------|:-------------------------------------------------------------------------------------------------------------|
| warmup-knn-indices | Warm up knn indices with retry until success.       | 1. index - name of index to warmup                                                                           |

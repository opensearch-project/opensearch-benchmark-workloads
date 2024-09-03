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

| Name                                    | Description                                                                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| target_index_name                       | Name of index to add vectors to                                                                                             |
| target_field_name                       | Name of field to add vectors to. Use "." to indicate a nested field                                                         |
| target_index_body                       | Path to target index definition                                                                                             |
| target_index_primary_shards             | Target index primary shards                                                                                                 |
| target_index_replica_shards             | Target index replica shards                                                                                                 |
| target_index_dimension                  | Dimension of target index                                                                                                   |
| target_index_space_type                 | Target index space type                                                                                                     |
| target_index_bulk_size                  | Target index bulk size                                                                                                      |
| target_index_bulk_index_data_set_format | Format of vector data set                                                                                                   |
| target_index_bulk_index_data_set_path   | Path to vector data set                                                                                                     |
| target_index_bulk_index_data_set_corpus | Corpus name to vector data set                                                                                              |
| target_index_bulk_index_clients         | Clients to be used for bulk ingestion (must be divisor of data set size)                                                    |
| target_index_max_num_segments           | Number of segments to merge target index down to before beginning search                                                    |
| target_index_force_merge_timeout        | Timeout for of force merge requests in seconds                                                                              |
| hnsw_ef_search                          | HNSW ef search parameter                                                                                                    | 
| hnsw_ef_construction                    | HNSW ef construction parameter                                                                                              |
| id_field_name                           | Name of field that will be used to identify documents in an index                                                           |
| hnsw_m                                  | HNSW m parameter                                                                                                            |
| query_k                                 | The number of neighbors to return for the search (only one of query_k, query_max_distance, query_min_score can be provided) |
| query_max_distance                      | The maximum distance to be returned for the vector search (only one of query_k, query_max_distance, query_min_score can be provided) |
| query_min_score                         | The minimum score to be returned for the vector search (only one of query_k, query_max_distance, query_min_score can be provided)    |
| query_data_set_format                   | Format of vector data set for queries                                                                                       |
| query_data_set_path                     | Path to vector data set for queries                                                                                         |
| query_count                             | Number of queries for search operation                                                                                      |
| query_body                              | Json properties that will be merged with search body                                                                        |
| search_clients                          | Number of clients to use for running queries                                                                                |
| repetitions                             | Number of repetitions until the data set is exhausted (default 1)                                                           |
| target_throughput                       | Target throughput for each query operation in requests per second (default 10)                                              |
| time_period                             | The period of time dedicated for the benchmark execution in seconds (default 900)                                           |



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
| pq_encoder_code_size                 | PQ Encoding [code size setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#pq-parameters).
| pq_encoder_m                         | PQ Encoding [m setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#pq-parameters)
| encoder_type                      | SQ Encoding [type setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#sq-parameters)
| encoder_clip                      | SQ Encoding [clip setting](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#sq-parameters)
| nprobes                           | IVF nprobes setting. [See here](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#ivf-parameters)|
| nlist                             | IVF nlist setting. [See here](https://opensearch.org/docs/latest/search-plugins/knn/knn-index/#ivf-parameters)|
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
| target_dataset_filter_attributes        | Used in filter benchmarks. List of names of attribute fields in a dataset.                   | 

#### Sample Outputs

Below are sample outputs for the Faiss IVF benchmarking procedure. For the sake of time we ran 100 search queries instead of the 10000 specified in the parameter files. The rest of the parameters are the same as those in the `params/train` folder. The first run is without quantization, the second run is with scalar quantization, and the third run is with product quantization. Note that quantization may cause search recall to drop.

##### Faiss IVF -- no quantization/flat encoding

```
|                                                         Metric |                     Task |       Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                          |     11.7662 |    min |
|             Min cumulative indexing time across primary shards |                          | 0.000266667 |    min |
|          Median cumulative indexing time across primary shards |                          |      0.1423 |    min |
|             Max cumulative indexing time across primary shards |                          |     11.6236 |    min |
|            Cumulative indexing throttle time of primary shards |                          |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |           0 |    min |
|                        Cumulative merge time of primary shards |                          |     1.09872 |    min |
|                       Cumulative merge count of primary shards |                          |          21 |        |
|                Min cumulative merge time across primary shards |                          |           0 |    min |
|             Median cumulative merge time across primary shards |                          |     0.00045 |    min |
|                Max cumulative merge time across primary shards |                          |     1.09827 |    min |
|               Cumulative merge throttle time of primary shards |                          |    0.872417 |    min |
|       Min cumulative merge throttle time across primary shards |                          |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |    0.872417 |    min |
|                      Cumulative refresh time of primary shards |                          |    0.113733 |    min |
|                     Cumulative refresh count of primary shards |                          |          59 |        |
|              Min cumulative refresh time across primary shards |                          |     0.00235 |    min |
|           Median cumulative refresh time across primary shards |                          |  0.00516667 |    min |
|              Max cumulative refresh time across primary shards |                          |    0.106217 |    min |
|                        Cumulative flush time of primary shards |                          |     0.01685 |    min |
|                       Cumulative flush count of primary shards |                          |           8 |        |
|                Min cumulative flush time across primary shards |                          |           0 |    min |
|             Median cumulative flush time across primary shards |                          |  0.00791667 |    min |
|                Max cumulative flush time across primary shards |                          |  0.00893333 |    min |
|                                        Total Young Gen GC time |                          |       5.442 |      s |
|                                       Total Young Gen GC count |                          |        3739 |        |
|                                          Total Old Gen GC time |                          |           0 |      s |
|                                         Total Old Gen GC count |                          |           0 |        |
|                                                     Store size |                          |      1.3545 |     GB |
|                                                  Translog size |                          |   0.0304573 |     GB |
|                                         Heap used for segments |                          |           0 |     MB |
|                                       Heap used for doc values |                          |           0 |     MB |
|                                            Heap used for terms |                          |           0 |     MB |
|                                            Heap used for norms |                          |           0 |     MB |
|                                           Heap used for points |                          |           0 |     MB |
|                                    Heap used for stored fields |                          |           0 |     MB |
|                                                  Segment count |                          |          14 |        |
|                                                 Min Throughput | custom-vector-bulk-train |     32222.6 | docs/s |
|                                                Mean Throughput | custom-vector-bulk-train |     32222.6 | docs/s |
|                                              Median Throughput | custom-vector-bulk-train |     32222.6 | docs/s |
|                                                 Max Throughput | custom-vector-bulk-train |     32222.6 | docs/s |
|                                        50th percentile latency | custom-vector-bulk-train |     26.5199 |     ms |
|                                        90th percentile latency | custom-vector-bulk-train |     34.9823 |     ms |
|                                        99th percentile latency | custom-vector-bulk-train |     196.712 |     ms |
|                                       100th percentile latency | custom-vector-bulk-train |     230.342 |     ms |
|                                   50th percentile service time | custom-vector-bulk-train |     26.5158 |     ms |
|                                   90th percentile service time | custom-vector-bulk-train |     34.9823 |     ms |
|                                   99th percentile service time | custom-vector-bulk-train |     196.712 |     ms |
|                                  100th percentile service time | custom-vector-bulk-train |     230.342 |     ms |
|                                                     error rate | custom-vector-bulk-train |           0 |      % |
|                                                 Min Throughput |             delete-model |       10.58 |  ops/s |
|                                                Mean Throughput |             delete-model |       10.58 |  ops/s |
|                                              Median Throughput |             delete-model |       10.58 |  ops/s |
|                                                 Max Throughput |             delete-model |       10.58 |  ops/s |
|                                       100th percentile latency |             delete-model |     93.6958 |     ms |
|                                  100th percentile service time |             delete-model |     93.6958 |     ms |
|                                                     error rate |             delete-model |           0 |      % |
|                                                 Min Throughput |          train-knn-model |        0.63 |  ops/s |
|                                                Mean Throughput |          train-knn-model |        0.63 |  ops/s |
|                                              Median Throughput |          train-knn-model |        0.63 |  ops/s |
|                                                 Max Throughput |          train-knn-model |        0.63 |  ops/s |
|                                       100th percentile latency |          train-knn-model |     1577.49 |     ms |
|                                  100th percentile service time |          train-knn-model |     1577.49 |     ms |
|                                                     error rate |          train-knn-model |           0 |      % |
|                                                 Min Throughput |       custom-vector-bulk |       11055 | docs/s |
|                                                Mean Throughput |       custom-vector-bulk |     14163.8 | docs/s |
|                                              Median Throughput |       custom-vector-bulk |     12878.9 | docs/s |
|                                                 Max Throughput |       custom-vector-bulk |     33841.3 | docs/s |
|                                        50th percentile latency |       custom-vector-bulk |     81.6677 |     ms |
|                                        90th percentile latency |       custom-vector-bulk |     117.848 |     ms |
|                                        99th percentile latency |       custom-vector-bulk |     202.484 |     ms |
|                                      99.9th percentile latency |       custom-vector-bulk |     406.209 |     ms |
|                                     99.99th percentile latency |       custom-vector-bulk |     458.823 |     ms |
|                                       100th percentile latency |       custom-vector-bulk |     459.417 |     ms |
|                                   50th percentile service time |       custom-vector-bulk |     81.6621 |     ms |
|                                   90th percentile service time |       custom-vector-bulk |     117.843 |     ms |
|                                   99th percentile service time |       custom-vector-bulk |     202.294 |     ms |
|                                 99.9th percentile service time |       custom-vector-bulk |     406.209 |     ms |
|                                99.99th percentile service time |       custom-vector-bulk |     458.823 |     ms |
|                                  100th percentile service time |       custom-vector-bulk |     459.417 |     ms |
|                                                     error rate |       custom-vector-bulk |           0 |      % |
|                                                 Min Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                                Mean Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                              Median Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                                 Max Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                       100th percentile latency |     force-merge-segments |     10017.4 |     ms |
|                                  100th percentile service time |     force-merge-segments |     10017.4 |     ms |
|                                                     error rate |     force-merge-segments |           0 |      % |
|                                                 Min Throughput |           warmup-indices |        9.63 |  ops/s |
|                                                Mean Throughput |           warmup-indices |        9.63 |  ops/s |
|                                              Median Throughput |           warmup-indices |        9.63 |  ops/s |
|                                                 Max Throughput |           warmup-indices |        9.63 |  ops/s |
|                                       100th percentile latency |           warmup-indices |     103.228 |     ms |
|                                  100th percentile service time |           warmup-indices |     103.228 |     ms |
|                                                     error rate |           warmup-indices |           0 |      % |
|                                                 Min Throughput |             prod-queries |      120.06 |  ops/s |
|                                                Mean Throughput |             prod-queries |      120.06 |  ops/s |
|                                              Median Throughput |             prod-queries |      120.06 |  ops/s |
|                                                 Max Throughput |             prod-queries |      120.06 |  ops/s |
|                                        50th percentile latency |             prod-queries |     1.75219 |     ms |
|                                        90th percentile latency |             prod-queries |     2.29527 |     ms |
|                                        99th percentile latency |             prod-queries |     50.4419 |     ms |
|                                       100th percentile latency |             prod-queries |     97.9905 |     ms |
|                                   50th percentile service time |             prod-queries |     1.75219 |     ms |
|                                   90th percentile service time |             prod-queries |     2.29527 |     ms |
|                                   99th percentile service time |             prod-queries |     50.4419 |     ms |
|                                  100th percentile service time |             prod-queries |     97.9905 |     ms |
|                                                     error rate |             prod-queries |           0 |      % |
|                                                  Mean recall@k |             prod-queries |        0.96 |        |
|                                                  Mean recall@1 |             prod-queries |        0.99 |        |


---------------------------------
[INFO] SUCCESS (took 218 seconds)
---------------------------------
```

##### Faiss IVF with Scalar Quantization (100 search queries)

```         
|                                                         Metric |                     Task |       Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                          |        11.5 |    min |
|             Min cumulative indexing time across primary shards |                          | 0.000283333 |    min |
|          Median cumulative indexing time across primary shards |                          |     0.10915 |    min |
|             Max cumulative indexing time across primary shards |                          |     11.3905 |    min |
|            Cumulative indexing throttle time of primary shards |                          |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |           0 |    min |
|                        Cumulative merge time of primary shards |                          |     1.03638 |    min |
|                       Cumulative merge count of primary shards |                          |          22 |        |
|                Min cumulative merge time across primary shards |                          |           0 |    min |
|             Median cumulative merge time across primary shards |                          | 0.000266667 |    min |
|                Max cumulative merge time across primary shards |                          |     1.03612 |    min |
|               Cumulative merge throttle time of primary shards |                          |    0.798767 |    min |
|       Min cumulative merge throttle time across primary shards |                          |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |    0.798767 |    min |
|                      Cumulative refresh time of primary shards |                          |    0.107117 |    min |
|                     Cumulative refresh count of primary shards |                          |          61 |        |
|              Min cumulative refresh time across primary shards |                          |  0.00236667 |    min |
|           Median cumulative refresh time across primary shards |                          |  0.00543333 |    min |
|              Max cumulative refresh time across primary shards |                          |   0.0993167 |    min |
|                        Cumulative flush time of primary shards |                          |   0.0193167 |    min |
|                       Cumulative flush count of primary shards |                          |           9 |        |
|                Min cumulative flush time across primary shards |                          |           0 |    min |
|             Median cumulative flush time across primary shards |                          |  0.00871667 |    min |
|                Max cumulative flush time across primary shards |                          |      0.0106 |    min |
|                                        Total Young Gen GC time |                          |       5.267 |      s |
|                                       Total Young Gen GC count |                          |        3688 |        |
|                                          Total Old Gen GC time |                          |           0 |      s |
|                                         Total Old Gen GC count |                          |           0 |        |
|                                                     Store size |                          |     1.11609 |     GB |
|                                                  Translog size |                          |   0.0304573 |     GB |
|                                         Heap used for segments |                          |           0 |     MB |
|                                       Heap used for doc values |                          |           0 |     MB |
|                                            Heap used for terms |                          |           0 |     MB |
|                                            Heap used for norms |                          |           0 |     MB |
|                                           Heap used for points |                          |           0 |     MB |
|                                    Heap used for stored fields |                          |           0 |     MB |
|                                                  Segment count |                          |          18 |        |
|                                                 Min Throughput | custom-vector-bulk-train |     35950.5 | docs/s |
|                                                Mean Throughput | custom-vector-bulk-train |     35950.5 | docs/s |
|                                              Median Throughput | custom-vector-bulk-train |     35950.5 | docs/s |
|                                                 Max Throughput | custom-vector-bulk-train |     35950.5 | docs/s |
|                                        50th percentile latency | custom-vector-bulk-train |     22.8328 |     ms |
|                                        90th percentile latency | custom-vector-bulk-train |      34.864 |     ms |
|                                        99th percentile latency | custom-vector-bulk-train |      99.471 |     ms |
|                                       100th percentile latency | custom-vector-bulk-train |     210.424 |     ms |
|                                   50th percentile service time | custom-vector-bulk-train |      22.823 |     ms |
|                                   90th percentile service time | custom-vector-bulk-train |      34.864 |     ms |
|                                   99th percentile service time | custom-vector-bulk-train |      99.471 |     ms |
|                                  100th percentile service time | custom-vector-bulk-train |     210.424 |     ms |
|                                                     error rate | custom-vector-bulk-train |           0 |      % |
|                                                 Min Throughput |             delete-model |        8.39 |  ops/s |
|                                                Mean Throughput |             delete-model |        8.39 |  ops/s |
|                                              Median Throughput |             delete-model |        8.39 |  ops/s |
|                                                 Max Throughput |             delete-model |        8.39 |  ops/s |
|                                       100th percentile latency |             delete-model |     118.241 |     ms |
|                                  100th percentile service time |             delete-model |     118.241 |     ms |
|                                                     error rate |             delete-model |           0 |      % |
|                                                 Min Throughput |          train-knn-model |        0.64 |  ops/s |
|                                                Mean Throughput |          train-knn-model |        0.64 |  ops/s |
|                                              Median Throughput |          train-knn-model |        0.64 |  ops/s |
|                                                 Max Throughput |          train-knn-model |        0.64 |  ops/s |
|                                       100th percentile latency |          train-knn-model |     1564.44 |     ms |
|                                  100th percentile service time |          train-knn-model |     1564.44 |     ms |
|                                                     error rate |          train-knn-model |           0 |      % |
|                                                 Min Throughput |       custom-vector-bulk |     11313.1 | docs/s |
|                                                Mean Throughput |       custom-vector-bulk |     14065.7 | docs/s |
|                                              Median Throughput |       custom-vector-bulk |     12894.8 | docs/s |
|                                                 Max Throughput |       custom-vector-bulk |     30050.8 | docs/s |
|                                        50th percentile latency |       custom-vector-bulk |     81.4293 |     ms |
|                                        90th percentile latency |       custom-vector-bulk |     111.812 |     ms |
|                                        99th percentile latency |       custom-vector-bulk |      196.45 |     ms |
|                                      99.9th percentile latency |       custom-vector-bulk |     370.543 |     ms |
|                                     99.99th percentile latency |       custom-vector-bulk |     474.156 |     ms |
|                                       100th percentile latency |       custom-vector-bulk |     499.048 |     ms |
|                                   50th percentile service time |       custom-vector-bulk |     81.4235 |     ms |
|                                   90th percentile service time |       custom-vector-bulk |     111.833 |     ms |
|                                   99th percentile service time |       custom-vector-bulk |     197.125 |     ms |
|                                 99.9th percentile service time |       custom-vector-bulk |     370.543 |     ms |
|                                99.99th percentile service time |       custom-vector-bulk |     474.156 |     ms |
|                                  100th percentile service time |       custom-vector-bulk |     499.048 |     ms |
|                                                     error rate |       custom-vector-bulk |           0 |      % |
|                                                 Min Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                                Mean Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                              Median Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                                 Max Throughput |     force-merge-segments |         0.1 |  ops/s |
|                                       100th percentile latency |     force-merge-segments |     10015.2 |     ms |
|                                  100th percentile service time |     force-merge-segments |     10015.2 |     ms |
|                                                     error rate |     force-merge-segments |           0 |      % |
|                                                 Min Throughput |           warmup-indices |          19 |  ops/s |
|                                                Mean Throughput |           warmup-indices |          19 |  ops/s |
|                                              Median Throughput |           warmup-indices |          19 |  ops/s |
|                                                 Max Throughput |           warmup-indices |          19 |  ops/s |
|                                       100th percentile latency |           warmup-indices |     52.1685 |     ms |
|                                  100th percentile service time |           warmup-indices |     52.1685 |     ms |
|                                                     error rate |           warmup-indices |           0 |      % |
|                                                 Min Throughput |             prod-queries |      159.49 |  ops/s |
|                                                Mean Throughput |             prod-queries |      159.49 |  ops/s |
|                                              Median Throughput |             prod-queries |      159.49 |  ops/s |
|                                                 Max Throughput |             prod-queries |      159.49 |  ops/s |
|                                        50th percentile latency |             prod-queries |     1.92377 |     ms |
|                                        90th percentile latency |             prod-queries |     2.63867 |     ms |
|                                        99th percentile latency |             prod-queries |      48.513 |     ms |
|                                       100th percentile latency |             prod-queries |      90.543 |     ms |
|                                   50th percentile service time |             prod-queries |     1.92377 |     ms |
|                                   90th percentile service time |             prod-queries |     2.63867 |     ms |
|                                   99th percentile service time |             prod-queries |      48.513 |     ms |
|                                  100th percentile service time |             prod-queries |      90.543 |     ms |
|                                                     error rate |             prod-queries |           0 |      % |
|                                                  Mean recall@k |             prod-queries |        0.96 |        |
|                                                  Mean recall@1 |             prod-queries |        0.98 |        |


---------------------------------
[INFO] SUCCESS (took 218 seconds)
---------------------------------
```

##### Faiss IVF with Product Quantization (100 search queries)
```            
|                                                         Metric |                     Task |       Value |   Unit |
|---------------------------------------------------------------:|-------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                          |     11.3862 |    min |
|             Min cumulative indexing time across primary shards |                          |      0.0003 |    min |
|          Median cumulative indexing time across primary shards |                          |     0.12735 |    min |
|             Max cumulative indexing time across primary shards |                          |     11.2586 |    min |
|            Cumulative indexing throttle time of primary shards |                          |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                          |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                          |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                          |           0 |    min |
|                        Cumulative merge time of primary shards |                          |     1.50842 |    min |
|                       Cumulative merge count of primary shards |                          |          19 |        |
|                Min cumulative merge time across primary shards |                          |           0 |    min |
|             Median cumulative merge time across primary shards |                          | 0.000233333 |    min |
|                Max cumulative merge time across primary shards |                          |     1.50818 |    min |
|               Cumulative merge throttle time of primary shards |                          |     0.58095 |    min |
|       Min cumulative merge throttle time across primary shards |                          |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                          |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                          |     0.58095 |    min |
|                      Cumulative refresh time of primary shards |                          |      0.2059 |    min |
|                     Cumulative refresh count of primary shards |                          |          61 |        |
|              Min cumulative refresh time across primary shards |                          |  0.00238333 |    min |
|           Median cumulative refresh time across primary shards |                          |  0.00526667 |    min |
|              Max cumulative refresh time across primary shards |                          |     0.19825 |    min |
|                        Cumulative flush time of primary shards |                          |   0.0254667 |    min |
|                       Cumulative flush count of primary shards |                          |          10 |        |
|                Min cumulative flush time across primary shards |                          |           0 |    min |
|             Median cumulative flush time across primary shards |                          |   0.0118333 |    min |
|                Max cumulative flush time across primary shards |                          |   0.0136333 |    min |
|                                        Total Young Gen GC time |                          |       6.477 |      s |
|                                       Total Young Gen GC count |                          |        3565 |        |
|                                          Total Old Gen GC time |                          |           0 |      s |
|                                         Total Old Gen GC count |                          |           0 |        |
|                                                     Store size |                          |    0.892541 |     GB |
|                                                  Translog size |                          |   0.0304573 |     GB |
|                                         Heap used for segments |                          |           0 |     MB |
|                                       Heap used for doc values |                          |           0 |     MB |
|                                            Heap used for terms |                          |           0 |     MB |
|                                            Heap used for norms |                          |           0 |     MB |
|                                           Heap used for points |                          |           0 |     MB |
|                                    Heap used for stored fields |                          |           0 |     MB |
|                                                  Segment count |                          |          21 |        |
|                                                 Min Throughput | custom-vector-bulk-train |       31931 | docs/s |
|                                                Mean Throughput | custom-vector-bulk-train |       31931 | docs/s |
|                                              Median Throughput | custom-vector-bulk-train |       31931 | docs/s |
|                                                 Max Throughput | custom-vector-bulk-train |       31931 | docs/s |
|                                        50th percentile latency | custom-vector-bulk-train |     25.3297 |     ms |
|                                        90th percentile latency | custom-vector-bulk-train |     35.3864 |     ms |
|                                        99th percentile latency | custom-vector-bulk-train |     144.372 |     ms |
|                                       100th percentile latency | custom-vector-bulk-train |      209.37 |     ms |
|                                   50th percentile service time | custom-vector-bulk-train |     25.3226 |     ms |
|                                   90th percentile service time | custom-vector-bulk-train |     35.3864 |     ms |
|                                   99th percentile service time | custom-vector-bulk-train |     144.372 |     ms |
|                                  100th percentile service time | custom-vector-bulk-train |      209.37 |     ms |
|                                                     error rate | custom-vector-bulk-train |           0 |      % |
|                                                 Min Throughput |             delete-model |        8.65 |  ops/s |
|                                                Mean Throughput |             delete-model |        8.65 |  ops/s |
|                                              Median Throughput |             delete-model |        8.65 |  ops/s |
|                                                 Max Throughput |             delete-model |        8.65 |  ops/s |
|                                       100th percentile latency |             delete-model |     114.725 |     ms |
|                                  100th percentile service time |             delete-model |     114.725 |     ms |
|                                                     error rate |             delete-model |           0 |      % |
|                                                 Min Throughput |          train-knn-model |        0.03 |  ops/s |
|                                                Mean Throughput |          train-knn-model |        0.03 |  ops/s |
|                                              Median Throughput |          train-knn-model |        0.03 |  ops/s |
|                                                 Max Throughput |          train-knn-model |        0.03 |  ops/s |
|                                       100th percentile latency |          train-knn-model |     37222.2 |     ms |
|                                  100th percentile service time |          train-knn-model |     37222.2 |     ms |
|                                                     error rate |          train-knn-model |           0 |      % |
|                                                 Min Throughput |       custom-vector-bulk |     10669.3 | docs/s |
|                                                Mean Throughput |       custom-vector-bulk |     14468.6 | docs/s |
|                                              Median Throughput |       custom-vector-bulk |     12496.1 | docs/s |
|                                                 Max Throughput |       custom-vector-bulk |     35027.8 | docs/s |
|                                        50th percentile latency |       custom-vector-bulk |     74.2584 |     ms |
|                                        90th percentile latency |       custom-vector-bulk |     113.426 |     ms |
|                                        99th percentile latency |       custom-vector-bulk |     293.075 |     ms |
|                                      99.9th percentile latency |       custom-vector-bulk |     1774.41 |     ms |
|                                     99.99th percentile latency |       custom-vector-bulk |     1969.99 |     ms |
|                                       100th percentile latency |       custom-vector-bulk |     1971.29 |     ms |
|                                   50th percentile service time |       custom-vector-bulk |     74.2577 |     ms |
|                                   90th percentile service time |       custom-vector-bulk |     113.477 |     ms |
|                                   99th percentile service time |       custom-vector-bulk |     292.481 |     ms |
|                                 99.9th percentile service time |       custom-vector-bulk |     1774.41 |     ms |
|                                99.99th percentile service time |       custom-vector-bulk |     1969.99 |     ms |
|                                  100th percentile service time |       custom-vector-bulk |     1971.29 |     ms |
|                                                     error rate |       custom-vector-bulk |           0 |      % |
|                                                 Min Throughput |     force-merge-segments |        0.05 |  ops/s |
|                                                Mean Throughput |     force-merge-segments |        0.05 |  ops/s |
|                                              Median Throughput |     force-merge-segments |        0.05 |  ops/s |
|                                                 Max Throughput |     force-merge-segments |        0.05 |  ops/s |
|                                       100th percentile latency |     force-merge-segments |     20015.2 |     ms |
|                                  100th percentile service time |     force-merge-segments |     20015.2 |     ms |
|                                                     error rate |     force-merge-segments |           0 |      % |
|                                                 Min Throughput |           warmup-indices |       47.06 |  ops/s |
|                                                Mean Throughput |           warmup-indices |       47.06 |  ops/s |
|                                              Median Throughput |           warmup-indices |       47.06 |  ops/s |
|                                                 Max Throughput |           warmup-indices |       47.06 |  ops/s |
|                                       100th percentile latency |           warmup-indices |     20.6798 |     ms |
|                                  100th percentile service time |           warmup-indices |     20.6798 |     ms |
|                                                     error rate |           warmup-indices |           0 |      % |
|                                                 Min Throughput |             prod-queries |       87.76 |  ops/s |
|                                                Mean Throughput |             prod-queries |       87.76 |  ops/s |
|                                              Median Throughput |             prod-queries |       87.76 |  ops/s |
|                                                 Max Throughput |             prod-queries |       87.76 |  ops/s |
|                                        50th percentile latency |             prod-queries |     1.81677 |     ms |
|                                        90th percentile latency |             prod-queries |     2.80454 |     ms |
|                                        99th percentile latency |             prod-queries |     51.2039 |     ms |
|                                       100th percentile latency |             prod-queries |     98.2032 |     ms |
|                                   50th percentile service time |             prod-queries |     1.81677 |     ms |
|                                   90th percentile service time |             prod-queries |     2.80454 |     ms |
|                                   99th percentile service time |             prod-queries |     51.2039 |     ms |
|                                  100th percentile service time |             prod-queries |     98.2032 |     ms |
|                                                     error rate |             prod-queries |           0 |      % |
|                                                  Mean recall@k |             prod-queries |        0.62 |        |
|                                                  Mean recall@1 |             prod-queries |        0.52 |        |

---------------------------------
[INFO] SUCCESS (took 413 seconds)
---------------------------------
```

### Custom Runners

Currently, there is only one custom runner defined in [runners.py](runners.py).

| Syntax             | Description                                         | Parameters                                                                                                   |
|--------------------|-----------------------------------------------------|:-------------------------------------------------------------------------------------------------------------|
| warmup-knn-indices | Warm up knn indices with retry until success.       | 1. index - name of index to warmup                                                                           |

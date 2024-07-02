# Semantic Search Workload

This workload is to benchmark performance of search of Semantic Search queries of OpenSearch. 

## Datasets

This workload is based on a [daily weather measurement from NOAA](ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/by_year/).

### Example Document

```json
{
  "date": "2016-01-01T00:00:00",
  "TAVG": 22.9,
  "station": {
    "elevation": 34.0,
    "name": "SHARJAH INTER. AIRP",
    "country": "United",
    "gsn_flag": "GSN",
    "location": {
      "lat": 25.333,
      "lon": 55.517
    },
    "country_code": "AE",
    "wmo_id": "41196",
    "id": "AE000041196"
  },
  "TMIN": 15.5
}
```

## Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `max_num_segments` : Number segments that used for force merge, force merge is skipped if parameter has not been set
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `target_throughput` (default: default values for each operation): Number of requests per second, `none` for no limit.
* `search_clients`: Number of clients that issues search requests.
* `concurrent_segment_search_enabled` (default: "false"): Setting enables or disables consurrent segment search feature for the cluster. Setting is avaliable starting from version 2.12.

### Running a benchmark

Before running a benchmark, ensure that the load generation host is able to access your cluster endpoint and that the 
appropriate dataset is available on the host.

Currently, we support 5 test procedures for the semantic search workload. The default procedure is `hybrid-query-aggs-light` and does create an index, ingest data and run a base set of search queries.

To run the default workload, invoke the following command. In that example we set some extra parameters directly as part of the command.

```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT=  
# Absolute file path of Workload file
export WORKLOAD_FILE=

opensearch-benchmark execute-test \
    --target-hosts $ENDPOINT \
    --workload-path=${WORKLOAD_FILE} \
    --workload-params="number_of_shards:6,max_num_segments:8,concurrent_segment_search_enabled:'false',ingest_percentage:5" \
    --pipeline benchmark-only \
    --kill-running-processes
```

Below is another example of command. In this example we refer to a workload by its name, use file for workflow params and choose a non-default test procedure. Keep workload parameters in file is helping to keep command for workload short and decreases chance of errors. Users are welcome to use one of example parameter files from `params` folder

```
# OpenSearch Cluster End point url with hostname and port
export ENDPOINT=  
# Absolute file path of Workload param file
export PARAMS_FILE=./noaa_semantic_search/params/one_replica_with_concurrent_segment_search.json

opensearch-benchmark execute-test \
    --target-hosts $ENDPOINT \
    --workload noaa_semantic_search \
    --workload-params ${PARAMS_FILE} \
    --test-procedure=hybrid-query-aggs-full \
    --pipeline benchmark-only \
    --kill-running-processes
```


## Current Procedures

### Hybrid Query Aggregations Light

The Hybrid Query Aggregations Light procedure is used to run a basic workload for search using hybrid query that has aggregations. As part of this precedure
we create an index and ingest documents, then run search queries. 
Procedure name `hybrid-query-aggs-light`.
This is a default precedure for this workload.

### Hybrid Query Aggregations Full

The Hybrid Query Aggregations Full procedure is used to run set of multiple search queries with hybrid query and identical bool query, both with aggregations. As part of this precedure
we create an index and ingest documents, then run search queries. Workload ment to compare performance of hybrid query and bool query.
Procedure name `hybrid-query-aggs-full`.

### Create and Index

The Create and Index procedure is used to set up a cluster for other workloads. As part of this precedure we create an index and ingest documents, no search queries are executed.
Procedure name `create-and-index`.

### Hybrid Query Aggregations No Index

The Hybrid Query Aggregations No Index procedure is used to run set of multiple search queries with hybrid query and identical bool query, both with aggregations. We do not create index and do not ingest any documents in this procedure, the assumption is that index already exists.
Procedure name `hybrid-query-aggs-no-index`.

### Profiling

The Profiling of Hybrid Query with Aggregations procedure is used to run small set of hybrid queries with aggregations to collect runtime metrics thaty can be used for analysis like profiling or debug. It does not create index or ingestg documents.
Procedure name `search-profiling`.

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

[INFO] Executing test with workload [workload], test_procedure [hybrid-query-aggs-light] and provision_config_instance ['external'] with version [2.14.0].

[WARNING] indexing_total_time is 11 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] refresh_total_time is 27 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
[WARNING] flush_total_time is 11 ms indicating that the cluster is not in a defined clean state. Recorded index time metrics may be misleading.
Running delete-index                                                           [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health-before-index-creation                             [100% done]
Running index                                                                  [100% done]
Running refresh-after-index-created                                            [100% done]
Running check-cluster-health                                                   [100% done]
Running set-concurent-segment-search-setting                                   [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running create-normalization-processor-no-weights-search-pipeline              [100% done]
Running hybrid-query-only-range                                                [100% done]
Running bool-only-range                                                        [100% done]
Running Aggs query for min, avg and sum for one subquery case                  [100% done]
Running aggs-query-min-avg-sum-bool-one-subquery                               [100% done]
Running aggs-query-min-avg-sum-hybrid-one-subquery                             [100% done]
Running Aggs query for term and min for one subquery case                      [100% done]
Running aggs-query-term-min-bool-one-subquery                                  [100% done]
Running aggs-query-term-min-hybrid-one-subquery                                [100% done]
Running Aggs query for date historgram and geohash grid for one subquery case  [100% done]
Running aggs-query-date-histo-geohash-grid-bool-one-subquery                   [100% done]
Running aggs-query-date-histo-geohash-grid-hybrid-one-subquery                 [100% done]
Running Aggs query for range and significant terms for one subquery case       [100% done]
Running aggs-query-range-numeric-significant-terms-bool-one-subquery           [100% done]
Running aggs-query-range-numeric-significant-terms-hybrid-one-subquery         [100% done]

------------------------------------------------------
    _______             __   _____
   / ____(_)___  ____ _/ /  / ___/_________  ________
  / /_  / / __ \/ __ `/ /   \__ \/ ___/ __ \/ ___/ _ \
 / __/ / / / / / /_/ / /   ___/ / /__/ /_/ / /  /  __/
/_/   /_/_/ /_/\__,_/_/   /____/\___/\____/_/   \___/
------------------------------------------------------

|                                                         Metric |                                                                  Task |       Value |   Unit |
|---------------------------------------------------------------:|----------------------------------------------------------------------:|------------:|-------:|
|                     Cumulative indexing time of primary shards |                                                                       |    0.897317 |    min |
|             Min cumulative indexing time across primary shards |                                                                       | 0.000183333 |    min |
|          Median cumulative indexing time across primary shards |                                                                       |    0.141783 |    min |
|             Max cumulative indexing time across primary shards |                                                                       |      0.1723 |    min |
|            Cumulative indexing throttle time of primary shards |                                                                       |           0 |    min |
|    Min cumulative indexing throttle time across primary shards |                                                                       |           0 |    min |
| Median cumulative indexing throttle time across primary shards |                                                                       |           0 |    min |
|    Max cumulative indexing throttle time across primary shards |                                                                       |           0 |    min |
|                        Cumulative merge time of primary shards |                                                                       |   0.0405167 |    min |
|                       Cumulative merge count of primary shards |                                                                       |          11 |        |
|                Min cumulative merge time across primary shards |                                                                       |           0 |    min |
|             Median cumulative merge time across primary shards |                                                                       |  0.00556667 |    min |
|                Max cumulative merge time across primary shards |                                                                       |      0.0114 |    min |
|               Cumulative merge throttle time of primary shards |                                                                       |           0 |    min |
|       Min cumulative merge throttle time across primary shards |                                                                       |           0 |    min |
|    Median cumulative merge throttle time across primary shards |                                                                       |           0 |    min |
|       Max cumulative merge throttle time across primary shards |                                                                       |           0 |    min |
|                      Cumulative refresh time of primary shards |                                                                       |    0.191783 |    min |
|                     Cumulative refresh count of primary shards |                                                                       |         131 |        |
|              Min cumulative refresh time across primary shards |                                                                       |     0.00045 |    min |
|           Median cumulative refresh time across primary shards |                                                                       |   0.0308333 |    min |
|              Max cumulative refresh time across primary shards |                                                                       |   0.0420333 |    min |
|                        Cumulative flush time of primary shards |                                                                       | 0.000183333 |    min |
|                       Cumulative flush count of primary shards |                                                                       |           7 |        |
|                Min cumulative flush time across primary shards |                                                                       |           0 |    min |
|             Median cumulative flush time across primary shards |                                                                       |           0 |    min |
|                Max cumulative flush time across primary shards |                                                                       | 0.000183333 |    min |
|                                        Total Young Gen GC time |                                                                       |        0.64 |      s |
|                                       Total Young Gen GC count |                                                                       |         219 |        |
|                                          Total Old Gen GC time |                                                                       |           0 |      s |
|                                         Total Old Gen GC count |                                                                       |           0 |        |
|                                                     Store size |                                                                       |    0.358935 |     GB |
|                                                  Translog size |                                                                       | 4.09782e-07 |     GB |
|                                         Heap used for segments |                                                                       |           0 |     MB |
|                                       Heap used for doc values |                                                                       |           0 |     MB |
|                                            Heap used for terms |                                                                       |           0 |     MB |
|                                            Heap used for norms |                                                                       |           0 |     MB |
|                                           Heap used for points |                                                                       |           0 |     MB |
|                                    Heap used for stored fields |                                                                       |           0 |     MB |
|                                                  Segment count |                                                                       |          47 |        |
|                                                 Min Throughput |                                                                 index |     5702.79 | docs/s |
|                                                Mean Throughput |                                                                 index |     6938.19 | docs/s |
|                                              Median Throughput |                                                                 index |     6904.34 | docs/s |
|                                                 Max Throughput |                                                                 index |     9134.52 | docs/s |
|                                        50th percentile latency |                                                                 index |     2924.82 |     ms |
|                                        90th percentile latency |                                                                 index |     10885.4 |     ms |
|                                        99th percentile latency |                                                                 index |     33643.2 |     ms |
|                                       100th percentile latency |                                                                 index |       34908 |     ms |
|                                   50th percentile service time |                                                                 index |     2924.82 |     ms |
|                                   90th percentile service time |                                                                 index |     10885.4 |     ms |
|                                   99th percentile service time |                                                                 index |     33643.2 |     ms |
|                                  100th percentile service time |                                                                 index |       34908 |     ms |
|                                                     error rate |                                                                 index |           0 |      % |
|                                                 Min Throughput |                                              wait-until-merges-finish |        5.59 |  ops/s |
|                                                Mean Throughput |                                              wait-until-merges-finish |        5.59 |  ops/s |
|                                              Median Throughput |                                              wait-until-merges-finish |        5.59 |  ops/s |
|                                                 Max Throughput |                                              wait-until-merges-finish |        5.59 |  ops/s |
|                                       100th percentile latency |                                              wait-until-merges-finish |      178.13 |     ms |
|                                  100th percentile service time |                                              wait-until-merges-finish |      178.13 |     ms |
|                                                     error rate |                                              wait-until-merges-finish |           0 |      % |
|                                                 Min Throughput |                                               hybrid-query-only-range |        5.97 |  ops/s |
|                                                Mean Throughput |                                               hybrid-query-only-range |        5.98 |  ops/s |
|                                              Median Throughput |                                               hybrid-query-only-range |        5.99 |  ops/s |
|                                                 Max Throughput |                                               hybrid-query-only-range |        5.99 |  ops/s |
|                                        50th percentile latency |                                               hybrid-query-only-range |     100.609 |     ms |
|                                        90th percentile latency |                                               hybrid-query-only-range |     118.742 |     ms |
|                                        99th percentile latency |                                               hybrid-query-only-range |     186.626 |     ms |
|                                       100th percentile latency |                                               hybrid-query-only-range |     231.556 |     ms |
|                                   50th percentile service time |                                               hybrid-query-only-range |     98.5628 |     ms |
|                                   90th percentile service time |                                               hybrid-query-only-range |     116.906 |     ms |
|                                   99th percentile service time |                                               hybrid-query-only-range |     184.897 |     ms |
|                                  100th percentile service time |                                               hybrid-query-only-range |     229.856 |     ms |
|                                                     error rate |                                               hybrid-query-only-range |           0 |      % |
|                                                 Min Throughput |                                                       bool-only-range |        5.95 |  ops/s |
|                                                Mean Throughput |                                                       bool-only-range |        5.98 |  ops/s |
|                                              Median Throughput |                                                       bool-only-range |        5.98 |  ops/s |
|                                                 Max Throughput |                                                       bool-only-range |        5.99 |  ops/s |
|                                        50th percentile latency |                                                       bool-only-range |     88.0508 |     ms |
|                                        90th percentile latency |                                                       bool-only-range |     101.207 |     ms |
|                                        99th percentile latency |                                                       bool-only-range |     124.185 |     ms |
|                                       100th percentile latency |                                                       bool-only-range |     188.001 |     ms |
|                                   50th percentile service time |                                                       bool-only-range |     87.3025 |     ms |
|                                   90th percentile service time |                                                       bool-only-range |     98.1776 |     ms |
|                                   99th percentile service time |                                                       bool-only-range |     119.033 |     ms |
|                                  100th percentile service time |                                                       bool-only-range |     146.967 |     ms |
|                                                     error rate |                                                       bool-only-range |           0 |      % |
|                                                 Min Throughput |                 Aggs query for min, avg and sum for one subquery case |        5.84 |  ops/s |
|                                                Mean Throughput |                 Aggs query for min, avg and sum for one subquery case |        5.92 |  ops/s |
|                                              Median Throughput |                 Aggs query for min, avg and sum for one subquery case |        5.93 |  ops/s |
|                                                 Max Throughput |                 Aggs query for min, avg and sum for one subquery case |        5.96 |  ops/s |
|                                        50th percentile latency |                 Aggs query for min, avg and sum for one subquery case |     112.333 |     ms |
|                                        90th percentile latency |                 Aggs query for min, avg and sum for one subquery case |     152.229 |     ms |
|                                        99th percentile latency |                 Aggs query for min, avg and sum for one subquery case |     227.534 |     ms |
|                                       100th percentile latency |                 Aggs query for min, avg and sum for one subquery case |     261.563 |     ms |
|                                   50th percentile service time |                 Aggs query for min, avg and sum for one subquery case |     107.203 |     ms |
|                                   90th percentile service time |                 Aggs query for min, avg and sum for one subquery case |     132.942 |     ms |
|                                   99th percentile service time |                 Aggs query for min, avg and sum for one subquery case |     190.227 |     ms |
|                                  100th percentile service time |                 Aggs query for min, avg and sum for one subquery case |     214.326 |     ms |
|                                                     error rate |                 Aggs query for min, avg and sum for one subquery case |           0 |      % |
|                                                 Min Throughput |                              aggs-query-min-avg-sum-bool-one-subquery |        5.97 |  ops/s |
|                                                Mean Throughput |                              aggs-query-min-avg-sum-bool-one-subquery |        5.99 |  ops/s |
|                                              Median Throughput |                              aggs-query-min-avg-sum-bool-one-subquery |        5.99 |  ops/s |
|                                                 Max Throughput |                              aggs-query-min-avg-sum-bool-one-subquery |        5.99 |  ops/s |
|                                        50th percentile latency |                              aggs-query-min-avg-sum-bool-one-subquery |     87.6926 |     ms |
|                                        90th percentile latency |                              aggs-query-min-avg-sum-bool-one-subquery |     104.576 |     ms |
|                                        99th percentile latency |                              aggs-query-min-avg-sum-bool-one-subquery |     203.709 |     ms |
|                                       100th percentile latency |                              aggs-query-min-avg-sum-bool-one-subquery |     269.109 |     ms |
|                                   50th percentile service time |                              aggs-query-min-avg-sum-bool-one-subquery |     85.8629 |     ms |
|                                   90th percentile service time |                              aggs-query-min-avg-sum-bool-one-subquery |     101.632 |     ms |
|                                   99th percentile service time |                              aggs-query-min-avg-sum-bool-one-subquery |       180.6 |     ms |
|                                  100th percentile service time |                              aggs-query-min-avg-sum-bool-one-subquery |     195.283 |     ms |
|                                                     error rate |                              aggs-query-min-avg-sum-bool-one-subquery |           0 |      % |
|                                                 Min Throughput |                            aggs-query-min-avg-sum-hybrid-one-subquery |        5.94 |  ops/s |
|                                                Mean Throughput |                            aggs-query-min-avg-sum-hybrid-one-subquery |        5.97 |  ops/s |
|                                              Median Throughput |                            aggs-query-min-avg-sum-hybrid-one-subquery |        5.98 |  ops/s |
|                                                 Max Throughput |                            aggs-query-min-avg-sum-hybrid-one-subquery |        5.99 |  ops/s |
|                                        50th percentile latency |                            aggs-query-min-avg-sum-hybrid-one-subquery |     95.0633 |     ms |
|                                        90th percentile latency |                            aggs-query-min-avg-sum-hybrid-one-subquery |     113.668 |     ms |
|                                        99th percentile latency |                            aggs-query-min-avg-sum-hybrid-one-subquery |     219.286 |     ms |
|                                       100th percentile latency |                            aggs-query-min-avg-sum-hybrid-one-subquery |     245.169 |     ms |
|                                   50th percentile service time |                            aggs-query-min-avg-sum-hybrid-one-subquery |     93.7066 |     ms |
|                                   90th percentile service time |                            aggs-query-min-avg-sum-hybrid-one-subquery |     110.172 |     ms |
|                                   99th percentile service time |                            aggs-query-min-avg-sum-hybrid-one-subquery |     217.966 |     ms |
|                                  100th percentile service time |                            aggs-query-min-avg-sum-hybrid-one-subquery |     244.169 |     ms |
|                                                     error rate |                            aggs-query-min-avg-sum-hybrid-one-subquery |           0 |      % |
|                                                 Min Throughput |                     Aggs query for term and min for one subquery case |        5.68 |  ops/s |
|                                                Mean Throughput |                     Aggs query for term and min for one subquery case |        5.85 |  ops/s |
|                                              Median Throughput |                     Aggs query for term and min for one subquery case |        5.87 |  ops/s |
|                                                 Max Throughput |                     Aggs query for term and min for one subquery case |        5.92 |  ops/s |
|                                        50th percentile latency |                     Aggs query for term and min for one subquery case |     125.115 |     ms |
|                                        90th percentile latency |                     Aggs query for term and min for one subquery case |     146.388 |     ms |
|                                        99th percentile latency |                     Aggs query for term and min for one subquery case |     210.877 |     ms |
|                                       100th percentile latency |                     Aggs query for term and min for one subquery case |     233.741 |     ms |
|                                   50th percentile service time |                     Aggs query for term and min for one subquery case |     124.173 |     ms |
|                                   90th percentile service time |                     Aggs query for term and min for one subquery case |     144.226 |     ms |
|                                   99th percentile service time |                     Aggs query for term and min for one subquery case |     174.317 |     ms |
|                                  100th percentile service time |                     Aggs query for term and min for one subquery case |     232.337 |     ms |
|                                                     error rate |                     Aggs query for term and min for one subquery case |           0 |      % |
|                                                 Min Throughput |                                 aggs-query-term-min-bool-one-subquery |        5.94 |  ops/s |
|                                                Mean Throughput |                                 aggs-query-term-min-bool-one-subquery |        5.97 |  ops/s |
|                                              Median Throughput |                                 aggs-query-term-min-bool-one-subquery |        5.97 |  ops/s |
|                                                 Max Throughput |                                 aggs-query-term-min-bool-one-subquery |        5.98 |  ops/s |
|                                        50th percentile latency |                                 aggs-query-term-min-bool-one-subquery |     85.5141 |     ms |
|                                        90th percentile latency |                                 aggs-query-term-min-bool-one-subquery |       102.2 |     ms |
|                                        99th percentile latency |                                 aggs-query-term-min-bool-one-subquery |     135.633 |     ms |
|                                       100th percentile latency |                                 aggs-query-term-min-bool-one-subquery |     145.392 |     ms |
|                                   50th percentile service time |                                 aggs-query-term-min-bool-one-subquery |     84.2466 |     ms |
|                                   90th percentile service time |                                 aggs-query-term-min-bool-one-subquery |     100.799 |     ms |
|                                   99th percentile service time |                                 aggs-query-term-min-bool-one-subquery |     134.249 |     ms |
|                                  100th percentile service time |                                 aggs-query-term-min-bool-one-subquery |     143.953 |     ms |
|                                                     error rate |                                 aggs-query-term-min-bool-one-subquery |           0 |      % |
|                                                 Min Throughput |                               aggs-query-term-min-hybrid-one-subquery |         5.9 |  ops/s |
|                                                Mean Throughput |                               aggs-query-term-min-hybrid-one-subquery |        5.95 |  ops/s |
|                                              Median Throughput |                               aggs-query-term-min-hybrid-one-subquery |        5.96 |  ops/s |
|                                                 Max Throughput |                               aggs-query-term-min-hybrid-one-subquery |        5.98 |  ops/s |
|                                        50th percentile latency |                               aggs-query-term-min-hybrid-one-subquery |     95.5761 |     ms |
|                                        90th percentile latency |                               aggs-query-term-min-hybrid-one-subquery |     98.9932 |     ms |
|                                        99th percentile latency |                               aggs-query-term-min-hybrid-one-subquery |     195.871 |     ms |
|                                       100th percentile latency |                               aggs-query-term-min-hybrid-one-subquery |     228.879 |     ms |
|                                   50th percentile service time |                               aggs-query-term-min-hybrid-one-subquery |     94.3535 |     ms |
|                                   90th percentile service time |                               aggs-query-term-min-hybrid-one-subquery |     96.5676 |     ms |
|                                   99th percentile service time |                               aggs-query-term-min-hybrid-one-subquery |     158.959 |     ms |
|                                  100th percentile service time |                               aggs-query-term-min-hybrid-one-subquery |     227.959 |     ms |
|                                                     error rate |                               aggs-query-term-min-hybrid-one-subquery |           0 |      % |
|                                                 Min Throughput | Aggs query for date historgram and geohash grid for one subquery case |        4.33 |  ops/s |
|                                                Mean Throughput | Aggs query for date historgram and geohash grid for one subquery case |        4.97 |  ops/s |
|                                              Median Throughput | Aggs query for date historgram and geohash grid for one subquery case |        5.08 |  ops/s |
|                                                 Max Throughput | Aggs query for date historgram and geohash grid for one subquery case |        5.27 |  ops/s |
|                                        50th percentile latency | Aggs query for date historgram and geohash grid for one subquery case |        2235 |     ms |
|                                        90th percentile latency | Aggs query for date historgram and geohash grid for one subquery case |     2672.43 |     ms |
|                                        99th percentile latency | Aggs query for date historgram and geohash grid for one subquery case |     2763.52 |     ms |
|                                       100th percentile latency | Aggs query for date historgram and geohash grid for one subquery case |     2779.09 |     ms |
|                                   50th percentile service time | Aggs query for date historgram and geohash grid for one subquery case |     163.851 |     ms |
|                                   90th percentile service time | Aggs query for date historgram and geohash grid for one subquery case |     199.071 |     ms |
|                                   99th percentile service time | Aggs query for date historgram and geohash grid for one subquery case |     203.129 |     ms |
|                                  100th percentile service time | Aggs query for date historgram and geohash grid for one subquery case |     214.436 |     ms |
|                                                     error rate | Aggs query for date historgram and geohash grid for one subquery case |           0 |      % |
|                                                 Min Throughput |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |        5.89 |  ops/s |
|                                                Mean Throughput |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |        5.99 |  ops/s |
|                                              Median Throughput |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |        5.99 |  ops/s |
|                                                 Max Throughput |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |           6 |  ops/s |
|                                        50th percentile latency |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     91.0849 |     ms |
|                                        90th percentile latency |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |      111.41 |     ms |
|                                        99th percentile latency |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     331.864 |     ms |
|                                       100th percentile latency |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     391.862 |     ms |
|                                   50th percentile service time |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     89.6302 |     ms |
|                                   90th percentile service time |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     95.8593 |     ms |
|                                   99th percentile service time |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |     115.561 |     ms |
|                                  100th percentile service time |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |      330.52 |     ms |
|                                                     error rate |                  aggs-query-date-histo-geohash-grid-bool-one-subquery |           0 |      % |
|                                                 Min Throughput |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |        5.88 |  ops/s |
|                                                Mean Throughput |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |        5.97 |  ops/s |
|                                              Median Throughput |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |        5.98 |  ops/s |
|                                                 Max Throughput |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |        5.99 |  ops/s |
|                                        50th percentile latency |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     90.0542 |     ms |
|                                        90th percentile latency |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     140.712 |     ms |
|                                        99th percentile latency |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |      418.95 |     ms |
|                                       100th percentile latency |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     473.984 |     ms |
|                                   50th percentile service time |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     88.8075 |     ms |
|                                   90th percentile service time |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     106.082 |     ms |
|                                   99th percentile service time |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     198.375 |     ms |
|                                  100th percentile service time |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |     326.313 |     ms |
|                                                     error rate |                aggs-query-date-histo-geohash-grid-hybrid-one-subquery |           0 |      % |
|                                                 Min Throughput |      Aggs query for range and significant terms for one subquery case |        3.57 |  ops/s |
|                                                Mean Throughput |      Aggs query for range and significant terms for one subquery case |        3.71 |  ops/s |
|                                              Median Throughput |      Aggs query for range and significant terms for one subquery case |        3.73 |  ops/s |
|                                                 Max Throughput |      Aggs query for range and significant terms for one subquery case |         3.8 |  ops/s |
|                                        50th percentile latency |      Aggs query for range and significant terms for one subquery case |     7573.73 |     ms |
|                                        90th percentile latency |      Aggs query for range and significant terms for one subquery case |     11072.2 |     ms |
|                                        99th percentile latency |      Aggs query for range and significant terms for one subquery case |       11850 |     ms |
|                                       100th percentile latency |      Aggs query for range and significant terms for one subquery case |     11941.7 |     ms |
|                                   50th percentile service time |      Aggs query for range and significant terms for one subquery case |     254.273 |     ms |
|                                   90th percentile service time |      Aggs query for range and significant terms for one subquery case |     269.217 |     ms |
|                                   99th percentile service time |      Aggs query for range and significant terms for one subquery case |     287.574 |     ms |
|                                  100th percentile service time |      Aggs query for range and significant terms for one subquery case |     501.832 |     ms |
|                                                     error rate |      Aggs query for range and significant terms for one subquery case |           0 |      % |
|                                                 Min Throughput |          aggs-query-range-numeric-significant-terms-bool-one-subquery |         5.9 |  ops/s |
|                                                Mean Throughput |          aggs-query-range-numeric-significant-terms-bool-one-subquery |        5.97 |  ops/s |
|                                              Median Throughput |          aggs-query-range-numeric-significant-terms-bool-one-subquery |        5.98 |  ops/s |
|                                                 Max Throughput |          aggs-query-range-numeric-significant-terms-bool-one-subquery |        5.99 |  ops/s |
|                                        50th percentile latency |          aggs-query-range-numeric-significant-terms-bool-one-subquery |      93.431 |     ms |
|                                        90th percentile latency |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     110.077 |     ms |
|                                        99th percentile latency |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     176.629 |     ms |
|                                       100th percentile latency |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     176.785 |     ms |
|                                   50th percentile service time |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     92.6441 |     ms |
|                                   90th percentile service time |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     109.314 |     ms |
|                                   99th percentile service time |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     120.183 |     ms |
|                                  100th percentile service time |          aggs-query-range-numeric-significant-terms-bool-one-subquery |     125.586 |     ms |
|                                                     error rate |          aggs-query-range-numeric-significant-terms-bool-one-subquery |           0 |      % |
|                                                 Min Throughput |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |        5.87 |  ops/s |
|                                                Mean Throughput |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |        5.94 |  ops/s |
|                                              Median Throughput |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |        5.94 |  ops/s |
|                                                 Max Throughput |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |        5.97 |  ops/s |
|                                        50th percentile latency |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     96.1517 |     ms |
|                                        90th percentile latency |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     163.551 |     ms |
|                                        99th percentile latency |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     263.177 |     ms |
|                                       100th percentile latency |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     299.442 |     ms |
|                                   50th percentile service time |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     94.7605 |     ms |
|                                   90th percentile service time |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     112.209 |     ms |
|                                   99th percentile service time |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |      245.69 |     ms |
|                                  100th percentile service time |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |     275.583 |     ms |
|                                                     error rate |        aggs-query-range-numeric-significant-terms-hybrid-one-subquery |           0 |      % |


---------------------------------
[INFO] SUCCESS (took 683 seconds)
---------------------------------
```

## License

[US Government Work data license](https://www.usa.gov/government-works)

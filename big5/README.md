## Big5 OSB Workload

This repository contains the **_Big5_** workload for benchmarking OpenSearch using OpenSearch Benchmark. This workload focuses on five essential areas in OpenSearch performance and querying: Text Querying, Sorting, Date Histogram, Range Queries, and Terms Aggregation.

This workload is derived from the Elasticsearch vs. OpenSearch comparison benchmark.  It has been modified to conform to OpenSearch Benchmark terminology and comply with OpenSearch features.


### The "Big 5" Areas

1. Text Querying:

   Free text search is vital for databases due to its flexibility, ease of use, and ability to quickly filter data. It allows users to input natural language queries, eliminating the need for complex query languages and making data retrieval more intuitive. With free text search, users can find information using familiar terms, such as names, email addresses, or user IDs, without requiring knowledge about the underlying schema. It is particularly useful for handling unstructured data, supporting partial matches, and facilitating data exploration.

2. Sorting:

   Sorting is a process of arranging data in a particular order, such as alphabetical, numerical, or chronological. The sort query in OpenSearch is useful for organizing search results based on specific criteria, ensuring that the most relevant results are presented to users. It is a vital feature that enhances the user experience and improves the overall effectiveness of the search process.

   In the context of observability and security, in which signals from multiple systems are correlated, sorting is a crucial operation. By sorting results based on timestamp, metrics, or any other relevant field, analysts can more efficiently identify issues, security threats, or correlations within the data. With this information, it becomes easier to identify patterns, trends, and insights that can inform business decisions to protect your data and ensure uptime.

3. Date Histogram:

   The date histogram aggregation in OpenSearch is useful for aggregating and analyzing time-based data by dividing it into intervals, or buckets. This capability allows users to visualize and better understand trends, patterns, and anomalies over time.

4. Range Queries:

   The range query in OpenSearch is useful for filtering search results based on a specific range of values in a given field. This capability allows users to narrow down their search results and find more relevant information quickly.

5. Terms Aggregation:

   Terms allow users to dynamically build into buckets to source based on aggregation values. These can be 100s or 1000s of unique terms that get returned individually or in composite aggregations. Larger size values use more memory and compute to push the aggregations through.


### Prerequisites

Before using this repository, ensure you have the following installed:

- [OpenSearch](https://opensearch.org) (v2.11 or later)
- [OpenSearch Benchmark](https://opensearch.org/docs/latest/benchmark) (v1.2 or later)
- [OpenSearch SQL Plugin](https://opensearch.org/docs/latest/search-plugins/sql/index/) (required for PPL operations)


### PPL Operations Support

This workload includes PPL (Piped Processing Language) operations that provide an alternative query interface to OpenSearch. PPL operations are available in the `operations/ppl.json` file and include:

- **ppl-default**: Basic PPL query with head operation
- **ppl-term**: Term filtering using PPL where clause
- **ppl-range**: Range filtering with timestamp conditions
- **ppl-*-sort-***: Various sorting operations (ascending/descending, with/without shortcuts)
- **ppl-date-histogram-***: Date histogram aggregations (hourly/minute intervals)
- **ppl-composite-***: Composite aggregations for terms and date histograms
- **ppl-keyword-***: Keyword-based operations and aggregations
- **ppl-query-string-***: Query string operations with filtering and sorting
- **ppl-range-***: Range queries with various conditions and sorting
- **ppl-sort-***: Sorting operations on different field types
- **ppl-terms-***: Terms aggregations for statistical analysis

To use PPL operations, run the workload with the `ppl` test procedure:

```bash
osb execute-test --workload=big5 --test-procedure=ppl
```

This will execute all PPL operations including basic queries, sorting, aggregations, and range operations using the PPL syntax instead of the standard OpenSearch Query DSL.

#### PPL Operations Troubleshooting

If your cluster doesn't have the SQL plugin installed, all PPL operations will fail with the following error:

```
[ERROR] no handler found for uri [/_plugins/_ppl] and method [POST] ({'error': 'no handler found for uri [/_plugins/_ppl] and method [POST]'})
```

To resolve this issue, **install the OpenSearch SQL Plugin** on your cluster (required for PPL operations).

#### Enabling Calcite for PPL Operations

By default, Calcite is disabled. To enable it for PPL operations, use the following command:

```bash
curl -XPUT "http://localhost:9200/_cluster/settings" \
-H "Content-Type: application/json" \
-d'{
  "persistent": {
    "plugins.calcite.enabled": true
  }
}'
```

#### PPL Test Procedures for Version 3.2.0

For OpenSearch version 3.2.0, two test procedures are available depending on whether Calcite is enabled:

**When Calcite is enabled:**
```bash
osb execute-test --workload=big5 --test-procedure=ppl
```
This runs all 50 PPL operations including histogram queries.

**When Calcite is disabled:**
```bash
osb execute-test --workload=big5 --test-procedure=ppl-calcite-disabled
```
This runs 42 PPL operations, excluding the following queries that require Calcite support:
- `ppl-composite-date-histogram-daily`
- `ppl-date-histogram-hourly-agg`
- `ppl-date-histogram-minute-agg`
- `ppl-range-auto-date-histo-with-metrics`
- `ppl-range-auto-date-histo`
- `ppl-range-agg-1`
- `ppl-range-agg-2`
- `ppl-cardinality-agg-high-2`

### gRPC Operations Support

Limited gRPC support is provided for the big5 workload over an protobuf/gRPC transport. gRPC operations can be found in `operations/grpc.json` with new operations added as support is expanded for gRPC APIs in OpenSearch. All supported big5 operations can be run with the `big5/test_procedures/grpc/grpc-schedule.json` (`--test-procedure="grpc-big5"`). To benchmark with the gRPC transport ensure the `transport-grpc` plugin is installed on the cluster and enabled in settings. See the `transport-grpc` [README.md](https://github.com/opensearch-project/OpenSearch/tree/main/modules/transport-grpc#readme) for guidance on enabling and using this transport. Note that the gRPC transport starts on a seperate endpoint from the default REST API, specify this endpoint with `--grpc-target-hosts=<host:port>`. 

### gRPC Operations Support

This workload includes limited gRPC/protobuf support for big5 operations. that provide an alternative query interface to OpenSearch. Find supported gRPC operations in `operations/grpc.json`.

- **grpc-index-append**: Bulk ingestion of big5 index
- **grpc-match-all**: Match all query.
- **grpc-term**: Simple term query on `log.file.path`.

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `bulk_size` (default: 5000): The number of documents in each bulk during indexing.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `corpus_size` (default: "100"): The size of the data corpus to use in GiB.  The currently provided sizes are 100, 880 and 1000.  Note that there are [certain considerations when using the 1000 GiB (~1 TiB) data corpus](#considerations-when-using-larger-data-corpora).
* `document_compressed_size_in_bytes`: If specifying an alternate data corpus, the compressed size of the corpus.
* `document_count`: If specifying an alternate data corpus, the number of documents in that corpus.
* `document_file`: If specifying an alternate data corpus, the file name of the corpus.
* `document_uncompressed_size_in_bytes`: If specifying an alternate data corpus, the uncompressed size of the corpus.
* `document_url`:  If specifying an alternate data corpus, the full path to the corpus file (optional).
* `distribution_version` (default 2.11.0):  Used to specify the target cluster's version so as to select the appropriate mappings for that version.  This is distinct from the command line option and should be in the 3-part dotted semantic version format.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `index_body` (default: "index.json"): The name of the file containing the index settings and mappings.
* `index_name` (default: "big5"): The name of the index the workload should create and use for its operations.
* `index_merge_policy` (default: "log_byte_size"): The merge policy for the underlying Lucene segments, either "log_byte_size" or "tiered".
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `number_of_replicas` (default: 1): The number of replicas to use for the index.
* `number_of_shards` (default: 1): The number of shards to use for the index.
* `query_cache_enabled` (default: false): Whether the query cache should be enabled.
* `requests_cache_enabled` (default: false): Whether the requests cache should be enabled.
* `search_clients`: (default: 1): Number of clients that issue search requests.
* `test_iterations` (default: 200): Number of test iterations per query that will have their latency and throughput measured.
* `target_throughput` (default: 2): Target throughput for each query operation in requests per second, use 0 or "" for no throughput throttling.
* `warmup_iterations` (default: 100): Number of warmup query iterations prior to actual measurements commencing.
* `index_translog_durability` (default: "async"): Controls the transaction log flush behavior. "request" flushes after every operation to avoid data loss, while "async" batches changes for efficiency.

NOTE: If disabling `target_throughput`, know that `target_throughput:""` is snynonymous with `target_throughput:0`.

### Data Document Structure

The document schema can be found in the `index.json` file.  An example document from the data corpus is provided below.

```json
{
    "message": "2023-04-30T21:48:56.160Z Apr 30 21:48:56 ip-66-221-134-40 journal: donkey glazer fly shark whip servant thornfalcon",
    "process": {
        "name": "journal"
    },
    "aws.cloudwatch": {
        "ingestion_time": "2023-04-30T21:48:56.160Z",
        "log_group": "/var/log/messages",
        "log_stream": "luckcrafter"
    },
    "tags": [
        "preserve_original_event"
    ],
    "meta": {
        "file": "2023-01-02/1682891301-gotext.ndjson.gz"
    },
    "cloud": {
        "region": "eu-central-1"
    },
    "@timestamp": "2023-01-02T22:02:34.000Z",
    "input": {
        "type": "aws-cloudwatch"
    },
    "metrics": {
        "tmin": 849,
        "size": 1981
    },
    "log.file.path": "/var/log/messages/luckcrafter",
    "event": {
        "id": "sunsetmark",
        "dataset": "generic",
        "ingested": "2023-07-20T03:36:30.223806Z"
    },
    "agent": {
        "id": "c315dc22-3ea6-44dc-8d56-fd02f675367b",
        "name": "fancydancer",
        "ephemeral_id": "c315dc22-3ea6-44dc-8d56-fd02f675367b",
        "type": "filebeat",
        "version": "8.8.0"
    }
}

```

### Sample Run Output

#### Default Test Procedure

```bash
osb execute-test --workload=big5
```

```
   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] You did not provide an explicit timeout in the client options. Assuming default of 10 seconds.
[INFO] Executing test with workload [big5], test_procedure [big5] and provision_config_instance ['external'] with version [2.5.0].

Running delete-index                                                           [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running default                                                                [100% done]
Running desc_sort_timestamp                                                    [100% done]
Running asc_sort_timestamp                                                     [100% done]
Running desc_sort_with_after_timestamp                                         [100% done]
Running asc_sort_with_after_timestamp                                          [100% done]
Running desc_sort_timestamp_can_match_shortcut                                 [100% done]
Running desc_sort_timestamp_no_can_match_shortcut                              [100% done]
Running asc_sort_timestamp_can_match_shortcut                                  [100% done]
Running asc_sort_timestamp_no_can_match_shortcut                               [100% done]
Running term                                                                   [100% done]
Running multi_terms-keyword                                                    [100% done]
Running keyword-terms                                                          [100% done]
Running keyword-terms-low-cardinality                                          [100% done]
Running composite-terms                                                        [100% done]
Running composite_terms-keyword                                                [100% done]
Running composite-date_histogram-daily                                         [100% done]
Running range                                                                  [100% done]
Running range-numeric                                                          [100% done]
Running keyword-in-range                                                       [100% done]
Running date_histogram_hourly_agg                                              [100% done]
Running date_histogram_minute_agg                                              [100% done]
Running scroll                                                                 [100% done]
Running query-string-on-message                                                [100% done]
Running query-string-on-message-filtered                                       [100% done]
Running query-string-on-message-filtered-sorted-num                            [100% done]
Running sort_keyword_can_match_shortcut                                        [100% done]
Running sort_keyword_no_can_match_shortcut                                     [100% done]
Running sort_numeric_desc                                                      [100% done]
Running sort_numeric_asc                                                       [100% done]
Running sort_numeric_desc_with_match                                           [100% done]
Running sort_numeric_asc_with_match                                            [100% done]
Running range_field_conjunction_big_range_big_term_query                       [100% done]
Running range_field_disjunction_big_range_small_term_query                     [100% done]
Running range_field_conjunction_small_range_small_term_query                   [100% done]
Running range_field_conjunction_small_range_big_term_query                     [100% done]
Running range-auto-date-histo                                                  [100% done]
Running range-auto-date-histo-with-metrics                                     [100% done]

------------------------------------------------------
```

#### PPL Test Procedure

```bash
osb execute-test --workload=big5 --test-procedure=ppl
```

```
[INFO] Executing test with workload [big5], test_procedure [ppl] and provision_config_instance ['external'] with version [3.0.0].

Running delete-index                                                           [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running index-append                                                           [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running ppl-default                                                            [100% done]
Running ppl-term                                                               [100% done]
Running ppl-range                                                              [100% done]
Running ppl-asc-sort-timestamp-can-match-shortcut                              [100% done]
Running ppl-asc-sort-timestamp-no-can-match-shortcut                           [100% done]
Running ppl-asc-sort-timestamp                                                 [100% done]
Running ppl-asc-sort-with-after-timestamp                                      [100% done]
Running ppl-composite-date-histogram-daily                                     [100% done]
Running ppl-composite-terms-keyword                                            [100% done]
Running ppl-composite-terms                                                    [100% done]
Running ppl-date-histogram-hourly-agg                                          [100% done]
Running ppl-date-histogram-minute-agg                                          [100% done]
Running ppl-desc-sort-timestamp-can-match-shortcut                             [100% done]
Running ppl-desc-sort-timestamp-no-can-match-shortcut                          [100% done]
Running ppl-desc-sort-timestamp                                                [100% done]
Running ppl-desc-sort-with-after-timestamp                                     [100% done]
Running ppl-keyword-in-range                                                   [100% done]
Running ppl-keyword-terms-low-cardinality                                      [100% done]
Running ppl-keyword-terms                                                      [100% done]
Running ppl-multi-terms-keyword                                                [100% done]
Running ppl-query-string-on-message                                            [100% done]
Running ppl-query-string-on-message-filtered                                   [100% done]
Running ppl-query-string-on-message-filtered-sorted-num                        [100% done]
Running ppl-range-auto-date-histo                                              [100% done]
Running ppl-range-auto-date-histo-with-metrics                                 [100% done]
Running ppl-range-field-conjunction-big-range-big-term-query                   [100% done]
Running ppl-range-field-conjunction-small-range-big-term-query                 [100% done]
Running ppl-range-field-conjunction-small-range-small-term-query               [100% done]
Running ppl-range-field-disjunction-big-range-small-term-query                 [100% done]
Running ppl-range-numeric                                                      [100% done]
Running ppl-range-with-asc-sort                                                [100% done]
Running ppl-range-with-desc-sort                                               [100% done]
Running ppl-scroll                                                             [100% done]
Running ppl-sort-keyword-can-match-shortcut                                    [100% done]
Running ppl-sort-keyword-no-can-match-shortcut                                 [100% done]
Running ppl-sort-numeric-asc                                                   [100% done]
Running ppl-sort-numeric-asc-with-match                                        [100% done]
Running ppl-sort-numeric-desc                                                  [100% done]
Running ppl-sort-numeric-desc-with-match                                       [100% done]
Running ppl-terms-significant-1                                                [100% done]
Running ppl-terms-significant-2                                                [100% done]

------------------------------------------------------
```

#### gRPC Test Procedure

```bash
opensearch-benchmark run \
    --pipeline=benchmark-only \
    --workload-path="big5" \
    --test-procedure="grpc-big5" \
    --target-host=http://localhost:9200 \
    --grpc-target-hosts=http://localhost:9400
```

```
[INFO] [Test Run ID]: 8a193e44-6a36-4dff-a516-5bc07c10d382
[INFO] Running test with workload [big5], test_procedure [grpc-big5] and cluster_config ['external'] with version [3.4.0-SNAPSHOT].

Running delete-index                                                           [100% done]
Running create-index                                                           [100% done]
Running check-cluster-health                                                   [100% done]
Running grpc-index-append                                                      [100% done]
Running refresh-after-index                                                    [100% done]
Running force-merge                                                            [100% done]
Running refresh-after-force-merge                                              [100% done]
Running wait-until-merges-finish                                               [100% done]
Running grpc-match-all                                                         [100% done]
Running grpc-term                                                              [100% done]
------------------------------------------------------
```

### Considerations when Using Larger Data Corpora

There are several points to note when carrying out performance runs using large data corpora:

  * Use an external data store to record metrics.  Using the in-memory store will likely result in the system running out of memory and becoming unresponsive, resulting in inaccurate performance numbers.
  * Use a load generation host with at least 8 cores and 32 GB memory or more.  It should have sufficient disk space to hold the corpus.
  * Ensure the target cluster has adequate storage and at least 3 data nodes.
  * Specify an appropriate shard count and number of replicas so that shards are evenly distributed and appropriately sized.
  * Running the workload requires an instance type with at least 8 cores and 32 GB memory.
  * If you are using an older version of OSB, install the `pbzip2` decompressor to speed up decompression of the corpus.
  * Set the client timeout to a sufficiently large value, since some queries take a long time to complete.
  * Allow sufficient time for the workload to run.  _Approximate_ times for the various steps involved, using an 8-core loadgen host:
    - 15 minutes to download the corpus
    - 4 hours to decompress the corpus (assuming `pbzip2` is available) and pre-process it
    - 4 hours to index the data
    - 30 minutes for the force-merge
    - 8 hours to run the set of included queries


### License

Please see the included LICENSE.txt file for details about the license applicable to this workload and its associated artifacts.


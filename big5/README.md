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


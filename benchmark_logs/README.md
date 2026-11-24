## Benchmark Logs OSB Workload

This workload runs the **_Big5_** queries and corpus against a **data stream** instead of a regular index. It is a copy of the [big5](../big5) workload: the corpus, mappings, settings and queries are the same, but documents are bulk-loaded into a data stream backed by a composable index template. This lets you measure big5 indexing and query performance on data streams and compare it with the index-based big5 workload.

### Differences from big5

* The workload defines `data-streams` and `composable-templates` instead of `indices`. The data stream is named `logs-benchmark-dev` by default; change it with the `data_stream_name` parameter.
* `index-template.json` is a composable index template. It matches `<data_stream_name>*`, uses `@timestamp` as the data stream timestamp field, and carries the big5 settings and mappings under `template`.
* Setup (`test_procedures/common/data-stream-setup.json`) deletes the data stream, its ISM policy and its template if they exist, recreates the policy, template and data stream, waits for cluster health, bulk-loads the corpus, and then waits for ISM to finish rolling over and migrating backing indices to UltraWarm (see below). There is no force-merge step: UltraWarm indices are read-only, and the migration handles segment merging itself. OpenSearch Benchmark sends `create` bulk actions automatically when the target is a data stream.
* An Index State Management (ISM) policy (`ism-policy.json`) is attached to the data stream's backing indices through an `ism_template`. When the write index reaches `ism_rollover_min_size` (default 2gb) and/or `ism_rollover_min_doc_count` documents, ISM rolls the data stream over, and the rolled-over backing index is migrated to UltraWarm with the `warm_migration` action. `warm_migration` is only available on Amazon OpenSearch Service domains with UltraWarm enabled; on other clusters, creating the policy fails.
* After ingestion, the `wait-for-ism-warm-migration` step (a custom runner in `workload.py`) polls the data stream until every rolled-over backing index has completed its ISM policy and the write index is below the rollover thresholds, so no further rollovers or migrations happen while queries run. It fails the step if ISM reports a failed action or if `ism_wait_timeout` expires.
* All queries, including the PPL queries, target the data stream name.
* The gRPC test procedure has been removed: the gRPC bulk path sends `index` actions, which data streams reject.
* Restoring from a snapshot (`use_snapshot`) is not supported.

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

Before using this workload, ensure you have the following installed:

- [OpenSearch](https://opensearch.org) (v2.11 or later)
- [OpenSearch Benchmark](https://opensearch.org/docs/latest/benchmark) (v1.2 or later)
- [OpenSearch SQL Plugin](https://opensearch.org/docs/latest/search-plugins/sql/index/) (required for PPL operations)

### Test Procedures

* `benchmark-logs` (default): Sets up the data stream, ingests the corpus and runs the big5 queries.
* `test`: Sets up the data stream, ingests the corpus and runs a reduced query schedule.
* `ppl`: Runs the PPL queries. Requires the SQL plugin.
* `ppl-test`: Runs a single PPL query to check SQL plugin availability.
* `ppl-calcite-disabled`: Runs the PPL queries that do not need Calcite.
* `intra-segment`: Runs queries for testing intra-segment search.

```bash
opensearch-benchmark execute-test --workload-path=benchmark_logs --pipeline=benchmark-only --target-hosts=localhost:9200
```

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
osb execute-test --workload-path=benchmark_logs --test-procedure=ppl
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
osb execute-test --workload-path=benchmark_logs --test-procedure=ppl
```
This runs all 50 PPL operations including histogram queries.

**When Calcite is disabled:**
```bash
osb execute-test --workload-path=benchmark_logs --test-procedure=ppl-calcite-disabled
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

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `bulk_size` (default: 5000): The number of documents in each bulk during indexing.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `corpus_size` (default: "100"): The size of the data corpus to use in GiB.  The currently provided sizes are 60, 100, 880 and 1000.  Note that there are [certain considerations when using the 1000 GiB (~1 TiB) data corpus](#considerations-when-using-larger-data-corpora).
* `data_stream_name` (default: "logs-benchmark-dev"): The name of the data stream the workload creates and queries. The index template is named `<data_stream_name>-template` and matches `<data_stream_name>*`.
* `document_compressed_size_in_bytes`: If specifying an alternate data corpus, the compressed size of the corpus.
* `document_count`: If specifying an alternate data corpus, the number of documents in that corpus.
* `document_file`: If specifying an alternate data corpus, the file name of the corpus.
* `document_uncompressed_size_in_bytes`: If specifying an alternate data corpus, the uncompressed size of the corpus.
* `document_url`:  If specifying an alternate data corpus, the full path to the corpus file (optional).
* `distribution_version` (default 2.11.0):  Used to specify the target cluster's version so as to select the appropriate mappings for that version.  This is distinct from the command line option and should be in the 3-part dotted semantic version format.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `ism_policy_id` (default: "<data_stream_name>-rollover-warm"): ID of the ISM policy the workload creates.
* `ism_rollover_min_doc_count` (default: unset): Number of documents in the write index that triggers a rollover. When set on its own, rollover is by document count only.
* `ism_rollover_min_size` (default: "2gb"): Primary-shard storage size of the write index that triggers a rollover. Used by default, or alongside `ism_rollover_min_doc_count` when both are set; the data stream then rolls over when either threshold is reached. ISM checks conditions every 5 to 8 minutes, so backing indices can grow well past these thresholds during fast ingestion.
* `ism_template_priority` (default: 100): Priority of the policy's `ism_template`. Raise it if another ISM policy matches the same indices.
* `ism_wait_poll_interval` (default: 30): Seconds between checks in the `wait-for-ism-warm-migration` step.
* `ism_wait_timeout` (default: 14400): Seconds the `wait-for-ism-warm-migration` step waits before failing.
* `ism_warm_migration_retry_count` (default: 5): Number of times ISM retries a failed `warm_migration`.
* `ism_warm_migration_retry_delay` (default: "1m"): Delay between `warm_migration` retries.
* `index_merge_policy` (default: "log_byte_size"): The merge policy for the underlying Lucene segments, either "log_byte_size" or "tiered".
* `index_sort` (default: false): If true, enables index-time ascending sort on the `@timestamp` field.
* `index_translog_durability` (default: "async"): Controls the transaction log flush behavior. "request" flushes after every operation to avoid data loss, while "async" batches changes for efficiency.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 1): The number of replicas for each backing index.
* `number_of_shards` (default: 1): The number of shards for each backing index.
* `query_cache_enabled` (default: false): Whether the query cache should be enabled.
* `requests_cache_enabled` (default: false): Whether the requests cache should be enabled.
* `search_clients`: (default: 1): Number of clients that issue search requests.
* `target_throughput` (default: 2): Target throughput for each query operation in requests per second, use 0 or "" for no throughput throttling.
* `template_priority` (default: 500): Priority of the composable index template. Raise it if another template on the cluster also matches the data stream name.
* `test_iterations` (default: 200): Number of test iterations per query that will have their latency and throughput measured.
* `use_zstd` (default: false): If true, downloads the zstd-compressed corpus instead of bz2.
* `warmup_iterations` (default: 100): Number of warmup query iterations prior to actual measurements commencing.

NOTE: If disabling `target_throughput`, know that `target_throughput:""` is synonymous with `target_throughput:0`.

### Data Document Structure

The document schema can be found in the `index-template.json` file (under the `template` key).  An example document from the data corpus is provided below.

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

### Setup Steps

Every test procedure starts with the following setup steps before running its queries:

```
delete-data-stream
delete-ism-policy
delete-composable-template
create-ism-policy
create-composable-template
create-data-stream
check-cluster-health
index-append
refresh-after-index
wait-for-ism-warm-migration
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
    - Additional time for ISM to roll over and migrate backing indices to UltraWarm
    - 8 hours to run the set of included queries


### License

Please see the included LICENSE.txt file for details about the license applicable to this workload and its associated artifacts.

## PMC workload

This workload contains data retrieved from [PMC](https://www.ncbi.nlm.nih.gov/pmc/tools/ftp/).

Note that we have filtered the data set so only a subset of the articles is included.

### Example Document

Note that the ``body`` content is actually much longer has been shortened here to increase readability.

```json
{
  "name": "3_Biotech_2015_Dec_13_5(6)_1007-1019",
  "journal": "3 Biotech",
  "date": "2015 Dec 13",
  "volume": "5(6)",
  "issue": "1007-1019",
  "accession": "PMC4624133",
  "timestamp": "2015-10-30 20:08:11",
  "pmid": "",
  "body": "\n==== Front\n3 Biotech3 Biotech3 Biotech2190-572X2190-5738Springer ..."
}
```

### Parameters

This workload allows to overwrite the following parameters with Benchmark 0.8.0+ using `--workload-params`:

* `bulk_size` (default: 500)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `conflicts` (default: "random"): Type of id conflicts to simulate. Valid values are: 'sequential' (A document id is replaced with a document id with a sequentially increasing id), 'random' (A document id is replaced with a document id with a random other id).
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. This requires to run the respective test_procedure. Combining ``conflicts=sequential`` and ``conflict-probability=0`` makes Benchmark generate index ids by itself, instead of relying on OpenSearch's `automatic id generation`.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict.
* `recency` (default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the [Benchmark docs](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md) for the full definition of this parameter. This requires to run the respective test_procedure.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 5)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `default_search_timeout` (default: -1)
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.

### License

All articles that are included are licensed as CC-BY (http://creativecommons.org/licenses/by/2.0/)

This data set is licensed under the same terms. Please refer to http://creativecommons.org/licenses/by/2.0/ for details.

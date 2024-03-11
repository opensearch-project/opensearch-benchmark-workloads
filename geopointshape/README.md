## Geopoint workload

This workload is based on [PlanetOSM](http://wiki.openstreetmap.org/wiki/Planet.osm) data. It contains the same data as the geopoint workload but indexes all points as geoshapes.

### Example Document

```json
{
  "location": "POINT (-0.1485188 51.5250666)"
}
```

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. This requires to run the respective test_procedure.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict.
* `recency` (default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the [Benchmark docs](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md) for the full definition of this parameter. This requires to run the respective test_procedure.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `query_cache_enabled` (default: false)
* `requests_cache_enabled` (default: false)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `target_throughput` (default: default values for each operation): Number of requests per second, `none` for no limit.
* `search_clients`: Number of clients that issues search requests.

### License

Same license as the original data from PlanetOSM: [Open Database License](http://wiki.openstreetmap.org/wiki/Open_Database_License).

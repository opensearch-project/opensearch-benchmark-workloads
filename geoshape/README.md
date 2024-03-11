## Geoshape workload

This workload is based on [PlanetOSM](http://wiki.openstreetmap.org/wiki/Planet.osm) data.

### Example Document

```json
{
  "shape": "LINESTRING(-1.8212114 52.5538901, -1.8205573 52.554324)"
}
```

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `linestring_bulk_size` (default: 100): The bulk request size for indexing linestrings.
* `multilinestring_bulk_size` (default: 100): The bulk request size for indexing multilinestrings.
* `polygon_bulk_size` (default: 100): The bulk request size for indexing polygons.
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
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

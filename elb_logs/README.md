## ELB logs workload

This workload is based on [Application Load Balancer access logs](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html).
Each document is one access log entry, with the raw `request` field additionally broken out into
`http_method`, `request_url`, `url_host`, `url_path`, `url_query` and `http_version`.

### Example document

```json
{
  "@timestamp": "2026-10-14T00:00:00.123456Z",
  "type": "https",
  "elb": "app/my-loadbalancer/50dc6c495c0c9188",
  "client_ip": "192.168.131.39",
  "client_port": 2817,
  "target_ip": "10.0.0.1",
  "target_port": 80,
  "request_processing_time": 0.000,
  "target_processing_time": 0.001,
  "response_processing_time": 0.000,
  "elb_status_code": 200,
  "target_status_code": 200,
  "received_bytes": 34,
  "sent_bytes": 366,
  "request": "GET https://www.example.com:443/index.html HTTP/1.1",
  "http_method": "GET",
  "request_url": "https://www.example.com:443/index.html",
  "url_host": "www.example.com",
  "url_path": "/index.html",
  "url_query": "",
  "http_version": "HTTP/1.1",
  "user_agent": "curl/7.46.0",
  "ssl_cipher": "ECDHE-RSA-AES128-GCM-SHA256",
  "ssl_protocol": "TLSv1.2",
  "target_group_arn": "arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/my-targets/73e2d6bc24d8a067",
  "trace_id": "Root=1-58337281-1d84f3d73c47ec4e58577259",
  "domain_name": "www.example.com",
  "chosen_cert_arn": "arn:aws:acm:us-east-2:123456789012:certificate/3775be48-f3d7-4b0a-9d1a-example",
  "matched_rule_priority": 0,
  "request_creation_time": "2026-10-14T00:00:00.000000Z",
  "actions_executed": "forward",
  "redirect_url": "",
  "error_reason": "",
  "target_ip_port_list": "10.0.0.1:80",
  "target_status_code_list": "200",
  "classification": "",
  "classification_reason": "",
  "conn_trace_id": "TID_e4a2b3c4d5e6f708",
  "lb_node_ip": "10.0.1.15"
}
```

### Test procedures

* `elb_logs` (default): indexes the corpus, then runs the PPL query suite.
* `elb_logs-test`: same, but one warmup iteration and one iteration per query, for validating the workload end to end.
* `append-no-conflicts-index-only`: indexing only, no queries.

### Index maintenance operations

Besides `index-append`, the workload defines these operations for use in custom schedules.
The bundled test procedures already refresh and force-merge after indexing (via
`common_operations/workload_setup.json`), so they are not referenced there.

* `refresh-index`: refreshes the index.
* `force-merge-index`: force-merges down to `max_num_segments` (default: 1) with a `request_timeout` (default: 7200s).
* `wait-until-merges-finish-index`: polls index stats until no merges are in flight.
* `flush-index`: raw `POST /<index>/_flush`.

### Queries

The PPL queries live in `operations/default.json` and are named after their source IDs
(`t1-*` for the observability/ELB-analysis set, `t2-*` for the engine stress set). Per-query
scheduling can be overridden with `<query_name_with_underscores>_warmup_iterations`,
`_iterations`, `_target_throughput` and `_clients`, e.g.
`--workload-params=t1_01_status_504_iterations:10`.

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `index_name` (default: "elb_logs"): Name of the index to create and index into.
* `index_body` (default: "index.json"): Index definition file to use.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `query_cache_enabled` (default: false)
* `requests_cache_enabled` (default: false)
* `index_translog_durability` (default: "async")
* `parquet_enabled_index` (default: true): Whether to create the index with the composite (parquet primary, lucene secondary) data format.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `warmup_time_period` (default: 120): Warmup time period in seconds for the bulk indexing operation.
* `request_timeout` (default: 60): Request timeout for the force-merge operation.
* `max_num_segments`: Number of segments to force-merge down to. Not set by default.
* `use_snapshot` (default: false): Restore the index from a snapshot instead of indexing the corpus.
* `warmup_iterations` (default: 100): Warmup iterations for each query.
* `test_iterations` (default: 100): Iterations for each query.
* `target_throughput` (default: 2): Number of requests per second per query, `none` for no limit.
* `search_clients` (default: 1): Number of clients that issue query requests.
* `legacy_syntax` (default: "false"): Value of the transient `plugins.ppl.syntax.legacy.preferred` cluster setting.

### License

TODO: fill in the license of the corpus before contributing this workload upstream.

# TPC-H SF=100 OpenSearch Benchmark Workload

> **OSB cannot set JVM flags — this is the first thing you must do manually.**
>
> OSB applies cluster settings but cannot set JVM flags on an externally-provisioned cluster. The
> `mustang-settings` step inside each procedure covers half the required configuration. Without the
> JVM half the coordinator deadlocks: pinned virtual threads starve every carrier,
> `-Djdk.virtualThreadScheduler.parallelism` is too low, and
> `-Dio.netty.allocator.numDirectArenas=0` (the upstream default) is rejected at boot. q4 hangs,
> and because the sweep does not restart between queries, every query after it times out. That is
> how a 3/22 result was produced before the mitigation; with the correct JVM flags, 10/22.
>
> See [Required JVM flags](#required-jvm-flags) before you run anything.

This workload runs the 22 TPC-H queries at scale factor 100 against the OpenSearch analytics
engine (PPL -> Calcite -> DataFusion MPP path). It is the shareable, reproducible form of the
bespoke sweep script at `sandbox/dev-tools/tpch/per_query_stress.py` (in the OpenSearch
analytics-engine repository).

**This workload is opinionated toward the Mustang analytics stack.** Indices default to
composite/parquet format and the test procedures configure the cluster for the MPP path. A stock
OpenSearch cluster will fail the join-heavy queries. A vendor-neutral variant is out of scope.

## Corpus

The corpus is **not hosted** — same position as `clickbench`, whose corpus was withdrawn pending
a data-license review.

| table | rows | shard default | measured store |
|---|---|---|---|
| lineitem | 600,037,902 | 32 | ~65 GB |
| orders | 150,000,000 | 16 | 11.4 GB |
| partsupp | 80,000,000 | 16 | 6.8 GB |
| part | 20,000,000 | 8 | 2.3 GB |
| customer | 15,000,000 | 8 | 1.9 GB |
| supplier | 1,000,000 | 8 | 149 MB |
| nation | 25 | 1 | 11 KB |
| region | 5 | 1 | 8 KB |
| **total** | **866,037,932** | **90 primaries, 0 replicas** | **~88 GB** |

### Generating the corpus

Run `generate_corpus.py` on a node inside the VPC. The script writes the full uncompressed export
(~200 GB), gzips it, then deletes the raw file — so allow ~200 GB free for generation plus the gz
output. OSB decompresses the gz again in the data directory, so the node running OSB needs a
further ~200 GB of working space.

```bash
python generate_corpus.py --sf 100 --out-dir /tmp/tpch_sf_100_gen
```

OSB resolves local corpora (no `base-url`) from `~/.benchmark/benchmarks/data/tpch_sf_100/`. If
the files are anywhere else, OSB raises `DataError: Cannot download data because no base URL is
provided.` Move the 8 `.gz` files there after generation:

```bash
mkdir -p ~/.benchmark/benchmarks/data/tpch_sf_100
mv /tmp/tpch_sf_100_gen/*.gz ~/.benchmark/benchmarks/data/tpch_sf_100/
```

The script calls DuckDB's `dbgen(sf=100)`, exports each table as gzipped NDJSON, and prints the
`document-count`, `compressed-bytes`, and `uncompressed-bytes` values to paste into `workload.json`.

**Note on the `sf` column:** the generator defensively projects `EXCLUDE (sf)` when DuckDB's
`dbgen` appends that spurious extra column. This was not present in DuckDB 1.5.3 when the workload
was validated; the script detects the column rather than assuming it is always there.

## Reference cluster

The sf=100 sweeps ran on 9 nodes of `m8g.2xlarge` (8 vCPU, 30.75 GiB RAM, aarch64 / Graviton4).

| role | count | instance | heap |
|---|---|---|---|
| coordinator + cluster_manager | 1 | `m8g.2xlarge` | `-Xmx8g` |
| data | 8 | `m8g.2xlarge` | `-Xmx16g` |

> **Resilience caveat.** Combining coordinator and cluster_manager on one node means a wedged
> coordinator takes cluster-state publication with it: the cluster goes *unavailable* rather than
> degraded, with no failover target. When the coordinator wedged during the q4 deadlock it dropped
> out of the cluster entirely. 9 nodes is the accepted trade for a benchmark cluster; this caveat
> is here so you know what you are accepting.

### Memory model

The native memory budget is **derived**, not configured: `0.80 x (MemTotal - heap)`, split by
`CacheSettings` (71% DataFusion operator pool, 5% Arrow query, 5% Arrow flight, remainder caches
/ ingest / parquet). Heap and the DataFusion pool trade off strictly — raising heap shrinks the
DataFusion pool.

| data-node heap | native budget | DataFusion pool | shuffle on-heap | measured PASS |
|---|---|---|---|---|
| 12g | 15.0 GiB | ~10.7 GiB | 9.6 GiB | 11/22 but 1.91x slower |
| **16g (recommended)** | **11.8 GiB** | **~8.4 GiB** | **12.8 GiB** | **10/22** |
| 24g | 5.4 GiB | ~3.8 GiB | 19.2 GiB | 4/22 |

16g is recommended: 12g completes one more query but runs 1.91x slower over the seven queries
passing at both settings (305.3 s vs 159.7 s, driven by q3 at 25.5 -> 167.5 s). **Raising heap
is actively harmful** — at 24g even the join-free q6 (0.3 s at 16g) fails on the DataFusion pool
breaker.

## Required cluster configuration

### `opensearch.yml` beyond stock

Add the following to every node's `opensearch.yml`. Settings not listed here are left at their
OpenSearch defaults.

```yaml
cluster.pluggable.dataformat.enabled: true
cluster.pluggable.dataformat: composite
analytics.planner.prefer_metadata_driver: false
opensearch.experimental.feature.transport.stream.enabled: true
opensearch.experimental.feature.pluggable.dataformat.enabled: true
arrow.flight.host:         ["<own private IP>"]
arrow.flight.bind_host:    ["<own private IP>"]
arrow.flight.publish_host: ["<own private IP>"]
analytics.mpp.shuffle.spill.enabled: true
analytics.mpp.shuffle.spill.directory: <data path>/spill
datafusion.spill_directory: <data path>/spill
```

**`arrow.flight.*` does not inherit `network.host`.** If left unset, every node advertises
`grpc+tcp://127.0.0.1:9400`, so the coordinator dispatches fragments to its own Flight server
(which holds no shards) and queries fail in milliseconds with `no such index` while no worker
logs the request.

**`analytics.mpp.shuffle.spill.enabled: true`** — the sf=100 pass/fail numbers in this document
were all measured with spill enabled, which differs from the shipped default (false). Do not
compare these numbers against sf=10 results measured without spill.

### Required JVM flags

Add the following to `jvm.options` on every node. The three `netty` flags are mandatory:
`ServerConfig.Netty4Configs.init` throws at boot if they are absent, and it also rejects
`numDirectArenas=0` — which is upstream's default in `SystemJvmOptions`, so it must be
overridden explicitly.

```
-Dio.netty.noUnsafe=false                  # MANDATORY
-Dio.netty.tryUnsafe=true                  # MANDATORY
-Dio.netty.tryReflectionSetAccessible=true # MANDATORY
-Dio.netty.allocator.numDirectArenas=8     # coordinator (use 1 on data nodes)
-Djdk.virtualThreadScheduler.parallelism=64
-Djdk.virtualThreadScheduler.maxPoolSize=512
--add-modules=jdk.incubator.vector
--enable-native-access=ALL-UNNAMED
-Djava.library.path=<install>/native
-Dorg.apache.lucene.store.MMapDirectory.sharedArenaMaxPermits=1
-da:org.apache.calcite...
```

### Swap

**A 32 GiB swapfile at `swappiness=10` is required on every node.** With zero swap an
over-budget node refault-storms for hours — the kernel always "makes progress" evicting clean
mmap pages, so the OOM-killer never fires and there is no `hs_err` or `.hprof` to read. Swap lets
the process fail cleanly.

```bash
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo sysctl vm.swappiness=10
```

## How to run

Commands below use the `run` subcommand, validated against OSB 2.2.0. The subcommand name changed
across versions (`execute-test` was used in older releases). On OSB 2.2.0, `execute-test` prints
`[INFO] Did you mean 'run'?` and exits 0 — a scripted sweep on the old name would report success
having run nothing. Verify with `opensearch-benchmark --help`.

The `mustang-settings` task is the first step in both procedures. It applies four transient
cluster settings. Transient settings are lost on a full cluster restart, so the procedures apply
them at the start of every run — this also means a restart between runs is safe.

### Query-only (the normal case for iteration)

```bash
opensearch-benchmark run \
  --workload-path=<repo>/tpch_sf_100 \
  --test-procedure=tpch_sf_100-query-only \
  --target-hosts=<coordinator>:9200 \
  --pipeline=benchmark-only
```

This procedure applies `mustang-settings` then runs the 22 queries against an already-loaded
cluster. Re-indexing 866 M rows per iteration is impractical, so this is how the sf=100 sweeps
are actually run.

### Full ingest and query

> **`--test-mode` cannot be used with this procedure.** OSB rewrites `source-file` to
> `<name>-1k.<ext>` in test mode, and no `-1k` files exist. Use `tpch_sf_100-query-only`
> for test-mode runs against an already-loaded cluster.

```bash
opensearch-benchmark run \
  --workload-path=<repo>/tpch_sf_100 \
  --test-procedure=tpch_sf_100 \
  --target-hosts=<coordinator>:9200 \
  --pipeline=benchmark-only \
  --offline
```

This procedure runs 32 tasks: applies `mustang-settings`, waits for cluster green, deletes and
recreates all eight indices, bulk-loads the corpus (8 clients), refreshes, **force-merges all
90 primaries** (required for parquet segment commit — allow several hours for 88 GB across
90 shards), refreshes again, waits for merges to finish, issues `POST /_flush?force=true`
(parquet segments commit on `_flush`, not `_refresh`; without it queries return zero rows), and
runs the 22 queries.

`--offline` prevents OSB from phoning home during the run. Corpus resolution depends on file
placement (see [Generating the corpus](#generating-the-corpus)), not on this flag.

## Parameters

The following parameters can be passed via `--workload-params`.

| parameter | default | description |
|---|---|---|
| `parquet_enabled_index` | `true` | Enable composite/parquet index format. |
| `lineitem_shards` | 32 | Primary shards for the lineitem index. |
| `orders_shards` | 16 | Primary shards for the orders index. |
| `partsupp_shards` | 16 | Primary shards for the partsupp index. |
| `part_shards` | 8 | Primary shards for the part index. |
| `customer_shards` | 8 | Primary shards for the customer index. |
| `supplier_shards` | 8 | Primary shards for the supplier index. |
| `nation_shards` | 1 | Primary shards for the nation index. |
| `region_shards` | 1 | Primary shards for the region index. |
| `number_of_replicas` | 0 | Replicas per primary. |
| `bulk_size` | 5000 | Documents per bulk request during ingest. |
| `warmup_iterations` | 1 | Default warmup iterations per query. |
| `test_iterations` | 3 | Default test iterations per query. |
| `search_clients` | 1 | Concurrent clients per query. |
| `arrow_query_pool_max` | 2147483648 | Arrow query allocator ceiling (bytes), applied as `native.allocator.pool.query.max`. Raised because the derived default (~522 MB on the coordinator) aborts the gather before it completes. |
| `mpp_enabled` | `true` | Enable MPP distributed execution. Set to `false` to run the coordinator-centric baseline — this is the MPP-on/MPP-off switch the comparison depends on. |
| `prefer_metadata_driver` | `false` | Use the metadata-driver planner path. Leave `false` for the DataFusion-only path measured in this document. |
| `rebalance_enable` | `none` | Shard-rebalancing policy during the run. `none` pins shards in place during ingest and queries. |
| `index_translog_durability` | `async` | Translog durability for all indices during ingest. |
| `ingest_percentage` | 100 | Percentage of each corpus file to ingest (use a smaller value for partial test runs). |

The default ingest procedure also accepts the standard `common_operations/workload_setup.json`
parameters, notably `bulk_indexing_clients` (default 8) and `cluster_health`.

Every query also supports per-query overrides in the clickbench style, for example:
`q01_pricing_summary_iterations`, `q01_pricing_summary_warmup_iterations`,
`q01_pricing_summary_clients`. The pattern is `q<NN>_<snake_case_name>_<param>`.

## Expected results

On the reference cluster (9 × `m8g.2xlarge`, data nodes at `-Xmx16g`, spill enabled), the sweep
passes roughly 10 of 22 queries. The failures are predominantly
`CircuitBreakingException [analytics_backend_datafusion]` — the DataFusion pool runs out — not
scheduler bugs.

The 10/22 count is a **floor**: the sweep shares one cluster with no restart between queries, so
cross-query memory pressure depresses the tail. The same queries run on fresh clusters pass at a
higher rate.

Reference answers for correctness verification live at
`sandbox/dev-tools/tpch/tpch_duckdb_ref_sf100.json` in the OpenSearch analytics-engine
repository. Known-good anchors: q1's first row is `A / F / count_order=148047881`; q4's first
row is `1-URGENT / 1051801`.

## Provenance

All paths below are in the **OpenSearch analytics-engine repository**, not in
`opensearch-benchmark-workloads`.

- Index mappings: `sandbox/qa/analytics-engine-rest/src/test/resources/datasets/tpch/mapping_<table>.json`
  (`mappings.properties`). The `mappings.properties` fields were taken verbatim from those files;
  the workload adds `"dynamic": "strict"` and replaces `number_of_shards` with the workload
  parameter. Re-sync the field list from there if the engine's schema changes.
- PPL queries: `sandbox/qa/analytics-engine-rest/src/test/resources/datasets/tpch/ppl/q<N>.ppl`.
  The operations in `operations/default.json` are taken verbatim from those files.

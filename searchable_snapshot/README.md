# Searchable Snapshot Workload

Workload for measuring performance for Searchable Snapshot feature. This workload uses the same corpora as the NYC taxis workload. See [../nyc_taxis/README.md](../nyc_taxis/README.md) for more details on how to generate the dataset and for example records.

In contrast with the NYC taxis workload which running query on index with local storage, this workload runs query on index backed by a remote snapshot.

The remote snapshot stores in Amazon S3, an Amazon S3 bucket for storing the snapshot and an AWS account user credential that has permission to access the bucket is required for the workload,
to learn more in configuring Amazon S3 bucket as a snapshot repository, see the [OpenSearch docs](https://opensearch.org/docs/latest/opensearch/snapshots/snapshot-restore#amazon-s3).

## Parameters

#### The workload allows to overwrite the following parameters using `--workload-params`:

Same parameters which exist in NYC taxis workload:
* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `conflicts` (default: "random"): Type of id conflicts to simulate. Valid values are: 'sequential' (A document id is replaced with a document id with a sequentially increasing id), 'random' (A document id is replaced with a document id with a random other id).
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. Only used by the `update` test_procedure. Combining ``conflicts=sequential`` and ``conflict-probability=0`` makes Benchmark generate index ids by itself, instead of relying on OpenSearch's `automatic id generation`.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict. Only used by the `update` test_procedure.
* `recency` (default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the [Benchmark docs](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md) for the full definition of this parameter. Only used by the `update` test_procedure.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `target_throughput` (default: default values for each operation): Number of requests per second, `none` for no limit.
* `search_clients`: Number of clients that issues search requests.

Additional parameters in contrast to NYC taxis workload:
* `snapshot_repository_name` (default: "test-repository"): Name of the snapshot repository.
* `snapshot_name` (default: "test-snapshot"): Name of the snapshot. 
  It's recommended to assign a different value for different test executions, because there is no operation defined by opensearch-benchmark to delete a snapshot, and new snapshot won't be created if a snapshot with the same name exists in the repository.
* `s3_bucket_name` (default: "opensearch-snapshot"): Name of the Amazon S3 bucket that stores the snapshot.
* `s3_bucket_region` (default: "us-east-1"): The AWS Region where the Amazon S3 bucket exists.

#### The workload requires to provide parameters for `repository-s3` plugin using `--plugin-params`:
See the [Benchmark docs](https://github.com/opensearch-project/opensearch-benchmark/blob/main/osbenchmark/resources/provision_configs/main/plugins/v1/repository_s3/README.md
) for detail.

Example:
```
{
  "s3_client_name": "default",
  "s3_access_key": "your AWS access key",
  "s3_secret_key": "your AWS secret key"
}
 ```
Save it as `params.json` and provide it to Benchmark with `--opensearch-plugins="repository-s3" --plugin-params="/path/to/params.json"`.

#### The workload requires to provide parameters for the "provision_config_instance" using `--provision-config-instance-params`:

A "provision_config_instance" is a specific configuration of OpenSearch. The parameter is used for setting feature flag in jvm options to enable experimental feature (for OpenSearch 2.4), and set the node role `search`.

Note that built-in instances can be seen from the [Benchmark repository](https://github.com/opensearch-project/opensearch-benchmark/tree/main/osbenchmark/resources/provision_configs/main/provision_config_instances/v1), and the parameter usage can be seen [here](https://github.com/opensearch-project/opensearch-benchmark/blob/main/osbenchmark/resources/provision_configs/main/provision_config_instances/v1/vanilla/README.md) in the same repository.

Example:
```
{
  "additional_cluster_settings": {
    "node.roles": "ingest, remote_cluster_client, data, cluster_manager, search"
  },
  "additional_java_settings": [
    "-Dopensearch.experimental.feature.searchable_snapshot.enabled=true"
  ]
}
```
Save it as `params.json` and provide it to Benchmark with `--provision-config-instance-params="/path/to/params.json"`.

### License

According to the [Open Data Law](https://opendata.cityofnewyork.us/open-data-law/) this data is available as public domain.
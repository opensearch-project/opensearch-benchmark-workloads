# Test Procedures

## searchable_snapshot 

A test procedure for measuring performance for the Searchable Snapshots feature. It runs the same search queries as the default test procedure `append-no-conflicts`.

In contrast with `append-no-conflicts` which runs queries on an index stored on the cluster itself, this test procedure runs queries on index backed by a remote snapshot.

The test procedure will create a remote snapshot that is stored in Amazon S3, so an Amazon S3 bucket for storing the snapshot and credentials for an AWS account that has permission to access the bucket are required to run the test procedure. To learn more about configuring Amazon S3 as a snapshot repository, see the [OpenSearch docs](https://opensearch.org/docs/latest/opensearch/snapshots/snapshot-restore#amazon-s3).

The Searchable Snapshots feature is supported by OpenSearch since version 2.4.0, see the [OpenSearch docs](https://opensearch.org/docs/2.4/opensearch/snapshots/searchable_snapshot) to learn more.

### Parameters

#### The test procedure allows the following parameters to be specified using `--workload-params`:

In addition to those mentioned in [README](README.md) of NYC taxis workload:
* `snapshot_repository_name` (default: "test-repository"): Name of the snapshot repository.
* `snapshot_name` (default: "test-snapshot"): Name of the snapshot. 
  It is recommended to assign a different value for different test executions, because there is no operation defined by opensearch-benchmark to delete a snapshot, and a new snapshot will not be created if a previous snapshot with the same name exists in the repository.
* `s3_bucket_name`: Name of the Amazon S3 bucket that stores the snapshot. The S3 bucket needs to be prepared manually.
* `s3_bucket_region`: The AWS Region where the Amazon S3 bucket exists. For example, "us-east-1".

#### The test procedure requires parameters to be provided for the `repository-s3` plugin using `--plugin-params`:
See the [Benchmark docs](https://github.com/opensearch-project/opensearch-benchmark/blob/main/osbenchmark/resources/provision_configs/main/plugins/v1/repository_s3/README.md
) for details.

Example:
```
{
  "s3_client_name": "default",
  "s3_access_key": "your AWS access key",
  "s3_secret_key": "your AWS secret key"
}
 ```
Save it as `params.json` and provide it to Benchmark with `--opensearch-plugins="repository-s3" --plugin-params="/path/to/params.json"`.

#### The test procedure requires parameters to be provided for the "provision_config_instance" using `--provision-config-instance-params`:

A "provision_config_instance" is a specific configuration of OpenSearch. The parameter is used for setting a feature flag in JVM options to enable an experimental feature (for OpenSearch 2.4), and assigning `search` role to the node.

Note that use of built-in instances can be seen at [Benchmark repository](https://github.com/opensearch-project/opensearch-benchmark/tree/main/osbenchmark/resources/provision_configs/main/provision_config_instances/v1), and the parameter usage can be seen [here](https://github.com/opensearch-project/opensearch-benchmark/blob/main/osbenchmark/resources/provision_configs/main/provision_config_instances/v1/vanilla/README.md) in the same repository.

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

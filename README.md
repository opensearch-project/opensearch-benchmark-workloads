OpenSearch Benchmark Workloads
------------

This repository contains the default workload specifications for the OpenSearch benchmarking tool [OpenSearch Benchmark](https://github.com/opensearch-project/OpenSearch-Benchmark).

You should not need to use this repository directly, except if you want to look under the hood or create your own workloads.

How to Contribute
-----------------

If you want to contribute a workload, please ensure that it works against the main version of OpenSearch (i.e. submit PRs against the `main` branch). We can then check whether it's feasible to backport the track to earlier OpenSearch/Elasticsearch versions.

After making changes to a workload, it's recommended for developers to run a simple test with that workload in `test-mode` to determine if there are any breaking changes. 
 
See all details in the [contributor guidelines](https://github.com/opensearch-project/opensearch-benchmark/blob/main/CONTRIBUTING.md).

**Following are the steps to consider when contributing.**
### Create a README.md

- The purpose of the workload. When creating a description for the workload, consider its specific use and how the that use case differs from others in the repository.
- An example document from the dataset that helps users understand the data’s structure.
- The workload parameters that can be used to customize the workload.
- A list of default test procedures included in the workload as well as other test procedures that the workload can run.
- An output sample produced by the workload after a test is run.
- A copy of the open-source license that gives the user and OpenSearch Benchmark permission to use the dataset.

For an example workload README file, go to the [http_logs](https://github.com/opensearch-project/opensearch-benchmark-workloads/blob/main/http_logs/README.md).

### Verify the workload’s structure

The workload must include the following files:
- `workload.json`
- `index.json`
- `files.txt`
- `test_procedures/default.json`
- `operations/default.json`

Both default.json file names can be customized to have a descriptive name. The workload can include an optional workload.py file to add more dynamic functionality. For more information about a file’s contents, go to [Anatomy of a workload](https://opensearch.org/docs/latest/benchmark/user-guide/understanding-workloads/anatomy-of-a-workload/).

### Testing the workload

- All tests run to explore and produce an example from the workload must target an OpenSearch cluster.
- The workload must pass all integration tests. Follow these steps to ensure that the workload passes the integration tests:
  1. Add the workload to your forked copy of the [workloads repository](https://github.com/opensearch-project/opensearch-benchmark-workloads/). Make sure that you’ve forked both the opensearch-benchmark-workloads repository and the OpenSearch Benchmark repository.
  2. In your forked OpenSearch Benchmark repository, update the `benchmark-os-it.ini` and `benchmark-in-memory.ini` files in the `/osbenchmark/it/resources` directory to point to the forked workloads repository containing your workload.
  3. After you’ve modified the `.ini` files, commit your changes to a branch for testing.
  4. Run your integration tests using GitHub actions by selecting the branch for which you committed your changes. Verify that the tests have run as expected.
  5. If your integration tests run as expected, go to your forked workloads repository and merge your workload changes into branches 1 and 2. This allows for your workload to appear in both major versions of OpenSearch Benchmark.

### Create a PR

After testing the workload, create a pull request (PR) from your fork to the opensearch-project [workloads repository](https://github.com/opensearch-project/opensearch-benchmark-workloads/). Add a sample output and summary result to the PR description. The OpenSearch Benchmark maintainers will review the PR.

Once the PR is approved, you must share the data corpora of your dataset. The OpenSearch Benchmark team can then add the dataset to a shared S3 bucket. If your data corpora is stored in an S3 bucket, you can use [AWS DataSync](https://docs.aws.amazon.com/datasync/latest/userguide/create-s3-location.html) to share the data corpora. Otherwise, you must inform the maintainers of where the data corpora resides.

For more details, see this [guide](https://opensearch.org/docs/latest/benchmark/user-guide/contributing-workloads/)

Backporting changes
-------------------

With each pull request, maintainers of this repository will be responsible for determining if a change can be backported.
Backporting a change involves cherry-picking a commit onto the branches which correspond to earlier versions of OpenSearch/Elasticsearch.
This ensures that workloads work for the latest `main` version of OpenSearch as well as older versions. 

Changes should be `git cherry-pick`ed from `main` to the most recent version of OpenSearch and backward from there. 
Example:
```
main → OpenSearch 2 → OpenSearch 1 → Elasticsearch 7 → ... 
```
In the case of a merge conflict for a backported change a new pull request should be raised which merges the change.

 
License
-------
 
There is no single license for this repository. Licenses are chosen per workload. They are typically licensed under the same terms as the source data. See the README files of each workload for more details.

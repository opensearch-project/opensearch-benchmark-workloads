OpenSearch-Benchmark-Workloads
------------------------------

This repository contains the default track specifications for the OpenSearch benchmarking tool [Benchmark](https://opensearch.org/).

Workloads are used to describe benchmarks in Benchmark.

You should not need to use this repository directly, except if you want to look under the hood or create your own workloads. We have created a [tutorial on how to create your own workloads](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md).

Versioning Scheme
-----------------

Refer to the official [Benchmark docs](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md) for more details.

How to Contribute
-----------------

If you want to contribute a track, please ensure that it works against the master version of OpenSearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier OpenSearch versions.

See all details in the [contributor guidelines](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/CONTRIBUTING.md).

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

If you are a contributor with direct commit access to this repository then please backport your changes. This ensures that tracks do not work only for the latest `main` version of OpenSearch but also for older versions. Apply backports with cherr-picks. Below you can find a walkthrough:

Assume we've pushed commit `a7e0937` to master and want to backport it. This is a change to the `noaa` track. Let's check what branches are available for backporting:

```
daniel@io:tracks/default ‹master›$ git branch -r
  origin/1
  origin/2
  origin/5
  origin/HEAD -> origin/master
  origin/master
```

We'll go backwards starting from branch `5`, then branch `2` and finally branch `1`. After applying a change, we will test whether the track works as is for an older version of OpenSearch.

```
git checkout 5
git cherry-pick a7e0937

# test the change now with an OpenSearch 5.x distribution
osbenchmark execute_test --workload=noaa --distribution-version=5.4.3 --test-mode

# push the change
git push origin 5
```

This particular track uses features that are only available in OpenSearch 5 and later so we will stop here but the process continues until we've reached the earliest branch.

Sometimes it is necessary to remove individual operations from a track that are not supported by earlier versions. This graceful fallback is a compromise to allow to run a subset of the track on older versions of OpenSearch too. If this is necessary then it's best to do these changes in a separate commit. Also, don't forget to cherry-pick this separate commit too to even earlier versions if necessary.


License
-------

There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.
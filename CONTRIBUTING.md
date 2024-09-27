# Contributor Guidelines

This repository contains the default workload specifications for the OpenSearch benchmarking tool [OpenSearch Benchmark](https://github.com/opensearch-project/OpenSearch-Benchmark). This is a general guide on best practices for contributing to this repository.

### Contents
- [Contributing a change to existing workload(s)](#contributing-a-change-to-existing-workloads)
- [Test changes](#test-changes)
    - [Testing changes locally](#testing-changes-locally)
    - [Testing changes with integration tests](#testing-changes-with-integration-tests)
- [Contributing a workload](#contributing-a-workload)
- [Publish changes in a pull-request](#publish-changes-in-a-pull-request)
- [Reviewing pull-requests](#reviewing-pull-requests)
     - [Backporting](#backporting)
     - [Important note on backporting reverted commits](#important-note-on-backporting-reverted-commits)

### Contributing a change to existing workload(s)

Before making a change, we recommend you fork the official workloads repository and make the change there.

You should also consider whether or not your change should be applied to one or more branches.
- If you know your change is only applicable to a specific branch, create the feature branch based off of that specific branch and make the changes there.
- If the change is applicable to several branches, create the feature branch based off of `main` branch and make the changes there.

### Test changes

Once you've made your change in your feature branch, we recommend testing it locally and with integration tests via your forked OpenSearch Benchmark repository.

#### Testing changes locally
It's recommended to test your change locally by performing the following:
1. Set up or use an existing OpenSearch cluster to test your changes against.
2. Based on the major version of the test cluster, cherry-pick the commit(s) with your change to the corresponding major version branch in your forked workloads repository. For example, if you're testing against an OpenSearch 2.X.X cluster, cherry-pick the changes from the feature branch to `2` branch.
3. Run the OpenSearch Benchmark command and against your cluster in `--test-mode`. Ensure it works successfully.
Other tips when running the command in test mode against your cluster:
- Ensure you are using the workloads repository that you committed your changes in. To enforce this, provide the path to your repository via the `--workloads-repository` parameter.
- Alternatively, you can force OSB to use a specific branch by specifying the distribution version of your OpenSearch cluster via the `--distribution-version` parameter. To build on the example from the previous step, to ensure you are using branch `2`, set `--distribution-version=2.0.0` in the OpenSearch Benchmark command.

#### Testing changes with integration tests

To ensure that there are no other breaking changes, we recommend testing with your forked OpenSearch Benchmark repository Github Actions.

**Prerequisites:**
In your forked OpenSearch Benchmark repository, create a separate branch that's based off of `main` and call it `workloads-test`. In this branch, update two files -- `benchmark-os-it.ini` and `benchmark-in-memory.ini` files in the `/osbenchmark/it/resources` directory -- to point to the forked workloads repository containing your workload, similar to the output below.
```
[workloads]
default.url = https://github.com/<YOUR GITHUB USERNAME>/opensearch-benchmark-workloads
```
Once these changes are in the remote branch of `workloads-test`, you can now run integration tests against your forked repository

**To run integration tests against your forked repository:**

1. Cherry-pick the commit(s) with your change to the branches that you expect your changes to be merged into.
2. Push these changes up to the remote branches of your forked workloads repository
3. Run your integration tests using GitHub actions by selecting the branch for which you committed your changes. See the screen shot below for reference. Verify that the tests have run as expected.


### Contributing a workload

For information on how to contribute a workload to the repository, please see [Sharing Custom Workloads](https://opensearch.org/docs/latest/benchmark/user-guide/contributing-workloads/) in the official documentation.

### Publish changes in a pull-request

Before publishing the pull-request containg your changes, please ensure you've addressed the following in the PR:

1. **Describe the changes**: In PR description, indicate what this change does and what it solves. If it fixes a bug, provide a sample output of what users experience before the fix and what they can expect after the fix is applied. If it's supporting a new feature, provide an output of what users can expect.
2. **Indicate where to backport**: It is the contributor's responsibility to indicate whether this change should be merged into a single branch or into several branches. The changes should always go into `main` branch but might only apply to specific branches.
    - If your change needs to go into different branches, determine if they will smoothly backport. To do this, perform a diff between `main` branch containing your cherry-picked commit and the other branches that need the change. If there are some conflicts or changes that you might introduce that are not related to your PR, take note of that in the PR description. Maintainers will use all this information to properly label the pull-request.
3. **Provide evidence that your changes were tested**: If you tested locally, paste a short sample output in the description or attach a file displaying the output. If you tested with your forked OSB repository's Github Actions, link that.
4. **Request additional members to review**: If your change is adding support for a new features in OpenSearch, please tag an individual who is a subject-matter expert (SME) and can review the change.

Create a pull request (PR) from your fork to the OpenSearch Benchmark [workloads repository](https://github.com/opensearch-project/opensearch-benchmark-workloads/)

### Reviewing pull-requests

Reviewers and maintainers should review pull-requests and ensure that the changes are well-defined and well-scoped.

Other tips:
1. Review changes. If the PR deals with adding support for specific features in OpenSearch, ensure a subject-matter expert (SME) reviews the change in addition to your review
2. Ensure that the change is tested
3. Label with backporting options based on the PR description before approving. The contributor should have included which branches, aside from `main` branch, the PR should be merged into.

#### Backporting
Ensure that there are no backport errors or conflicts. If there are If there are, be careful on backporting changes.

Changes should be `git cherry-pick`ed from `main` to the most recent version of OpenSearch and backward from there.
Example:
```
main → OpenSearch 3 → OpenSearch 2 → OpenSearch 1 → Elasticsearch 7 → Elasticsearch 6
```
In the case of a merge conflict for a backported change introduced by the contributor's PR, a separate pull request should be raised which merges the change directly into that target branch. **Ensure the only changes added to the branch are the ones from the PR the contributor raised.**

#### Important note on backporting reverted commits
Sometimes we'll need to revert a change. In those cases, we should revert the change across all branches. Do not revert the change only on main and backport that change across all branches. This can create other issues since each branch contains variations of workloads that slightly differ.









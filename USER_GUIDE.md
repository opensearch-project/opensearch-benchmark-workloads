# OpenSearch Benchmark Workloads User Guide

OpenSearch Benchmark (OSB) comes packaged with several workloads that are included in this repository. This guide provides a brief overview of the organization of this repository as well as how OSB uses these workloads.

### Contents
- [What do branches represent](#what-do-the-numbered-branches-represent)
- [How does OSB select which branch to use](#how-does-osb-select-which-branch-to-use)
- [Force OSB to use a Specific Branch](#force-osb-to-use-a-specific-branch)

### What do the numbered branches represent?

Don't worry, these numbers are not the same [numbers](https://lostpedia.fandom.com/wiki/The_Numbers) in the series [Lost](https://en.wikipedia.org/wiki/Lost_(2004_TV_series)). Each branch -- `main`, `6`, `7`, `1`, `2`, `3` -- is associated with a specific major version of OpenSearch or Elasticsearch and contains variations of each workload.

### How does OSB select which branch to use?
OSB has a mechanism to detect the major version of the target cluster.

Based off the major version it detects:
- OSB will select workloads from branches `1`, `2`, or `3` if the target cluster has an OpenSearch major version of 1.X.X, 2.X.X, or 3.X.X respectively.
- OSB will select workloads from branches `6` or `7` if the target cluster has an Elasticsearch major versions 6.X.X or 7.X.X respectively.

If OSB cannot determine the major version or if the major version does not exist as a branch in the repository, OSB will select workloads from `main` branch as a last resort.

### Force OSB to use a specific branch
Users can force OSB to use a specific branch by specifying `--distribution-version=X.X.X`. For example, if a user is testing a cluster with OpenSearch version 2.0.0 but wants to use the workloads associated with OpenSearch version 1.X.X, they can supply `--distribution-version=1.0.0` when invoking OSB.

However, it's not recommended to force testing workloads from a branch that is greater than the target cluster's major version (e.g. testing workloads from branch `2` on OpenSearch cluster 1.X.X). This can cause issues as earlier versions might not have operations that are included in later version workloads.

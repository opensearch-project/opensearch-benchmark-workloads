OpenSearch Benchmark Workloads
------------

This repository contains the default workload specifications for the OpenSearch benchmarking tool [OpenSearch Benchmark](https://github.com/opensearch-project/OpenSearch-Benchmark).

You should not need to use this repository directly, except if you want to look under the hood or create your own workloads.

How to Contribute
-----------------

If you want to contribute a workload, please ensure that it works against the main version of OpenSearch (i.e. submit PRs against the `main` branch). We can then check whether it's feasible to backport the track to earlier OpenSearch/Elasticsearch versions.

After making changes to a workload, it's recommended for developers to run a simple test with that workload in `test-mode` to determine if there are any breaking changes. 
 
See all details in the [contributor guidelines](https://github.com/opensearch-project/opensearch-benchmark/blob/main/CONTRIBUTING.md).

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

OpenSearch Benchmark Workloads
------------

This repository contains the default workload specifications for the OpenSearch benchmarking tool [OpenSearch Benchmark](https://github.com/opensearch-project/OpenSearch-Benchmark).

You should not need to use this repository directly, except if you want to look under the hood or create your own workloads.

How to Contribute
-----------------

If you want to contribute a workload, please ensure that it works against the main version of OpenSearch (i.e. submit PRs against the `main` branch). We can then check whether it's feasible to backport the track to earlier OpenSearch versions.
 
See all details in the [contributor guidelines](https://github.com/opensearch-project/opensearch-benchmark/blob/main/CONTRIBUTING.md).

Backporting changes
-------------------

With each pull request, maintainers of this repository will be responsible for determining if a change can be backported.
Backporting a change involves cherry-picking a commit onto the branches which correspond to earlier versions of OpenSearch/Elasticsearch.
This ensures that workloads work for the latest `main` version of OpenSearch and also for older versions. 

 
License
-------
 
There is no single license for this repository. Licenses are chosen per workload. They are typically licensed under the same terms as the source data. See the README files of each workload for more details.
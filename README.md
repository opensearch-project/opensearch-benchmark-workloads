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

If you are a contributor with direct commit access to this repository then please backport your changes. This ensures that workloads do not work only for the latest `main` version of OpenSearch but also for older versions. Apply backports with cherry-picks. Below you can find a walkthrough:

Assume we've pushed commit `a7e0937` to `main` and want to backport it. This is a change to the `noaa` workload. Let's check what branches are available for backporting:

```
daniel@io:workloads/default ‹main›$ git branch -r
  origin/1
  origin/7
  origin/6
  origin/HEAD -> origin/main
  origin/main
```


Since branches 7 and 6 correspond to ElasticSearch, we'll go backwards starting from branch `1` (OpenSearch 1), then branch `7` (Elasticsearch 7) and finally branch `6` (Elasticsearch 6). After applying a change, we will test whether the workload works as is for an older version of OpenSearch/Elasticsearch.

 
License
-------
 
There is no single license for this repository. Licenses are chosen per workload. They are typically licensed under the same terms as the source data. See the README files of each workload for more details.
[![Chat](https://img.shields.io/badge/chat-on%20forums-blue)](https://forum.opensearch.org/categories)
![PRs welcome!](https://img.shields.io/badge/PRs-welcome!-success)

OpenSearch Benchmark Workloads
------------------------------

This repository contains the default workload specifications for the OpenSearch benchmarking tool [OpenSearch Benchmark](https://github.com/opensearch-project/OpenSearch-Benchmark).

You should not need to use this repository directly, except if you want to look under the hood or create your own workloads.

How to contribute a change
--------------------------

See an area to make improvements or add support? Follow these major steps:

1. Fork this repository and make the change on a feature branch that's based off of `main`
2. After making changes to an existing workload, it's recommended for developers to run a simple test against the change in `test-mode` to determine if there are any breaking changes. It's also recommended to [test the changes against the OpenSearch Benchmark's integration tests](https://github.com/opensearch-project/opensearch-benchmark-workloads/blob/main/CONTRIBUTING.md#testing-changes-with-integration-tests).
3. Lastly, create a pull-request against `main` branch of this repository and ensure you have include how you tested it and which branches the change should be backported to.

For more details, see the [contributor guidelines](https://github.com/opensearch-project/opensearch-benchmark-workloads/blob/main/CONTRIBUTING.md).


How to Contribute a Workload
----------------------------

Please see the [sharing custom workloads guide](https://opensearch.org/docs/latest/benchmark/user-guide/contributing-workloads/) in the official documentation for OpenSearch Benchmark.


Getting help
------------

- Want to contribute to OpenSearch Benchmark? See [OpenSearch Benchmark's Developer Guide](https://github.com/opensearch-project/OpenSearch-Benchmark/blob/main/DEVELOPER_GUIDE.md) for more information.
- Want to contribute to OpenSearch Benchmark Workloads? Look at OpenSearch Benchmark workloads repository's [Contribution Guide](https://github.com/opensearch-project/opensearch-benchmark-workloads/blob/main/CONTRIBUTING.md) for more information.
- For any questions or answers, visit [our community forum](https://forum.opensearch.org/).
- File improvements or bug reports in our [Github repository](https://github.com/opensearch-project/opensearch-benchmark-workloads/issues).
License
-------

There is no single license for this repository. Licenses are chosen per workload. They are typically licensed under the same terms as the source data. See the README files of each workload for more details.

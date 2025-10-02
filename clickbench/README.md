# ClickBench OpenSearch Benchmark Workload

This workload is based on the ClickHouse ClickBench dataset, which contains web analytics data from Yandex.Metrica. It's designed to benchmark OpenSearch performance using PPL (Piped Processing Language) queries that cover typical web analytics operations including aggregations, filtering, sorting, and complex analytical queries.

## Dataset

The dataset contains approximately 100 million records of web analytics events with the following key fields:
- **EventTime/EventDate**: Timestamp fields for time-based queries
- **CounterID**: Website counter identifier
- **UserID**: Unique user identifier
- **URL/Referer**: Page URLs and referrer information
- **RegionID**: Geographic region data
- **SearchPhrase**: Search query terms
- **IsMobile**: Mobile device indicator
- **Age/Sex**: User demographic data

## Operations

The workload includes 43 PPL-based operations from the ClickBench benchmark suite:

1. **q01-count-all**: Count all records
2. **q02-count-adv-engine**: Count records with AdvEngineID
3. **q03-sum-count-avg**: Basic aggregations (sum, count, avg)
4. **q04-avg-userid**: Average UserID
5. **q05-distinct-userid**: Distinct count of UserID
6. **q06-distinct-searchphrase**: Distinct count of SearchPhrase
7. **q07-min-max-eventdate**: Min/max EventDate
8. **q08-group-by-adv-engine**: Group by AdvEngineID
9. **q09-region-users**: Region analysis with unique users
10. **q10-region-stats**: Complex region statistics
11. **q11-mobile-phone-model**: Mobile phone model analysis
12. **q12-mobile-phone-stats**: Mobile phone statistics
13. **q13-search-phrase-count**: Search phrase popularity
14. **q14-search-phrase-users**: Search phrase user analysis
15. **q15-search-engine-phrase**: Search engine and phrase analysis
16. **q16-user-activity**: User activity ranking
17. **q17-user-search-activity**: User search activity
18. **q18-user-search-limit**: Limited user search results
19. **q19-user-minute-search**: User activity by minute
20. **q20-specific-user**: Specific user lookup
21. **q21-google-urls**: Google URL filtering
22. **q22-google-search-phrases**: Google search phrase analysis
23. **q23-google-title-search**: Google title search analysis
24. **q24-google-urls-sorted**: Sorted Google URLs
25. **q25-search-phrases-by-time**: Search phrases sorted by time
26. **q26-search-phrases-sorted**: Alphabetically sorted search phrases
27. **q27-search-phrases-multi-sort**: Multi-field sorting
28. **q28-counter-url-length**: URL length analysis by counter
29. **q29-referer-analysis**: Referer domain analysis
30. **q30-resolution-width-sums**: Resolution width calculations
31. **q31-search-engine-client-stats**: Search engine client statistics
32. **q32-watch-client-stats**: Watch ID client statistics
33. **q33-watch-client-all**: All watch client statistics
34. **q34-url-popularity**: URL popularity ranking
35. **q35-url-with-constant**: URL analysis with constants
36. **q36-client-ip-variations**: Client IP variations
37. **q37-counter-62-urls**: Counter 62 URL analysis
38. **q38-counter-62-titles**: Counter 62 title analysis
39. **q39-counter-62-links**: Counter 62 link analysis
40. **q40-traffic-source-analysis**: Traffic source analysis
41. **q41-url-hash-date**: URL hash and date analysis
42. **q42-window-client-dimensions**: Window client dimensions
43. **q43-hourly-pageviews**: Hourly pageview analysis

## Parameters

This workload supports the following parameters:

* `bulk_indexing_clients` (default: 8): Number of clients for bulk indexing
* `bulk_size` (default: 5000): Documents per bulk request
* `cluster_health` (default: "green"): Required cluster health
* `index_name` (default: "clickbench"): Index name
* `number_of_replicas` (default: 1): Number of replicas
* `number_of_shards` (default: 1): Number of shards
* `query_cache_enabled` (default: false): Enable query cache
* `requests_cache_enabled` (default: false): Enable request cache
* `search_clients` (default: 1): Number of search clients
* `target_throughput` (default: 2): Target throughput per operation
* `warmup_iterations` (default: 100): Warmup iterations
* `test_iterations` (default: 100): Test iterations
* `ingest_percentage` (default: 100): Percentage of data to ingest

## Test Procedures
* `clickbench` (default): Indexes the ClickBench dataset and runs OpenSearch PPL queries to benchmark analytical use case performance
* `clickbench-test`: Lightweight test procedure for validating ClickBench workload setup and basic functionality
* `dsl-clickbench`: Indexes the whole document corpus using OpenSearch default settings and runs DSL (Domain-Specific Language) queries. The DSL queries were converted from PPL via OpenSearch's _plugins/_sql/_explain API.
* `dsl-clickbench-test`: Lightweight test procedure for validating ClickBench workload setup and basic functionality. Runs DSL (Domain-Specific Language) queries. The DSL queries were converted from PPL via OpenSearch's _plugins/_sql/_explain API.

## Usage

```bash
opensearch-benchmark execute-test --workload=clickbench --target-hosts=localhost:9200
```

## License & Attribution

### Dataset License
**Source**: ClickHouse hits dataset from Yandex.Metrica
**Original Source**: https://datasets.clickhouse.com/hits_compatible/hits.json.gz
**License**: CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0)
**Copyright**: © Yandex LLC

### Changes Made
- Converted ClickBench SQL queries to OpenSearch PPL format (based on https://github.com/opensearch-project/sql/pull/3860)
- Created OpenSearch Benchmark workload configuration (JSON mappings, operations, test procedures)
- Optimized index mappings for OpenSearch compatibility
- Added benchmark-specific parameters and configurations

### Usage Guidelines
**Non-Commercial Use**: Research, education, personal projects, open source development
**Attribution Required**: When publishing benchmark results, include:
- Credit to original ClickHouse/Yandex.Metrica dataset
- Link to this workload and original dataset source
- CC BY-NC-SA 4.0 license notice
- Description of modifications made

**Commercial Use**: Contact Yandex LLC for commercial licensing or use synthetic data with same schema

### Workload Configuration License
**License**: Apache 2.0
**Applies to**: JSON configurations, mappings, operations, and benchmark setup code created for this workload
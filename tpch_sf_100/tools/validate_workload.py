#!/usr/bin/env python3
"""Structural checks for the tpch_sf_100 workload.

These files are Jinja2 templates, so they are not valid JSON until rendered. We strip the
template expressions with a placeholder substitution and then parse, which catches real
syntax errors (trailing commas, unbalanced braces) without needing a Jinja environment.
"""
import json
import os
import re
import sys

TABLES = {
    "lineitem": {"shards": 32, "fields": 16, "docs": 600037902},
    "orders":   {"shards": 16, "fields": 9,  "docs": 150000000},
    "partsupp": {"shards": 16, "fields": 5,  "docs": 80000000},
    "part":     {"shards": 8,  "fields": 9,  "docs": 20000000},
    "customer": {"shards": 8,  "fields": 8,  "docs": 15000000},
    "supplier": {"shards": 8,  "fields": 7,  "docs": 1000000},
    "nation":   {"shards": 1,  "fields": 4,  "docs": 25},
    "region":   {"shards": 1,  "fields": 3,  "docs": 5},
}
TOTAL_DOCS = 866037932


def render(text):
    """Replace Jinja expressions/blocks with JSON-safe stand-ins so the result parses."""
    text = re.sub(r"\{%-?\s*if .*?%\}", "", text, flags=re.S)
    text = re.sub(r"\{%-?\s*endif\s*-?%\}", "", text)
    text = re.sub(r"\{\{[^}]*\|\s*tojson\s*\}\}", '"async"', text)
    text = re.sub(r"\{\{[^}]*\}\}", "1", text)
    return text


def load(path):
    with open(path) as fh:
        return json.loads(render(fh.read()))


def check_indices(workload_dir):
    failures = []
    for table, meta in TABLES.items():
        path = os.path.join(workload_dir, f"index-{table}.json")
        if not os.path.exists(path):
            failures.append(f"{table}: missing {path}")
            continue
        try:
            body = load(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{table}: not parseable after render: {exc}")
            continue
        props = body.get("mappings", {}).get("properties", {})
        if len(props) != meta["fields"]:
            failures.append(f"{table}: expected {meta['fields']} fields, found {len(props)}")
        if "sf" in props:
            failures.append(f"{table}: spurious dbgen 'sf' column present in mapping")
        if body.get("mappings", {}).get("dynamic") != "strict":
            failures.append(f"{table}: mappings.dynamic must be 'strict' so an unmapped column fails loudly")
        raw = open(path).read()
        if "index.number_of_shards" not in raw:
            failures.append(f"{table}: settings missing index.number_of_shards")
        if f"default({meta['shards']})" not in raw:
            failures.append(f"{table}: default shard count default({meta['shards']}) not present")
        raw_nows = re.sub(r"\s+", " ", raw)
        if "parquet_enabled_index | default(true)" not in raw_nows:
            failures.append(f"{table}: missing global constraint 'parquet_enabled_index | default(true)'")
        if "number_of_replicas | default(0)" not in raw_nows:
            failures.append(f"{table}: missing global constraint 'number_of_replicas | default(0)'")
    return failures


QUERY_OPS = [
    "q01-pricing-summary", "q02-minimum-cost-supplier", "q03-shipping-priority",
    "q04-order-priority-checking", "q05-local-supplier-volume", "q06-forecasting-revenue-change",
    "q07-volume-shipping", "q08-national-market-share", "q09-product-type-profit-measure",
    "q10-returned-item-reporting", "q11-important-stock-identification",
    "q12-shipping-modes-and-order-priority", "q13-customer-distribution",
    "q14-promotion-effect", "q15-top-supplier", "q16-parts-supplier-relationship",
    "q17-small-quantity-order-revenue", "q18-large-volume-customer",
    "q19-discounted-revenue", "q20-potential-part-promotion",
    "q21-suppliers-who-kept-orders-waiting", "q22-global-sales-opportunity",
]


def check_operations(workload_dir):
    failures = []
    path = os.path.join(workload_dir, "operations", "default.json")
    if not os.path.exists(path):
        return [f"operations: missing {path}"]
    try:
        ops = json.loads("[" + render(open(path).read()) + "]")
    except json.JSONDecodeError as exc:
        return [f"operations: not parseable after render: {exc}"]
    by_name = {o.get("name"): o for o in ops}
    for required in ("index-append", "flush-all"):
        if required not in by_name:
            failures.append(f"operations: missing required op '{required}'")
    flush = by_name.get("flush-all", {})
    if "force=true" not in flush.get("path", ""):
        failures.append("operations: flush-all must call _flush?force=true (parquet commits on flush, not refresh)")
    for name in QUERY_OPS:
        op = by_name.get(name)
        if op is None:
            failures.append(f"operations: missing query op '{name}'")
            continue
        if op.get("operation-type") != "raw-request":
            failures.append(f"{name}: operation-type must be raw-request")
        if op.get("method") != "POST":
            failures.append(f"{name}: method must be POST")
        if op.get("path") != "/_plugins/_ppl":
            failures.append(f"{name}: path must be /_plugins/_ppl")
        query = (op.get("body") or {}).get("query")
        if not query:
            failures.append(f"{name}: body.query is empty")
        elif not query.startswith("source ="):
            failures.append(f"{name}: body.query must start with 'source =' (got {query[:30]!r})")
    extra = set(by_name) - set(QUERY_OPS) - {"index-append", "flush-all"}
    if extra:
        failures.append(f"operations: unexpected ops {sorted(extra)}")
    return failures


def check_procedures(workload_dir):
    failures = []
    proc = os.path.join(workload_dir, "test_procedures", "default.json")
    sched = os.path.join(workload_dir, "test_procedures", "ppl", "tpch-schedule.json")
    settings = os.path.join(workload_dir, "test_procedures", "ppl", "mustang-settings.json")
    for path in (proc, sched, settings):
        if not os.path.exists(path):
            failures.append(f"procedures: missing {path}")
    if failures:
        return failures
    proc_raw = open(proc).read()
    for name in ("tpch_sf_100", "tpch_sf_100-query-only"):
        if f'"name": "{name}"' not in proc_raw:
            failures.append(f"procedures: missing procedure '{name}'")
    if proc_raw.count('"default": true') != 1:
        failures.append("procedures: exactly one procedure must be marked default")
    if "workload_setup.json" not in proc_raw:
        failures.append("procedures: ingest procedure must collect common_operations/workload_setup.json")
    pos_setup = proc_raw.find("workload_setup.json")
    pos_flush = proc_raw.find("flush-all")
    pos_sched = proc_raw.find("tpch-schedule.json")
    if pos_setup == -1 or pos_flush == -1 or pos_sched == -1:
        failures.append(
            "procedures: default.json must contain workload_setup.json, flush-all, and tpch-schedule.json"
        )
    elif not (pos_setup < pos_flush < pos_sched):
        failures.append(
            "procedures: in default.json, flush-all must appear after workload_setup.json collect"
            " and before tpch-schedule.json collect (checked by string index)"
        )
    sched_raw = open(sched).read()
    for name in QUERY_OPS:
        if name not in sched_raw:
            failures.append(f"schedule: query op '{name}' not scheduled")
    settings_raw = open(settings).read()
    if "persistent" in settings_raw:
        failures.append("settings: must use transient only, never persistent")
    for key in ("analytics.mpp.enabled", "analytics.planner.prefer_metadata_driver",
                "native.allocator.pool.query.max", "cluster.routing.rebalance.enable"):
        if key not in settings_raw:
            failures.append(f"settings: missing '{key}'")
    return failures


def check_corpus(workload_dir):
    """Assert workload.json document-counts and target-indices match TABLES, and files.txt lists
    exactly the expected source files.  These numbers are load-bearing at runtime: OSB raises a
    hard DataError on any mismatch after building an offset table over the full decompressed corpus.
    """
    failures = []
    workload_path = os.path.join(workload_dir, "workload.json")
    files_path = os.path.join(workload_dir, "files.txt")
    for path in (workload_path, files_path):
        if not os.path.exists(path):
            failures.append(f"corpus: missing {path}")
    if failures:
        return failures

    try:
        wl = load(workload_path)
    except json.JSONDecodeError as exc:
        return [f"corpus: workload.json not parseable after render: {exc}"]

    corpora = wl.get("corpora", [])
    if len(corpora) != 1:
        failures.append(f"corpus: expected exactly 1 corpus, found {len(corpora)}")
        return failures
    documents = corpora[0].get("documents", [])

    # Index by target-index for easy lookup
    by_index = {d["target-index"]: d for d in documents if "target-index" in d}

    total = 0
    expected_source_files = set()
    for table, meta in TABLES.items():
        expected_source_file = f"{table}.json.gz"
        expected_source_files.add(expected_source_file)
        doc = by_index.get(table)
        if doc is None:
            failures.append(f"corpus: no corpus entry for target-index '{table}'")
            continue
        if doc.get("source-file") != expected_source_file:
            failures.append(
                f"corpus: {table} source-file is {doc.get('source-file')!r}, expected {expected_source_file!r}"
            )
        count = doc.get("document-count")
        if count != meta["docs"]:
            failures.append(
                f"corpus: {table} document-count is {count}, expected {meta['docs']}"
            )
        else:
            total += count

    if not failures:
        if total != TOTAL_DOCS:
            failures.append(f"corpus: document-count sum is {total}, expected {TOTAL_DOCS}")

    # Check files.txt lists exactly the 8 expected source files
    with open(files_path) as fh:
        listed_files = {line.strip() for line in fh if line.strip()}
    if listed_files != expected_source_files:
        extra = listed_files - expected_source_files
        missing = expected_source_files - listed_files
        if extra:
            failures.append(f"corpus: files.txt has unexpected entries: {sorted(extra)}")
        if missing:
            failures.append(f"corpus: files.txt missing entries: {sorted(missing)}")

    return failures


CHECKS = {"indices": check_indices, "operations": check_operations, "procedures": check_procedures, "corpus": check_corpus}


def main():
    workload_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    selected = sys.argv[2:] or list(CHECKS)
    failures = []
    for name in selected:
        failures += CHECKS[name](workload_dir)
    for f in failures:
        print(f"FAIL {f}")
    print(f"{len(failures)} failure(s) over checks: {', '.join(selected)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

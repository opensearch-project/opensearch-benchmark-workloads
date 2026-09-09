#!/usr/bin/env python3
"""Generate the TPC-H corpus for the tpch_sf_100 OSB workload.

The corpus is not hosted (same position as the clickbench workload), so it is produced
locally. DuckDB does both the data generation and the JSON encoding; Python only drives it
and gzips the output.

Run this on a node INSIDE the VPC when generating sf=100 -- the NDJSON is on the order of
200 GB and should not cross the WAN.

    python3 generate_corpus.py --sf 100 --out-dir /data/tpch-corpus

Requires: pip install duckdb
"""
import argparse
import gzip
import json
import os
import shutil
import sys

TABLES = ["lineitem", "orders", "partsupp", "part", "customer", "supplier", "nation", "region"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sf", type=float, default=100, help="TPC-H scale factor")
    ap.add_argument("--out-dir", required=True, help="directory to write <table>.json.gz files into")
    ap.add_argument("--db", default=None, help="path for the file-backed DuckDB database")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb not installed: pip install duckdb")

    os.makedirs(args.out_dir, exist_ok=True)
    db = args.db or os.path.join(args.out_dir, "tpch.duckdb")
    con = duckdb.connect(db)
    con.execute("INSTALL tpch;")
    con.execute("LOAD tpch;")
    print(f"generating TPC-H sf={args.sf} into {db} (this is the slow part)")
    con.execute(f"CALL dbgen(sf={args.sf})")

    entries = []
    for table in TABLES:
        raw = os.path.join(args.out_dir, f"{table}.json")
        gz = raw + ".gz"
        # EXCLUDE (sf): DuckDB's dbgen appends a spurious `sf` column to every table
        # (lineitem gets 17 columns, not the spec's 16). It is not in the TPC-H mappings,
        # and the index mappings are `dynamic: strict`, so leaving it in fails the bulk load.
        cols = [c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()]
        projection = "* EXCLUDE (sf)" if "sf" in cols else "*"
        con.execute(f"COPY (SELECT {projection} FROM {table}) TO '{raw}' (FORMAT JSON)")

        count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        uncompressed = os.path.getsize(raw)
        tmp = gz + ".tmp"
        try:
            with open(raw, "rb") as src, gzip.open(tmp, "wb", compresslevel=6) as dst:
                shutil.copyfileobj(src, dst, length=16 * 1024 * 1024)
            os.remove(raw)
            os.rename(tmp, gz)
        except BaseException:
            # Clean up both the partial temp and the raw export so the next run starts clean.
            for leftover in (tmp, raw):
                try:
                    os.remove(leftover)
                except FileNotFoundError:
                    pass
            raise
        compressed = os.path.getsize(gz)
        print(f"  {table:9s} {count:>12,} rows  {uncompressed:>15,} B -> {compressed:>14,} B gz")
        entries.append({
            "source-file": f"{table}.json.gz",
            "target-index": table,
            "document-count": count,
            "compressed-bytes": compressed,
            "uncompressed-bytes": uncompressed,
        })

    print("\nPaste into workload.json corpora[0].documents:")
    print(json.dumps(entries, indent=2))


if __name__ == "__main__":
    main()

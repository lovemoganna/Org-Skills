#!/usr/bin/env python3
"""Blind multi-table data preflight: fixed public source commit, bytes, DuckDB QA.

No answer keys, downstream analysis SQL, or existing published analyses are read.
"""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

SOURCE_COMMIT = "b199b7a4dfd5d38f2c995d97816816bd03033d28"
SOURCE_REPO = "ryanariefe/RYStore-Retail-Dataset"
FILES = {
    "orders": ("orders.csv", "7697ca8bdc27f5d203b6ce3fd012b05a6f941ed7"),
    "order_items": ("order_items.csv", "267a9dfbb351eba886158ca802e902bdb4cecb88"),
    "products": ("products.csv", "49ffa5a0f8e4ef51e69dea81f1bf5d7df4f63851"),
    "promotions": ("promotions.csv", "b2e735b22458bf77384d6df099a9c03d0f242e4f"),
}


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def ingest(out):
    import duckdb
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dbpath = out / "blind.duckdb"
    if dbpath.exists():
        dbpath.unlink()
    entries = {}
    with duckdb.connect(str(dbpath)) as con:
        for table, (filename, expected_blob) in FILES.items():
            url = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{filename}"
            req = urllib.request.Request(url, headers={"User-Agent": "sql-blind-eval/1.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError("SOURCE_TOO_LARGE: " + filename)
            blob = git_blob_sha(data)
            if blob != expected_blob:
                raise ValueError(f"SOURCE_HASH_MISMATCH {filename} expected={expected_blob} got={blob}")
            path = out / filename
            path.write_bytes(data)
            # The table name is a fixed whitelist constant; only trusted bytes are imported.
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto(?, HEADER=true)", [str(path)])
            rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            columns = [{"name": c[0], "type": c[1]} for c in
                       con.execute(f"DESCRIBE SELECT * FROM {table}").fetchall()]
            entries[table] = {
                "source_url": url,
                "blob_sha1": blob,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "rows": rows,
                "columns": columns,
            }
        checks = {}
        checks["duplicate_orders"] = con.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders").fetchone()[0]
        checks["duplicate_items"] = con.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT order_item_id) FROM order_items").fetchone()[0]
        checks["unmatched_item_orders"] = con.execute(
            "SELECT COUNT(*) FROM order_items i LEFT JOIN orders o ON i.order_id=o.order_id "
            "WHERE o.order_id IS NULL").fetchone()[0]
        checks["unmatched_item_products"] = con.execute(
            "SELECT COUNT(*) FROM order_items i LEFT JOIN products p ON i.product_id=p.product_id "
            "WHERE p.product_id IS NULL").fetchone()[0]
        checks["order_status_distribution"] = [
            {"status": a, "rows": n} for a, n in con.execute(
                "SELECT order_status, COUNT(*) FROM orders GROUP BY 1 ORDER BY 1").fetchall()
        ]
        checks["nonzero_promotion_item_rows"] = con.execute(
            "SELECT COUNT(*) FROM order_items WHERE promotion_id IS NOT NULL").fetchone()[0]
        checks["unique_promotion_ids"] = con.execute(
            "SELECT COUNT(DISTINCT promotion_id) FROM promotions").fetchone()[0]
        # A one-to-many JOIN is observable; do not treat the joined row count as orders.
        checks["orders_after_items_join"] = con.execute(
            "SELECT COUNT(*) FROM orders o JOIN order_items i USING(order_id)").fetchone()[0]
    result = {
        "status": "SOURCE_VERIFIED",
        "dataset_type": "public fictional retailer; not real company transactions",
        "commit": SOURCE_COMMIT,
        "files": entries,
        "data_quality_observations": checks,
        "excluded_materials": ["README.md", "data_dictionary.csv", "published dashboards", "analysis queries", "expected results"],
        "data_version": "sha256 per file and fixed git blob SHA, no live source ambiguity",
    }
    (out / "source-receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "tables": {k: v["rows"] for k, v in entries.items()},
                      "checks": checks}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    try:
        ingest(sys.argv[1] if len(sys.argv)>1 else "blind-evidence")
    except Exception as exc:
        print("SOURCE_BLOCKED: " + str(exc), file=sys.stderr)
        raise

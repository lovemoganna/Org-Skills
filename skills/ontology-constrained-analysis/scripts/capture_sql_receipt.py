#!/usr/bin/env python3
"""Append a post-execution SQL Result receipt in the current DuckDB CLI run."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: capture_sql_receipt.py <query-id>")
    ident = sys.argv[1]
    allowed = {
        "ontology-instrument-status", "ontology-uid-integrity",
        "ontology-account-snapshot", "ontology-status-timestamps",
        "ontology-rate-temporality", "ontology-cross-rail", "ontology-usdt-driver",
    }
    if ident not in allowed:
        raise SystemExit("UNREGISTERED_QUERY_ID")
    f = Path(ident + ".csv")
    if not f.is_file():
        raise SystemExit(f"MISSING_SQL_RESULT:{ident}")
    with f.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    record = {
        "id": ident,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "rows": len(rows),
        "columns": list(rows[0]) if rows else [],
        "result_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        "data_source": "current DuckDB SQL Result exported from materialized table(s)",
    }
    with Path("ontology-query-receipts.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("SQL_RECEIPT", json.dumps(record, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()

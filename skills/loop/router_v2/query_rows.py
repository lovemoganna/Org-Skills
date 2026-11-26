"""Run one read-only SQLite query over a bounded, isolated table of host-provided rows."""
import json
import re
import sqlite3
import sys
import time


def query_rows(rows, sql):
    if not isinstance(rows, list) or not 0 < len(rows) <= 10_000:
        raise ValueError("expected 1..10000 input rows")
    if not isinstance(rows[0], dict):
        raise ValueError("expected named columns")
    columns = list(rows[0])
    if not 0 < len(columns) <= 64 or any(
        not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", key) for key in columns
    ):
        raise ValueError("invalid column names")
    if any(not isinstance(row, dict) or row.keys() != rows[0].keys() for row in rows):
        raise ValueError("inconsistent row shape")
    if not isinstance(sql, str) or len(sql.encode()) > 16_384:
        raise ValueError("invalid query size")
    connection = sqlite3.connect(":memory:")
    try:
        # No declared affinity: preserve the scalar types supplied by the host.
        fields = ", ".join(f'"{key}"' for key in columns)
        binds = ", ".join("?" for _ in columns)
        connection.execute(f"CREATE TABLE input_rows ({fields})")
        connection.executemany(f"INSERT INTO input_rows VALUES ({binds})",
                               ([r[k] for k in columns] for r in rows))
        connection.execute("PRAGMA query_only = ON")
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
        connection.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
        allowed_functions = {"abs", "avg", "coalesce", "count", "length", "lower",
                             "max", "min", "nullif", "round", "sum", "total", "upper"}
        def authorize(action, arg1, arg2, database, trigger):
            allowed = (action == sqlite3.SQLITE_SELECT
                       or (action == sqlite3.SQLITE_READ and arg1 == "input_rows")
                       or (action == sqlite3.SQLITE_FUNCTION and arg2 in allowed_functions))
            return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY
        connection.set_authorizer(authorize)
        deadline = time.monotonic() + 2
        connection.set_progress_handler(lambda: time.monotonic() >= deadline, 1000)
        cursor = connection.execute(sql)
        names = [field[0] for field in cursor.description]
        values = cursor.fetchmany(1001)
        if len(values) > 1000 or len(set(names)) != len(names):
            raise ValueError("result exceeds row limit or has duplicate column labels")
        return {"engine": f"SQLite {sqlite3.sqlite_version}", "input_count": len(rows),
                "columns": names, "rows": [dict(zip(names, row)) for row in values]}
    finally:
        connection.close()


if __name__ == "__main__":
    payload = sys.stdin.buffer.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("payload too large")
    print(json.dumps(query_rows(**json.loads(payload)), ensure_ascii=False, allow_nan=False))

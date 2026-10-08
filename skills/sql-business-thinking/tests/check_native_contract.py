"""Native read_xlsx contract regression: original SQL and independent mutation tests.
Synthetic mutations are negative tests, never business-data evidence.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx"
SHEETS = ("users", "fiat_transactions", "crypto_transactions", "exchange_rates")
READ = re.compile(r"\bFROM\s+read_xlsx\s*\(\s*'([^']+)'\s*,\s*sheet\s*=\s*'([^']+)'\s*,\s*header\s*=\s*(true|false)\s*\)", re.I)

def extract(stage):
    workflow = ("sql-business-thinking-native-duckdb-url-test.yml" if stage == "d02"
                else "sql-business-thinking-native-d03-quality.yml")
    raw = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    match = re.search(r"cat > " + stage + r"\.sql <<'SQL'\n([\s\S]*?)\n\s+SQL\b", raw)
    assert match, "SQL_BLOCK_NOT_FOUND:" + stage
    return "\n".join(line[10:] if line.startswith("          ") else line
                     for line in match.group(1).splitlines())

def validate(sql, stage):
    def require(value, failure):
        if not value:
            raise ValueError(failure)
    lines = [line.strip() for line in sql.splitlines()]
    for command in ("INSTALL httpfs;", "LOAD httpfs;", "INSTALL excel;", "LOAD excel;"):
        require(lines.count(command) == 1, "INIT_ONCE")
    reads = READ.findall(sql)
    require(len(reads) == sql.lower().count("read_xlsx(") == 4, "READ_COUNT")
    require(reads == [(SOURCE, sheet, "true") for sheet in SHEETS], "READ_SOURCE_CONTRACT")
    for sheet in SHEETS:
        table = sheet if stage == "d02" else sheet + "_raw"
        pattern = rf"\bCREATE\s+TEMP\s+TABLE\s+{table}\s+AS\s+SELECT\s+\*\s+FROM\s+read_xlsx\s*\("
        require(len(re.findall(pattern, sql, re.I)) == 1, "MATERIALIZATION")
    require(len(re.findall(r"\bCREATE\s+TEMP\s+TABLE\b", sql, re.I)) == 4, "TABLE_COUNT")
    require("CREATE OR REPLACE TEMP VIEW" not in sql.upper(), "REPEATED_SOURCE_SCAN")
    if stage == "d02":
        for table in SHEETS:
            require(bool(re.search(rf"(?m)^\.once\s+{table}\.csv\s*\nSELECT\s+\*\s+FROM\s+{table}\s*;", sql, re.I)), "EXPORT_NOT_MATERIALIZED")

def mutations(sql, stage):
    table = "users" if stage == "d02" else "users_raw"
    cases = {
        "alias": sql.replace(SOURCE, "workbook.xlsx", 1),
        "wrong_url": sql.replace("export?format=xlsx", "export?format=csv", 1),
        "banned_sheet": sql.replace("sheet = 'users'", "sheet = 'Executive_Dashboard'", 1),
        "duplicate_sheet": sql.replace("sheet = 'fiat_transactions'", "sheet = 'users'", 1),
        "header_changed": sql.replace("header = true", "header = false", 1),
        "fifth_read": sql + "\nSELECT * FROM read_xlsx('workbook.xlsx', sheet = 'users', header = true);",
        "duplicate_bootstrap": "INSTALL excel;\n" + sql,
        "missing_bootstrap": sql.replace("LOAD excel;", "", 1),
        "view_not_table": sql.replace(f"CREATE TEMP TABLE {table} AS", f"CREATE TEMP VIEW {table} AS", 1),
    }
    if stage == "d02":
        cases["second_raw_read"] = sql.replace(
            "FROM users;", "FROM read_xlsx('workbook.xlsx', sheet = 'users', header = true);", 1)
    return cases

def main():
    total = 0
    for stage in ("d02", "d03"):
        sql = extract(stage)
        validate(sql, stage)
        for name, changed in mutations(sql, stage).items():
            assert changed != sql, (stage, "MUTATION_NOT_APPLIED", name)
            try:
                validate(changed, stage)
            except ValueError:
                total += 1
            else:
                raise AssertionError((stage, "MUTATION_NOT_REJECTED", name))
        print(f"PASS: {stage} original contract + {len(mutations(sql, stage))} mutation rejections")
    assert total == sum(len(mutations(extract(stage), stage)) for stage in ("d02", "d03"))
    print(f"PASS: {total} independent negative tests; no business data accessed")

if __name__ == "__main__":
    main()

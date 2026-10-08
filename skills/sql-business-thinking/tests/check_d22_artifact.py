"""D22: verify published HTML against read-only D20 and D21 inputs."""
from pathlib import Path
from html import unescape
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "tests" / "verified-d20-report-spec.json"
PLAN_PATH = ROOT / "tests" / "verified-d21-visualization-plan.json"
HTML_PATH = ROOT / "artifacts" / "verified-d22-report.html"
SQL_PATH = ROOT / "tests" / "d10-fiat-direction-status.sql"


def git_blob_sha(raw: str) -> str:
    b = raw.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def verify(html: str, spec: dict, plan: dict, raw_spec: str, sql: str) -> None:
    meta = spec["meta"]
    assert spec["delivery_mode"] == plan["delivery_mode"] == "report"
    assert plan["source_spec_blob_sha"] == git_blob_sha(raw_spec), "STALE_D20"
    assert plan["source_result_run_id"] == meta["source_run_id"], "STALE_RUN"
    assert plan["source_data_revision"] == meta["data_revision"], "STALE_DATA"
    assert plan["renderer_contract"]["read_only_d20"]
    assert plan["renderer_contract"]["no_new_sql"]
    assert plan["renderer_contract"]["no_dashboard"]
    assert meta["gate_state"] == "PASS"
    assert html.lower().startswith("<!doctype html>")
    assert html.count("<table>") == 2, "CHANGED_PRESENTATION"
    assert html.count("<details>") == 2, "MISSING_AUDIT"
    assert "<script src=" not in html and "<link rel=\"stylesheet\"" not in html, "EXTERNAL_DEPENDENCY"
    assert "data-content-ref=\"dashboard" not in html and "DashboardSpec" not in html, "DASHBOARD_LEAK"

    up = {x["id"]: x for x in spec["answer_blocks"] + spec["findings"]}
    refs = [x["content_ref"] for x in plan["items"] if x["visibility"] in ("PRIMARY", "SECONDARY", "AUDIT")]
    assert len(set(refs)) == len(refs) == len(up), "WRONG_CONTENT_COUNT"
    for ref in refs:
        assert ref in up
        assert html.count('data-content-ref="' + ref + '"') == 1, "MISSING_OR_DUPLICATE_CONTENT"
        assert up[ref]["gate_state"] == "PASS"
        assert up[ref]["result_refs"] == [meta["result_ref"]]

    assert spec["answers"]["primary"] in html, "CHANGED_CONCLUSION"
    assert spec["findings"][0]["judgment"] in html, "CHANGED_FINDING"
    assert spec["answers"]["operational_action"] in html, "INVENTED_ACTION"
    assert meta["data_revision"] in html, "MISSING_SOURCE_REVISION"
    assert str(meta["source_run_id"]) in html, "MISSING_RUN"
    assert plan["source_spec_blob_sha"] in html, "MISSING_SPEC_BLOB"

    statuses = next(x for x in spec["answer_blocks"] if x["id"] == "report-status-breakdown")["rows"]
    denominators = next(x for x in spec["answer_blocks"] if x["id"] == "report-denominator-sensitivity")["rows"]
    assert sum(x["total"] for x in statuses) == 25
    assert sum(x["completed"] for x in statuses) == 21
    for item in denominators:
        for key in ("original", "alternate"):
            expected = f'{100*item[key]:.2f}%'
            assert expected in html, "CHANGED_RATIO_" + expected
    # Compare individual status counts with the two HTML table rows.
    table_match = re.findall(r'<table>.*?</table>', html, re.S)
    assert len(table_match) == 2
    status_table = table_match[1]
    lines = re.findall(r'<tr>.*?</tr>', status_table, re.S)[1:]
    assert len(lines) == 2
    for source, line in zip(statuses, lines):
        digits = [int(x) for x in re.findall(r'<td class="num">(\d+)</td>', line)]
        assert digits == [source["total"], source["completed"], source["ongoing"],
                          source["terminal_noncompleted"], source["unknown"]], "CHANGED_COUNTS"

    code = re.search(r'<pre id="sql-source"><code>(.*?)</code></pre>', html, re.S)
    assert code, "MISSING_SQL_AUDIT"
    recovered = unescape(code.group(1))
    assert recovered == sql, "CHANGED_SQL"
    sql_sha = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    assert sql_sha == meta["source_sql_sha256"] and sql_sha in html, "SQL_SHA_MISMATCH"


def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    raw_spec = SPEC_PATH.read_text(encoding="utf-8")
    spec = json.loads(raw_spec)
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    sql = SQL_PATH.read_text(encoding="utf-8")
    verify(html, spec, plan, raw_spec, sql)
    for label, tamper in (
        ("wrong ratio", html.replace("83.33%", "89.99%")),
        ("wrong count", html.replace('class="num">12</td>', 'class="num">20</td>')),
        ("missing content ref", html.replace('data-content-ref="report-decision"', 'data-content-ref="none"')),
        ("wrong SQL", html.replace("COUNT(*) AS total_order_records", "COUNT(uid) AS total_order_records")),
        ("dashboard leak", html.replace("</main>", '<div data-content-ref="dashboard">x</div></main>')),
    ):
        try:
            verify(tamper, spec, plan, raw_spec, sql)
        except AssertionError:
            pass
        else:
            raise AssertionError("failed to reject: " + label)
    print("PASS: D22 grounded HTML + five tamper regressions (report-only)")


if __name__ == "__main__":
    main()

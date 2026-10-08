"""D21 actual Report visualization plan regression; no new SQL or renderer."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "verified-d20-report-spec.json"
PLAN = ROOT / "tests" / "verified-d21-visualization-plan.json"
ALLOWED = {"PRIMARY", "SECONDARY", "AUDIT"}
CHARTS = {"text", "comparison_table", "count_table"}


def blob_sha(text):
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def validate(plan, spec, source_text):
    if spec.get("delivery_mode") != "report" or plan.get("delivery_mode") != "report":
        raise ValueError("MODE_LEAK")
    if plan.get("source_spec_blob_sha") != blob_sha(source_text):
        raise ValueError("STALE_D20_BLOB")
    meta = spec["meta"]
    if plan.get("source_result_run_id") != meta["source_run_id"]:
        raise ValueError("STALE_RUN")
    if plan.get("source_data_revision") != meta["data_revision"]:
        raise ValueError("STALE_DATA")
    if meta["gate_state"] != "PASS":
        raise ValueError("BLOCKED_SOURCE")
    if plan.get("source_result_ref") != meta["result_ref"]:
        raise ValueError("RESULT_REF_MISMATCH")
    if plan.get("layout_archetype") != "Evidence Report":
        raise ValueError("INVALID_REPORT_LAYOUT")
    flags = plan.get("renderer_contract", {})
    for flag in ("read_only_d20", "no_new_sql", "no_new_metrics",
                 "no_recompute", "no_dashboard", "not_an_artifact"):
        if flags.get(flag) is not True:
            raise ValueError("UNSAFE_RENDERER_CONTRACT")
    if "dashboard" in plan or "dashboard" in spec:
        raise ValueError("DASHBOARD_LEAK")
    content = spec["answer_blocks"] + spec["findings"]
    ids = [x["id"] for x in content]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_UPSTREAM_CONTENT")
    valid = {x["id"]: x for x in content}
    selected = set()
    for item in plan["items"]:
        ref = item.get("content_ref")
        if ref not in valid or ref in selected:
            raise ValueError("DANGLING_OR_DUPLICATE_REF")
        selected.add(ref)
        source = valid[ref]
        if source.get("gate_state") != "PASS" or source.get("result_refs") != [meta["result_ref"]]:
            raise ValueError("UNVERIFIED_CONTENT")
        if item.get("visibility") not in ALLOWED:
            raise ValueError("INVALID_VISIBILITY")
        if item.get("selected_chart") not in CHARTS:
            raise ValueError("INVALID_CHART_TYPE")
        for required in ("presentation_question", "data_shape", "unit_contract", "layout_role"):
            if not item.get(required):
                raise ValueError("MISSING_PLAN_FIELD")
        # A visualization plan can only reference data in upstream, not embed new findings.
        if any(key in item for key in ("rows", "values", "new_sql", "new_finding", "new_metric")):
            raise ValueError("D21_GENERATED_NEW_DATA")
    if selected != set(ids):
        raise ValueError("UNACCOUNTED_UPSTREAM_CONTENT")
    return True


def reject(plan, spec, raw, label):
    try:
        validate(plan, spec, raw)
    except ValueError:
        return
    raise AssertionError("should reject " + label)


def main():
    raw = SOURCE.read_text(encoding="utf-8")
    spec = json.loads(raw)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    validate(plan, spec, raw)
    assert len(plan["items"]) == 3
    assert {x["content_ref"] for x in plan["items"]} == {
        "report-status-breakdown", "report-denominator-sensitivity", "report-decision"}
    tests = [
        ("stale source blob", lambda x: x.update(source_spec_blob_sha="bad")),
        ("stale run", lambda x: x.update(source_result_run_id=1)),
        ("dashboard leak", lambda x: x.update(delivery_mode="dashboard")),
        ("ghost content", lambda x: x["items"][0].update(content_ref="invented")),
        ("duplicate reference", lambda x: x["items"][1].update(content_ref="report-decision")),
        ("made up result", lambda x: x["items"][0].update(rows=[{"amount": 9000}])),
        ("changed metric", lambda x: x["items"][0].update(new_metric="false")),
        ("missing units", lambda x: x["items"][1].update(unit_contract="")),
        ("invalid display layer", lambda x: x["items"][0].update(visibility="HERO-ALWAYS")),
        ("dashboard permission", lambda x: x["renderer_contract"].update(no_dashboard=False)),
    ]
    for label, change in tests:
        bad = copy.deepcopy(plan)
        change(bad)
        reject(bad, spec, raw, label)
    bad_spec = copy.deepcopy(spec)
    bad_spec["meta"]["gate_state"] = "BLOCKED"
    reject(plan, bad_spec, raw, "blocked upstream")
    print("PASS: D21 actual D20 content references, layout, units and read-only contract")
    print("PASS: D21 11 negative provenance, scope and fabrication cases")
    print("NOTE: no new SQL was run; D22 HTML rendering not executed")


if __name__ == "__main__":
    main()

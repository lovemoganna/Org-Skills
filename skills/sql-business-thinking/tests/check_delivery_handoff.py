"""D20/D21 handoff contract tests. All values here are synthetic fixtures."""
from copy import deepcopy


def check_handoff(mode, stages, spec, results, plan=None):
    """Reject missing upstream proof, unsupported content and dangling visual refs."""
    requires = {"report": ("D18",), "dashboard": ("D19",),
                "hybrid": ("D18", "D19")}
    if mode not in requires:
        raise ValueError("unknown delivery mode")
    for stage in requires[mode]:
        if stages.get(stage) != "通过":
            raise ValueError("upstream not approved: " + stage)
    if not isinstance(spec, dict) or spec.get("delivery_mode") != mode:
        raise ValueError("missing or wrong delivery spec")
    if mode == "hybrid":
        if set(("report_spec", "dashboard_spec")) - set(spec):
            raise ValueError("hybrid must contain two independent specs")
        parts = (("report", spec["report_spec"]),
                 ("dashboard", spec["dashboard_spec"]))
    else:
        parts = ((mode, spec),)
    allowed_ids = set()
    for kind, section in parts:
        if section.get("delivery_mode") != kind:
            raise ValueError("mixed delivery spec")
        if kind == "report":
            if "dashboard" in section:
                raise ValueError("dashboard field in report")
            items = section.get("answer_blocks", []) + section.get("findings", [])
            if not items and not section.get("limitations"):
                raise ValueError("empty report shell")
        else:
            if "findings" in section or "answer_blocks" in section:
                raise ValueError("report fields in dashboard")
            dash = section.get("dashboard", {})
            items = dash.get("core_items", []) + dash.get("drilldown_items", [])
        for item in items:
            ident = item.get("id")
            if not ident or ident in allowed_ids:
                raise ValueError("missing or duplicate content id")
            refs = item.get("result_refs")
            if not refs or item.get("gate_state") != "PASS":
                raise ValueError("content lacks verified evidence")
            if any(results.get(r) != "PASS" for r in refs):
                raise ValueError("missing or blocked result")
            allowed_ids.add(ident)
    if plan is not None:
        if not isinstance(plan, dict) or not isinstance(plan.get("items"), list):
            raise ValueError("invalid visualization plan")
        for item in plan["items"]:
            if item.get("content_ref") not in allowed_ids:
                raise ValueError("unverified or dangling content_ref")
            if item.get("visibility") not in {"PRIMARY", "SECONDARY", "AUDIT"}:
                raise ValueError("invalid display visibility")
    return True


def expect_rejected(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("must reject: " + label)


def main():
    # Fixtures are not findings from the user's workbook.
    report = {"delivery_mode": "report", "answer_blocks": [
        {"id": "a1", "result_refs": ["R1"], "gate_state": "PASS"}],
        "findings": []}
    dashboard = {"delivery_mode": "dashboard", "dashboard": {
        "core_items": [{"id": "m1", "result_refs": ["R2"], "gate_state": "PASS"}],
        "drilldown_items": [], "excluded_items": []}}
    hybrid = {"delivery_mode": "hybrid",
              "report_spec": deepcopy(report), "dashboard_spec": deepcopy(dashboard)}
    results = {"R1": "PASS", "R2": "PASS"}
    states = {"D18": "通过", "D19": "通过"}
    rpt_plan = {"items": [{"content_ref": "a1", "visibility": "PRIMARY",
                           "selected_chart": "table"}]}
    check_handoff("report", states, report, results, rpt_plan)
    check_handoff("dashboard", states, dashboard, results, {"items": [
        {"content_ref": "m1", "visibility": "PRIMARY"}]})
    check_handoff("hybrid", states, hybrid, results, {"items": [
        {"content_ref": "a1", "visibility": "PRIMARY"},
        {"content_ref": "m1", "visibility": "SECONDARY"}]})
    expect_rejected(lambda: check_handoff(
        "report", {"D18": "待执行"}, report, results), "missing D18")
    expect_rejected(lambda: check_handoff(
        "report", states, {"delivery_mode": "report", "answer_blocks": [],
                           "findings": []}, results), "empty shell")
    expect_rejected(lambda: check_handoff(
        "report", states, report, {"R1": "BLOCKED"}), "blocked result")
    expect_rejected(lambda: check_handoff(
        "report", states, report, results, {"items": [
            {"content_ref": "invented", "visibility": "PRIMARY"}]}),
            "invented visualization")
    expect_rejected(lambda: check_handoff(
        "report", states, {"**": True}, results), "wrong spec")
    expect_rejected(lambda: check_handoff(
        "dashboard", {"D19": "待检查"}, dashboard, results), "unapproved D19")
    assert report["answer_blocks"][0]["id"] == "a1"
    print("PASS: 9 synthetic D20/D21 handoff cases; no actual dataset findings verified")


if __name__ == "__main__":
    main()

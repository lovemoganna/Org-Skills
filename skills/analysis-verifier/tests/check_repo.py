#!/usr/bin/env python3
"""Controlled before/after test for S3→S4 claim-scope promotion; fixture only."""
import copy
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scope_gate", root / "scripts/scope_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

qa = {
    "verdict": "PARTIAL", "run_id": "fixture-one-session",
    "source_id": "fixture-authorized-four-sheet",
    "materialization_id": "fixture-one-read-each",
    "read_plan_sha256": "fixture-hash-not-source-bytes",
    "qa_receipt_ref": "fixture-qa",
    "checked_scopes": [{
        "grain": "uid-in-usd-completed-fiat",
        "population": "USD fiat completed",
        "time_window": "fixture-covered-period",
        "status_meaning": "completed flag, not settlement",
        "metrics": ["native_total", "top1_native_total", "trimmed_top1_share_pct", "same_top_user"]
    }]
}
finding = {
    "verdict": "VERIFIED", "run_id": qa["run_id"], "source_id": qa["source_id"],
    "materialization_id": qa["materialization_id"],
    "read_plan_sha256": qa["read_plan_sha256"],
    "packet_id": "Q002", "revision": 1, "verified_packet_id": "Q002", "verified_revision": 1,
    "result_receipt_ref": "fixture-q002-result",
    "verification_receipt_ref": "fixture-b-verdict",
    "scope": copy.deepcopy(qa["checked_scopes"][0])
}

cases = [
    ("within_partial_scope", {}, {}, True),
    ("foreign_currency", {}, {"scope": dict(finding["scope"], population="EUR fiat completed")}, False),
    ("status_as_settled", {}, {"scope": dict(finding["scope"], status_meaning="bank settled")}, False),
    ("different_run", {}, {"run_id": "new-run"}, False),
    ("different_time", {}, {"scope": dict(finding["scope"], time_window="real-time")}, False),
    ("unverified_metric", {}, {"scope": dict(finding["scope"], metrics=["exchange_liquidity"])}, False),
    ("missing_result", {}, {"result_receipt_ref": ""}, False),
    ("stale_feedback", {}, {"verified_revision": 2}, False),
    ("qa_blocked", {"verdict": "BLOCKED"}, {}, False),
    ("invalid_qa_metrics", {"checked_scopes": [dict(qa["checked_scopes"][0], metrics=[{}])]}, {}, False),
]

# Baseline rule from four-stage contract checks only status labels; it has no runtime provenance/scope comparison.
baseline = lambda q, f: q.get("verdict") in ("PASS", "PARTIAL") and f.get("verdict") == "VERIFIED"
base_ok = new_ok = 0
for name, change_qa, change_finding, expected in cases:
    q, f = copy.deepcopy(qa), copy.deepcopy(finding)
    q.update(change_qa)
    f.update(change_finding)
    old = baseline(q, f)
    new = gate.check_scope(q, f)["verdict"] == "PASS"
    base_ok += old == expected
    new_ok += new == expected
    assert new == expected, (name, gate.check_scope(q, f))
    print(f"{name}: baseline={old} patched={new} expected={expected}")

assert new_ok == len(cases) and base_ok < new_ok
owner = (root / "../business-owner/references/four-stage-review.md").read_text(encoding="utf-8")
analyst = (root / "../business-reasoning/SKILL.md").read_text(encoding="utf-8")
verifier = (root / "SKILL.md").read_text(encoding="utf-8")
for value, source in [
    ("scope_gate.py", verifier),
    ("scope_gate.py", owner),
    ("证据范围", analyst),
]:
    assert value in source, value
print(f"SCOPE_HANDOFF_AB_PASS baseline={base_ok}/{len(cases)} patched={new_ok}/{len(cases)}; synthetic controls only")

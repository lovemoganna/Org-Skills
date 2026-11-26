#!/usr/bin/env python3
"""Reconstruct a bounded 3-role handoff from the SAME native DuckDB CI run.

This is a deterministic workflow replay, not three independently running LLM agents.
The original XLSX bytes are not hashed; provenance is limited to the same run.
"""
import copy
import json
import os
from pathlib import Path
from scope_gate import check_scope

evidence = Path("dual-evidence")
def load(name):
    return json.loads((evidence / name).read_text(encoding="utf-8"))

quality = load("quality.json")
groups = load("concentration.json")
orders = load("q002-orders.json")[0]
metrics = load("q002-mechanism.json")[0]
feedback = load("q002-verification-feedback.json")
counts = load("source-counts.json")[0]
usd = next((g for g in groups if g["rail"] == "fiat" and g["asset"] == "USD"), None)
fiat = next((q for q in quality if q["rail"] == "fiat"), None)
assert usd and fiat and feedback["packet_id"] == "Q002" and feedback["revision"] == 1
assert feedback["verdict"] == "VERIFIED", "independent Q002 verification has not passed"
assert all(int(counts[f]) > 0 for f in ("users_rows", "fiat_rows", "crypto_rows", "exchange_rate_rows"))
assert all(int(fiat[x]) == 0 for x in ("invalid_amounts", "missing_assets", "missing_uids"))
assert int(orders["completed_usd_orders"]) == int(orders["distinct_order_ids"])
assert not int(orders["invalid_amounts"]) and not int(orders["null_uids"])
assert int(usd["completed_orders"]) == int(metrics["completed_usd_orders"])
assert abs(float(usd["native_total"]) - float(metrics["native_total"])) < 0.000001
assert all(k in metrics and metrics[k] is not None for k in
           ("native_total", "trimmed_top1_share_pct", "same_top_user"))

run = os.environ.get("GITHUB_RUN_ID")
assert run, "same-run provenance cannot be established outside CI"
read_plan = (evidence / "original-read.sha256").read_text(encoding="utf-8").strip()
assert len(read_plan) == 64, "missing immutable read-plan digest (not an XLSX byte digest)"
common = {
    "run_id": run,
    "source_id": "https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx",
    "materialization_id": "same-ci-run-four-sheets-read-once:" + run,
    "read_plan_sha256": read_plan,
}
scope = {
    "grain": "USD-fiat-completed-orders-and-UID-aggregates",
    "population": "fiat_transactions currency=USD status=completed",
    "time_window": "full-existing-XLSX-sample; not real-time",
    "status_meaning": "completed status field; external settlement unknown",
    "metrics": ["native_total", "top1_native_total", "trimmed_top1_share_pct", "same_top_user"],
}
qa = dict(common, verdict="PARTIAL", qa_receipt_ref="dual-evidence/quality.json",
          checked_scopes=[scope], note="reconstructed scoped QA; unrelated assets are not approved")
finding = dict(common, verdict=feedback["verdict"], packet_id=feedback["packet_id"],
               revision=feedback["revision"], verified_packet_id=feedback["packet_id"],
               verified_revision=feedback["revision"],
               result_receipt_ref="dual-evidence/q002-mechanism.json",
               verification_receipt_ref="dual-evidence/q002-verification-feedback.json",
               scope=dict(scope, metrics=["native_total", "trimmed_top1_share_pct", "same_top_user"]))
good = check_scope(qa, finding)
wrong = copy.deepcopy(finding)
wrong["scope"]["population"] = "crypto_transactions asset=USDT status=completed"
bad = check_scope(qa, wrong)
assert good["verdict"] == "PASS" and bad["verdict"] == "BLOCKED", (good,bad)

review = {
    "execution_type": "deterministic_s1_s4_replay_not_independent_llm_agents",
    "source_revision": "UNKNOWN; read-plan hash is not source-byte hash",
    "task": "Q002 USD completed-fiat top-user concentration sensitivity",
    "s1_business_owner": "Should this historical concentration alone trigger a risk escalation?",
    "s2_result_grain": scope["grain"],
    "s3_scope_gate": good,
    "s4_independent_arithmetic": {
        k: metrics[k] for k in
        ("completed_usd_orders", "distinct_users", "native_total", "top1_native_total",
         "largest_single_order", "trimmed_top1_native_total",
         "trimmed_top1_share_pct", "same_top_user")
    },
    "negative_control_foreign_crypto": bad,
    "owner_review": {
        "decision": "NEEDS_EVIDENCE",
        "reason": "A completed-status user concentration ratio cannot establish market manipulation, liquidity stress, or wrongdoing.",
        "next_evidence": "Order-level directions, verified settlement status, time distribution and supported risk indicators."
    },
}
for name, body in (("s3-scoped-qa.json", qa), ("s4-scoped-finding.json", finding), ("s1-s4-review.json", review)):
    (evidence / name).write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(review, ensure_ascii=False))

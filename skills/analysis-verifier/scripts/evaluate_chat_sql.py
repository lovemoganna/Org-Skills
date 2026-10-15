#!/usr/bin/env python3
"""Chat-requested old-vs-3-role SQL analysis trial; uses native DuckDB 1.4.2.

This is a deterministic SQL/handoff comparison, NOT a blinded multi-model trial.
The holdout is independently calculated from source CSV without either SQL result.
"""
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import duckdb

DIR = Path(sys.argv[1] if len(sys.argv)>1 else "blind-evidence")
SOURCE = json.loads((DIR/"source-receipt.json").read_text(encoding="utf-8"))
assert SOURCE["status"] == "SOURCE_VERIFIED"
DB = DIR/"blind.duckdb"
TASK = "2025 年不同渠道的取消率和退款率是否值得优先调查？"

# S1 Business Owner: a channel-specific operational investigation decision.
brief = {
    "question": TASK,
    "population": "every 2025 order; all lifecycle statuses, not just completed",
    "decision": "Which, if any, channel merits investigation based solely on status incidence?",
    "competing_explanations": [
        "A channel has genuinely different cancellation/refund propensity",
        "Small differences are normal sample variation or different channel/customer composition",
    ],
    "decision_boundary": "No inferred fraud, fulfillment root cause, cash refund amount, or company-specific threshold.",
}
# Legacy direct mode: one conventional SQL query, followed by normal review.
legacy_sql = """
SELECT order_channel AS channel,
       COUNT(*) AS orders,
       COUNT(*) FILTER (WHERE order_status='Completed') AS completed,
       COUNT(*) FILTER (WHERE order_status='Cancelled') AS cancelled,
       COUNT(*) FILTER (WHERE order_status='Refunded') AS refunded
FROM orders GROUP BY order_channel ORDER BY order_channel
"""
# New S2 Business Reasoning: one row per channel; preaggregate channel × status.
new_sql = """
WITH by_status AS (
 SELECT order_channel, order_status, COUNT(DISTINCT order_id) AS n
 FROM orders GROUP BY order_channel,order_status
)
SELECT order_channel AS channel,
       SUM(n) AS orders,
       SUM(CASE WHEN order_status='Completed' THEN n ELSE 0 END) AS completed,
       SUM(CASE WHEN order_status='Cancelled' THEN n ELSE 0 END) AS cancelled,
       SUM(CASE WHEN order_status='Refunded' THEN n ELSE 0 END) AS refunded
FROM by_status GROUP BY order_channel ORDER BY order_channel
"""
qa_sql = """
SELECT
 COUNT(*) AS source_rows,
 COUNT(DISTINCT order_id) AS unique_orders,
 COUNT(*) FILTER(WHERE order_id IS NULL OR TRIM(order_id)='') AS missing_order_id,
 COUNT(*) FILTER(WHERE order_channel IS NULL OR TRIM(order_channel)='') AS missing_channel,
 COUNT(*) FILTER(WHERE order_status NOT IN ('Completed','Cancelled','Refunded')
                  OR order_status IS NULL) AS unknown_states,
 COUNT(*) FILTER(WHERE order_status='Cancelled' AND total_amount=0 AND subtotal>0)
    AS cancelled_zero_total_but_positive_subtotal,
 COUNT(*) FILTER(WHERE order_status='Refunded' AND total_amount>0)
    AS refunded_with_positive_original_total
FROM orders
"""
def fetched(c, sql):
    start = time.perf_counter()
    rel = c.execute(sql)
    cols = [m[0] for m in rel.description]
    result = [dict(zip(cols,row)) for row in rel.fetchall()]
    return result, round((time.perf_counter()-start)*1000,3)

with duckdb.connect(str(DB), read_only=True,
                    config={"enable_external_access": "false"}) as c:
    assert c.execute("SELECT version()").fetchone()[0].startswith("v1.4.2"), "unexpected DuckDB version"
    baseline_rows, baseline_ms = fetched(c, legacy_sql)
    new_rows, new_ms = fetched(c, new_sql)
    check = fetched(c, qa_sql)[0][0]
    source_order_count = SOURCE["files"]["orders"]["rows"]
    assert int(check["source_rows"]) == source_order_count
    assert int(check["unique_orders"]) == int(check["source_rows"])
    assert not check["missing_order_id"] and not check["missing_channel"] and not check["unknown_states"]

    # S3 adversarial controls: intentionally wrong SQL must be rejected by independent grain tests.
    joined_count = c.execute("SELECT COUNT(*) FROM orders JOIN order_items USING(order_id)").fetchone()[0]
    distinct_joined = c.execute("SELECT COUNT(DISTINCT order_id) FROM orders JOIN order_items USING(order_id)").fetchone()[0]
    assert joined_count > distinct_joined == int(check["source_rows"])
    bad_join = {"wrong_denominator_if_count_joined_rows": joined_count,
                "correct_distinct_orders": distinct_joined,
                "expected_gate": "REJECT_JOIN_AMPLIFICATION"}
    doubled_count = c.execute("""
      WITH duplicated_products AS (SELECT * FROM products UNION ALL SELECT * FROM products)
      SELECT COUNT(*) FROM order_items JOIN duplicated_products USING(product_id)
    """).fetchone()[0]
    assert doubled_count == SOURCE["files"]["order_items"]["rows"]*2
    duplicate_dimension = {"injected_dimension_duplicate_join_rows": doubled_count,
                           "original_line_count": SOURCE["files"]["order_items"]["rows"],
                           "expected_gate": "REJECT_NONUNIQUE_JOIN_KEY"}

    overlap = fetched(c, """
        WITH gr AS (
           SELECT o.order_id,
             COUNT(*) FILTER (WHERE i.promotion_id IS NOT NULL) AS promo,
             COUNT(*) FILTER (WHERE i.promotion_id IS NULL) AS nonpromo
           FROM orders o JOIN order_items i USING(order_id)
           WHERE o.order_status='Completed' GROUP BY o.order_id
        )
        SELECT COUNT(*) AS completed_orders,
               COUNT(*) FILTER(WHERE promo>0) AS promo_orders,
               COUNT(*) FILTER(WHERE nonpromo>0) AS nonpromo_orders,
               COUNT(*) FILTER(WHERE promo>0 AND nonpromo>0) AS overlapping_orders
        FROM gr
    """)[0][0]
    assert overlap["promo_orders"]+overlap["nonpromo_orders"]-overlap["overlapping_orders"] == overlap["completed_orders"]
    assert overlap["overlapping_orders"] > 0
    assert check["cancelled_zero_total_but_positive_subtotal"] > 0
    assert check["refunded_with_positive_original_total"] > 0

# Independent standard-library source check: intentionally does not inspect SQL results.
with (DIR/"orders.csv").open(encoding="utf-8",newline="") as handle:
    records=csv.DictReader(handle)
    holdout=collections.defaultdict(lambda: collections.Counter())
    for r in records:
        holdout[r["order_channel"]][r["order_status"]]+=1
holdout_rows = [{
    "channel": channel,
    "orders": sum(states.values()),
    "completed": states.get("Completed",0),
    "cancelled": states.get("Cancelled",0),
    "refunded": states.get("Refunded",0),
} for channel,states in sorted(holdout.items())]
assert baseline_rows == holdout_rows, "legacy query differs from independently parsed source"
assert new_rows == holdout_rows, "new query differs from independently parsed source"
assert sum(r["orders"] for r in new_rows) == source_order_count

def wilson(k, n):
    z=1.959963984540054
    p=k/n
    center=(p+z*z/(2*n))/(1+z*z/n)
    rad=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/(1+z*z/n)
    return [round(center-rad,6),round(center+rad,6)]

def rate_row(x):
    n=x["orders"]
    cancelled=x["cancelled"];refunded=x["refunded"]
    return {
        **x,
        "cancel_rate_pct": round(100*cancelled/n,4),
        "refund_status_rate_pct": round(100*refunded/n,4),
        "noncompleted_rate_pct": round(100*(cancelled+refunded)/n,4),
        "noncompleted_rate_95pct_wilson":wilson(cancelled+refunded,n)
    }

rates = [rate_row(x) for x in new_rows]
combined_values=[x["noncompleted_rate_pct"] for x in rates]
# This is a descriptive gap, not a causality, statistical significance, or policy threshold.
gap=max(combined_values)-min(combined_values)
source_id=SOURCE["commit"]
data_hash=hashlib.sha256(json.dumps({
    k:v["sha256"] for k,v in SOURCE["files"].items()},sort_keys=True).encode()).hexdigest()
run_id=os.getenv("GITHUB_RUN_ID","CHAT-LOCAL")
provenance={
  "run_id":run_id, "source_id":source_id,
  "materialization_id":f"{run_id}:{data_hash}",
  "read_plan_sha256": hashlib.sha256(
      (data_hash+"|read_csv_auto 4 pinned CSV into DuckDB tables").encode()).hexdigest()
}
scope={
  "grain":"order_channel",
  "population":"all orders with statuses Completed,Cancelled,Refunded",
  "time_window":"2025-01-01 through 2025-12-31",
  "status_meaning":"raw order_status field, not confirmed funds refund or settled amount",
  "metrics":["orders","cancelled","refunded","completed","cancel_rate_pct",
             "refund_status_rate_pct","noncompleted_rate_pct"]
}
qa={
    **provenance, "verdict":"PASS","qa_receipt_ref":"sql-eval-evidence/qa.json",
    "checked_scopes":[scope], "source_counts":check,
    "note":"Positive refunded order total is not confirmed cash refund; cancelled zero total does not erase order attempt"
}
finding={
    **provenance,"verdict":"VERIFIED","packet_id":"CHANNEL-STATE-2025","revision":1,
    "verified_packet_id":"CHANNEL-STATE-2025","verified_revision":1,
    "result_receipt_ref":"sql-eval-evidence/new-result.json",
    "verification_receipt_ref":"sql-eval-evidence/holdout.json",
    "scope":scope
}
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from scope_gate import check_scope
good_gate=check_scope(qa,finding)
assert good_gate["verdict"]=="PASS",good_gate
out_of_scope=dict(finding, scope=dict(scope, status_meaning="settled cash refunds"))
bad_gate=check_scope(qa,out_of_scope)
assert bad_gate["verdict"]=="BLOCKED"
def save(name,obj):
    (DIR/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
save("sql-eval-baseline.json",{"skill":"sql-business-thinking legacy / Direct",
    "question": TASK,"candidate_sql":legacy_sql,"results":baseline_rows,
    "runtime_ms":baseline_ms, "notice":"SQL produced under one simulated chat workflow, not independently blinded."})
save("sql-eval-split.json",{"skills":["business-owner","business-reasoning","analysis-verifier"],
    "brief":brief,"grain":"order_channel","candidate_sql":new_sql,"results":new_rows,
    "runtime_ms":new_ms, "notice":"Same model/context; not a multi-model A/B claim"})
save("sql-eval-qa.json",qa)
save("sql-eval-finding.json",finding)
save("sql-eval-holdout.json",{"method":"separate Python csv.DictReader, not SQL result",
    "rows":holdout_rows,"source_sha256":SOURCE["files"]["orders"]["sha256"]})
save("sql-eval-regression.json",{"join_fanout":bad_join,"duplicate_dimension":duplicate_dimension,
    "promo_overlap":overlap,"cancelled_value_semantics":check["cancelled_zero_total_but_positive_subtotal"],
    "refund_cash_semantics":check["refunded_with_positive_original_total"],
    "scope_gate_pass":good_gate,"scope_gate_negative":bad_gate})
decision={
    "source":"fictional retail data, real DuckDB execution",
    "findings":rates,
    "channel_noncompleted_max_min_gap_pct_points":round(gap,4),
    "business_owner_final_decision":"NEEDS_EVIDENCE",
    "reason":"Observed differences are descriptive and small; no agreed operating threshold, customer mix, timeline, causal evidence, or confirmed cash refund event.",
    "next_step":"Request order-level reason codes and an operational benchmark before channel priority or intervention.",
    "verdict":"STRUCTURAL_SCOPE_PASS; BUSINESS_DECISION_NOT_READY",
    "a_b_verdict":"BOTH_SQL_ARMS_VERIFIED_EQUAL; no demonstrated SQL correctness gain. New stages added explicit independent reconciliation and scope receipts.",
    "limits":"Same chat-model authorship; deterministic regressions do not measure autonomous agent competence.",
}
save("sql-eval-summary.json",decision)
print(json.dumps({
 "stage":"DUCKDB_SQL_EVAL_COMPLETED","version":duckdb.__version__,
 "source_rows":source_order_count,"baseline_matches_independent":True,
 "split_matches_independent":True,"rates":rates,"gap_pp":round(gap,4),
 "adversarial":{"joined_rows":joined_count,"duplicated_dimension":doubled_count,
   "promo_overlap":overlap["overlapping_orders"],
   "cancelled_zero_total_positive_subtotal":check["cancelled_zero_total_but_positive_subtotal"],
   "refund_status_positive_original_total":check["refunded_with_positive_original_total"]},
 "scope_gate":good_gate,"negative_scope":bad_gate,
 "owner_decision":"NEEDS_EVIDENCE"
},ensure_ascii=False,default=str))

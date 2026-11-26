#!/usr/bin/env python3
"""Temporal-state assertion guard: independent synthetic negative controls."""
import copy
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from temporal_state_gate import evaluate

SCHEMA=[{"column_name":n} for n in ("uid","account_status","created_at")]
EVENTS=[
 {"order_id":"a1","asset":"USD","amount":800,"account_status":"frozen",
  "direction":"withdrawal","status":"completed",
  "created_at":"2025-09-20 16:45:00","completed_at":"2025-09-21 09:30:00"},
 {"order_id":"a2","asset":"USD","amount":20,"account_status":"frozen",
  "direction":"withdrawal","status":"completed",
  "created_at":"2025-10-25 11:00:00","completed_at":"2025-10-25 15:30:00"}]
a=evaluate(SCHEMA,EVENTS)
assert a["verdict"]=="NEEDS_AUTHORIZED_HISTORY"
assert a["completed_withdrawals"]==2
assert a["amount_sum_same_asset_only"]=="820"
assert not a["account_status_at_withdrawal_identified"]
assert all(r["account_status_at_order_time"]=="UNKNOWN" for r in a["events"])
assert len(a["hypotheses_not_observations"])==3
assert evaluate(SCHEMA+[{"column_name":"frozen_at"}],EVENTS)["verdict"]=="IN_SOURCE_FIELD_REVIEW_REQUIRED"
def must_reject(case):
  try:evaluate(SCHEMA,case)
  except ValueError:return
  raise AssertionError("unsafe event record accepted")
bad=copy.deepcopy(EVENTS)
bad[0]["completed_at"]="2024-01-01 00:00:00"
must_reject(bad)
bad=copy.deepcopy(EVENTS)
bad[0]["order_id"]=bad[1]["order_id"]
must_reject(bad)
bad=copy.deepcopy(EVENTS)
bad[0]["account_status"]="active"
must_reject(bad)
print("PASS: snapshot vs event-time distinction and three negative controls")

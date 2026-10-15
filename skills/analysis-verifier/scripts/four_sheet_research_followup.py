#!/usr/bin/env python3
"""Choose second-stage SQL from first-stage DuckDB result receipts.

This is a deterministic evidence-directed planner, not independently running
LLM agents. It reads derived JSON receipts only, never remote Excel or other
sheets. The SQL it writes runs in the same open native DuckDB session.
"""
from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import re
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "discovery")
def load(name):
    return json.loads((root/(name+".json")).read_text(encoding="utf-8"))
fiat=load("fiat_details")
crypto=load("crypto_details")
pairs=load("crossrail_status_and_time")
returns=load("fiat_roundtrip_7d")
profiles=load("joined_users")
frozen=load("frozen_account_activity")
schema=load("schema_users")
assert len(fiat)==25 and len(crypto)==25 and len(profiles)==10
uid_name={x["uid"]:x["user_name"] for x in profiles}
cases=[]
# Evidence of a real data-semantics pitfall: completion timestamp != completed status.
misleading=[x for x in fiat+crypto if x["status"]!="completed" and x["completed_at"]]
if misleading:
    target=sorted(misleading,key=lambda x:x["created_at"])[0]
    cases.append({"code":"STATUS_NOT_SETTLEMENT","uid":str(int(float(target["uid"]))),
                  "order_id":target["order_id"],"name":uid_name[str(int(float(target["uid"])))],
                  "hypothesis":"A populated completed_at implies completed status",
                  "discriminator":"Count completed_at not null versus status completed"})
# Sequence candidate: same-asset deposit/withdrawal close together is not proof of transfer.
if returns:
    x=min(returns,key=lambda x:x["elapsed_min"])
    cases.append({"code":"SAME_ASSET_TURNOVER","uid":x["uid"],"name":uid_name[x["uid"]],
                  "order_ids":[x["in_order"],x["out_order"]],
                  "hypothesis":"Quick recorded in-and-out means funds were the same or illicit",
                  "discriminator":"Verify event ordering and peer occurrence; trace linkage absent"})
# Cross-rail candidate, if not already captured by turnover. Full event chronology
# is still essential: create time may differ from actual completion order.
if pairs:
    x=min(pairs,key=lambda x:x["gap_minutes"])
    if x["uid"] not in [c["uid"] for c in cases]:
        cases.append({"code":"CROSS_RAIL_NEARBY","uid":x["uid"],"name":uid_name[x["uid"]],
                      "order_ids":[x["fiat_order"],x["crypto_order"]],
                      "hypothesis":"Near-created fiat and crypto orders are one conversion",
                      "discriminator":"Check completion order, source/target directions and external linkage"})
freeze_fields={"frozen_at","status_effective_at","account_status_changed_at"}
known_fields={x["column_name"] for x in schema}
blocked=bool(frozen) and not bool(known_fields & freeze_fields)
study={"selection_basis":"First-stage native DuckDB results, not a fixed name or UID",
       "investigate":cases,"blocked":[{"code":"FROZEN_HISTORICAL_STATE",
          "reason":"No historical freeze effective time in authorized users schema",
          "candidate_orders":[x["order_id"] for x in frozen]}] if blocked else [],
       "discarded_hypotheses":["similar amounts and close creation times alone establish asset conversion",
                               "frozen snapshot proves frozen at historical withdrawal"],
       "source_reads":4,"new_source_reads":0}
assert cases,"No testable finding present; do not generate narrative."
assert all(re.fullmatch(r"[0-9]{6,15}",x["uid"]) for x in cases)
(root/"research-plan.json").write_text(json.dumps(study,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
uids=",".join("'"+x["uid"]+"'" for x in cases)
sql=".mode json\n"
def emit(name,q):
    global sql
    assert "read_xlsx" not in q.lower()
    sql+="\n.once "+(root/name).as_posix()+".json\n"+q.strip()+";\n"
emit("stage2_subject_events",f"""
SELECT * FROM (
 SELECT CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) uid,'fiat' rail,
 CAST(fiat_order_id AS VARCHAR) order_id,CAST(currency AS VARCHAR) asset,
 CAST(direction AS VARCHAR) direction,CAST(status AS VARCHAR) status,
 CAST(amount AS DECIMAL(24,8)) amount,CAST(fee AS DECIMAL(24,8)) fee,
 CAST(created_at AS VARCHAR) created_at,CAST(completed_at AS VARCHAR) completed_at
 FROM fiat_transactions
 UNION ALL
 SELECT CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR),'crypto',
 CAST(crypto_order_id AS VARCHAR),CAST(asset AS VARCHAR),
 CAST(direction AS VARCHAR),CAST(status AS VARCHAR),
 CAST(amount AS DECIMAL(24,8)),CAST(fee AS DECIMAL(24,8)),
 CAST(created_at AS VARCHAR),CAST(completed_at AS VARCHAR)
 FROM crypto_transactions
) t WHERE uid IN ({uids}) ORDER BY uid,created_at,rail
""")
emit("stage2_completion_invariant","""
WITH x AS (
 SELECT 'fiat' rail,CAST(status AS VARCHAR) status,
 CAST(direction AS VARCHAR) direction,CAST(amount AS DECIMAL(24,8)) amount,
 CAST(currency AS VARCHAR) asset, completed_at
 FROM fiat_transactions
 UNION ALL
 SELECT 'crypto',CAST(status AS VARCHAR),CAST(direction AS VARCHAR),
 CAST(amount AS DECIMAL(24,8)),CAST(asset AS VARCHAR),completed_at
 FROM crypto_transactions
)
SELECT rail,asset,direction,status,COUNT(*) records,
 COUNT(*) FILTER(WHERE completed_at IS NOT NULL) with_completed_at,
 SUM(amount) amount_native
FROM x GROUP BY rail,asset,direction,status ORDER BY rail,asset,status
""")
emit("stage2_completed_at_mismatch","""
SELECT 'fiat' rail,CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) uid,
 CAST(fiat_order_id AS VARCHAR) order_id,currency asset,direction,status,amount,
 CAST(created_at AS VARCHAR) created_at,CAST(completed_at AS VARCHAR) completed_at
 FROM fiat_transactions WHERE status <> 'completed' AND completed_at IS NOT NULL
UNION ALL
SELECT 'crypto',CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR),
 CAST(crypto_order_id AS VARCHAR),asset,direction,status,amount,
 CAST(created_at AS VARCHAR),CAST(completed_at AS VARCHAR)
 FROM crypto_transactions WHERE status <> 'completed' AND completed_at IS NOT NULL
""")
emit("stage2_completed_pair_peer_baseline","""
WITH ordered AS (
 SELECT TRY_CAST(uid AS BIGINT) uid,fiat_order_id,currency,direction,status,created_at,completed_at
 FROM fiat_transactions
), pairs AS (
 SELECT CAST(a.uid AS VARCHAR) uid, a.currency,
  a.fiat_order_id deposit_order,b.fiat_order_id withdrawal_order,
  DATE_DIFF('minute',a.created_at,b.created_at) create_gap,
  DATE_DIFF('minute',a.completed_at,b.completed_at) completion_gap
 FROM ordered a JOIN ordered b ON a.uid=b.uid AND a.currency=b.currency
 WHERE a.status='completed' AND b.status='completed'
  AND a.direction='deposit' AND b.direction='withdrawal'
  AND b.created_at>=a.created_at AND b.created_at<=a.created_at+INTERVAL 1 DAY
)
SELECT * FROM pairs ORDER BY create_gap,uid
""")
emit("stage2_crossrail_completion_order","""
SELECT CAST(TRY_CAST(f.uid AS BIGINT) AS VARCHAR) uid,
 CAST(f.fiat_order_id AS VARCHAR) fiat_id, f.direction fiat_direction,
 CAST(f.created_at AS VARCHAR) fiat_created,
 CAST(f.completed_at AS VARCHAR) fiat_completed,
 CAST(c.crypto_order_id AS VARCHAR) crypto_id,c.direction crypto_direction,
 CAST(c.created_at AS VARCHAR) crypto_created,
 CAST(c.completed_at AS VARCHAR) crypto_completed,
 DATE_DIFF('minute',f.created_at,c.created_at) created_gap_crypto_minus_fiat,
 DATE_DIFF('minute',f.completed_at,c.completed_at) completed_gap_crypto_minus_fiat,
 CAST(c.network AS VARCHAR) crypto_network,CAST(c.confirmations AS DOUBLE) confirmations,
 CASE WHEN c.tx_hash IS NOT NULL AND LENGTH(TRIM(c.tx_hash))>0 THEN true ELSE false END has_hash
 FROM fiat_transactions f JOIN crypto_transactions c
 ON TRY_CAST(f.uid AS BIGINT)=TRY_CAST(c.uid AS BIGINT)
 WHERE f.status='completed' AND c.status='completed'
 AND ABS(DATE_DIFF('minute',f.created_at,c.created_at))<=1440
 ORDER BY ABS(DATE_DIFF('minute',f.created_at,c.created_at)),uid
""")
(root/"second-pass.sql").write_text(sql,encoding="utf-8")
print(json.dumps({"stage":"ADAPTIVE_HANDOFF","testable_cases":[c["code"] for c in cases],
       "blocked_unresolvable":len(study["blocked"]),
       "new_queries":5,"additional_remote_reads":0},ensure_ascii=False))

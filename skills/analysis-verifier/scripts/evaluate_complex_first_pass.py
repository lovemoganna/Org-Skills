#!/usr/bin/env python3
"""Three complex first-pass SQL cases: same task/data, two authored strategies.

Evidence: pinned public fictional retail 2025 CSVs; native DuckDB v1.4.2;
independent Python Decimal/csv holdout. No model API / independent agents.
Always preserve each initial attempt before any repair. No fabricated failures.
"""
import collections
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import duckdb

OUT=Path(sys.argv[1] if len(sys.argv)>1 else "complex-evidence")
receipt=json.loads((OUT/"source-receipt.json").read_text(encoding="utf-8"))
assert receipt["status"]=="SOURCE_VERIFIED" and duckdb.__version__=="1.4.2"
assert set(receipt["files"])=={"orders","order_items","products","promotions"}
db=OUT/"blind.duckdb"
Q4=Decimal("0.0001")
Q2=Decimal("0.01")
D=lambda x:Decimal(str(x))
def round4(x):return x.quantize(Q4,rounding=ROUND_HALF_UP)
def round2(x):return x.quantize(Q2,rounding=ROUND_HALF_UP)
def pct(k,n):return round4(Decimal(100)*D(k)/D(n)) if n else None

CASE_SPECS={
  "Q1": {"question":"按渠道对比 2025 Q2、Q3 订单取消或 Refunded 状态占比变化；是否值得优先调查？",
        "grain":"order_channel", "scope":"all 2025 orders with Q2/Q3 creation dates; status not actual cash return",
        "cols":["channel","q2_orders","q2_noncompleted","q2_rate_pct","q3_orders","q3_noncompleted","q3_rate_pct","change_pp"],
        "legacy":"""
SELECT order_channel AS channel,
COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2) AS q2_orders,
COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2
 AND order_status IN ('Cancelled','Refunded')) AS q2_noncompleted,
ROUND(100.0*COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2
 AND order_status IN ('Cancelled','Refunded')) /
 NULLIF(COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2),0),4) AS q2_rate_pct,
COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3) AS q3_orders,
COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3
 AND order_status IN ('Cancelled','Refunded')) AS q3_noncompleted,
ROUND(100.0*COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3
 AND order_status IN ('Cancelled','Refunded')) /
 NULLIF(COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3),0),4) AS q3_rate_pct,
ROUND(100.0*COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3
 AND order_status IN ('Cancelled','Refunded')) /
 NULLIF(COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=3),0)
 - 100.0*COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2
 AND order_status IN ('Cancelled','Refunded')) /
 NULLIF(COUNT(*) FILTER(WHERE EXTRACT(QUARTER FROM order_datetime)=2),0),4) AS change_pp
FROM orders WHERE EXTRACT(QUARTER FROM order_datetime) IN (2,3)
GROUP BY order_channel ORDER BY channel
""",
        "split":"""
WITH by_period AS (
  SELECT order_channel,EXTRACT(QUARTER FROM order_datetime) AS quarter,
         COUNT(DISTINCT order_id) AS n,
         COUNT(DISTINCT CASE WHEN order_status IN ('Cancelled','Refunded') THEN order_id END) AS noncompleted
  FROM orders WHERE EXTRACT(QUARTER FROM order_datetime) IN (2,3)
  GROUP BY order_channel,quarter
), pivoted AS (
 SELECT order_channel AS channel,
 SUM(n) FILTER(WHERE quarter=2) AS q2_orders,
 SUM(noncompleted) FILTER(WHERE quarter=2) AS q2_noncompleted,
 SUM(n) FILTER(WHERE quarter=3) AS q3_orders,
 SUM(noncompleted) FILTER(WHERE quarter=3) AS q3_noncompleted
 FROM by_period GROUP BY order_channel
)
SELECT channel,q2_orders,q2_noncompleted,
 ROUND(100.0*q2_noncompleted/NULLIF(q2_orders,0),4) AS q2_rate_pct,
 q3_orders,q3_noncompleted,
 ROUND(100.0*q3_noncompleted/NULLIF(q3_orders,0),4) AS q3_rate_pct,
 ROUND(100.0*q3_noncompleted/NULLIF(q3_orders,0)
       -100.0*q2_noncompleted/NULLIF(q2_orders,0),4) AS change_pp
FROM pivoted ORDER BY channel
"""
  },
  "Q2":{"question":"2025 已完成订单中，促销商品、含促销订单和混合订单各占多大规模？可否声称促销提升了销售？",
        "grain":"order_channel","scope":"Completed only; line_net excludes VAT; promo membership at line grain, overlap allowed",
        "cols":["channel","completed_orders","promo_orders","mixed_orders","line_net","promo_line_net","promo_order_line_net"],
        "legacy":"""
WITH joined AS (
 SELECT o.order_channel AS channel,o.order_id,i.promotion_id,i.line_net_amount,
 MAX(CASE WHEN i.promotion_id IS NOT NULL THEN 1 ELSE 0 END)
 OVER (PARTITION BY o.order_id) AS has_promo
 FROM orders o JOIN order_items i USING(order_id)
 WHERE o.order_status='Completed'
)
SELECT channel,COUNT(DISTINCT order_id) AS completed_orders,
 COUNT(DISTINCT CASE WHEN has_promo=1 THEN order_id END) AS promo_orders,
 COUNT(DISTINCT CASE WHEN has_promo=1 AND promotion_id IS NULL THEN order_id END) AS mixed_orders,
 ROUND(SUM(line_net_amount),2) AS line_net,
 ROUND(SUM(CASE WHEN promotion_id IS NOT NULL THEN line_net_amount ELSE 0 END),2) AS promo_line_net,
 ROUND(SUM(CASE WHEN has_promo=1 THEN line_net_amount ELSE 0 END),2) AS promo_order_line_net
FROM joined GROUP BY channel ORDER BY channel
""",
        "split":"""
WITH by_order AS (
 SELECT o.order_channel AS channel,o.order_id,
 SUM(i.line_net_amount) AS line_net,
 SUM(CASE WHEN i.promotion_id IS NOT NULL THEN i.line_net_amount ELSE 0 END) AS promo_line_net,
 MAX(CASE WHEN i.promotion_id IS NOT NULL THEN 1 ELSE 0 END) AS has_promo,
 MAX(CASE WHEN i.promotion_id IS NULL THEN 1 ELSE 0 END) AS has_nonpromo
 FROM orders o JOIN order_items i USING(order_id)
 WHERE o.order_status='Completed'
 GROUP BY o.order_channel,o.order_id
)
SELECT channel,COUNT(*) AS completed_orders,
 SUM(has_promo) AS promo_orders,
 SUM(CASE WHEN has_promo=1 AND has_nonpromo=1 THEN 1 ELSE 0 END) AS mixed_orders,
 ROUND(SUM(line_net),2) AS line_net,
 ROUND(SUM(promo_line_net),2) AS promo_line_net,
 ROUND(SUM(CASE WHEN has_promo=1 THEN line_net ELSE 0 END),2) AS promo_order_line_net
FROM by_order GROUP BY channel ORDER BY channel
"""
  },
  "Q3":{"question":"按商品类目核实已完成订单的商品金额、商品成本代理及贡献代理，并区分促销商品金额与真实盈利。",
        "grain":"products.category","scope":"Completed order_items; line_net-cost proxy, not net profit; order counts overlap categories",
        "cols":["category","lines","unique_orders","line_net","cost_proxy","contribution_proxy","promo_line_net"],
        "legacy":"""
SELECT p.category,COUNT(*) AS lines,COUNT(DISTINCT o.order_id) AS unique_orders,
 ROUND(SUM(i.line_net_amount),2) AS line_net,
 ROUND(SUM(i.quantity*p.unit_cost),2) AS cost_proxy,
 ROUND(SUM(i.line_net_amount-i.quantity*p.unit_cost),2) AS contribution_proxy,
 ROUND(SUM(CASE WHEN i.promotion_id IS NOT NULL THEN i.line_net_amount ELSE 0 END),2) AS promo_line_net
FROM orders o JOIN order_items i USING(order_id)
JOIN products p USING(product_id)
WHERE o.order_status='Completed'
GROUP BY p.category ORDER BY p.category
""",
        "split":"""
WITH by_order_category AS (
 SELECT p.category,o.order_id,COUNT(*) AS line_count,
 SUM(i.line_net_amount) AS goods_net,
 SUM(i.quantity*p.unit_cost) AS goods_cost,
 SUM(CASE WHEN i.promotion_id IS NOT NULL THEN i.line_net_amount ELSE 0 END) AS promo_net
 FROM orders o JOIN order_items i USING(order_id)
 JOIN products p USING(product_id)
 WHERE o.order_status='Completed'
 GROUP BY p.category,o.order_id
)
SELECT category,SUM(line_count) AS lines,COUNT(*) AS unique_orders,
 ROUND(SUM(goods_net),2) AS line_net,ROUND(SUM(goods_cost),2) AS cost_proxy,
 ROUND(SUM(goods_net-goods_cost),2) AS contribution_proxy,
 ROUND(SUM(promo_net),2) AS promo_line_net
FROM by_order_category GROUP BY category ORDER BY category
"""
  }
}

# A separate parser over source data; not SQL result, not the first candidate answer.
with (OUT/"orders.csv").open(encoding="utf-8",newline="") as f:
    orders={r["order_id"]:r for r in csv.DictReader(f)}
with (OUT/"products.csv").open(encoding="utf-8",newline="") as f:
    products={r["product_id"]:r for r in csv.DictReader(f)}
assert len(orders)==receipt["files"]["orders"]["rows"]
assert len(products)==receipt["files"]["products"]["rows"]
joined=collections.defaultdict(list)
category_rows=collections.defaultdict(list)
with (OUT/"order_items.csv").open(encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
        o=orders[r["order_id"]]
        joined[r["order_id"]].append(r)
        if o["order_status"]=="Completed":
            p=products[r["product_id"]]
            category_rows[p["category"]].append((o,r,p))

def independent_q1():
    grouped=collections.defaultdict(lambda:collections.Counter())
    for o in orders.values():
        quarter=(int(o["order_datetime"][5:7])-1)//3+1
        if quarter not in (2,3):continue
        key=o["order_channel"],quarter
        grouped[key]["n"]+=1
        if o["order_status"] in ("Cancelled","Refunded"):
            grouped[key]["bad"]+=1
    out=[]
    for channel in sorted({x["order_channel"] for x in orders.values()}):
        a,b=grouped[(channel,2)],grouped[(channel,3)]
        if not a["n"] or not b["n"]:raise AssertionError("Q2_OR_Q3_UNAVAILABLE")
        out.append({"channel":channel,"q2_orders":a["n"],"q2_noncompleted":a["bad"],
            "q2_rate_pct":pct(a["bad"],a["n"]),"q3_orders":b["n"],
            "q3_noncompleted":b["bad"],"q3_rate_pct":pct(b["bad"],b["n"]),
            "change_pp":round4(Decimal(100)*(
                  D(b["bad"])/D(b["n"])-D(a["bad"])/D(a["n"])))})
    return out

def independent_q2():
    a=collections.defaultdict(lambda:{"completed_orders":0,"promo_orders":0,
       "mixed_orders":0,"line_net":Decimal(0),"promo_line_net":Decimal(0),
       "promo_order_line_net":Decimal(0)})
    for oid,o in orders.items():
        if o["order_status"]!="Completed":continue
        rows=joined[oid]
        if not rows:raise AssertionError("COMPLETED_ORDER_HAS_NO_LINES")
        s=a[o["order_channel"]];s["completed_orders"]+=1
        promo=[x for x in rows if x["promotion_id"]]
        notpromo=[x for x in rows if not x["promotion_id"]]
        goods=sum((D(x["line_net_amount"]) for x in rows),Decimal(0))
        s["line_net"]+=goods
        s["promo_line_net"]+=sum((D(x["line_net_amount"]) for x in promo),Decimal(0))
        if promo:
            s["promo_orders"]+=1;s["promo_order_line_net"]+=goods
        if promo and notpromo:s["mixed_orders"]+=1
    return [dict(channel=k,**{name:round2(v) if isinstance(v,Decimal) else v
                       for name,v in values.items()}) for k,values in sorted(a.items())]

def independent_q3():
    output=[]
    for category, rows in sorted(category_rows.items()):
        net=sum((D(i["line_net_amount"]) for _,i,_ in rows),Decimal(0))
        cost=sum((D(i["quantity"])*D(p["unit_cost"]) for _,i,p in rows),Decimal(0))
        promo=sum((D(i["line_net_amount"]) for _,i,_ in rows if i["promotion_id"]),Decimal(0))
        output.append({"category":category,"lines":len(rows),
            "unique_orders":len({o["order_id"] for o,_,_ in rows}),
            "line_net":round2(net),"cost_proxy":round2(cost),
            "contribution_proxy":round2(net-cost),"promo_line_net":round2(promo)})
    return output

HOLDOUT={"Q1":independent_q1(),"Q2":independent_q2(),"Q3":independent_q3()}
# Independently determined keys/columns remain part of sealed evaluator, not candidate SQL.
def canonical(row):
    return tuple((k, D(v) if isinstance(v,(int,float,Decimal)) else v)
                 for k,v in sorted(row.items()))
def evaluate(rows, golden, expected_cols):
    if len(rows)!=len(golden):return "ROW_COUNT_MISMATCH"
    if any(set(row)!=set(expected_cols) for row in rows):return "OUTPUT_SCHEMA_MISMATCH"
    for x,y in zip(rows,golden):
        if x.keys()!=y.keys() and set(x)!=set(y):return "OUTPUT_COLUMNS_MISMATCH"
        if canonical(x)!=canonical(y):
            return "INDEPENDENT_RESULT_MISMATCH"
    return "PASS"

attempts=[];summary={"case_count":len(CASE_SPECS),"run_id":os.getenv("GITHUB_RUN_ID","LOCAL"),
 "source_commit":receipt["commit"],"duckdb":duckdb.__version__,
 "kind":"scripted SQL-candidate first-pass reliability, not independent AI Skill benchmark",
 "caveat":"Both arms authored in same ChatGPT context, under different procedural styles.",
 "cases":[]}
with duckdb.connect(str(db),read_only=True,
                    config={"enable_external_access":"false"}) as c:
    for cid,spec in CASE_SPECS.items():
        expected=HOLDOUT[cid]
        case={"id":cid,"business_question":spec["question"],"grain":spec["grain"],
              "scope":spec["scope"],"data_sha256":receipt["files"]["orders"]["sha256"],
              "arms":[]}
        for arm in ("legacy","split"):
            attempt={"case":cid,"arm":arm,"initial_sql":spec[arm],
                     "attempt_number":1,"authoring_context":"same ChatGPT conversation",
                     "result_rows":None,"elapsed_ms":None}
            start=time.monotonic()
            try:
                cursor=c.execute(spec[arm])
                names=[d[0] for d in cursor.description]
                rows=[dict(zip(names,row)) for row in cursor.fetchall()]
                attempt["result_rows"]=rows
                attempt["status"]=evaluate(rows,expected,spec["cols"])
            except Exception as e:
                attempt["status"]="EXECUTION_FAILURE"
                attempt["error"]=str(e)[:350]
            attempt["elapsed_ms"]=round((time.monotonic()-start)*1000,2)
            attempt["first_pass"]=(attempt["status"]=="PASS")
            attempt["repairs"]=0  # these frozen SQLs have had no repair; failures stay visible.
            attempts.append(attempt)
            case["arms"].append({"arm":arm,"first_pass":attempt["first_pass"],
                   "status":attempt["status"],"repairs":0,
                   "elapsed_ms":attempt["elapsed_ms"]})
        summary["cases"].append(case)
    # Mutations check the evaluator; these do not count as failures of either SQL arm.
    for cid in CASE_SPECS:
        values=[dict(x) for x in HOLDOUT[cid]]
        assert evaluate(values,HOLDOUT[cid],CASE_SPECS[cid]["cols"])=="PASS"
        bad=[dict(x) for x in values]
        key=next(k for k,v in bad[0].items() if isinstance(v,(int,Decimal)) and not isinstance(v,bool))
        bad[0][key]=bad[0][key]+1
        assert evaluate(bad,HOLDOUT[cid],CASE_SPECS[cid]["cols"])!="PASS",cid
    # SQL controls required by complex multi-table scope.
    exploded=c.execute("SELECT COUNT(*) FROM orders JOIN order_items USING(order_id)").fetchone()[0]
    assert exploded>len(orders)
    conflict=c.execute("""SELECT COUNT(*) FROM(
       SELECT o.order_id FROM orders o JOIN order_items i USING(order_id)
       WHERE o.order_status='Completed' GROUP BY o.order_id
       HAVING COUNT(*) FILTER(WHERE i.promotion_id IS NOT NULL)>0
          AND COUNT(*) FILTER(WHERE i.promotion_id IS NULL)>0)""").fetchone()[0]
    assert conflict==sum(x["mixed_orders"] for x in HOLDOUT["Q2"])

summary["counts"]={arm:{"first_pass":sum(a["arm"]==arm and a["first_pass"] for a in attempts),
                       "total_cases":len(CASE_SPECS),
                       "observed_rework":sum(a["repairs"] for a in attempts if a["arm"]==arm)}
 for arm in ("legacy","split")}
summary["negative_controls"]={"mutated_expected_metrics_detected":3,
  "join_exploded_rows":exploded,"mixed_promo_completed_orders":conflict}
summary["decision_verdict"]="NO_UNSUPPORTED_CHANNEL_CAUSALITY_OR_PROMOTION_UPLIFT_OR_TRUE_PROFIT"
summary["promotion_rule"]="Only change the Skills if independent evidence demonstrates a reproducible skill-caused defect."
(OUT/"complex-first-pass-attempts.json").write_text(json.dumps(attempts,default=str,ensure_ascii=False,indent=2)+"\n")
(OUT/"complex-first-pass-summary.json").write_text(json.dumps(summary,default=str,ensure_ascii=False,indent=2)+"\n")
(OUT/"complex-first-pass-holdout.json").write_text(json.dumps(HOLDOUT,default=str,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"result":"FIRST_PASS_TRIAL","counts":summary["counts"],
                  "cases":[{"id":x["id"],"arms":x["arms"]} for x in summary["cases"]],
                  "negative_controls":summary["negative_controls"]},ensure_ascii=False))
if any(a["status"]!="PASS" for a in attempts):
    raise SystemExit(2)

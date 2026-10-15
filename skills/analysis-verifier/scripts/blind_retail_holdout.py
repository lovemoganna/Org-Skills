#!/usr/bin/env python3
"""Sealed retail benchmark: independent SQL checks, never injected into model prompts.

Computes observations only after real CSV hash-verification and DuckDB materialization.
This is a verifier benchmark, NOT a model/agent output or causal promotion study.
"""
import json
from pathlib import Path
import sys

def run(data_dir):
    import duckdb
    d=Path(data_dir)
    receipt=json.loads((d/"source-receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"]=="SOURCE_VERIFIED"
    assert receipt["files"]["orders"]["rows"] > 0
    with duckdb.connect(str(d/"blind.duckdb"),read_only=True,
                        config={"enable_external_access":"false"}) as c:
        def single(q):
            r=c.execute(q)
            cols=[x[0] for x in r.description]
            vals=r.fetchone()
            return dict(zip(cols,vals))
        def rows(q):
            r=c.execute(q)
            cols=[x[0] for x in r.description]
            return [dict(zip(cols,row)) for row in r.fetchall()]

        integrity=single("""
        SELECT COUNT(*) AS item_rows,
         COUNT(*) FILTER (WHERE oi.quantity <= 0 OR oi.unit_price < 0) AS invalid_quantity_or_price,
         COUNT(*) FILTER (WHERE oi.line_net_amount IS NULL OR p.unit_cost IS NULL) AS missing_net_or_cost,
         COUNT(*) FILTER (WHERE ABS(
             CAST(oi.line_net_amount AS DECIMAL(18,4)) -
             (CAST(oi.quantity AS DECIMAL(18,4))*CAST(oi.unit_price AS DECIMAL(18,4))
             - CAST(oi.discount_amount AS DECIMAL(18,4)))) > 0.02) AS line_arithmetic_mismatch,
         COUNT(*) FILTER (WHERE oi.promotion_id IS NOT NULL AND prom.promotion_id IS NULL) AS orphan_promotion_lines,
         COUNT(*) FILTER (WHERE oi.promotion_id IS NOT NULL AND prom.category <> p.category) AS promo_category_mismatch,
         COUNT(*) FILTER (WHERE oi.promotion_id IS NOT NULL AND (
              CAST(o.order_datetime AS DATE) < prom.start_date
              OR CAST(o.order_datetime AS DATE) > prom.end_date)) AS promotion_outside_valid_dates
        FROM order_items oi
        JOIN orders o ON o.order_id=oi.order_id
        JOIN products p ON p.product_id=oi.product_id
        LEFT JOIN promotions prom ON oi.promotion_id=prom.promotion_id
        """)
        by_status=rows("""
        SELECT o.order_status, COUNT(DISTINCT o.order_id) AS orders,
          COUNT(*) AS lines,
          SUM(oi.line_net_amount) AS line_net_native,
          SUM(oi.quantity*p.unit_cost) AS cost_native
        FROM orders o JOIN order_items oi USING (order_id)
         JOIN products p USING(product_id)
        GROUP BY 1 ORDER BY 1
        """)
        by_promo=rows("""
        SELECT CASE WHEN oi.promotion_id IS NULL THEN 'NO_PROMO' ELSE 'PROMO' END AS promotion_usage,
          COUNT(DISTINCT o.order_id) AS orders_in_group,
          COUNT(*) AS line_count,
          SUM(oi.line_net_amount) AS line_net_native,
          SUM(oi.quantity*p.unit_cost) AS product_cost_native,
          SUM(oi.line_net_amount - oi.quantity*p.unit_cost) AS contribution_proxy,
          COUNT(*) FILTER (WHERE oi.line_net_amount < oi.quantity*p.unit_cost) AS negative_proxy_lines
        FROM orders o JOIN order_items oi USING(order_id)
        JOIN products p USING(product_id)
        WHERE o.order_status='Completed'
        GROUP BY 1 ORDER BY 1
        """)
        campaign=rows("""
        SELECT oi.promotion_id, COUNT(*) AS lines,
          COUNT(DISTINCT o.order_id) AS orders,
          SUM(oi.line_net_amount) AS line_net_native,
          SUM(oi.quantity*p.unit_cost) AS product_cost_native,
          SUM(oi.line_net_amount-oi.quantity*p.unit_cost) AS contribution_proxy
        FROM orders o JOIN order_items oi USING(order_id)
        JOIN products p USING(product_id)
        WHERE o.order_status='Completed' AND oi.promotion_id IS NOT NULL
        GROUP BY 1 ORDER BY 1
        """)
        # Independent non-joined sums for line-level reconciliation.
        completed_line_total=single("""
        SELECT COUNT(*) AS lines, SUM(line_net_amount) AS line_net_native
        FROM order_items WHERE order_id IN (
          SELECT order_id FROM orders WHERE order_status='Completed')
        """)
    by_status_completed=next(x for x in by_status if x["order_status"]=="Completed")
    summary_line_total=sum(float(x["line_net_native"]) for x in by_promo)
    assert int(completed_line_total["lines"])==sum(int(x["line_count"]) for x in by_promo)
    assert abs(float(completed_line_total["line_net_native"])-summary_line_total)<0.01
    assert abs(float(by_status_completed["line_net_native"])-summary_line_total)<0.01
    material_issue=any(int(integrity[x])>0 for x in
        ("invalid_quantity_or_price","missing_net_or_cost","line_arithmetic_mismatch",
         "orphan_promotion_lines","promo_category_mismatch","promotion_outside_valid_dates"))
    result={
      "source_commit":receipt["commit"],
      "source_sha256":{k:v["sha256"] for k,v in receipt["files"].items()},
      "source_integrity":integrity,
      "order_status_breakdown":by_status,
      "completed_promo_comparison":by_promo,
      "completed_campaign_breakdown":campaign,
      "independent_line_reconciliation":completed_line_total,
      "evidence_scope":"2025 fictional retail transaction records, completed statuses; line_net - product unit_cost proxy; not net profit",
      "decision_limit":"Descriptive association only: no randomized control, operating expense, causal uplift or real company approvals.",
      "verdict":"PARTIAL_REQUIRES_SEMANTIC_REVIEW" if material_issue else "DESCRIPTIVE_DATA_CHECKED_NO_CAUSAL_CLAIM"
    }
    (d/"holdout-verifier.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,default=str))
    return result

if __name__=="__main__":
    run(sys.argv[1] if len(sys.argv)>1 else "blind-evidence")

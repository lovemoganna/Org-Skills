#!/usr/bin/env python3
"""Fail-closed, current-source Gate 1 for the real four-sheet CI smoke run.

Only neutral per-table CSV exports and DESCRIBE are consumed here. The ontology
fixture contains stable meaning, not expected quantities, anomalies or Findings.
This is a necessary automated contract check, not independent model evaluation.
"""
import csv
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

from check_ontology_sources import load_schemas, validate

SHEETS = ("users", "fiat_transactions", "crypto_transactions", "exchange_rates")
REQUIRED = {
    "users": ("uid",),
    "fiat_transactions": ("fiat_order_id", "uid", "direction", "status", "currency", "amount"),
    "crypto_transactions": ("crypto_order_id", "uid", "direction", "status", "asset", "amount"),
    "exchange_rates": ("asset", "effective_date", "rate_to_usdt"),
}

def atom(name, kind, subject, grain, domain, relation, source, note):
    return dict(zip((
        "一级标签", "二级标签", "三级标签", "原子名称", "原子层级",
        "本体类别", "类型", "单位或值域", "主体", "粒度",
        "时间语义", "关系", "知识点解释", "证据来源",
    ), (
        "资金", "实体与事件", name, name, "基础事实", kind, "原始记录",
        domain, subject, grain, "记录时点或当前快照",
        relation, note, source,
    )))

def rule(label, entity):
    return {
        "一级标签": "资金", "二级标签": "交易模式", "三级标签": label,
        "识别标准": "交易方向为 deposit 且记录状态为 completed",
        "Lisp 表达式": f"({entity} (AND (= 方向 deposit) (= 状态 completed)))",
        "规则定义": f"{entity}中同时符合方向及状态条件的记录，不推断清算或余额",
        "当前状态": "待业务结果验证",
    }

def make_model():
    return {
        "ontology_atoms": [
            atom("用户", "对象", "用户", "每用户", "用户标识",
                 "用户|关联|法币交易", "users.uid", "用户原始记录"),
            atom("法币交易", "事件", "法币交易", "每笔法币交易", "订单标识",
                 "法币交易|归属|用户", "fiat_transactions.fiat_order_id", "法币渠道订单记录"),
            atom("加密交易", "事件", "加密交易", "每笔加密交易", "订单标识",
                 "加密交易|归属|用户", "crypto_transactions.crypto_order_id", "加密资产渠道订单记录"),
            atom("法币方向", "属性", "法币交易", "每笔法币交易", "方向枚举",
                 "法币交易|具有|法币方向", "fiat_transactions.direction", "订单记录的交易方向"),
            atom("加密方向", "属性", "加密交易", "每笔加密交易", "方向枚举",
                 "加密交易|具有|加密方向", "crypto_transactions.direction", "订单记录的交易方向"),
            atom("法币金额", "属性", "法币交易", "每笔法币交易", "原生币种单位",
                 "法币交易|具有|法币金额", "fiat_transactions.amount", "不跨币种直接累加"),
            atom("加密数量", "属性", "加密交易", "每笔加密交易", "原生资产单位",
                 "加密交易|具有|加密数量", "crypto_transactions.amount", "不跨资产直接累加"),
            atom("法币状态", "状态", "法币交易", "每笔法币交易", "记录状态",
                 "法币交易|具有|法币状态", "fiat_transactions.status", "记录状态不等于最终结算"),
            atom("加密状态", "状态", "加密交易", "每笔加密交易", "记录状态",
                 "加密交易|具有|加密状态", "crypto_transactions.status", "记录状态不等于最终结算"),
            atom("汇率记录", "对象", "汇率记录", "每条报价", "计价标识",
                 "汇率记录|标识|计价对象", "exchange_rates.asset", "中性计价标识，不断言全是加密资产"),
        ],
        "ontology_rules": [rule("法币已记录入金", "法币交易"), rule("加密已记录入金", "加密交易")],
    }

def verify(root):
    errors = []
    schemas = load_schemas([f"{s}={root / (s + '-schema.csv')}" for s in SHEETS])
    for tab, fields in REQUIRED.items():
        for field in fields:
            if field not in schemas[tab]:
                errors.append(f"MISSING_CURRENT_FIELD:{tab}.{field}")
    model = make_model()
    errors += validate(model, schemas)
    samples = {}
    for sheet in SHEETS:
        with (root / (sheet + ".csv")).open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            errors.append(f"EMPTY_SOURCE:{sheet}")
        samples[sheet] = {"rows": len(rows), "fields": reader.fieldnames}
    # Negative ontology boundary: a mixed rate-symbol set must never be
    # silently retyped as a subset of the crypto-transaction asset symbols.
    with (root / "exchange_rates.csv").open(newline="", encoding="utf-8-sig") as f:
        rates = {r["asset"] for r in csv.DictReader(f) if r.get("asset")}
    with (root / "crypto_transactions.csv").open(newline="", encoding="utf-8-sig") as f:
        crypto = {r["asset"] for r in csv.DictReader(f) if r.get("asset")}
    category_boundary = {
        "rate_symbols": len(rates),
        "crypto_symbols": len(crypto),
        "rate_symbols_not_in_crypto": sorted(rates - crypto),
        "narrowed_category_allowed": rates.issubset(crypto),
    }
    return model, errors, samples, category_boundary

def main():
    root = Path(".")
    try:
        model, errors, samples, boundary = verify(root)
    except (OSError, KeyError, ValueError, csv.Error) as exc:
        model, samples, boundary = {}, {}, {}
        errors = [f"GATE1_INPUT_UNAVAILABLE:{exc}"]
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_STRUCTURE_AND_NARROW_SEMANTICS" if not errors else "BLOCKED",
        "limits": "No full semantic model evaluation, no Gate 2/3/4 Finding validation",
        "source_check": "PASS_STRUCTURE_AND_SOURCE_ONLY" if not errors else "FAIL_CLOSED",
        "errors": errors,
        "source_summary": samples,
        "relation_category_boundary": boundary,
        "semantic_review": {
            "status": "NEEDS_INDEPENDENT_REVIEW",
            "evidence": ["current DESCRIBE CSVs", "current authorized per-table CSVs"],
        },
    }
    (root / "ontology-gate1.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "gate1-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Fail CLOSED until a separate semantic Gate 1 review is completed.
    # CI materialization smoke tests must not silently become business analysis.
    reason = "GATE1_INDEPENDENT_SEMANTIC_REVIEW_REQUIRED" if not errors else "GATE1_SOURCE_VALIDATION_FAILED"
    (root / "gate1-decision.sql").write_text(f"SELECT error('{reason}');\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2), flush=True)
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())

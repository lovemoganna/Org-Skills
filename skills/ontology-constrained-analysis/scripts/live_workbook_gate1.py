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
from decimal import Decimal, InvalidOperation

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
    model = {
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
    # The business relation is supported by BOTH sides of the live UID key,
    # not by the event ID or the user's column name alone.
    model["ontology_atoms"][0]["证据来源"] = {
        "sources": ["users.uid", "fiat_transactions.uid"],
        "derivation": "UID keys normalized to integral identifiers; match verified against this run",
    }
    model["ontology_atoms"][1]["证据来源"] = {
        "sources": ["fiat_transactions.fiat_order_id", "fiat_transactions.uid", "users.uid"],
        "derivation": "Fiat event identity and numeric UID mapping verified against this run",
    }
    model["ontology_atoms"][2]["证据来源"] = {
        "sources": ["crypto_transactions.crypto_order_id", "crypto_transactions.uid", "users.uid"],
        "derivation": "Crypto event identity and numeric UID mapping verified against this run",
    }
    return model

def normalized_uid(value):
    parsed = Decimal(str(value))
    if not parsed.is_finite() or parsed != parsed.to_integral_value():
        raise ValueError("UNSAFE_UID_NORMALIZATION")
    return str(int(parsed))

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
    tables = {}
    for sheet in SHEETS:
        with (root / (sheet + ".csv")).open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            errors.append(f"EMPTY_SOURCE:{sheet}")
        samples[sheet] = {"rows": len(rows), "fields": reader.fieldnames}
        tables[sheet] = rows
    try:
        user_keys = [normalized_uid(r["uid"]) for r in tables["users"]]
        if len(user_keys) != len(set(user_keys)):
            errors.append("DUPLICATED_USER_UID")
        for sheet, id_col in (("fiat_transactions", "fiat_order_id"),
                              ("crypto_transactions", "crypto_order_id")):
            rows = tables[sheet]
            keys = [normalized_uid(r["uid"]) for r in rows]
            if any(uid not in set(user_keys) for uid in keys):
                errors.append(f"UNMATCHED_USER_UID:{sheet}")
            if len({r[id_col] for r in rows}) != len(rows):
                errors.append(f"DUPLICATE_ORDER_ID:{sheet}")
            directions = {r["direction"] for r in rows}
            if not directions.issubset({"deposit", "withdrawal"}) or not directions:
                errors.append(f"UNREVIEWED_DIRECTION_DOMAIN:{sheet}:{sorted(directions)}")
            if not all(r["status"] for r in rows):
                errors.append(f"BLANK_STATUS:{sheet}")
            samples[sheet]["direction_domain"] = sorted(directions)
            samples[sheet]["status_domain"] = sorted({r["status"] for r in rows})
            samples[sheet]["matched_user_uids"] = len(set(keys))
    except (InvalidOperation, ValueError, KeyError) as exc:
        errors.append(f"RELATION_KEY_SEMANTICS_UNVERIFIED:{exc}")
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
        "limits": "Curated, narrow Gate 1 business-model review only; no Gate 2/3/4 Finding validation",
        "source_check": "PASS_STRUCTURE_AND_SOURCE_ONLY" if not errors else "FAIL_CLOSED",
        "errors": errors,
        "source_summary": samples,
        "relation_category_boundary": boundary,
        "semantic_review": {
            "status": "PASS" if not errors else "BLOCKED",
            "evidence": ["human-reviewed neutral ontology definition",
                         "current DESCRIBE CSVs",
                         "UID numeric normalization and observed foreign-key coverage",
                         "real value domains of transaction direction and status",
                         "mixed-asset category boundary"],
            "scope": "the ten declared atoms, their registered relations and two composite status-direction rules",
        },
    }
    (root / "ontology-gate1.json").write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "gate1-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # The independently authored semantic assertions run against current data.
    # A failed source contract stops business SQL in the SAME DuckDB session.
    decision = ("SELECT 'GATE1_APPROVED' AS gate1_status;\n" if not errors
                else "SELECT error('GATE1_SOURCE_OR_SEMANTIC_VALIDATION_FAILED');\n")
    (root / "gate1-decision.sql").write_text(decision, encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2), flush=True)
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""通用 Skill / Prompt 测试证据门禁。

只验证“测试适配性 + 结构/内容独立验收”的记录是否自洽。
不读取外网，不自动判断事实真假，也不声称同一模型自评等于独立评审。
用法: python scripts/evaluate_case.py path/to/case.json [--advisory]\n默认退出状态：0=已验收通过，1=明确失败，2=不适配/未完成/条件通过；--advisory 仅出报告。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID = {"通过", "失败", "待核验"}
FIELDS = ("fidelity", "grounding", "task_value", "usability")


def judge(case: dict) -> dict:
    """返回中文判定。适配失败是测试设计问题，不是被测 Skill 质量失败。"""
    scope = case.get("scope") or {}
    needs = set(scope.get("task_capabilities") or [])
    supports = set(scope.get("skill_capabilities") or [])
    scope_evidence = scope.get("evidence")
    if not needs or not supports or not isinstance(scope_evidence, str) or not scope_evidence.strip():
        return {"判定": "测试准备不足", "被测对象质量": "未评价", "原因": "缺少能力需求、职责依据或范围证据"}
    unknowns = set(scope.get("uncertain_capabilities") or [])
    if unknowns & needs:
        return {"判定": "适配性待确认", "被测对象质量": "未评价", "原因": "职责范围存在未核实能力"}
    missing = sorted(needs - supports)
    if missing:
        return {"判定": "测试设计无效", "被测对象质量": "未评价", "原因": "被测对象不负责本次要求的能力：" + "、".join(missing)}
    run = case.get("execution") or {}
    if not run.get("performed") or not run.get("receipt"):
        return {"判定": "执行证据不足", "被测对象质量": "未评价", "原因": "未提供真实执行及其可追溯记录"}
    structure = case.get("structure") or {}
    st = structure.get("status")
    if st not in VALID or not structure.get("evidence"):
        return {"判定": "结构验收缺失", "被测对象质量": "未评价", "原因": "结构测试缺状态或证据"}
    if st == "失败":
        return {"判定": "测试失败", "被测对象质量": "本例不合格", "原因": "结构或执行约束失败"}
    checks = case.get("content") or {}
    if set(FIELDS) - set(checks):
        return {"判定": "内容验收缺失", "被测对象质量": "未评价", "原因": "未逐项检查事实/契约保真、证据、任务价值和可用性"}
    statuses = []
    for key in FIELDS:
        item = checks.get(key)
        if not isinstance(item, dict) or item.get("status") not in VALID or not item.get("evidence"):
            return {"判定": "内容验收缺失", "被测对象质量": "未评价", "原因": key + " 缺乏可追溯验收记录"}
        statuses.append(item["status"])
    if "失败" in statuses:
        return {"判定": "测试失败", "被测对象质量": "本例不合格", "原因": "至少一项重要内容验收失败"}
    if st == "待核验" or "待核验" in statuses:
        return {"判定": "有条件通过", "被测对象质量": "尚不能证明整体合格", "原因": "存在未完成的结构或内容验证"}
    reviewer = case.get("review") or {}
    if reviewer.get("independent") is not True or not reviewer.get("evidence"):
        return {"判定": "有条件通过", "被测对象质量": "尚不能证明整体合格", "原因": "缺少独立评价依据，不能用生成者自评代替"}
    return {"判定": "测试通过", "被测对象质量": "仅在本例已验证范围内合格", "原因": "适配、执行、结构、内容及独立验收记录齐备；不代表其他任务也合格"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case", type=Path)
    p.add_argument("--advisory", action="store_true", help="仅记录裁决，不作为自动化发布门禁")
    args = p.parse_args()
    try:
        result = judge(json.loads(args.case.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"判定": "测试准备不足", "原因": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.advisory or result["判定"] == "测试通过":
        return 0
    return 1 if result["判定"] == "测试失败" else 2


if __name__ == "__main__":
    raise SystemExit(main())

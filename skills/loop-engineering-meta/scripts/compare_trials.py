#!/usr/bin/env python3
"""Compare paired baseline/candidate Skill trials by verified outcomes.

This checks evidence-record integrity and simple observed success counts, not the
truth of external artifacts or statistical significance. No model calls.
Exit: 0=improvement candidate; 1=regression or no gain; 2=invalid/incomplete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ARMS = ("baseline", "candidate")
SUITES = {"failure", "regression", "generalization"}
CONTROLS = ("model", "task_input_hash", "tools_hash", "environment_hash", "rubric_hash")
VERIFIERS = {"deterministic", "independent_model", "human"}


class InvalidRecord(ValueError):
    pass


def require(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidRecord(f"{label}: 缺失非空字符串")
    return value.strip()


def compare(data: object) -> dict:
    if not isinstance(data, dict):
        raise InvalidRecord("顶层必须是对象")
    require(data.get("experiment_id"), "experiment_id")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise InvalidRecord("缺少 cases")
    totals = {arm: {"passed": 0, "trials": 0, "cost_usd": 0.0, "cost_recorded": True} for arm in ARMS}
    seen_runs, seen_cases, covered, findings = set(), set(), set(), []
    for case in cases:
        if not isinstance(case, dict):
            raise InvalidRecord("case 必须是对象")
        cid = require(case.get("id"), "case.id")
        if cid in seen_cases:
            raise InvalidRecord(f"重复 case: {cid}")
        seen_cases.add(cid)
        suite = case.get("suite")
        if suite not in SUITES:
            raise InvalidRecord(f"{cid}: 无效 suite")
        covered.add(suite)
        controls = case.get("controls")
        if not isinstance(controls, dict):
            raise InvalidRecord(f"{cid}: 缺少 controls")
        for key in CONTROLS:
            require(controls.get(key), f"{cid}.controls.{key}")
        arms = case.get("trials")
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            raise InvalidRecord(f"{cid}: 必须包含 baseline/candidate 两组")
        counts = {}
        for arm in ARMS:
            trials = arms[arm]
            if not isinstance(trials, list) or len(trials) < 3:
                raise InvalidRecord(f"{cid}/{arm}: 至少三个实际 trial")
            passed = 0
            for trial in trials:
                if not isinstance(trial, dict):
                    raise InvalidRecord(f"{cid}/{arm}: trial 必须是对象")
                rid = require(trial.get("run_id"), "run_id")
                if rid in seen_runs:
                    raise InvalidRecord(f"重复 run_id: {rid}")
                seen_runs.add(rid)
                worker = require(trial.get("worker_id"), f"{rid}.worker_id")
                for key in CONTROLS:
                    if trial.get(key) != controls[key]:
                        raise InvalidRecord(f"{rid}: {key} 不一致，无法控制变量")
                require(trial.get("trace_ref"), f"{rid}.trace_ref")
                require(trial.get("artifact_ref"), f"{rid}.artifact_ref")
                outcome = trial.get("outcome")
                if not isinstance(outcome, dict) or type(outcome.get("passed")) is not bool:
                    raise InvalidRecord(f"{rid}: 缺少布尔结果态")
                require(outcome.get("evidence_ref"), f"{rid}.outcome.evidence_ref")
                verifier = outcome.get("verifier")
                if not isinstance(verifier, dict) or verifier.get("kind") not in VERIFIERS:
                    raise InvalidRecord(f"{rid}: 缺少有效结果态校验者")
                verifier_id = require(verifier.get("id"), f"{rid}.verifier.id")
                if verifier.get("kind") != "deterministic" and verifier_id == worker:
                    raise InvalidRecord(f"{rid}: 主观验收不能由执行者自评")
                cost = trial.get("cost_usd")
                if cost is None:
                    totals[arm]["cost_recorded"] = False
                elif isinstance(cost, bool) or not isinstance(cost, (int, float)) or not (0 <= cost < float("inf")):
                    raise InvalidRecord(f"{rid}: cost_usd 无效")
                else:
                    totals[arm]["cost_usd"] += cost
                totals[arm]["trials"] += 1
                passed += outcome["passed"]
            counts[arm] = passed
        if len(arms["baseline"]) != len(arms["candidate"]):
            raise InvalidRecord(f"{cid}: 两组 trial 数不相等")
        totals["baseline"]["passed"] += counts["baseline"]
        totals["candidate"]["passed"] += counts["candidate"]
        findings.append({"case": cid, "suite": suite, "trials_per_arm": len(arms["baseline"]), "baseline_pass": counts["baseline"], "candidate_pass": counts["candidate"]})
    if covered != SUITES:
        raise InvalidRecord("缺少原失败/历史通过/泛化三类案例: " + ", ".join(sorted(SUITES - covered)))
    regression = any(x["candidate_pass"] < x["baseline_pass"] for x in findings)
    improvement = any(x["suite"] != "regression" and x["candidate_pass"] > x["baseline_pass"] for x in findings)
    for arm in ARMS:
        totals[arm]["success_rate"] = round(totals[arm]["passed"] / totals[arm]["trials"], 4)
        if not totals[arm]["cost_recorded"]:
            totals[arm]["cost_usd"] = None
        else:
            totals[arm]["cost_usd"] = round(totals[arm]["cost_usd"], 6)
    verdict = "发现回归" if regression else "未观察到实质改善" if not improvement else "候选改善（待人工复核）"
    return {"判定": verdict, "统计": totals, "逐案例": findings, "注意": "只核验记录格式与观察到的结果差异；不验证外部证据真实性、评审独立性或统计显著性，不自动批准发布。"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path)
    args = ap.parse_args()
    try:
        result = compare(json.loads(args.path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, InvalidRecord, ValueError, TypeError) as exc:
        print(json.dumps({"判定": "证据不足", "原因": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["判定"].startswith("候选改善") else 1


if __name__ == "__main__":
    raise SystemExit(main())

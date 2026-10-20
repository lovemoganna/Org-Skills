#!/usr/bin/env python3
"""Run L1, L2, and L3 evaluations on existing run outputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from validators.l1_deterministic import validate_l1
from validators.l2_semantic_grader import grade_l2
from validators.l3_task_transfer import evaluate_l3

def evaluate_single_arm(
    arm_name: str,
    case_meta: dict,
    source_text: str,
    arm_dir: Path
) -> dict:
    output_file = arm_dir / "output.md"
    if not output_file.exists():
        raise FileNotFoundError(f"Missing output file: {output_file}")
    output_content = output_file.read_text(encoding="utf-8")

    print(f"    Evaluating {arm_name}...")

    # 1. L1 Deterministic Validation
    l1_res = validate_l1(source_text, output_content, case_meta)
    (arm_dir / "l1_result.json").write_text(json.dumps(l1_res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      L1 Pass: {l1_res['pass']} (Detected: {l1_res['decision_detected']}, Matched: {l1_res['decision_matched']})")

    # Rate limiting pause
    time.sleep(2.0)

    # 2. L2 Semantic Grading (Blind)
    l2_res = grade_l2(source_text, output_content, case_meta)
    (arm_dir / "l2_result.json").write_text(json.dumps(l2_res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      L2 Score: {l2_res.get('total_score', 0)}/10 (Hard Failure: {l2_res.get('hard_failure', False)})")

    # Rate limiting pause
    time.sleep(2.0)

    # 3. L3 Downstream Task Transfer
    l3_res = evaluate_l3(output_content, case_meta.get("reader_tasks", []))
    (arm_dir / "l3_result.json").write_text(json.dumps(l3_res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      L3 Accuracy: {l3_res.get('accuracy', 0.0)*100:.1f}% ({l3_res.get('passed_count', 0)}/{l3_res.get('total_count', 0)})")

    metrics = {
        "arm": arm_name,
        "l1_pass": l1_res["pass"],
        "decision_detected": l1_res["decision_detected"],
        "decision_matched": l1_res["decision_matched"],
        "l2_total_score": l2_res.get("total_score", 0),
        "l2_scores": l2_res.get("scores", {}),
        "l2_hard_failure": l2_res.get("hard_failure", False),
        "l3_accuracy": l3_res.get("accuracy", 0.0),
        "l3_passed": l3_res.get("passed_count", 0),
        "l3_total": l3_res.get("total_count", 0),
        "output_chars": len(output_content)
    }
    (arm_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics

def evaluate_run(run_id: str):
    run_dir = EVALS_DIR / "runs" / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run dir does not exist: {run_dir}")

    cases_dir = EVALS_DIR / "cases"
    case_subdirs = [d for d in sorted(run_dir.glob("case_*")) if d.is_dir()]

    print(f"=== Evaluating Run: {run_id} ({len(case_subdirs)} cases) ===")
    results = []

    for cdir in case_subdirs:
        cid = cdir.name
        cfile = cases_dir / f"{cid}.yaml"
        case_meta = yaml.safe_load(cfile.read_text(encoding="utf-8"))
        snapshot_path = REPO_ROOT / case_meta["snapshot_file"]
        source_text = snapshot_path.read_text(encoding="utf-8")

        print(f"\n--> Case: {cid} (Expected: {case_meta.get('expected_decision')})")

        arm_a = evaluate_single_arm("arm_a_baseline", case_meta, source_text, cdir / "arm_a_baseline")
        arm_b = evaluate_single_arm("arm_b_skill", case_meta, source_text, cdir / "arm_b_skill")

        comparison = {
            "case_id": cid,
            "expected_decision": case_meta.get("expected_decision"),
            "arm_a_baseline": arm_a,
            "arm_b_skill": arm_b,
            "delta": {
                "l2_score_diff": arm_b["l2_total_score"] - arm_a["l2_total_score"],
                "l3_accuracy_diff": round(arm_b["l3_accuracy"] - arm_a["l3_accuracy"], 3),
                "char_length_diff": arm_b["output_chars"] - arm_a["output_chars"]
            }
        }
        (cdir / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(comparison)

    # Aggregates
    n = len(results)
    a_l1 = sum(1 for r in results if r["arm_a_baseline"]["l1_pass"])
    b_l1 = sum(1 for r in results if r["arm_b_skill"]["l1_pass"])
    a_dec = sum(1 for r in results if r["arm_a_baseline"]["decision_matched"])
    b_dec = sum(1 for r in results if r["arm_b_skill"]["decision_matched"])
    a_l2 = round(sum(r["arm_a_baseline"]["l2_total_score"] for r in results) / n, 2)
    b_l2 = round(sum(r["arm_b_skill"]["l2_total_score"] for r in results) / n, 2)
    a_l3 = round(sum(r["arm_a_baseline"]["l3_accuracy"] for r in results) / n, 3)
    b_l3 = round(sum(r["arm_b_skill"]["l3_accuracy"] for r in results) / n, 3)
    a_l3_passed = sum(r["arm_a_baseline"]["l3_passed"] for r in results)
    a_l3_total = sum(r["arm_a_baseline"]["l3_total"] for r in results)
    b_l3_passed = sum(r["arm_b_skill"]["l3_passed"] for r in results)
    b_l3_total = sum(r["arm_b_skill"]["l3_total"] for r in results)
    a_pooled_l3 = round(a_l3_passed / a_l3_total, 3) if a_l3_total else 0
    b_pooled_l3 = round(b_l3_passed / b_l3_total, 3) if b_l3_total else 0

    summary = {
        "run_id": run_id,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": n,
        "arm_a_baseline": {
            "l1_pass_rate": f"{a_l1}/{n} ({a_l1/n*100:.1f}%)",
            "decision_accuracy": f"{a_dec}/{n} ({a_dec/n*100:.1f}%)",
            "avg_l2_score": a_l2,
            "avg_l3_accuracy": a_l3,
            "pooled_l3_task_accuracy": a_pooled_l3,
            "l3_tasks": f"{a_l3_passed}/{a_l3_total}"
        },
        "arm_b_skill": {
            "l1_pass_rate": f"{b_l1}/{n} ({b_l1/n*100:.1f}%)",
            "decision_accuracy": f"{b_dec}/{n} ({b_dec/n*100:.1f}%)",
            "avg_l2_score": b_l2,
            "avg_l3_accuracy": b_l3,
            "pooled_l3_task_accuracy": b_pooled_l3,
            "l3_tasks": f"{b_l3_passed}/{b_l3_total}"
        },
        "deltas": {
            "l1_pass_diff": f"{(b_l1 - a_l1):+d}",
            "decision_accuracy_diff": f"{(b_dec - a_dec):+d}",
            "l2_score_gain": round(b_l2 - a_l2, 2),
            "l3_accuracy_gain": round(b_l3 - a_l3, 3),
            "l3_pooled_task_accuracy_gain": round(b_pooled_l3 - a_pooled_l3, 3)
        },
        "case_summaries": results
    }

    summary_file = run_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n==================================================")
    print(f"Summary for Run {run_id}:")
    print(f"Arm A Baseline: Decision Acc {summary['arm_a_baseline']['decision_accuracy']}, L1 {summary['arm_a_baseline']['l1_pass_rate']}, L2 {a_l2}/10, L3 Macro {a_l3*100:.1f}%, L3 Pooled {a_pooled_l3*100:.1f}% ({a_l3_passed}/{a_l3_total})")
    print(f"Arm B Skill   : Decision Acc {summary['arm_b_skill']['decision_accuracy']}, L1 {summary['arm_b_skill']['l1_pass_rate']}, L2 {b_l2}/10, L3 Macro {b_l3*100:.1f}%, L3 Pooled {b_pooled_l3*100:.1f}% ({b_l3_passed}/{b_l3_total})")
    print(f"Net Gain      : L3 Macro {summary['deltas']['l3_accuracy_gain']*100:+.1f}%, L3 Pooled {summary['deltas']['l3_pooled_task_accuracy_gain']*100:+.1f}%, L2 Gain: {summary['deltas']['l2_score_gain']:+.2f}")
    print(f"==================================================")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id", type=str)
    args = parser.parse_args()
    evaluate_run(args.run_id)

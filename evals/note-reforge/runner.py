#!/usr/bin/env python3
"""A/B Experiment Runner for note-reforge evaluations.

Executes controlled trials:
- Arm A (Baseline): standard prompt, no skill loaded.
- Arm B (With Skill): canonical skills/note-reforge/SKILL.md loaded.

Applies L1, L2, L3 evaluation layers to both arms.
Outputs reproducible results, timing, token usage and capability comparisons.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = REPO_ROOT / "evals" / "note-reforge"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from llm_client import call_llm
from validators.l1_deterministic import validate_l1
from validators.l2_semantic_grader import grade_l2
from validators.l3_task_transfer import evaluate_l3

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD_PATH = REPO_ROOT / "skills" / "note-reforge" / "SKILL.md"
EVALS_DIR = REPO_ROOT / "evals" / "note-reforge"

BASELINE_SYSTEM_PROMPT = """你是一个严谨的 AI 助手。请根据用户任务和提供的原始文档执行任务。
要求：
- 遵守事实，不编造作者经验、项目数据或实测结论。
- 保留原文档的所有代码块、链接、重要参数和受保护配置。
- 如果原文已足够充分或找不到有依据的增量，请原样保留，不要制造无意义的改写；若存在严重冲突或事实缺失，请说明阻塞。
"""

def load_canonical_skill() -> str:
    return SKILL_MD_PATH.read_text(encoding="utf-8")

def run_single_arm(
    arm_name: str,
    case_meta: dict,
    source_text: str,
    run_dir: Path,
    skill_text: str | None = None
) -> dict:
    arm_dir = run_dir / arm_name
    arm_dir.mkdir(parents=True, exist_ok=True)

    task_prompt = f"""【用户任务】
{case_meta.get('task', '')}

【输入文档全文】
```
{source_text}
```

请根据你的规范执行此任务。严格给出你的决策（KEEP / PATCH / REFORGE / BLOCK）以及相应产物或理由。"""

    if arm_name == "arm_b_skill":
        system_prompt = f"你是具备以下 Skill 规范的专门 AI Agent:\n\n{skill_text}\n"
    else:
        system_prompt = BASELINE_SYSTEM_PROMPT

    llm_res = call_llm(task_prompt, system_prompt=system_prompt, temperature=0.0)
    output_content = llm_res["content"]

    output_file = arm_dir / "output.md"
    output_file.write_text(output_content, encoding="utf-8")

    # Run L1
    l1_res = validate_l1(source_text, output_content, case_meta)
    (arm_dir / "l1_result.json").write_text(json.dumps(l1_res, ensure_ascii=False, indent=2), encoding="utf-8")

    # Run L2 (Semantic Grader)
    l2_res = grade_l2(source_text, output_content, case_meta)
    (arm_dir / "l2_result.json").write_text(json.dumps(l2_res, ensure_ascii=False, indent=2), encoding="utf-8")

    # Run L3 (Reader Task Transfer)
    l3_res = evaluate_l3(output_content, case_meta.get("reader_tasks", []))
    (arm_dir / "l3_result.json").write_text(json.dumps(l3_res, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "arm": arm_name,
        "model": llm_res["model"],
        "latency_sec": llm_res["latency_sec"],
        "tokens": {
            "prompt": llm_res["prompt_tokens"],
            "completion": llm_res["completion_tokens"],
            "total": llm_res["total_tokens"]
        },
        "l1_pass": l1_res["pass"],
        "decision_detected": l1_res["decision_detected"],
        "decision_matched": l1_res["decision_matched"],
        "l2_total_score": l2_res.get("total_score", 0),
        "l2_hard_failure": l2_res.get("hard_failure", False),
        "l3_accuracy": l3_res.get("accuracy", 0.0),
        "l3_passed": l3_res.get("passed_count", 0),
        "l3_total": l3_res.get("total_count", 0)
    }

    (arm_dir / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary

def run_case_ab(case_file: Path, output_root: Path, skill_text: str) -> dict:
    case_meta = yaml.safe_load(case_file.read_text(encoding="utf-8"))
    cid = case_meta["case_id"]
    snapshot_path = REPO_ROOT / case_meta["snapshot_file"]
    source_text = snapshot_path.read_text(encoding="utf-8")

    case_run_dir = output_root / cid
    case_run_dir.mkdir(parents=True, exist_ok=True)

    print(f"--> Running Case: {cid} (Expected: {case_meta.get('expected_decision')})")

    # Run Arm A (Baseline)
    arm_a = run_single_arm("arm_a_baseline", case_meta, source_text, case_run_dir)
    print(f"    [Arm A Baseline] Dec: {arm_a['decision_detected']}, L1: {arm_a['l1_pass']}, L2: {arm_a['l2_total_score']}/10, L3: {arm_a['l3_accuracy']*100:.1f}%, Tokens: {arm_a['tokens']['total']}")

    # Run Arm B (With Skill)
    arm_b = run_single_arm("arm_b_skill", case_meta, source_text, case_run_dir, skill_text=skill_text)
    print(f"    [Arm B Skill   ] Dec: {arm_b['decision_detected']}, L1: {arm_b['l1_pass']}, L2: {arm_b['l2_total_score']}/10, L3: {arm_b['l3_accuracy']*100:.1f}%, Tokens: {arm_b['tokens']['total']}")

    comparison = {
        "case_id": cid,
        "expected_decision": case_meta.get("expected_decision"),
        "is_held_out": case_meta.get("is_held_out", False),
        "arm_a_baseline": arm_a,
        "arm_b_skill": arm_b,
        "delta": {
            "l2_score_diff": arm_b["l2_total_score"] - arm_a["l2_total_score"],
            "l3_accuracy_diff": round(arm_b["l3_accuracy"] - arm_a["l3_accuracy"], 3),
            "tokens_diff": arm_b["tokens"]["total"] - arm_a["tokens"]["total"],
            "latency_diff": round(arm_b["latency_sec"] - arm_a["latency_sec"], 3)
        }
    }
    (case_run_dir / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    return comparison

def main():
    parser = argparse.ArgumentParser(description="note-reforge A/B Evaluation Runner")
    parser.add_argument("--cases", nargs="*", help="Specific case IDs to run")
    parser.add_argument("--smoke", action="store_true", help="Run 4-case smoke test (1 KEEP, 1 PATCH, 1 REFORGE, 1 BLOCK)")
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()

    run_id = args.run_id or datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")
    run_dir = EVALS_DIR / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    skill_text = load_canonical_skill()

    cases_dir = EVALS_DIR / "cases"
    manifest = json.loads((cases_dir / "dataset_manifest.json").read_text(encoding="utf-8"))

    if args.smoke:
        # Pick 1 of each decision type
        target_case_ids = [
            "case_01_keep_recursive_discovery",
            "case_07_patch_project_operations",
            "case_15_reforge_agent_automations",
            "case_19_block_unverifiable_source_fabrication"
        ]
    elif args.cases:
        target_case_ids = args.cases
    else:
        # Run all non-held-out cases by default
        target_case_ids = [c["case_id"] for c in manifest["cases"] if not c["held_out"]]

    print(f"=== Starting note-reforge A/B Eval Run: {run_id} ===")
    print(f"Cases to evaluate ({len(target_case_ids)}): {target_case_ids}\n")

    results = []
    for cid in target_case_ids:
        cfile = cases_dir / f"{cid}.yaml"
        if not cfile.exists():
            print(f"Warning: case file not found: {cfile}")
            continue
        comp = run_case_ab(cfile, run_dir, skill_text)
        results.append(comp)

    # Aggregate statistics
    a_l1_passes = sum(1 for r in results if r["arm_a_baseline"]["l1_pass"])
    b_l1_passes = sum(1 for r in results if r["arm_b_skill"]["l1_pass"])
    a_dec_matches = sum(1 for r in results if r["arm_a_baseline"]["decision_matched"])
    b_dec_matches = sum(1 for r in results if r["arm_b_skill"]["decision_matched"])
    a_avg_l2 = round(sum(r["arm_a_baseline"]["l2_total_score"] for r in results) / len(results), 2) if results else 0
    b_avg_l2 = round(sum(r["arm_b_skill"]["l2_total_score"] for r in results) / len(results), 2) if results else 0
    a_avg_l3 = round(sum(r["arm_a_baseline"]["l3_accuracy"] for r in results) / len(results), 3) if results else 0
    b_avg_l3 = round(sum(r["arm_b_skill"]["l3_accuracy"] for r in results) / len(results), 3) if results else 0
    a_avg_tokens = round(sum(r["arm_a_baseline"]["tokens"]["total"] for r in results) / len(results)) if results else 0
    b_avg_tokens = round(sum(r["arm_b_skill"]["tokens"]["total"] for r in results) / len(results)) if results else 0

    run_summary = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases_evaluated": len(results),
        "model": "qwen/qwen3.8-27b",
        "temperature": 0.0,
        "aggregate_metrics": {
            "arm_a_baseline": {
                "l1_pass_rate": f"{a_l1_passes}/{len(results)} ({a_l1_passes/len(results)*100:.1f}%)" if results else 0,
                "decision_accuracy": f"{a_dec_matches}/{len(results)} ({a_dec_matches/len(results)*100:.1f}%)" if results else 0,
                "avg_l2_score": a_avg_l2,
                "avg_l3_accuracy": a_avg_l3,
                "avg_tokens": a_avg_tokens
            },
            "arm_b_skill": {
                "l1_pass_rate": f"{b_l1_passes}/{len(results)} ({b_l1_passes/len(results)*100:.1f}%)" if results else 0,
                "decision_accuracy": f"{b_dec_matches}/{len(results)} ({b_dec_matches/len(results)*100:.1f}%)" if results else 0,
                "avg_l2_score": b_avg_l2,
                "avg_l3_accuracy": b_avg_l3,
                "avg_tokens": b_avg_tokens
            },
            "deltas": {
                "l2_score_gain": round(b_avg_l2 - a_avg_l2, 2),
                "l3_accuracy_gain": round(b_avg_l3 - a_avg_l3, 3),
                "token_increase_pct": f"{((b_avg_tokens - a_avg_tokens) / a_avg_tokens * 100):.1f}%" if a_avg_tokens else "N/A"
            }
        },
        "cases": results
    }

    summary_file = run_dir / "summary.json"
    summary_file.write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Run Completed! Summary saved to {summary_file} ===")
    print(f"Arm A Baseline: Decision Acc {run_summary['aggregate_metrics']['arm_a_baseline']['decision_accuracy']}, L3 Acc {a_avg_l3*100:.1f}%, Tokens {a_avg_tokens}")
    print(f"Arm B Skill   : Decision Acc {run_summary['aggregate_metrics']['arm_b_skill']['decision_accuracy']}, L3 Acc {b_avg_l3*100:.1f}%, Tokens {b_avg_tokens}")
    print(f"Delta: L3 Gain: {run_summary['aggregate_metrics']['deltas']['l3_accuracy_gain']*100:+.1f}%, Token Overhead: {run_summary['aggregate_metrics']['deltas']['token_increase_pct']}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Trigger: held-out Copilot run 2026-10-20.
"""Prepare and summarize sealed note-reforge held-out A/B runs via Copilot CLI.

The subject prompts intentionally exclude expected decisions, reader-task answers,
acceptance criteria, hard-fail conditions, and previous evaluation outputs.
Semantic/L3 grading is performed separately after raw outputs exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import sys

import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
SKILL_PATH = EVALS_DIR.parent / "SKILL.md"
OUT_DIR = EVALS_DIR / "runs" / "supplemental_heldout_copilot_20261020"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from validators.l1_deterministic import validate_l1

CASES = [
    "case_21_heldout_patch_missing_navigation_mutation",
    "case_22_heldout_reforge_flattened_atlas_mutation",
]

BASELINE_RULES = """你是一个严谨的 AI 助手。请根据用户任务和原始文档执行任务。
- 遵守事实，不编造作者经验、项目数据或实测结论。
- 保留原文档代码块、链接、重要参数和受保护配置。
- 原文已经充分时不要制造无意义改写；存在严重冲突或事实缺失时明确阻塞。
- 不访问仓库、网络或任何工具；只使用本提示内给出的文本。
"""


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def subject_prompt(rules: str, task: str, source: str) -> str:
    return f"""【唯一执行规范】
{rules}

【用户任务】
{task}

【输入文档全文】
```
{source}
```

请独立完成任务。
禁止假设存在隐藏答案、隐藏评测标准或额外事实。
必须明确给出决策（KEEP / PATCH / REFORGE / BLOCK）以及相应最终产物或阻塞理由。
只输出最终结果，不输出自我评价、测试分数或对照分析。
"""


def load_case(case_id: str) -> tuple[dict, str]:
    case_path = EVALS_DIR / "cases" / f"{case_id}.yaml"
    meta = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    if not meta.get("is_held_out"):
        raise RuntimeError(f"CASE_NOT_HELD_OUT:{case_id}")
    snapshot_rel = str(meta["snapshot_file"]).replace("\\", "/")
    source_path = REPO_ROOT / snapshot_rel
    return meta, source_path.read_text(encoding="utf-8")


def prepare() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    skill = SKILL_PATH.read_text(encoding="utf-8")
    run = {
        "run_id": "supplemental_heldout_copilot_20261020",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "mode": "sealed_heldout_subject_ab",
        "executor": "GitHub Copilot CLI",
        "model": "ACCOUNT_DEFAULT_UNPINNED",
        "cases": CASES,
        "subject_requests_expected": len(CASES) * 2,
        "subject_requests_completed": 0,
        "status": "PREPARED",
        "limitations": [
            "Copilot account default model is not pinned or independently identified.",
            "Baseline and Skill arms use separate COPILOT_HOME sessions.",
            "Held-out answer keys and acceptance metadata are excluded from subject prompts.",
            "Semantic/L3 judging is separate from subject generation.",
        ],
        "results": [],
    }

    for case_id in CASES:
        meta, source = load_case(case_id)
        case_dir = OUT_DIR / case_id
        for arm, rules in (
            ("arm_a_baseline", BASELINE_RULES),
            ("arm_b_skill", "你是具备以下 canonical note-reforge Skill 的专门 Agent。\n\n" + skill),
        ):
            arm_dir = case_dir / arm
            arm_dir.mkdir(parents=True, exist_ok=True)
            prompt = subject_prompt(rules, meta.get("task", ""), source)
            (arm_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    write_json(OUT_DIR / "run.json", run)
    print(json.dumps({"status": "PREPARED", "cases": len(CASES), "requests": len(CASES) * 2}, ensure_ascii=False))
    return 0


def summarize() -> int:
    run_path = OUT_DIR / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    results = []
    completed = 0
    errors = []

    for case_id in CASES:
        meta, source = load_case(case_id)
        case_record = {"case_id": case_id, "arms": {}}
        for arm in ("arm_a_baseline", "arm_b_skill"):
            arm_dir = OUT_DIR / case_id / arm
            output_path = arm_dir / "output.md"
            if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
                case_record["arms"][arm] = {"status": "MISSING_OUTPUT"}
                errors.append([case_id, arm, "MISSING_OUTPUT"])
                continue
            output = output_path.read_text(encoding="utf-8")
            l1 = validate_l1(source, output, meta)
            write_json(arm_dir / "l1_result.json", l1)
            case_record["arms"][arm] = {
                "status": "EXECUTED",
                "output_chars": len(output),
                "l1": l1,
            }
            completed += 1
        results.append(case_record)

    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    run["subject_requests_completed"] = completed
    run["results"] = results
    run["errors"] = errors
    run["status"] = "EXECUTED_L1_ONLY" if completed == len(CASES) * 2 and not errors else "PARTIAL"
    write_json(run_path, run)
    print(json.dumps({
        "status": run["status"],
        "completed": completed,
        "expected": len(CASES) * 2,
        "errors": errors,
    }, ensure_ascii=False))
    return 0 if run["status"] == "EXECUTED_L1_ONLY" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "summarize"))
    args = parser.parse_args()
    return prepare() if args.mode == "prepare" else summarize()


if __name__ == "__main__":
    raise SystemExit(main())

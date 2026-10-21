#!/usr/bin/env python3
"""Sealed six-case regression for note-reforge KEEP/REFORGE candidate.

Compares frozen production Skill at commit 7674cf109ecfd69b59f8aeb3843742a3d9897db5
against the candidate branch Skill. Subject prompts receive only the selected Skill,
the user task, and the frozen/mutated source document. Answer keys and historical
adjudications are excluded until after raw outputs exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
SKILL_PATH = EVALS_DIR.parent / "SKILL.md"
OUT_DIR = EVALS_DIR / "runs" / "candidate_keep_reforge_20261021"
PRODUCTION_COMMIT = "7674cf109ecfd69b59f8aeb3843742a3d9897db5"
PRODUCTION_SKILL_PATH = "skills/note-reforge/SKILL.md"

if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from validators.l1_deterministic import validate_l1

CASES = [
    "case_06_heldout_keep_sql_blind_cases",
    "case_14_heldout_patch_thinking_reconstruction",
    "case_18_heldout_reforge_xianxia_talismans",
    "case_20_heldout_block_irreconcilable_contradiction",
    "case_21_heldout_patch_missing_navigation_mutation",
    "case_22_heldout_reforge_flattened_atlas_mutation",
]

ARMS = ("arm_a_production", "arm_b_candidate")
DECISION_RE = re.compile(r"\b(KEEP|PATCH|REFORGE|BLOCK)\b", re.IGNORECASE)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def load_production_skill() -> str:
    proc = subprocess.run(
        ["git", "show", f"{PRODUCTION_COMMIT}:{PRODUCTION_SKILL_PATH}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


def load_case(case_id: str) -> tuple[dict, str, Path]:
    case_path = EVALS_DIR / "cases" / f"{case_id}.yaml"
    meta = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    if not meta.get("is_held_out"):
        raise RuntimeError(f"CASE_NOT_HELD_OUT:{case_id}")
    snapshot_rel = str(meta["snapshot_file"]).replace("\\", "/")
    source_path = REPO_ROOT / snapshot_rel
    source = source_path.read_text(encoding="utf-8")
    return meta, source, source_path


def subject_prompt(skill: str, task: str, source: str) -> str:
    return f"""【唯一执行规范】
你是具备以下 note-reforge Skill 规范的专门 Agent。

{skill}

【用户任务】
{task}

【输入文档全文】
```
{source}
```

请独立完成任务。
禁止假设存在隐藏答案、隐藏评测标准、历史裁决或额外事实。
必须明确给出决策（KEEP / PATCH / REFORGE / BLOCK）以及相应最终产物或阻塞理由。
只输出最终结果，不输出自我评价、测试分数或 A/B 对照分析。
"""


def prepare() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    production = load_production_skill()
    candidate = SKILL_PATH.read_text(encoding="utf-8")
    if production == candidate:
        raise RuntimeError("CANDIDATE_EQUALS_PRODUCTION")

    run = {
        "run_id": "candidate_keep_reforge_20261021",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "mode": "sealed_production_vs_candidate_six_case_regression",
        "executor": "GitHub Copilot CLI",
        "subject_model": "ACCOUNT_DEFAULT_UNPINNED",
        "production_commit": PRODUCTION_COMMIT,
        "production_skill_sha256": sha256_text(production),
        "candidate_skill_sha256": sha256_text(candidate),
        "cases": CASES,
        "subject_requests_expected": len(CASES) * len(ARMS),
        "subject_requests_completed": 0,
        "status": "PREPARED",
        "anti_leakage": [
            "Subject prompts contain only Skill text, task text, and source document.",
            "Expected decisions, reader-task answers, acceptance criteria, hard-fail conditions, prior outputs, and prior adjudications are excluded from subject prompts.",
            "Production and candidate arms use separate COPILOT_HOME sessions.",
        ],
        "limitations": [
            "Copilot account default model is not pinned or independently identified.",
            "case_21 and case_22 are deterministic mutations of real historical snapshots.",
            "Semantic adjudication is performed only after raw subject outputs are preserved.",
        ],
        "results": [],
    }

    for case_id in CASES:
        meta, source, source_path = load_case(case_id)
        for arm, skill in (
            ("arm_a_production", production),
            ("arm_b_candidate", candidate),
        ):
            arm_dir = OUT_DIR / case_id / arm
            arm_dir.mkdir(parents=True, exist_ok=True)
            prompt = subject_prompt(skill, meta.get("task", ""), source)
            (arm_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
            write_json(
                arm_dir / "input_receipt.json",
                {
                    "case_id": case_id,
                    "arm": arm,
                    "source_path": str(source_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "source_sha256": sha256_text(source),
                    "skill_sha256": sha256_text(skill),
                    "expected_decision_hidden_from_subject": True,
                },
            )

    write_json(OUT_DIR / "run.json", run)
    print(json.dumps({"status": "PREPARED", "cases": len(CASES), "requests": len(CASES) * 2}, ensure_ascii=False))
    return 0


def summarize() -> int:
    run_path = OUT_DIR / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    results = []
    errors = []
    completed = 0

    for case_id in CASES:
        meta, source, _ = load_case(case_id)
        case_record = {
            "case_id": case_id,
            "expected_decision": meta.get("expected_decision"),
            "arms": {},
        }
        for arm in ARMS:
            arm_dir = OUT_DIR / case_id / arm
            output_path = arm_dir / "output.md"
            if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
                case_record["arms"][arm] = {"status": "MISSING_OUTPUT"}
                errors.append([case_id, arm, "MISSING_OUTPUT"])
                continue

            output = output_path.read_text(encoding="utf-8")
            decisions = DECISION_RE.findall(output[:1500])
            detected = decisions[0].upper() if decisions else "UNKNOWN"
            l1 = validate_l1(source, output, meta)
            write_json(arm_dir / "l1_result.json", l1)
            case_record["arms"][arm] = {
                "status": "EXECUTED",
                "output_chars": len(output),
                "output_sha256": sha256_text(output),
                "detected_decision": detected,
                "decision_matches_expected": detected == str(meta.get("expected_decision", "")).upper(),
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
        "decision_matches": {
            arm: sum(
                1
                for case in results
                if case["arms"].get(arm, {}).get("decision_matches_expected")
            )
            for arm in ARMS
        },
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

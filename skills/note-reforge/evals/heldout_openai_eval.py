#!/usr/bin/env python3
# Trigger marker: harness is now on main.
"""Run the sealed note-reforge held-out A/B subject trial with OpenAI Responses API.

Subject calls never receive expected decisions, reader-task answers, acceptance
criteria, hard-fail conditions, or prior eval outputs. Evaluation metadata is used
only after subject output exists, for deterministic L1 checks.

This script deliberately does NOT use an LLM judge. Semantic/L3 adjudication is
performed separately so subject generation and evaluation evidence remain separable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
SKILL_PATH = EVALS_DIR.parent / "SKILL.md"
OUT_DIR = EVALS_DIR / "runs" / "heldout_openai_20261020"
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

from validators.l1_deterministic import validate_l1

CASES = [
    "case_06_heldout_keep_sql_blind_cases",
    "case_14_heldout_patch_thinking_reconstruction",
    "case_18_heldout_reforge_xianxia_talismans",
    "case_20_heldout_block_irreconcilable_contradiction",
]

BASELINE_SYSTEM_PROMPT = """你是一个严谨的 AI 助手。请根据用户任务和提供的原始文档执行任务。
要求：
- 遵守事实，不编造作者经验、项目数据或实测结论。
- 保留原文档的所有代码块、链接、重要参数和受保护配置。
- 如果原文已足够充分或找不到有依据的增量，请原样保留，不制造无意义改写；若存在严重冲突或事实缺失，请说明阻塞。
"""

PREFERRED_MODELS = [
    "gpt-5.6",
    "gpt-5.4",
    "gpt-5.2",
    "gpt-5.1",
    "gpt-5",
    "gpt-5-mini",
]


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def choose_model(client) -> tuple[str, list[str]]:
    forced = os.environ.get("NOTE_REFORGE_EVAL_MODEL", "").strip()
    model_ids = sorted({m.id for m in client.models.list().data})
    if forced:
        if forced not in model_ids:
            raise RuntimeError(f"REQUESTED_MODEL_NOT_AVAILABLE:{forced}")
        return forced, model_ids

    for candidate in PREFERRED_MODELS:
        if candidate in model_ids:
            return candidate, model_ids

    gpt5 = [
        m for m in model_ids
        if m.startswith("gpt-5")
        and not any(x in m.lower() for x in ("audio", "image", "realtime", "transcribe", "tts"))
    ]
    if gpt5:
        return gpt5[-1], model_ids
    raise RuntimeError("NO_GPT5_FAMILY_MODEL_AVAILABLE")


def call_subject(client, model: str, instructions: str, prompt: str) -> dict:
    started = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=prompt,
        max_output_tokens=16000,
    )
    usage = getattr(response, "usage", None)
    return {
        "response_id": getattr(response, "id", None),
        "model": model,
        "output_text": response.output_text,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "usage": {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    run = {
        "run_id": "heldout_openai_20261020",
        "started_at": started_at,
        "mode": "sealed_heldout_subject_ab",
        "cases": CASES,
        "subject_requests_expected": len(CASES) * 2,
        "subject_requests_completed": 0,
        "status": "STARTED",
        "model": None,
        "limitations": [
            "Held-out expected answers and acceptance metadata are not passed to subject calls.",
            "This run performs subject generation plus deterministic L1 only; semantic/L3 judging is separate.",
            "A single selected model is pinned for both baseline and Skill arms.",
        ],
        "results": [],
    }

    if not os.environ.get("OPENAI_API_KEY"):
        run["status"] = "BLOCKED_API_CREDENTIAL_REQUIRED"
        write_json(OUT_DIR / "run.json", run)
        return 2

    try:
        from openai import OpenAI

        client = OpenAI(timeout=180, max_retries=2)
        model, available = choose_model(client)
        run["model"] = model
        run["available_gpt5_candidates"] = [
            m for m in available
            if m.startswith("gpt-5")
            and not any(x in m.lower() for x in ("audio", "image", "realtime", "transcribe", "tts"))
        ]
        skill_text = SKILL_PATH.read_text(encoding="utf-8")

        for case_id in CASES:
            case_path = EVALS_DIR / "cases" / f"{case_id}.yaml"
            meta = yaml.safe_load(case_path.read_text(encoding="utf-8"))
            if not meta.get("is_held_out"):
                raise RuntimeError(f"CASE_NOT_HELD_OUT:{case_id}")
            source_path = REPO_ROOT / meta["snapshot_file"]
            source_text = source_path.read_text(encoding="utf-8")
            prompt = f"""【用户任务】
{meta.get("task", "")}

【输入文档全文】
```
{source_text}
```

请独立完成任务。不要假设存在任何隐藏的参考答案或评测标准。
必须明确给出决策（KEEP / PATCH / REFORGE / BLOCK）以及相应最终产物或阻塞理由。
"""

            case_record = {"case_id": case_id, "arms": {}}
            for arm in ("arm_a_baseline", "arm_b_skill"):
                arm_dir = OUT_DIR / case_id / arm
                arm_dir.mkdir(parents=True, exist_ok=True)
                instructions = (
                    BASELINE_SYSTEM_PROMPT
                    if arm == "arm_a_baseline"
                    else "你是具备以下 canonical note-reforge Skill 规范的专门 AI Agent：\n\n" + skill_text
                )
                try:
                    subject = call_subject(client, model, instructions, prompt)
                    output = subject.pop("output_text")
                    (arm_dir / "output.md").write_text(output, encoding="utf-8")
                    l1 = validate_l1(source_text, output, meta)
                    write_json(arm_dir / "l1_result.json", l1)
                    write_json(arm_dir / "subject_metadata.json", subject)
                    case_record["arms"][arm] = {
                        "status": "EXECUTED",
                        "l1": l1,
                        "subject_metadata": subject,
                    }
                    run["subject_requests_completed"] += 1
                except Exception as exc:
                    err = {"status": "ERROR", "error": str(exc)[:700]}
                    write_json(arm_dir / "error.json", err)
                    case_record["arms"][arm] = err

            run["results"].append(case_record)
            write_json(OUT_DIR / "run.json", run)

        errors = [
            (r["case_id"], arm)
            for r in run["results"]
            for arm, info in r["arms"].items()
            if info.get("status") != "EXECUTED"
        ]
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
        run["status"] = "EXECUTED_L1_ONLY" if not errors else "PARTIAL"
        run["errors"] = errors
        write_json(OUT_DIR / "run.json", run)
        print(json.dumps({
            "status": run["status"],
            "model": run["model"],
            "completed": run["subject_requests_completed"],
            "expected": run["subject_requests_expected"],
            "errors": errors,
        }, ensure_ascii=False))
        return 0 if not errors else 2
    except Exception as exc:
        run["status"] = "BLOCKED"
        run["error"] = str(exc)[:700]
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
        write_json(OUT_DIR / "run.json", run)
        print("HELDOUT_EVAL_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

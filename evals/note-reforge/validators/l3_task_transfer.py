#!/usr/bin/env python3
"""L3 Downstream Reader Task Validator for note-reforge outputs.

Evaluates whether an independent reader, having access ONLY to the output document,
can successfully complete concrete operational questions / decisions.
Calculates downstream task accuracy rate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = REPO_ROOT / "evals" / "note-reforge"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from llm_client import call_llm

L3_READER_PROMPT = """你是一名根据技术文档执行具体运维与业务任务的工程师。
你只能根据提供的【文档内容】回答指定的【业务问题】。
要求：
1. 直接给出明确的事实与行动判断。
2. 指出文档中支持你判断的具体证据文字或位置。
3. 如果文档中未提及、缺少条件或存在不确定性，如实说明“文档未提供/无法判断”，禁止臆测。

必须输出严格 JSON 格式：
{
  "answers": [
    {
      "task_id": "T1",
      "answer": "你的直接结论与操作判断",
      "evidence_location": "文档中的原句或证据段落",
      "rationale": "为什么这样判断"
    }
  ]
}
"""

L3_JUDGE_PROMPT = """你是一名独立的评测裁判。
请对比【读者基于文档给出的回答】与【标准参考答案】，判定该读者任务是否成功通过。
判定原则：
- PASS（通过）：核心事实与操作判断正确，证据真实存在于文档中，未出现致命误导或未授权臆测。
- FAIL（未通过）：答案错误、将未验证推测当成确定事实、关键条件缺失导致操作失败，或文档遗漏关键信息导致读者无法完成任务。

必须输出严格 JSON 格式：
{
  "evaluations": [
    {
      "task_id": "T1",
      "verdict": "PASS" 或 "FAIL",
      "score": 1 或 0,
      "reason": "简述判分依据"
    }
  ],
  "passed_count": 0,
  "total_count": 0,
  "accuracy": 0.0
}
"""

def evaluate_l3(document_text: str, reader_tasks: list[dict]) -> dict:
    if not reader_tasks:
        return {"passed_count": 0, "total_count": 0, "accuracy": 1.0, "tasks": []}

    tasks_formatted = json.dumps(reader_tasks, ensure_ascii=False, indent=2)

    # Step 1: Independent reader answers the tasks using only the document
    reader_input = f"""【文档内容】
```
{document_text[:8000]}
```

【待解决的业务问题】
{tasks_formatted}
"""
    reader_res = call_llm(reader_input, system_prompt=L3_READER_PROMPT, temperature=0.0)
    raw_reader = reader_res["content"].strip()
    if "```json" in raw_reader:
        raw_reader = raw_reader.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_reader:
        raw_reader = raw_reader.split("```")[1].split("```")[0].strip()

    try:
        reader_data = json.loads(raw_reader)
        answers = reader_data.get("answers", [])
    except Exception as e:
        answers = [{"task_id": t.get("id"), "answer": f"Parse error: {e}", "evidence_location": "", "rationale": ""} for t in reader_tasks]

    # Step 2: Independent judge compares answers against expectations
    judge_input = f"""【预期标准】
{tasks_formatted}

【读者给出的回答】
{json.dumps(answers, ensure_ascii=False, indent=2)}
"""
    judge_res = call_llm(judge_input, system_prompt=L3_JUDGE_PROMPT, temperature=0.0)
    raw_judge = judge_res["content"].strip()
    if "```json" in raw_judge:
        raw_judge = raw_judge.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_judge:
        raw_judge = raw_judge.split("```")[1].split("```")[0].strip()

    try:
        judge_data = json.loads(raw_judge)
        evals = judge_data.get("evaluations", [])
        passed = sum(1 for e in evals if e.get("verdict") == "PASS")
        total = len(evals) if evals else len(reader_tasks)
        acc = round(passed / total, 3) if total > 0 else 0.0
        return {
            "passed_count": passed,
            "total_count": total,
            "accuracy": acc,
            "evaluations": evals,
            "reader_answers": answers,
            "tokens_used": reader_res["total_tokens"] + judge_res["total_tokens"]
        }
    except Exception as e:
        return {
            "passed_count": 0,
            "total_count": len(reader_tasks),
            "accuracy": 0.0,
            "evaluations": [{"task_id": t.get("id"), "verdict": "FAIL", "reason": f"Judge error: {e}"} for t in reader_tasks],
            "reader_answers": answers,
            "tokens_used": reader_res["total_tokens"] + judge_res["total_tokens"]
        }

def main():
    parser = argparse.ArgumentParser(description="L3 Downstream Task Evaluator")
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args()

    doc_text = args.document.read_text(encoding="utf-8")
    case_meta = yaml.safe_load(args.case.read_text(encoding="utf-8"))
    tasks = case_meta.get("reader_tasks", [])

    res = evaluate_l3(doc_text, tasks)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

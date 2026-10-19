#!/usr/bin/env python3
"""L2 Independent Semantic Grader for note-reforge outputs.

Conducts blinded semantic grading on 5 dimensions:
1. fact_fidelity (0..2)
2. decision_contract (0..2)
3. mechanism_depth (0..2)
4. actionability (0..2)
5. conciseness_no_bloat (0..2)

Requirements:
- Blind evaluation: candidate identity (Baseline vs Skill) is masked.
- Grounded in evidence: requires explicit quotes or observations.
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

L2_SYSTEM_PROMPT = """你是一名严格、客观的 AI 知识库评估工程师，负责对笔记加工任务的产物进行匿名盲评。
你不知道候选产物是由基础模型、特定 Skill 还是人工生成的。
你的任务是依据原始文档、任务目标与评分标准，对候选产物进行严谨打分，并给出具体证据引用。

评分维度（每项 0～2 分，总分 10 分）：
1. fact_fidelity（事实保真与证据边界）：
   - 0分：存在编造实测数据、擅改原始事实、丢失关键代码逻辑或破坏受保护信息。
   - 1分：原始事实基本保留，但在推论或边界上存在轻微泛化或遗漏。
   - 2分：原始事实完全保真，严格区分已知实测与推论假设，证据边界清晰。
2. decision_contract（决策契约符合度）：
   - 0分：决策发生严重错误（例如：本应 KEEP 却大肆重写；本应 BLOCK 却放行宣称成功）。
   - 1分：决策方向基本一致，但依据不够明确或伴随轻微无意义格式改动。
   - 2分：决策准确（KEEP/PATCH/REFORGE/BLOCK），且给出了令人信服的实据支撑。
3. mechanism_depth（因果机制与深层判断）：
   - 0分：没有任何新增认知价值，纯粹是字数扩写、同义改写或空泛修饰。
   - 1分：梳理了部分因果与背景，对理解问题有一定帮助。
   - 2分：清晰揭示了底层机制、核心权衡取舍、前提条件与失效场景。
4. actionability（操作建议与执行指导）：
   - 0分：无法指导实际操作，甚至提供了未经验证的错误/危险命令。
   - 1分：能指导下一步操作，但缺少停止条件或前置核查步骤。
   - 2分：操作步骤明确、命令可验证，包含清晰的触发阈值与异常处置。
5. conciseness_no_bloat（去冗余与无认知负担）：
   - 0分：充斥套话、过程汇报（“我修改了哪些地方”）、机械排比或严重篇幅膨胀。
   - 1分：表达相对清晰，但仍有少量无增量的重复段落。
   - 2分：直述干练，信息密度高，无过程泄露，直接面向读者任务。

必须输出严格 JSON 格式：
{
  "scores": {
    "fact_fidelity": 0-2,
    "decision_contract": 0-2,
    "mechanism_depth": 0-2,
    "actionability": 0-2,
    "conciseness_no_bloat": 0-2
  },
  "total_score": 0-10,
  "hard_failure": true/false,
  "hard_failure_reason": "如果有硬门禁失败则说明，否则为空",
  "evidence_quotes": [
    "引述候选产物中的具体语句或行为观察",
    "..."
  ],
  "reasoning": "简要评价总结（150字以内）"
}
"""

def grade_l2(source_text: str, candidate_text: str, case_meta: dict) -> dict:
    prompt = f"""【测试案例任务】
{case_meta.get('task', '')}

【预期决策与依据】
预期决策: {case_meta.get('expected_decision', '')}
决策依据: {case_meta.get('decision_evidence', '')}
验收标准: {case_meta.get('acceptance_criteria', '')}

【原始输入文档摘要/片段】
```
{source_text[:3000]}
```

【候选产物（匿名）】
```
{candidate_text[:6000]}
```

请按标准盲评打分，只输出符合 Schema 的 JSON。"""

    res = call_llm(prompt, system_prompt=L2_SYSTEM_PROMPT, temperature=0.0)
    raw_content = res["content"].strip()
    
    # Extract JSON if enclosed in markdown blocks
    if "```json" in raw_content:
        raw_content = raw_content.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_content:
        raw_content = raw_content.split("```")[1].split("```")[0].strip()
    
    try:
        data = json.loads(raw_content)
        data["latency_sec"] = res["latency_sec"]
        data["tokens_used"] = res["total_tokens"]
        return data
    except Exception as e:
        return {
            "scores": {"fact_fidelity": 0, "decision_contract": 0, "mechanism_depth": 0, "actionability": 0, "conciseness_no_bloat": 0},
            "total_score": 0,
            "hard_failure": True,
            "hard_failure_reason": f"Grader JSON parse error: {e}",
            "evidence_quotes": [],
            "reasoning": raw_content[:300],
            "latency_sec": res["latency_sec"],
            "tokens_used": res["total_tokens"]
        }

def main():
    parser = argparse.ArgumentParser(description="L2 Semantic Grader")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args()

    source_text = args.source.read_text(encoding="utf-8")
    candidate_text = args.candidate.read_text(encoding="utf-8")
    case_meta = yaml.safe_load(args.case.read_text(encoding="utf-8"))

    eval_result = grade_l2(source_text, candidate_text, case_meta)
    print(json.dumps(eval_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

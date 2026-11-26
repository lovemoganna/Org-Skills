#!/usr/bin/env python3
"""Prepare prompts and run directories for subagent evaluation runs."""
from __future__ import annotations

import json
from pathlib import Path
import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[2]
EVAL_ROOT = REPO_ROOT / "evals" / "note-reforge"
RUNS_DIR = EVAL_ROOT / "runs"

def prepare_case_run(run_id: str, case_id: str):
    case_file = EVAL_ROOT / "cases" / f"{case_id}.yaml"
    meta = yaml.safe_load(case_file.read_text(encoding="utf-8"))
    
    snapshot_path = REPO_ROOT / meta["snapshot_file"]
    source_text = snapshot_path.read_text(encoding="utf-8")
    
    case_run_dir = RUNS_DIR / run_id / case_id
    case_run_dir.mkdir(parents=True, exist_ok=True)
    
    arm_a_dir = case_run_dir / "arm_a_baseline"
    arm_b_dir = case_run_dir / "arm_b_skill"
    arm_a_dir.mkdir(parents=True, exist_ok=True)
    arm_b_dir.mkdir(parents=True, exist_ok=True)

    # Prompt for Arm A (Baseline):
    arm_a_prompt = f"""你正在执行笔记处理任务。你没有加载任何专门的 note-reforge Skill。
请遵循通用的严谨工程原则执行任务：
- 事实优先，不编造作者经验、项目数据或实测结论。
- 保留原文档的所有代码块、链接、重要参数和受保护配置。
- 如果原文已足够充分或找不到有依据的增量，请原样保留，不要制造无意义的改写；若存在严重冲突或事实缺失，请说明阻塞。
- 明确给出你的决策（KEEP / PATCH / REFORGE / BLOCK）以及相应产物或理由。

【用户任务】
{meta.get('task')}

【输入文档全文】
```org
{source_text}
```

请直接将你生成的最终结果（包括决策结论与正文产物）完整写入文件：
`{arm_a_dir / 'output.md'}`
完成后回复：DONE_ARM_A_{case_id}
"""

    # Prompt for Arm B (Skill):
    arm_b_prompt = f"""你正在执行笔记炼化任务。
【强制要求】你必须严格按照当前仓库的 `skills/note-reforge/SKILL.md` 规则执行本任务！
请先阅读 `skills/note-reforge/SKILL.md`，然后按照其规则执行：
- 严格执行决策协议（KEEP / PATCH / REFORGE / BLOCK 先裁决后动笔）。
- 原文已充分时选 KEEP，不制造无意义的改写稿。
- 关键缺口只做局部 PATCH；阻碍使用才 REFORGE；条件不足坚决 BLOCK。
- 完整保留所有非标题文件头、原始代码块、链接和发布身份。

【用户任务】
{meta.get('task')}

【输入文档全文】
```org
{source_text}
```

请直接将你生成的最终结果（包括决策结论与正文产物）完整写入文件：
`{arm_b_dir / 'output.md'}`
完成后回复：DONE_ARM_B_{case_id}
"""

    (arm_a_dir / "prompt.txt").write_text(arm_a_prompt, encoding="utf-8")
    (arm_b_dir / "prompt.txt").write_text(arm_b_prompt, encoding="utf-8")
    
    print(f"Prepared run prompts for {case_id} in {case_run_dir}")
    return {
        "case_id": case_id,
        "arm_a_prompt_file": str(arm_a_dir / "prompt.txt"),
        "arm_b_prompt_file": str(arm_b_dir / "prompt.txt")
    }

if __name__ == "__main__":
    import sys
    run_id = sys.argv[1] if len(sys.argv) > 1 else "smoke_ab_01"
    for cid in ["case_01_keep_recursive_discovery", "case_07_patch_project_operations", "case_15_reforge_agent_automations", "case_19_block_unverifiable_source_fabrication"]:
        prepare_case_run(run_id, cid)

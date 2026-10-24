#!/usr/bin/env python3
"""回归：真实历史审查 + 范围误派/虚假内容/自审伪通过等变异反例。"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
import os
import subprocess
import sys
import tempfile

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
for required in (
    "### 5.1a Intent and orchestration gate",
    "D0 DIRECT", "D1 SINGLE", "D2 DEPENDENCY", "D3 BRANCH/COMPARE",
    "Typed orchestration outside atomic prompts",
    "The same-model self-assessment is NOT independent evaluation",
    "Generalization check",
    "### 5.2a Skill / Prompt 调试专用：任务适配审查",
    "### 5.2b Skill / Prompt 调试专用：内容质量独立验收",
    "测试设计无效", "同一执行者的自评不能冒充独立质量合格证明",
    "scripts/evaluate_case.py", "内容与效果质量",
    "### 5.6a Principle Steering", "Attack the Premise",
    "Subtract Before You Add", "Prove It Works",
    "Test Behavior, Not Implementation", "Encode Lessons in Structure",
    "rejected choice -> chosen choice", "Omit the record when no choice changed",
    "Retire or revert principles", "Preserve contrary runs",
):
    assert required in skill, required

spec = spec_from_file_location("loop_evaluator", ROOT / "scripts/evaluate_case.py")
mod = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

historical = json.loads((ROOT / "tests/real-noncode-note-review.json").read_text(encoding="utf-8"))
checks = []

def check(label, case, expected, quality=None):
    result = mod.judge(case)
    assert result["判定"] == expected, (label, result)
    if quality:
        assert result["被测对象质量"] == quality, (label, result)
    checks.append((label, expected))

# 非代码文章的真实历史执行，不因结构通过而宣称“质量合格”。
check("真实非代码历史样本：价值尚无独立证据", historical, "有条件通过", "尚不能证明整体合格")
# 上一轮错误派发：这不是 note-reforge 的质量失败。
wrong = deepcopy(historical)
wrong["scope"]["task_capabilities"] = ["将代码教程改为可执行 Org 文学编程"]
check("代码教程误派", wrong, "测试设计无效", "未评价")
# 同一测试需求改派到适合对象应放行：不以材料包含代码作唯一判据。
literate = deepcopy(wrong)
literate["scope"]["skill_capabilities"] = ["将代码教程改为可执行 Org 文学编程"]
check("明确符合职责的代码可执行化", literate, "有条件通过")
# 结构可以通过，但凭空声称成功必须失败。
fabricated = deepcopy(historical)
fabricated["content"]["grounding"] = {"status": "失败", "evidence": "故意变异：生成物新增原始材料不存在的已实测成功声称"}
check("结构通过、事实捏造", fabricated, "测试失败", "本例不合格")
# 如果仅修改风格和篇幅，没有任务增量，不能用其他项目通过掩盖。
no_gain = deepcopy(historical)
no_gain["content"]["task_value"] = {"status": "失败", "evidence": "故意变异：仅改标题并冗余扩写"}
check("没有实际任务增量", no_gain, "测试失败")
# 自审不能升级成全面合格。
same_reviewer = deepcopy(historical)
for item in same_reviewer["content"].values():
    item["status"] = "通过"
check("生成者自审伪通过", same_reviewer, "有条件通过")
# 模拟独立且有证据审核的正向记录；仅验证裁决逻辑，不冒充真实独立审计。
separate = deepcopy(same_reviewer)
separate["review"] = {"independent": True, "evidence": "模拟独立审查记录，非真实测评"}
check("模拟独立验证的规则路径", separate, "测试通过")
# 证据与执行不齐全，不能宣称通过。
no_run = deepcopy(separate)
no_run["execution"] = {"performed": False, "receipt": ""}
check("未实际执行", no_run, "执行证据不足", "未评价")
no_structure = deepcopy(separate)
no_structure["structure"] = {"status": "失败", "evidence": "故意破坏头字段"}
check("结构验收失败", no_structure, "测试失败")
missing_value = deepcopy(separate)
del missing_value["content"]["task_value"]
check("缺内容评价维度", missing_value, "内容验收缺失")
unknown_fit = deepcopy(separate)
unknown_fit["scope"]["uncertain_capabilities"] = ["非代码知识文章炼化"]
check("职责不确定", unknown_fit, "适配性待确认", "未评价")
no_source = deepcopy(separate)
no_source["scope"]["evidence"] = ""
check("缺职责来源", no_source, "测试准备不足", "未评价")
# 校验自动化调用中的真实退出状态，避免“输出失败但 CI 仍成功”。
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "case.json"
    for label, data, code in (
        ("历史有条件通过不可以自动发布", historical, 2),
        ("故意伪造结论必须拦截", fabricated, 1),
        ("模拟独立完整合格可以执行", separate, 0),
    ):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_case.py"), str(path)], capture_output=True, text=True)
        assert result.returncode == code, (label, result.returncode, result.stdout, result.stderr)
        checks.append((label, "退出状态=" + str(code)))
    path.write_text(json.dumps(historical, ensure_ascii=False), encoding="utf-8")
    advised = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_case.py"), str(path), "--advisory"], capture_output=True, text=True)
    assert advised.returncode == 0 and "有条件通过" in advised.stdout
    checks.append(("不阻断的审计模式", "退出状态=0"))
    # 错误类型的 JSON 仍是有效 JSON；必须返回受控错误，不能泄露 traceback。
    for label, bad_case in (
        ("顶层数组拒绝", []),
        ("scope 非对象拒绝", {**historical, "scope": ["invalid"]}),
        ("review 非对象拒绝", {**separate, "review": ["invalid"]}),
    ):
        path.write_text(json.dumps(bad_case, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_case.py"), str(path)], capture_output=True, text=True)
        assert proc.returncode == 2 and not proc.stderr, (label, proc.returncode, proc.stdout, proc.stderr)
        verdict = json.loads(proc.stdout)
        assert verdict["判定"] == "测试准备不足", (label, verdict)
        checks.append((label, "退出状态=2"))
# 成对多次结果态门禁：模拟契约与变异反例，不冒充真实 Agent A/B。
paired = subprocess.run(
    [sys.executable, str(ROOT / "tests/check_trial_comparison.py")],
    capture_output=True, text=True,
)
assert paired.returncode == 0, (paired.returncode, paired.stdout, paired.stderr)
checks.append(("成对试验比较器的模拟契约与反例", "退出状态=0"))

print(json.dumps({"结论": "回归通过", "案例数": len(checks), "检查": checks}, ensure_ascii=False, indent=2))

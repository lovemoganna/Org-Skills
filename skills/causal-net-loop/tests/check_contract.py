#!/usr/bin/env python3
"""Static checks only, not a model-quality evaluation."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
s = (root / "SKILL.md").read_text(encoding="utf-8")
e = (root / "evals/cases.md").read_text(encoding="utf-8")
assert s.startswith("---\n"), "Missing frontmatter"
assert re.search(r"^name: causal-net-loop$", s, re.M), "Incorrect skill name"
assert re.search(r"^description: .{30,}$", s, re.M), "Missing activation description"
for term in ["见事", "寻因", "识网", "明己", "造因", "验果", "反事实", "竞争假设", "已观察", "未知", "可直接控制", "验收", "停止", "keypoint-loop"]:
    assert term in s, f"Missing core rule: {term}"
for case in [f"T{i}" for i in range(1, 11)]:
    assert re.search(rf"^## {case}", e, re.M), f"Missing eval case {case}"
for term in ["按需强化模块", "连锁影响", "最强证伪", "复发预防", "不强行写三阶结论", "没找到反例，不等于证实", "至少两次可比事件", "loop-engineering-meta", "表达预算", "一个真正改变决策的新增洞察", "传导检验"]:
    assert term in s, f"Missing candidate guardrail: {term}"
assert "不把“数据改善”自动归功于本次动作" in s
print("PASS: frontmatter, workflow, conditional modules, causal guardrails, routing, 10 eval cases")

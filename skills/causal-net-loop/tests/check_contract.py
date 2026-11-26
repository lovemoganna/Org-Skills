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
for case in ["T1", "T2", "T3", "T4", "T5"]:
    assert re.search(rf"^## {case}", e, re.M), f"Missing eval case {case}"
assert "不把“数据改善”自动归功于本次动作" in s
print("PASS: frontmatter, workflow, causal guardrails, skill routing, 5 eval cases")

#!/usr/bin/env python3
"""Deterministic package-contract checks only; not model-behavior or deployment E2E."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
evals = (ROOT / "evals/cases.md").read_text(encoding="utf-8")
assert skill.startswith("---\n"), "missing frontmatter"
match = re.match(r"\A---\n(.*?)\n---\n", skill, re.S)
assert match, "malformed frontmatter"
front = match.group(1)
assert re.search(r"^name: learning-knowledge-meta$", front, re.M)
assert re.search(r"^description: .{40,}$", front, re.M)
assert len(front) < 750, "metadata too large"
assert len(skill) < 12000, "skill should delegate, not duplicate"
assert len(set(re.findall(r"^\d+\. \*\*.*", skill, re.M))) == 8
for term in (
    "课程内容", "〔补〕", "待核实", "真实执行结果", "可定位", "未处理", "NOOP",
    "org-literate-engineering", "note-reforge", "llm-wiki-maintainer", "org-museum-ingest",
    "loop-engineering-meta", "Git", "Commit", "页面", "未经授权", "版权",
    "不大量复刻", "CONDITIONAL PASS", "不可访问", "未验证", "不触发远程写入",
):
    assert term in skill, f"critical contract missing: {term}"
for n in range(1, 6):
    assert re.search(rf"^## C{n} ", evals, re.M), f"C{n} missing"
assert "真正模型行为" in evals and "未运行的案例不得写 PASS" in evals
print("PASS: frontmatter, scope, safety/publication/loop contracts, five eval plans")

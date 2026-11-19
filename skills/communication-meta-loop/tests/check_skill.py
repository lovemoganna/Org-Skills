#!/usr/bin/env python3
"""Validate minimal local structure only; not behavioral efficacy."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
skill_path = root / "SKILL.md"
eval_path = root / "evals" / "cases.md"
errors = []

if not skill_path.is_file():
    errors.append("missing SKILL.md")
else:
    body = skill_path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", body, re.S)
    if not match:
        errors.append("missing YAML frontmatter")
    else:
        fm = match.group(1)
        if not re.search(r"(?m)^name:\s*communication-meta-loop\s*$", fm):
            errors.append("name mismatch")
        description = re.search(r"(?m)^description:\s*(.+)$", fm)
        if not description or len(description.group(1).strip().strip('"')) > 1024:
            errors.append("invalid description")
    for phrase in ("FRAME", "RESPOND", "VERIFY", "REPAIR", "NOT_VERIFIED", "无新证据"):
        if phrase not in body:
            errors.append("missing core phrase: " + phrase)

if not eval_path.is_file():
    errors.append("missing evals/cases.md")
else:
    eval_text = eval_path.read_text(encoding="utf-8")
    ids = re.findall(r"\|\s*(C\d\d)\s+", eval_text)
    if len(set(ids)) < 6:
        errors.append("insufficient distinct candidate test cases")

if errors:
    print("STATIC FAIL: " + "; ".join(errors))
    sys.exit(1)
print("STATIC PASS: structure/frontmatter/required sections/eval coverage")
print("Behavioral quality and independent A/B: NOT_VERIFIED")

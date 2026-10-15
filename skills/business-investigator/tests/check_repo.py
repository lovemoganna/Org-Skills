#!/usr/bin/env python3
"""Structural contract only. Real content quality is measured by independent
source-grounded investigation, not by passing keyword/static tests."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
skill=(root/"SKILL.md").read_text(encoding="utf-8")
case=(root/"references/four-sheet-case.md").read_text(encoding="utf-8")
assert skill.startswith("---\nname: business-investigator\n")
for rule in (
 "不可变读取与权限契约",
 "每轮只有一个有信息价值的问题",
 "真实执行",
 "竞争解释",
 "证据",
 "及时止损",
 "正文交付门禁",
 "未达到",
 "不得自称独立的三个 LLM Agent",
 "业务认知",
):
 assert rule in skill,rule
for datum in ("43 笔","44 笔","2 组","38748162141","38750016332"):
 assert datum in case,datum
assert "模拟交易样本" in skill or "小型教学样本" in skill
print("PASS: business investigator routing, evidence, value and stop contracts (STRUCTURAL ONLY)")

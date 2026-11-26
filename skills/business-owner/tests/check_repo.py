#!/usr/bin/env python3
"""Contract and adversarial scenario lint for business-owner. Textual checks only."""
from pathlib import Path
import re
import sys
root=Path(__file__).resolve().parents[1]
skill=(root/"SKILL.md").read_text(encoding="utf-8")
readme=(root/"README.md").read_text(encoding="utf-8")
ex=(root/"tests/bitget-withdrawal-resumption.md").read_text(encoding="utf-8")
gen=(root/"tests/generalization.md").read_text(encoding="utf-8")
alltext=skill+"\n"+readme+"\n"+ex+"\n"+gen
assert skill.startswith("---\nname: business-owner\n")
for x in ["事件→机制", "Decision", "Consequence", "Business Brief", "Decision Review","business-reasoning","analysis-verifier","NOT_DECISION_READY","申请","实际完成","竞争", "基线", "数据新鲜度", "资金", "不写 SQL","没有新增"]:
    assert x in alltext, "missing: "+x
for x in ("trigger_and_evidence_status","decision_to_make","priority_question","decision_branches","minimum_evidence","acceptance_criteria","data_freshness_and_feasibility"):
    assert x in skill, "business brief missing: "+x
for x in ("恢复前的0提现不作正常基线","申请≠成功外流","分币种分网络","数据源、时点、主体均不匹配","不能直接回答"):
    assert x in ex, "withdrawal scenario missing: "+x
for x in ("交易所现货交易量大涨","电商活动后 GMV","10%","强制讨论轮次"):
    assert x in gen, "generalization regression missing: "+x
assert "历史四表" in ex and "实时" in ex
assert "有即时行动风险" in skill
assert (root.parents[1]/"skills/business-reasoning/SKILL.md").exists()
assert (root.parents[1]/"skills/analysis-verifier/SKILL.md").exists()
assert "business-owner" in (root.parents[1]/"README.md").read_text(encoding="utf-8")
assert "status=completed" in ex
assert not re.search(r"(?m)^\s*(SELECT|CREATE TABLE|FROM|WHERE)\b",skill)
print("BUSINESS_OWNER_SCENARIO_AND_BOUNDARY_PASS")

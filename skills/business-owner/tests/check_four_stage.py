#!/usr/bin/env python3
"""Four-stage protocol and review ownership test; not a substitute for live SQL."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[3]
d=json.loads((root/"skills/business-owner/references/four-stage-contract.json").read_text(encoding="utf-8"))
st=d["stages"]
assert [x["id"] for x in st]==["S1","S2","S3","S4"]
assert [x["name"] for x in st]==["下达任务","基础梳理","基础校验","形成分析"]
assert [x["owner"] for x in st]==["business-owner","business-reasoning","analysis-verifier","business-reasoning"]
assert [x["reviewer"] for x in st]==["business_owner","analyst_peer","independent_verifier","business_owner"]
assert all(not x["produces_findings"] for x in st[:3])
assert st[3]["produces_findings"] and st[3]["verifier"]=="analysis-verifier"
assert all(x["requires"] for x in st[1:]) and not st[0]["requires"]
assert "QAReceipt" in st[3]["requires"]
r=d["review_rule"]
assert r["owner_receives_only"]=="DecisionReport" and r["stage3_pass_does_not_imply_finding_pass"]
assert r["phase4_findings_require_independent_verdict"] and r["blocked_disallows_claims"]
p=(root/"skills/business-owner/references/four-stage-review.md").read_text(encoding="utf-8")
for token in ("先想最终要什么结果表","一行代表谁","哪个表","取什么","筛什么","S3=BLOCKED","S3=PARTIAL","S3=PASS","管理层分析报告","老板"):
    assert token in p, token
a=(root/"skills/business-reasoning/SKILL.md").read_text(encoding="utf-8")
b=(root/"skills/analysis-verifier/SKILL.md").read_text(encoding="utf-8")
o=(root/"skills/business-owner/SKILL.md").read_text(encoding="utf-8")
for token in ("ResultSpec","SourceMap","S4 形成分析","老板只接收"):
    assert token in a, token
for token in ("QAReceipt","PARTIAL","S3 PASS","FindingVerdict"):
    assert token in b, token
assert "老板在 S4 完成后只收到" in o
assert "four-stage-review.md" in (root/"README.md").read_text(encoding="utf-8")
e=(root/"skills/business-owner/tests/four-stage-replay.md").read_text(encoding="utf-8")
assert "不是本轮再次读表" in e and "4 笔非完成 ≠ 4 笔排队" in e
# Negative control: blocked QA cannot be promoted to an apparently approved business finding.
def may_publish(qa, finding):
    return qa in ("PASS","PARTIAL") and finding=="VERIFIED"
for qa,verdict,ok in [("BLOCKED","VERIFIED",False),("PARTIAL","UNRESOLVED",False),("PASS","UNRESOLVED",False),("PASS","VERIFIED",True)]:
    assert may_publish(qa,verdict)==ok
print("FOUR_STAGE_REVIEW_CONTRACT_PASS; live SQL test is separate")

#!/usr/bin/env python3
"""Check the clarity and meaning of authored fixtures; NOT a live LLM evaluation."""
import json
from copy import deepcopy
from pathlib import Path

p=Path(__file__).with_name("plain-language-cases.json")
data=json.loads(p.read_text(encoding="utf-8"))
assert "NOT independently generated" in data["scope"]

JARGON=("IntentCard","TaskSpec","ChainSpec","Loop QA","MECE","D2 DEPENDENCY","质量门禁","阶段 A","阶段 B","元 Skill")
def validate(case):
    output=case["output"]
    if not output or len(output)>case["limit"]:
        return "TOO_LONG_OR_EMPTY"
    if any(term not in output for term in case["required"]):
        return "MISSING_ESSENTIAL"
    if case["type"]=="copy" and (not output.startswith("请") and not output.startswith("先")):
        return "NOT_COPY_READY"
    if case["type"]=="copy" and any(x in output for x in JARGON):
        return "INTERNAL_JARGON"
    if case["type"]=="copy" and "已部署" in output:
        return "FALSE_EXECUTION_CLAIM"
    return "OK"

for case in data["cases"]:
    assert validate(case)=="OK",(case["id"],validate(case))
    bad=deepcopy(case)
    bad["output"]=bad["output"].replace(bad["required"][0],"",1)
    assert validate(bad)=="MISSING_ESSENTIAL",(case["id"],"loss of meaning")
    bad=deepcopy(case)
    bad["output"]+=" 废话" * (case["limit"]+1)
    assert validate(bad)=="TOO_LONG_OR_EMPTY",(case["id"],"verbosity")
    if case["type"]=="copy":
        bad=deepcopy(case)
        bad["output"]="Loop QA："+bad["output"]
        assert validate(bad) in ("NOT_COPY_READY","INTERNAL_JARGON")
        bad=deepcopy(case)
        bad["output"]+=" 已部署"
        assert validate(bad)=="FALSE_EXECUTION_CLAIM"
print("PASS: %d authored outputs and %d rejected mutations; independent model/user evaluation NOT RUN" % (len(data["cases"]),sum(4 if c["type"]=="copy" else 2 for c in data["cases"])))

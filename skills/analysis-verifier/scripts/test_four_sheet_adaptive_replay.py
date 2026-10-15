#!/usr/bin/env python3
"""Counterfactual replay of stage-one receipts, without re-reading Excel.

The planning policy must change its question selection if the evidence changes,
and refuse a report when nothing testable remains.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

script=Path(__file__).with_name("four_sheet_research_followup.py")
root=Path(sys.argv[1] if len(sys.argv)>1 else "discovery")
names=["fiat_details.json","crypto_details.json",
       "crossrail_status_and_time.json","fiat_roundtrip_7d.json",
       "joined_users.json","frozen_account_activity.json","schema_users.json",
       "keys_quality.json"]
for n in names:assert (root/n).exists(),n
def run(config):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        for n in names:shutil.copy2(root/n,p/n)
        fiat=json.loads((p/"fiat_details.json").read_text())
        for row in fiat:
            if row["status"]!="completed":row["completed_at"]=None
        (p/"fiat_details.json").write_text(json.dumps(fiat))
        if config=="no_turnover":
            (p/"fiat_roundtrip_7d.json").write_text("[]")
        if config=="no_candidates":
            (p/"fiat_roundtrip_7d.json").write_text("[]")
            (p/"crossrail_status_and_time.json").write_text("[]")
        task=subprocess.run([sys.executable,str(script),str(p)],
                            capture_output=True,text=True)
        if config=="no_candidates":
            assert task.returncode!=0, "planner invented candidates when none exist"
            assert not (p/"second-pass.sql").exists(), "planner issued SQL without evidence"
            return {"scenario":config,"blocked_as_expected":True}
        assert task.returncode==0,(task.stdout,task.stderr)
        plan=json.loads((p/"research-plan.json").read_text())
        selected={c["code"] for c in plan["investigate"]}
        assert "STATUS_NOT_SETTLEMENT" not in selected
        if config=="no_turnover":
            assert "SAME_ASSET_TURNOVER" not in selected
            assert "CROSS_RAIL_NEARBY" in selected
        else:
            assert "SAME_ASSET_TURNOVER" in selected
        assert (p/"second-pass.sql").exists()
        return {"scenario":config,"selected":sorted(selected)}
results=[run("status_removed"),run("no_turnover"),run("no_candidates")]
print(json.dumps({"counterfactual": "PASS", "cases":results},ensure_ascii=False))

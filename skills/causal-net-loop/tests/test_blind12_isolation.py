#!/usr/bin/env python3
"""Unit-test the evaluation harness, using explicitly synthetic records.

This test does NOT run a language model and does NOT assert A/B quality.
"""
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS = HERE.parent / "evals"
spec = importlib.util.spec_from_file_location("blind12", EVALS / "blind12.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
data = mod.load_data()
assert len(data["cases"]) == 12

def fixtures(root):
    for arm in ("baseline", "candidate"):
        for case in data["cases"]:
            p = root / arm / f"{case['id']}.json"
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_text(json.dumps({
                "case_id": case["id"],
                "skill_blob": data["frozen"][f"{arm}_blob"],
                "model": "GPT-6.1 Sol",
                "tools": "none",
                "session_id": f"synthetic-{arm}-thread",
                "runner_id": f"synthetic-{arm}-runner",
                "response": "SYNTHETIC UNIT TEST ONLY. No model generated this output.",
                "evidence_ref": "synthetic://not-an-actual-trace"
            }, ensure_ascii=False), encoding="utf-8")

with tempfile.TemporaryDirectory(prefix="blind12-unit-") as td:
    d = Path(td)
    fixtures(d)
    assert len(mod.load_submitted(data, d)) == 24, "Two separate arm threads must be accepted"
    p = d / "candidate" / "N01.json"
    obj = json.loads(p.read_text(encoding="utf-8"))
    obj["session_id"] = "synthetic-baseline-thread"
    p.write_text(json.dumps(obj), encoding="utf-8")
    try:
        mod.load_submitted(data, d)
        raise AssertionError("Shared baseline/candidate thread should be rejected")
    except ValueError as err:
        assert "shared by both arms" in str(err), str(err)
    obj["session_id"] = "synthetic-candidate-thread"
    obj["runner_id"] = "synthetic-baseline-runner"
    p.write_text(json.dumps(obj), encoding="utf-8")
    try:
        mod.load_submitted(data, d)
        raise AssertionError("Shared executor should be rejected")
    except ValueError as err:
        assert "one reported executor" in str(err), str(err)
    obj["runner_id"] = "synthetic-candidate-runner"
    obj["model"] = "GPT-6 Astra"
    p.write_text(json.dumps(obj), encoding="utf-8")
    try:
        mod.load_submitted(data, d)
        raise AssertionError("Different models must be rejected")
    except ValueError as err:
        assert "Conditions mismatch" in str(err), str(err)
print("PASS: two-arm synthetic harness: 24 records, shared thread rejected, shared executor rejected, model mismatch rejected")

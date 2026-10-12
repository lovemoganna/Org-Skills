#!/usr/bin/env python3
"""Regression and adversarial tests for deterministic preflight contract."""
from copy import deepcopy
import json
import random
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from decision_gate import evaluate  # noqa: E402

skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
for term in ("loop-engineering-meta", "真实授权", "Phase", "不执行实际操作",
             "历史先例", "必须独立核验", "验收", "一键确认"):
    assert term in skill, term

BASE = {
    "task_id": "task-001", "phase": 1, "operation": "read", "resource": "repo/readme",
    "impact": "low", "cost": "none", "reversible": True, "rollback_ready": True,
    "authority": {"operations": ["read"], "resources": ["repo/readme"]},
    "critical_unknowns": [], "contradictions": [], "risk_flags": [], "needs_choice": False,
}


def check(name, patch, expected, reason=None):
    data = deepcopy(BASE)
    data.update(patch)
    got = evaluate(data)
    assert got["level"] == expected, (name, got)
    assert got["may_proceed"] is (expected <= 1), (name, got)
    if reason:
        assert got["reason"] == reason, (name, got)
    return got


checks = []
checks.append(check("safe read fast path", {}, 0))
checks.append(check("bounded cost notify", {"cost": "bounded"}, 1))
checks.append(check("medium impact notify", {"impact": "medium"}, 1))
checks.append(check("cross-option choice", {"needs_choice": True, "choices": ["A", "B"], "recommendation": "A"}, 2))
checks.append(check("three options", {"needs_choice": True, "choices": ["A", "B", "C"], "recommendation": "B"}, 2))
checks.append(check("four options invalid", {"needs_choice": True, "choices": ["A", "B", "C", "D"], "recommendation": "A"}, 4))
checks.append(check("missing recommendation invalid", {"needs_choice": True, "choices": ["A", "B"]}, 4))
checks.append(check("critical unknown dominates", {"critical_unknowns": ["project target unclear"]}, 4))
checks.append(check("contradiction dominates", {"contradictions": ["delete and preserve"]}, 4))
checks.append(check("out of scope operation", {"operation": "write"}, 4))
checks.append(check("out of scope resource", {"resource": "repo/other"}, 4))
checks.append(check("delete blocks without approval", {"operation": "delete", "reversible": False, "authority": {"operations": ["delete"], "resources": ["repo/readme"]}}, 3))
checks.append(check("publish blocks without approval", {"operation": "publish", "authority": {"operations": ["publish"], "resources": ["repo/readme"]}}, 3))
checks.append(check("privacy blocks even read", {"risk_flags": ["privacy"]}, 3))
checks.append(check("high impact blocks", {"impact": "high"}, 3))
checks.append(check("unbounded cost blocks", {"cost": "unbounded"}, 3))
checks.append(check("unprepared write blocks", {"operation": "write", "rollback_ready": False, "authority": {"operations": ["write"], "resources": ["repo/readme"]}}, 3))
checks.append(check("approval from past task insufficient", {"impact": "high", "approval": {"task_id": "old", "operation": "read", "resource": "repo/readme", "verified": True}}, 3))
checks.append(check("other resource approval insufficient", {"impact": "high", "approval": {"task_id": "task-001", "operation": "read", "resource": "repo/other", "verified": True}}, 3))
checks.append(check("unverified approval insufficient", {"impact": "high", "approval": {"task_id": "task-001", "operation": "read", "resource": "repo/readme", "verified": False}}, 3))
checks.append(check("exact high impact approval reports", {"impact": "high", "approval": {"task_id": "task-001", "operation": "read", "resource": "repo/readme", "verified": True}}, 1))
checks.append(check("no authority no override", {"impact": "high", "authority": {"operations": [], "resources": []}, "approval": {"task_id": "task-001", "operation": "read", "resource": "repo/readme", "verified": True}}, 4))
checks.append(check("invalid flag fail closed", {"risk_flags": ["mystery"]}, 4))
checks.append(check("missing field fail closed", {"authority": None}, 4))
checks.append(check("source cannot be inferred", {"authority": {}}, 4))
checks.append(check("plain text fails closed", {"impact": None}, 4))
checks.append(check("booleans must be booleans", {"reversible": "yes"}, 4))
checks.append(check("phase out of range", {"phase": 5}, 4))
checks.append(check("phase bool invalid", {"phase": True}, 4))
checks.append(check("impact list invalid", {"impact": ["high"]}, 4))
checks.append(check("cost map invalid", {"cost": {"limit": 0}}, 4))
checks.append(check("duplicate choices invalid", {"needs_choice": True, "choices": ["A", "A"], "recommendation": "A"}, 4))
checks.append(check("risk beats choice", {"needs_choice": True, "choices": ["A", "B"], "recommendation": "A", "impact": "high"}, 3))
checks.append(check("unknown beats approved risk", {"critical_unknowns": ["missing root"], "impact": "high", "approval": {"task_id": "task-001", "operation": "read", "resource": "repo/readme", "verified": True}}, 4))
assert evaluate([])["level"] == 4
checks.append({"level": 4})

with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / "case.json"
    for label, data, code in (
        ("safe", BASE, 0),
        ("block", {**BASE, "impact": "high"}, 2),
        ("invalid", [], 2),
    ):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/decision_gate.py"), str(path)], text=True, capture_output=True)
        assert proc.returncode == code and not proc.stderr, (label, proc.stdout, proc.stderr)
        assert json.loads(proc.stdout)["may_proceed"] == (code == 0)
    path.write_text("[invalid json", encoding="utf-8")
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/decision_gate.py"), str(path)], text=True, capture_output=True)
    assert proc.returncode == 2 and json.loads(proc.stdout)["reason"] == "unreadable_input"

# Deterministic malformed-input mutation coverage: no Python exception may escape.
rand = random.Random(20261012)
values = [None, {}, [], 1, 0, True, False, "", "x", "read", "high", [1, "x"]]
fields = list(BASE) + ["approval", "choices", "recommendation"]
for _ in range(1000):
    data = deepcopy(BASE)
    data[rand.choice(fields)] = deepcopy(rand.choice(values))
    assert evaluate(data)["level"] in range(5)

print(json.dumps({"verdict": "PASS", "cases": len(checks), "cli_cases": 4, "mutations": 1000}, ensure_ascii=False))

#!/usr/bin/env python3
"""Recompute archived cross-domain smoke-test dimensions without an LLM or API.

This checks file completeness and response lengths only; it cannot grade truth,
reasoning quality, isolation or user impact.
"""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
run = root / "runs"
files = {
    "baseline": "2026-11-17-cross-domain-baseline-raw.md",
    "candidate_v1": "2026-11-17-cross-domain-candidate-raw.md",
    "candidate_v2": "2026-11-17-cross-domain-v2-raw.md",
}
expected_blobs = {
    "baseline": "893b581a23fc2474d6d4fad761ecb4d2965c163c",
    "candidate_v1": "44156432c3f821d51e897fe8584824ba26562df7",
    "candidate_v2": "57581f87ba669cffe1900ad0b199a9fd24b0e6f6",
}
cases = [f"H{i}" for i in range(1, 7)]
pattern = re.compile(r"(?ms)^## (H[1-6]|T10)\s*\n\n(.*?)(?=^## (?:H[1-6]|T10)\s*$|\Z)")

def read_outputs(name):
    text = (run / files[name]).read_text(encoding="utf-8")
    assert expected_blobs[name] in text, f"{name}: version blob missing"
    pairs = pattern.findall(text)
    keys = [k for k, _ in pairs]
    assert len(keys) == len(set(keys)), f"{name}: duplicate sections"
    assert all(k in keys for k in cases), f"{name}: missing H1-H6"
    assert ("T10" in keys) == (name == "candidate_v2"), f"{name}: unexpected T10"
    return {k: v.strip() for k, v in pairs}

sets = {n: read_outputs(n) for n in files}
lengths = {
    k: {name: len(sets[name][k]) for name in files}
    for k in cases
}
totals = {name: sum(lengths[k][name] for k in cases) for name in files}
assert totals["candidate_v2"] < totals["candidate_v1"], "V2 not shorter than V1"
assert len(sets["candidate_v2"]["H6"]) <= 75, "simple question verbosity regression"
assert "不可能" in sets["candidate_v2"]["T10"], "T10 refutation missing"
assert "尚未改变" in sets["candidate_v2"]["T10"], "T10 temporal guard missing"

print(json.dumps({
    "check": "PASS (archived text structure and length only)",
    "cases": lengths,
    "totals": totals,
    "v2_vs_v1_pct": round(100 * (totals["candidate_v2"] / totals["candidate_v1"] - 1), 1),
    "v2_vs_baseline_pct": round(100 * (totals["candidate_v2"] / totals["baseline"] - 1), 1),
    "not_verified": ["model independence", "blind evaluation", "causal outcome", "token or latency cost"]
}, ensure_ascii=False, indent=2))

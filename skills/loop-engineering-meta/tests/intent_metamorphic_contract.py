#!/usr/bin/env python3
"""Metamorphic graph-contract tests, not an LLM or independent end-to-end evaluation."""
from copy import deepcopy

DOMAINS = ("visualization", "risk_investigation", "research", "content", "operations", "analytics")

def validate(plan):
    nodes = plan["nodes"]
    ids = [n["id"] for n in nodes]
    if len(set(ids)) != len(ids):
        return "DUPLICATE_NODE"
    route = plan["route"]
    if route not in ("D0", "D1", "D2", "D3"):
        return "BAD_ROUTE"
    if route in ("D0", "D1") and len(nodes) != 1:
        return "OVER_ORCHESTRATED"
    if route == "D2" and len(nodes) < 2:
        return "NO_DEPENDENCY"
    if route == "D2" and any(n.get("kind") == "compare" for n in nodes):
        return "COMPARISON_NOT_CHAIN"
    if route == "D3" and not any(n.get("kind") in ("compare", "join", "gate") for n in nodes):
        return "NO_BRANCH"
    by_id = {n["id"]: n for n in nodes}
    def visit(key, ancestry):
        if key in ancestry:
            return "DEPENDENCY_CYCLE"
        if key not in by_id:
            return "MISSING_UPSTREAM"
        for dep in by_id[key].get("deps", []):
            problem = visit(dep, ancestry | {key})
            if problem:
                return problem
        return None
    for key in ids:
        problem = visit(key, set())
        if problem:
            return problem
    for n in nodes:
        if n.get("write") and not plan.get("write_authorized"):
            return "UNAUTHORIZED_WRITE"
        if n.get("kind") == "compare":
            arms = [by_id.get(a) for a in n.get("deps", [])]
            if len(arms) < 2 or any(a is None for a in arms):
                return "BAD_ARMS"
            if len({a.get("baseline") for a in arms}) != 1:
                return "BASELINE_MISMATCH"
            if len({a.get("context_id") for a in arms}) != len(arms):
                return "SHARED_CONTEXT"
            arm_ids = {a["id"] for a in arms}
            if any(any(d in arm_ids for d in a.get("deps", [])) for a in arms):
                return "ARM_CONTAMINATION"
    if plan.get("claims_complete") and not plan.get("outcome_evidence"):
        return "OUTCOME_UNVERIFIED"
    return "OK"

positive = negative = 0
for domain in DOMAINS:
    direct = {"domain": domain, "route": "D0", "nodes": [{"id": "finish", "deps": []}]}
    assert validate(direct) == "OK"
    positive += 1
    for length in range(2, 8):
        chain = {"domain": domain, "route": "D2", "nodes": [
            {"id": str(i), "deps": [str(i-1)] if i else []}
            for i in range(length)]}
        assert validate(chain) == "OK"
        positive += 1
        bad = deepcopy(chain)
        bad["nodes"][0]["deps"] = [str(length-1)]
        assert validate(bad) == "DEPENDENCY_CYCLE"
        negative += 1
    compare = {"domain": domain, "route": "D3", "nodes": [
        {"id": "a", "deps": [], "baseline": "frozen", "context_id": "isolated_a"},
        {"id": "b", "deps": [], "baseline": "frozen", "context_id": "isolated_b"},
        {"id": "judge", "kind": "compare", "deps": ["a", "b"]}]}
    assert validate(compare) == "OK"
    positive += 1
    bad = deepcopy(compare)
    bad["nodes"][1]["baseline"] = "different"
    assert validate(bad) == "BASELINE_MISMATCH"
    negative += 1
    bad = deepcopy(compare)
    bad["nodes"][1]["context_id"] = "isolated_a"
    assert validate(bad) == "SHARED_CONTEXT"
    negative += 1
    bad = deepcopy(compare)
    bad["nodes"][1]["deps"] = ["a"]
    assert validate(bad) == "ARM_CONTAMINATION"
    negative += 1
    bad = deepcopy(direct)
    bad["nodes"][0]["write"] = True
    assert validate(bad) == "UNAUTHORIZED_WRITE"
    negative += 1
    bad = deepcopy(chain)
    bad["claims_complete"] = True
    assert validate(bad) == "OUTCOME_UNVERIFIED"
    negative += 1

print(f"PASS {positive} accepted graph variants, {negative} rejected mutations, {len(DOMAINS)} domains")
print("Scope: deterministic graph consistency only; it does not execute or evaluate an LLM.")

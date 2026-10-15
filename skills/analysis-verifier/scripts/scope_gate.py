#!/usr/bin/env python3
"""Fail-closed S3-to-S4 evidence-scope guard. Receipts are inputs, not inferred facts."""
import json
import sys

PROVENANCE = ("run_id", "source_id", "materialization_id", "read_plan_sha256")
SCOPE = ("grain", "population", "time_window", "status_meaning")


def check_scope(qa, finding):
    faults = []
    if qa.get("verdict") not in ("PASS", "PARTIAL"):
        faults.append("qa_not_usable")
    if finding.get("verdict") != "VERIFIED":
        faults.append("finding_not_verified")
    for name in PROVENANCE:
        a, b = qa.get(name), finding.get(name)
        if not isinstance(a, str) or not a.strip() or a != b:
            faults.append("provenance_mismatch:" + name)
    if not qa.get("qa_receipt_ref"):
        faults.append("missing_qa_receipt")
    if not finding.get("result_receipt_ref") or not finding.get("verification_receipt_ref"):
        faults.append("missing_finding_evidence")
    revision = finding.get("revision")
    if not finding.get("packet_id") or type(revision) is not int or revision < 1:
        faults.append("invalid_packet_key")
    if not (finding.get("verified_packet_id") == finding.get("packet_id") and
            finding.get("verified_revision") == revision):
        faults.append("feedback_packet_mismatch")
    demand = finding.get("scope")
    if not isinstance(demand, dict) or not isinstance(demand.get("metrics"), list) or not demand["metrics"]:
        faults.append("missing_finding_scope")
    else:
        scopes = qa.get("checked_scopes", [])
        if not isinstance(scopes, list):
            scopes = []

        def covers(allowed):
            return (isinstance(allowed, dict)
                and all(isinstance(demand.get(k), str) and demand[k].strip() and demand[k] == allowed.get(k) for k in SCOPE)
                and isinstance(allowed.get("metrics"), list)
                and all(isinstance(m, str) and m.strip() for m in demand["metrics"])
                and all(isinstance(m, str) and m.strip() for m in allowed["metrics"])
                and set(demand["metrics"]).issubset(set(allowed["metrics"])))

        if not any(covers(s) for s in scopes):
            faults.append("finding_outside_checked_scope")
    return {"verdict": "PASS" if not faults else "BLOCKED", "reasons": faults}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: scope_gate.py qa.json finding.json")
    with open(sys.argv[1], encoding="utf-8") as f:
        qa = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        finding = json.load(f)
    result = check_scope(qa, finding)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

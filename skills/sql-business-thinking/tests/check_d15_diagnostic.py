"""D15: validate one diagnostic design, not a query result."""
from pathlib import Path

SOURCE_RUN = 37725587099
CANDIDATE = {
    "source_run": SOURCE_RUN,
    "scope": ("withdrawal", ("failed", "cancelled")),
    "expected_records": 2,
    "columns": ("fiat_order_id", "uid", "direction", "status"),
    "question": "Do both terminal-noncompleted withdrawal events have the same uid?",
    "same_uid": ("H1_SUPPORTED", "H2_REFUTED", "CAUSE_UNRESOLVED"),
    "different_uid": ("H1_REFUTED", "H2_SUPPORTED", "CAUSE_UNRESOLVED"),
    "invalid_evidence": ("H1_UNTESTED", "H2_UNTESTED", "CAUSE_UNRESOLVED"),
}

def validate_design(q):
    if q.get("source_run") != SOURCE_RUN:
        return "INVALID_PROVENANCE"
    if q.get("scope") != CANDIDATE["scope"] or q.get("expected_records") != 2:
        return "SCOPE_DRIFT"
    if set(q.get("columns", ())) != set(CANDIDATE["columns"]):
        return "MISSING_OR_EXTRA_FIELDS"
    states = (q.get("same_uid"), q.get("different_uid"), q.get("invalid_evidence"))
    if states != (CANDIDATE["same_uid"], CANDIDATE["different_uid"],
                  CANDIDATE["invalid_evidence"]):
        return "NONDISCRIMINATING_BRANCH"
    if q.get("sql") or q.get("root_cause") or q.get("observed_uid"):
        return "PREMATURE_EVIDENCE"
    return "QUALIFIED"

def assess_records(rows):
    if len(rows) != 2 or len({r.get("fiat_order_id") for r in rows}) != 2:
        return CANDIDATE["invalid_evidence"]
    for r in rows:
        if not r.get("fiat_order_id") or not r.get("uid"):
            return CANDIDATE["invalid_evidence"]
        if r.get("direction") != "withdrawal" or r.get("status") not in {"failed", "cancelled"}:
            return CANDIDATE["invalid_evidence"]
    return CANDIDATE["same_uid"] if rows[0]["uid"] == rows[1]["uid"] else CANDIDATE["different_uid"]

def main():
    assert validate_design(CANDIDATE) == "QUALIFIED"
    a = {"fiat_order_id": "SIMULATED_1", "uid": "SIM_A", "direction": "withdrawal", "status": "failed"}
    b = {"fiat_order_id": "SIMULATED_2", "uid": "SIM_A", "direction": "withdrawal", "status": "cancelled"}
    assert assess_records([a, b]) == CANDIDATE["same_uid"]
    assert assess_records([a, {**b, "uid": "SIM_B"}]) == CANDIDATE["different_uid"]
    for sample in ([a], [a, a], [a, {**b, "uid": None}], [a, {**b, "status": "pending"}],
                   [a, {**b, "direction": "deposit"}]):
        assert assess_records(sample) == CANDIDATE["invalid_evidence"]
    for change, expected in [
        ({"source_run": 1}, "INVALID_PROVENANCE"),
        ({"scope": ("deposit", ("failed", "cancelled"))}, "SCOPE_DRIFT"),
        ({"columns": ("uid", "status")}, "MISSING_OR_EXTRA_FIELDS"),
        ({"same_uid": CANDIDATE["different_uid"]}, "NONDISCRIMINATING_BRANCH"),
        ({"root_cause": "bank failure"}, "PREMATURE_EVIDENCE"),
        ({"sql": "SELECT 1"}, "PREMATURE_EVIDENCE"),
    ]:
        assert validate_design({**CANDIDATE, **change}) == expected
    print("PASS: D15 one bounded diagnostic; 2 simulated outcomes, 11 invalid cases")
    print("NOTE: uid values above are synthetic. No D15 SQL or new business result.")

if __name__ == "__main__":
    main()

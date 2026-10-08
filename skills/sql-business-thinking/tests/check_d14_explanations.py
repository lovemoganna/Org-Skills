"""D14 competing hypotheses: D11 evidence and synthetic counterexamples only.

D11 run 37725587099 reports two terminal-noncompleted withdrawal records,
but does not return individual fiat_order_id or uid values.
The synthetic rows below MUST NOT be presented as real users or transactions.
"""


def evaluate(rows=None, claims_cause=False):
    if claims_cause:
        raise ValueError("Distribution is not evidence of root cause")
    if rows is None:
        return {
            "same_uid": "UNTESTED",
            "different_uid": "UNTESTED",
            "root_cause": "UNRESOLVED",
            "needed": ("fiat_order_id", "uid", "direction", "status"),
        }
    if len(rows) != 2:
        raise ValueError("Expected exactly two case records for this hypothesis")
    ids = [r.get("fiat_order_id") for r in rows]
    uids = [r.get("uid") for r in rows]
    if not all(ids) or len(set(ids)) != 2 or not all(uids):
        raise ValueError("Missing/duplicate case ID or unknown user")
    for r in rows:
        if r.get("direction") != "withdrawal" or r.get("status") not in {"failed", "cancelled"}:
            raise ValueError("Wrong direction or status scope")
    same = len(set(uids)) == 1
    return {
        "same_uid": "SUPPORTED" if same else "REFUTED",
        "different_uid": "REFUTED" if same else "SUPPORTED",
        "root_cause": "UNRESOLVED",
    }


def rejects(rows, claims_cause=False):
    try:
        evaluate(rows, claims_cause)
    except ValueError:
        return True
    return False


def main():
    initial = evaluate()
    assert initial["same_uid"] == "UNTESTED"
    assert initial["different_uid"] == "UNTESTED"
    assert initial["root_cause"] == "UNRESOLVED"
    # Counterfactual fixtures, NOT actual query results
    same = [
        {"fiat_order_id": "fake1", "uid": "testA", "direction": "withdrawal", "status": "failed"},
        {"fiat_order_id": "fake2", "uid": "testA", "direction": "withdrawal", "status": "cancelled"},
    ]
    different = [dict(same[0]), {**same[1], "uid": "testB"}]
    assert evaluate(same) == {
        "same_uid": "SUPPORTED", "different_uid": "REFUTED", "root_cause": "UNRESOLVED"}
    assert evaluate(different) == {
        "same_uid": "REFUTED", "different_uid": "SUPPORTED", "root_cause": "UNRESOLVED"}
    assert rejects([same[0]])
    assert rejects([same[0], same[0]])
    assert rejects([same[0], {**same[1], "uid": None}])
    assert rejects([same[0], {**same[1], "status": "pending"}])
    assert rejects([same[0], {**same[1], "direction": "deposit"}])
    assert rejects(same, claims_cause=True)
    assert evaluate()["root_cause"] == "UNRESOLVED"
    print("PASS: D14 competing user-distribution hypotheses, 2 synthetic outcomes, 6 invalid cases")
    print("NOTE: no user-level D11 results and no causal conclusion")


if __name__ == "__main__":
    main()

"""D09 quality and priority tests. Uses verified source counts, not invented query results."""

FIELDS = {"direction", "status", "fiat_order_id", "created_at", "completed_at"}


def evaluate(q):
    if not q.get("metric_ref") or not q.get("ontology_ref"):
        return "missing_origin"
    if not q.get("trigger") or not q.get("decision_goal"):
        return "no_decision_goal"
    if not set(q.get("fields", [])) <= FIELDS or not q.get("fields"):
        return "unanswerable"
    if not q.get("if_yes") or not q.get("if_no"):
        return "missing_result_branch"
    if q["if_yes"] == q["if_no"]:
        return "no_consequence"
    if q.get("premature_claim") or q.get("claims_systemic_issue"):
        return "premature_conclusion"
    if q.get("sparse") and not q.get("small_sample_limit"):
        return "missing_small_sample_boundary"
    if q.get("metric_only") or q.get("mechanical_slice"):
        return "low_value"
    return "QUALIFIED"


def choose(candidates):
    approved, rejected = [], []
    for q in candidates:
        result = evaluate(q)
        if result == "QUALIFIED":
            approved.append(q)
        else:
            rejected.append((q.get("id"), result))
    if not approved:
        return {"status": "NO_QUESTION", "selected": None, "rejected": rejected}
    if len(approved) > 1:
        return {"status": "PRIORITY_UNRESOLVED", "selected": None,
                "rejected": rejected}
    return {"status": "QUALIFIED_EXPLORATORY", "selected": approved[0],
            "rejected": rejected}


def test():
    # Count-only evidence from DuckDB-Wasm discovery: 25 fiat, 21 completed,
    # 2 ongoing, 2 terminal non-completed. Direction distribution NOT queried.
    assert 21 + 2 + 2 == 25
    q = {"id": "D08-Q1", "metric_ref": "D07/fiat-completed-status-share",
         "ontology_ref": "D06/fiat-direction-status",
         "trigger": "25 fiat records; 4 not completed, with distinct lifecycle states",
         "decision_goal": "Decide whether a direction-specific follow-up is justified",
         "fields": ["direction", "status", "fiat_order_id"],
         "if_yes": "Inspect individual records by direction, no structural claim",
         "if_no": "Stop direction drilldown",
         "small_sample_limit": "Descriptive comparison only; no statistical inference",
         "sparse": True,
         "premature_claim": False,
         "claims_systemic_issue": False,
         "metric_only": False,
         "mechanical_slice": False}
    ans = choose([q])
    assert ans["status"] == "QUALIFIED_EXPLORATORY"
    assert ans["selected"]["id"] == "D08-Q1"
    assert choose([])["status"] == "NO_QUESTION"
    for patch, expected in [
        ({"metric_ref": None}, "missing_origin"),
        ({"decision_goal": None}, "no_decision_goal"),
        ({"fields": ["source_wallet_identity"]}, "unanswerable"),
        ({"if_no": q["if_yes"]}, "no_consequence"),
        ({"if_yes": None}, "missing_result_branch"),
        ({"small_sample_limit": None}, "missing_small_sample_boundary"),
        ({"claims_systemic_issue": True}, "premature_conclusion"),
        ({"metric_only": True}, "low_value"),
        ({"mechanical_slice": True}, "low_value"),
    ]:
        r = choose([{**q, **patch}])
        assert r["status"] == "NO_QUESTION", (patch, r)
        assert r["rejected"][0][1] == expected
    other = {**q, "id": "D08-Q2", "decision_goal": "Another separate objective",
             "if_yes": "Different investigation", "if_no": "Stop other branch"}
    assert choose([q, other])["status"] == "PRIORITY_UNRESOLVED"
    print("PASS: D09 selects one bounded exploratory question; 11 rejection/ambiguity checks")
    print("NOTE: no directional SQL was executed; no observed direction difference is claimed")


if __name__ == "__main__":
    test()

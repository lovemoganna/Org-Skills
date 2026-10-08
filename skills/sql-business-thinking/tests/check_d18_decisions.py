"""D18 decision-value gate regression. Source: real D11 aggregate via D17.

This checks evidence/decision contracts. It does NOT execute new SQL or
establish operational causes, urgent incidents, user identities, or current states.
"""
from copy import deepcopy
from check_d17_findings import EVIDENCE, validate_and_derive

DISALLOWED_ACTIONS = {
    "prioritize_withdrawal_as_systemic_risk",
    "declare_current_backlog",
    "allocate_incident_resources",
    "claim_same_uid",
    "claim_root_cause",
    "publish_dashboard_alert",
}


def evaluate(evidence, *, declared_action=None, decision_goal="historical_analysis"):
    findings = validate_and_derive(evidence)
    facts = findings["verified"]
    counts = facts["record_counts"]
    original = facts["all_orders_completed_share"]
    terminal = facts["terminal_only_completed_share"]
    reversed_ranking = bool(facts["rank_reversal"])
    if declared_action in DISALLOWED_ACTIONS:
        raise ValueError("UNSUPPORTED_OPERATIONAL_DECISION")
    if decision_goal not in {"historical_analysis", "operational_triage"}:
        raise ValueError("UNKNOWN_DECISION_GOAL")

    decision_level = []
    if reversed_ranking:
        decision_level.append({
            "id": "D18-METRIC-CAUTION",
            "kind": "interpretation_decision",
            "source": ("D17/F1", "D17/F2"),
            "changes": "Do not use a single completed-share denominator to rank directions",
            "reason": "Direction ranking reverses between all-record and terminal-only denominators",
            "limits": "25 historical fiat order records; does not determine operational risk",
        })

    return {
        "decision_level": decision_level,
        "report_facts": [
            {"source": "D17/F1", "evidence": counts,
             "interpretation": "Recorded status composition differs by direction"},
            {"source": "D17/F2",
             "original_share": original,
             "terminal_only_share": terminal,
             "interpretation": "Auxiliary denominator is not the original KPI"},
        ],
        "operational_actions": [],
        "operational_status": "UNDETERMINED",
        "missing_evidence": [
            "current order statuses",
            "case-level fiat_order_id and uid for terminal-noncompleted withdrawal events",
            "failure or cancellation reasons",
            "business action threshold or defined operational objective",
        ],
        "excluded": sorted(DISALLOWED_ACTIONS),
    }


def rejects(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def main():
    d = evaluate(EVIDENCE)
    assert len(d["decision_level"]) == 1
    assert d["decision_level"][0]["kind"] == "interpretation_decision"
    assert "single completed-share denominator" in d["decision_level"][0]["changes"]
    assert d["report_facts"][0]["evidence"]["withdrawal"]["terminal_other"] == 2
    assert d["report_facts"][0]["evidence"]["deposit"]["ongoing"] == 2
    assert d["operational_actions"] == []
    assert d["operational_status"] == "UNDETERMINED"
    assert evaluate(EVIDENCE, decision_goal="operational_triage")["operational_actions"] == []
    for unsupported in DISALLOWED_ACTIONS:
        assert rejects(lambda x=unsupported: evaluate(EVIDENCE, declared_action=x))
    for field, altered in [("run_id", 0), ("data_revision", "stale"),
                           ("sql_sha256", "not-source"), ("gate_state", "BLOCKED")]:
        fake = deepcopy(EVIDENCE)
        fake[field] = altered
        assert rejects(lambda fake=fake: evaluate(fake))
    bad = deepcopy(EVIDENCE)
    bad["rows"][1]["completed"] = 10
    assert rejects(lambda: evaluate(bad))
    assert rejects(lambda: evaluate(EVIDENCE, decision_goal="make-up-a-budget"))
    assert "current order statuses" in d["missing_evidence"]
    print("PASS: D18 1 bounded metric-interpretation decision; operational claims rejected")
    print("PASS: D18 12 negative source/claim/goal tests; D17 aggregate reused, no fresh SQL")


if __name__ == "__main__":
    main()

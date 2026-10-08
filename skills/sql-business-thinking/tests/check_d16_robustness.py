"""D16 sensitivity-design regression; uses D11 aggregated facts, no new business SQL."""
RUN_ID = 37725587099
DATA_REVISION = "561287b5d150e3c11735562b0a4f3d670b9e5b8ccecb818d1a26bcfb720b3335"
# Values are from the verified D11 Result, NOT simulated user-level evidence.
RESULT = {
    "deposit": {"total": 12, "completed": 10, "ongoing": 2, "terminal_other": 0},
    "withdrawal": {"total": 13, "completed": 11, "ongoing": 0, "terminal_other": 2},
}
PLAN = {
    "source_run": RUN_ID,
    "data_revision": DATA_REVISION,
    "question": "Does the direction comparison survive excluding in-progress records?",
    "baseline_population": "all_authorized_fiat_orders",
    "sensitivity_population": "completed_failed_cancelled_only",
    "excluded_states": ("pending", "processing"),
    "numerator": "status_eq_completed",
    "group_by": "direction",
    "unit": "order_records",
    "criterion": "compare direction ranking under both definitions; no significance claim",
    "if_changes": "narrow original completed-share comparison to its all-record denominator",
    "if_stable": "retain descriptive result subject to 25-record and historical-status limits",
    "if_invalid": "stop, do not infer robustness from unknown states or missing evidence",
    "unresolved_diagnostics": True,
    "new_sql": None,
    "claims_cause": False,
}


def validate_plan(plan, rows):
    if plan.get("source_run") != RUN_ID or plan.get("data_revision") != DATA_REVISION:
        return "STALE_EVIDENCE"
    if set(rows) != {"deposit", "withdrawal"}:
        return "INVALID_GRAIN"
    for x in rows.values():
        if x["total"] != x["completed"] + x["ongoing"] + x["terminal_other"]:
            return "INVALID_STATE_PARTITION"
    if (plan.get("baseline_population") != "all_authorized_fiat_orders" or
        plan.get("sensitivity_population") != "completed_failed_cancelled_only" or
        tuple(plan.get("excluded_states", ())) != ("pending", "processing")):
        return "UNDISCLOSED_DENOMINATOR_CHANGE"
    if (plan.get("numerator") != "status_eq_completed" or
        plan.get("group_by") != "direction" or
        plan.get("unit") != "order_records"):
        return "METRIC_DRIFT"
    if not all(plan.get(k) for k in ("question", "criterion", "if_changes", "if_stable", "if_invalid")):
        return "NO_DISCRIMINATING_OUTCOME"
    if any(plan.get(k) for k in ("new_sql", "claims_cause", "claimed_uid", "significance_claim")):
        return "UNSUPPORTED_FACT"
    if plan.get("unresolved_diagnostics") is not True:
        return "FALSE_DIAGNOSTIC_EVIDENCE"
    return "QUALIFIED"


def descriptive_rates(rows):
    """Arithmetic cross-check of the fixture; never a new D11 SQL run."""
    result = {}
    for direction, row in rows.items():
        initial = row["completed"] / row["total"] if row["total"] else None
        final_den = row["completed"] + row["terminal_other"]
        sensitivity = row["completed"] / final_den if final_den else None
        result[direction] = (initial, sensitivity)
    return result


def main():
    assert validate_plan(PLAN, RESULT) == "QUALIFIED"
    rates = descriptive_rates(RESULT)
    assert rates["deposit"][0] < rates["withdrawal"][0]
    assert rates["deposit"][1] > rates["withdrawal"][1]
    # Counterexamples must be rejected rather than silently altering analysis meaning.
    for patch, reason in [
        ({"source_run": 1}, "STALE_EVIDENCE"),
        ({"baseline_population": "terminal_only"}, "UNDISCLOSED_DENOMINATOR_CHANGE"),
        ({"sensitivity_population": "all_authorized_fiat_orders"}, "UNDISCLOSED_DENOMINATOR_CHANGE"),
        ({"excluded_states": ("failed", "cancelled")}, "UNDISCLOSED_DENOMINATOR_CHANGE"),
        ({"group_by": "channel"}, "METRIC_DRIFT"),
        ({"unit": "users"}, "METRIC_DRIFT"),
        ({"if_changes": None}, "NO_DISCRIMINATING_OUTCOME"),
        ({"new_sql": "SELECT 1"}, "UNSUPPORTED_FACT"),
        ({"claims_cause": True}, "UNSUPPORTED_FACT"),
        ({"claimed_uid": "SIM_USER"}, "UNSUPPORTED_FACT"),
        ({"unresolved_diagnostics": False}, "FALSE_DIAGNOSTIC_EVIDENCE"),
    ]:
        got = validate_plan({**PLAN, **patch}, RESULT)
        assert got == reason, (patch, got, reason)
    modified = {**RESULT, "deposit": {**RESULT["deposit"], "ongoing": 3}}
    assert validate_plan(PLAN, modified) == "INVALID_STATE_PARTITION"
    print("PASS: D16 evidence-bounded alternative denominator sensitivity design; 12 invalid cases")
    print("NOTE: arithmetic derived from D11 aggregates; no new SQL or uid/cause evidence")


if __name__ == "__main__":
    main()

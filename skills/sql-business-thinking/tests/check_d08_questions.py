"""D08 candidate quality regression. Synthetic cases; no business SQL execution."""
from collections import Counter

FIAT = {"completed": 21, "failed": 1, "cancelled": 1, "pending": 1, "processing": 1}
CRYPTO = {"completed": 22, "failed": 1, "confirming": 1, "processing": 1}


def evidence(stats):
    ongoing = {"pending", "processing", "confirming"}
    terminal_other = {"failed", "cancelled"}
    return {
        "total": sum(stats.values()),
        "completed": stats.get("completed", 0),
        "ongoing": sum(v for k, v in stats.items() if k in ongoing),
        "terminal_other": sum(v for k, v in stats.items() if k in terminal_other),
    }


def validate(candidate, context):
    if not candidate.get("metric_ref") or not candidate.get("ontology_ref"):
        return "no_provenance"
    if candidate.get("already_known"):
        return "repeats_known_fact"
    if candidate.get("outcome") == "systemic_anomaly":
        return "assumes_anomaly"
    if candidate.get("status_group") == "noncompleted_as_failure":
        return "mixes_lifecycle_states"
    if candidate.get("single_judgment") is not True:
        return "non_atomic"
    if not candidate.get("a_changes") or not candidate.get("b_changes") or candidate["a_changes"] == candidate["b_changes"]:
        return "no_branching_value"
    if candidate.get("limited_evidence") and not candidate.get("limitation"):
        return "no_small_sample_boundary"
    if candidate.get("claims_test_result"):
        return "prejudges_unexecuted_sql"
    return "KEEP"


def main():
    assert evidence(FIAT) == {"total": 25, "completed": 21, "ongoing": 2, "terminal_other": 2}
    assert evidence(CRYPTO) == {"total": 25, "completed": 22, "ongoing": 2, "terminal_other": 1}
    good = {
        "metric_ref": "D07/fiat_completed_status_share",
        "ontology_ref": "D06/fiat_direction_with_status",
        "already_known": False,
        "outcome": "exploratory_question",
        "status_group": "completed_vs_other_descriptive",
        "single_judgment": True,
        "a_changes": "若方向差异值得后续验证，则进入独立解释路径",
        "b_changes": "若未见值得验证的方向差异，则停止该切片",
        "limited_evidence": True,
        "limitation": "25 条历史记录、仅 4 条非 completed；不推断显著性或系统性异常",
        "claims_test_result": False,
    }
    assert validate(good, FIAT) == "KEEP"
    for changes, expected in [
        ({"status_group": "noncompleted_as_failure"}, "mixes_lifecycle_states"),
        ({"outcome": "systemic_anomaly"}, "assumes_anomaly"),
        ({"already_known": True}, "repeats_known_fact"),
        ({"metric_ref": None}, "no_provenance"),
        ({"single_judgment": False}, "non_atomic"),
        ({"b_changes": good["a_changes"]}, "no_branching_value"),
        ({"limitation": None}, "no_small_sample_boundary"),
        ({"claims_test_result": True}, "prejudges_unexecuted_sql"),
    ]:
        test = {**good, **changes}
        assert validate(test, FIAT) == expected, (changes, expected)
    # Duplicate variants add no independent value: channel/network/direction alone are not a new question.
    variants = ["fiat_completed_share_by_direction", "fiat_completed_share_by_direction"]
    assert Counter(variants).most_common(1)[0][1] == 2
    assert len(set(variants)) == 1
    print("PASS: D08 real-baseline status arithmetic + 8 negative cases + duplicate check")
    print("NOTE: tests use DuckDB-Wasm verified counts as fixtures; D08 does not execute business SQL")


if __name__ == "__main__":
    main()

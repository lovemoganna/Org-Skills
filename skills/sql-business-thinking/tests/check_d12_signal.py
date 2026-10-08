"""D12 interpretation regression against verified D11 result snapshot, no SQL run.

Source: GitHub Actions run 37725587099, DuckDB-Wasm v1.5.4,
logical revision 561287b5d150e3c11735562b0a4f3d670b9e5b8ccecb818d1a26bcfb720b3335.
"""
from copy import deepcopy

RUN_ID = 37725587099
SQL_SHA256 = "93530dba3c5e19e0d33964e0e14f1d36180a1c66d1f62e2f492cbe5c59d30b50"
DATA_REVISION = "561287b5d150e3c11735562b0a4f3d670b9e5b8ccecb818d1a26bcfb720b3335"
ROWS = [
    {"direction": "deposit", "total": 12, "completed": 10, "in_progress": 2,
     "terminal_noncompleted": 0, "unknown": 0},
    {"direction": "withdrawal", "total": 13, "completed": 11, "in_progress": 0,
     "terminal_noncompleted": 2, "unknown": 0},
]


def interpret(rows):
    by_direction = {r["direction"]: r for r in rows}
    if len(rows) != 2 or set(by_direction) != {"deposit", "withdrawal"}:
        raise ValueError("Unexpected result grain")
    for row in rows:
        if row["total"] <= 0 or any(
            not isinstance(row[x], int) or row[x] < 0
            for x in ("total", "completed", "in_progress", "terminal_noncompleted", "unknown")
        ):
            raise ValueError("Invalid counts")
        if row["total"] != sum(row[k] for k in (
            "completed", "in_progress", "terminal_noncompleted", "unknown"
        )):
            raise ValueError("Non-exclusive or incomplete status classification")
    deposit, withdrawal = by_direction["deposit"], by_direction["withdrawal"]
    gap = 100 * (withdrawal["completed"] / withdrawal["total"] -
                 deposit["completed"] / deposit["total"])
    status_mix_contrast = (
        deposit["in_progress"] > 0 and deposit["terminal_noncompleted"] == 0
        and withdrawal["terminal_noncompleted"] > 0
        and withdrawal["in_progress"] == 0
    )
    return {"completed_gap_pp": gap,
            "observed_status_mix_contrast": status_mix_contrast,
            "scope": "recorded historical status, NOT current operational state",
            "limitation": "25 total records, 4 noncompleted; no inference of cause or systemic anomaly"}


def rejects(rows):
    try:
        interpret(rows)
    except ValueError:
        return True
    return False


def main():
    assert len(SQL_SHA256) == 64 and len(DATA_REVISION) == 64
    result = interpret(ROWS)
    assert abs(result["completed_gap_pp"] - 1.2820512820512775) < 1e-10
    assert result["observed_status_mix_contrast"] is True
    assert "NOT current operational state" in result["scope"]
    assert "no inference of cause" in result["limitation"]
    assert not rejects(ROWS)

    same_mix = deepcopy(ROWS)
    same_mix[1]["in_progress"] = 2
    same_mix[1]["terminal_noncompleted"] = 0
    assert interpret(same_mix)["observed_status_mix_contrast"] is False

    equal_rate_different_states = deepcopy(ROWS)
    equal_rate_different_states[1]["total"] = 12
    equal_rate_different_states[1]["completed"] = 10
    assert interpret(equal_rate_different_states)["observed_status_mix_contrast"] is True
    assert abs(interpret(equal_rate_different_states)["completed_gap_pp"]) < 1e-10

    invalid = deepcopy(ROWS)
    invalid[0]["in_progress"] = 3
    assert rejects(invalid)
    duplicate = deepcopy(ROWS)
    duplicate[1]["direction"] = "deposit"
    assert rejects(duplicate)
    zero = deepcopy(ROWS)
    zero[0]["total"] = 0
    assert rejects(zero)

    print("PASS: D12 actual-result arithmetic, status-mix contrast, historical-state limitation")
    print("PASS: 5 counterfactual/invalid result checks")
    print("NOTE: recorded D11 source result reused; no new SQL executed, no cause inferred")


if __name__ == "__main__":
    main()

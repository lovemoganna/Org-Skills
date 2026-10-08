"""D17 verified findings regression.

Evidence fixture copied from real DuckDB-Wasm D11 run 37725587099.
This does not execute a new business query or resolve D15's uid question.
"""
from copy import deepcopy

EVIDENCE = {
    "run_id": 37725587099,
    "sql_sha256": "93530dba3c5e19e0d33964e0e14f1d36180a1c66d1f62e2f492cbe5c59d30b50",
    "data_revision": "561287b5d150e3c11735562b0a4f3d670b9e5b8ccecb818d1a26bcfb720b3335",
    "gate_state": "PASS",
    "rows": [
        {"direction": "deposit", "total": 12, "completed": 10, "ongoing": 2,
         "terminal_other": 0, "unknown": 0},
        {"direction": "withdrawal", "total": 13, "completed": 11, "ongoing": 0,
         "terminal_other": 2, "unknown": 0},
    ],
}

EXPECTED_RUN = 37725587099
EXPECTED_REVISION = "561287b5d150e3c11735562b0a4f3d670b9e5b8ccecb818d1a26bcfb720b3335"
EXPECTED_SQL = "93530dba3c5e19e0d33964e0e14f1d36180a1c66d1f62e2f492cbe5c59d30b50"


def validate_and_derive(source, *, diagnostic_result=None, claim_cause=False):
    if (source.get("run_id") != EXPECTED_RUN or
        source.get("data_revision") != EXPECTED_REVISION or
        source.get("sql_sha256") != EXPECTED_SQL or
        source.get("gate_state") != "PASS"):
        raise ValueError("STALE_OR_UNVERIFIED_SOURCE")
    rows = source.get("rows")
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("INVALID_ROWS")
    by = {r.get("direction"): r for r in rows}
    if set(by) != {"deposit", "withdrawal"} or len(by) != len(rows):
        raise ValueError("INVALID_DIRECTION")
    for r in rows:
        vals = [r.get(k) for k in ("total", "completed", "ongoing", "terminal_other", "unknown")]
        if any(type(v) is not int or v < 0 for v in vals):
            raise ValueError("INVALID_COUNT")
        if vals[0] == 0 or vals[0] != sum(vals[1:]):
            raise ValueError("INVALID_PARTITION")
    if sum(r["total"] for r in rows) != 25:
        raise ValueError("SOURCE_TOTAL_MISMATCH")
    if claim_cause or diagnostic_result is not None:
        raise ValueError("UNSUPPORTED_DIAGNOSTIC_OR_CAUSE")

    d, w = by["deposit"], by["withdrawal"]
    original = {k: r["completed"] / r["total"] for k,r in by.items()}
    terminal = {}
    for key,r in by.items():
        terminal_denominator = r["completed"] + r["terminal_other"]
        terminal[key] = r["completed"] / terminal_denominator if terminal_denominator else None
    if None in terminal.values():
        raise ValueError("INVALID_TERMINAL_DENOMINATOR")

    return {
        "verified": {
            "record_counts": {key: {k: r[k] for k in (
                "total","completed","ongoing","terminal_other","unknown")}
                for key,r in by.items()},
            "all_orders_completed_share": original,
            "terminal_only_completed_share": terminal,
            "rank_reversal": original["deposit"] < original["withdrawal"]
                             and terminal["deposit"] > terminal["withdrawal"],
        },
        "rejected": ["systemic_direction_risk", "root_cause",
                     "same_uid_for_two_withdrawal_records", "current_pending_orders"],
        "limits": ["25 historical fiat order records", "4 noncompleted states",
                   "no uid diagnostic result", "no status-transition history",
                   "alternative denominator is not original metric"],
    }


def reject(source, *, diagnostic_result=None, claim_cause=False):
    try:
        validate_and_derive(source, diagnostic_result=diagnostic_result,
                            claim_cause=claim_cause)
    except ValueError:
        return True
    return False


def main():
    result = validate_and_derive(EVIDENCE)
    r = result["verified"]
    assert r["record_counts"]["deposit"]["total"] == 12
    assert r["record_counts"]["withdrawal"]["total"] == 13
    assert abs(r["all_orders_completed_share"]["deposit"] - 10/12) < 1e-12
    assert abs(r["all_orders_completed_share"]["withdrawal"] - 11/13) < 1e-12
    assert r["terminal_only_completed_share"]["deposit"] == 1.0
    assert abs(r["terminal_only_completed_share"]["withdrawal"] - 11/13) < 1e-12
    assert r["rank_reversal"] is True
    assert "same_uid_for_two_withdrawal_records" in result["rejected"]
    assert "root_cause" in result["rejected"]
    assert "alternative denominator is not original metric" in result["limits"]

    for patch in [
        {"run_id": 1}, {"data_revision": "stale"}, {"sql_sha256": "wrong"},
        {"gate_state": "BLOCKED"}
    ]:
        assert reject({**EVIDENCE, **patch}), patch
    for changed in [
        lambda x: x["rows"][0].update(total=13),
        lambda x: x["rows"][0].update(unknown=1),
        lambda x: x["rows"][0].update(completed=-1),
        lambda x: x["rows"][0].update(direction="withdrawal"),
        lambda x: x["rows"].pop(),
    ]:
        invalid = deepcopy(EVIDENCE)
        changed(invalid)
        assert reject(invalid)
    assert reject(EVIDENCE, claim_cause=True)
    assert reject(EVIDENCE, diagnostic_result={"uid_same": True})
    print("PASS: D17 two evidence-backed bounded findings, denominator reversal, 11 invalid/causal cases")
    print("NOTE: D11 recorded Result reused, no fresh business SQL, no D15 uid evidence")


if __name__ == "__main__":
    main()

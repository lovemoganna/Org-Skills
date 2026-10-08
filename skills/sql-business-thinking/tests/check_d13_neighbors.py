"""D13 ontology-local expansion regression. No business SQL is executed.

Evidence boundary:
D11 GitHub Actions run 37725587099 (DuckDB-Wasm).
D12 signal: withdrawal contains 2 recorded failed/cancelled rows;
deposit contains 2 recorded pending/processing rows.
Verified schema relationship: fiat_transactions.uid -> users.uid.
Actual per-row uid values have NOT been queried in D11.
"""
SIGNAL = {
    "source": "D12/D11-run-37725587099",
    "rail": "fiat",
    "direction": "withdrawal",
    "terminal_noncompleted_records": 2,
    "historical": True,
}
AUTHORIZED_FIELDS = {
    "fiat_transactions": {
        "fiat_order_id", "uid", "direction", "status",
        "channel", "created_at", "completed_at", "currency", "amount", "fee"
    },
    "users": {"uid", "account_status", "kyc_level", "country_code", "created_at"},
}
# This is a bounded schema/ontology relationship fixture, not a substitute for the D05/D06 tables.
VERIFIED_EDGES = {
    ("fiat_transactions", "uid", "users", "uid"),
}

def assess(candidate, signal=SIGNAL):
    if not signal or not signal.get("source"):
        return "NO_SIGNAL"
    if candidate.get("trace") != signal["source"]:
        return "NO_SIGNAL_PROVENANCE"
    table = candidate.get("table")
    field = candidate.get("field")
    if field not in AUTHORIZED_FIELDS.get(table, set()):
        return "FIELD_NOT_AUTHORIZED"
    if candidate.get("needs_edge"):
        if candidate.get("needs_edge") not in VERIFIED_EDGES:
            return "UNVERIFIED_RELATION"
    if candidate.get("claims_causation") or candidate.get("cross_domain_flow"):
        return "UNSUPPORTED_CAUSATION"
    if candidate.get("asserts_new_result"):
        return "PREMATURE_RESULT"
    if candidate.get("scope") != "two_record_case_review":
        return "BAD_GRAIN_OR_SCOPE"
    if candidate.get("yes_action") == candidate.get("no_action") or (
        not candidate.get("yes_action") or not candidate.get("no_action")
    ):
        return "NO_DECISION_VALUE"
    if candidate.get("already_answered"):
        return "REPEATS_KNOWN_FACT"
    return "CANDIDATE_ONLY"

def main():
    base = {
        "trace": SIGNAL["source"],
        "table": "fiat_transactions",
        "field": "uid",
        "needs_edge": ("fiat_transactions", "uid", "users", "uid"),
        "scope": "two_record_case_review",
        "claims_causation": False,
        "cross_domain_flow": False,
        "asserts_new_result": False,
        "already_answered": False,
        "yes_action": "Review whether two records belong to same user case",
        "no_action": "Review both records separately",
    }
    assert assess(base) == "CANDIDATE_ONLY"
    cases = [
        ({}, {"NO_SIGNAL"}),
        ({"source": None}, {"NO_SIGNAL"}),
    ]
    for signal, expected in cases:
        assert assess(base, signal) in expected
    negatives = [
        ({"trace": "invented"}, "NO_SIGNAL_PROVENANCE"),
        ({"table": "fiat_transactions", "field": "network"}, "FIELD_NOT_AUTHORIZED"),
        ({"needs_edge": ("fiat_transactions", "uid", "crypto_transactions", "tx_hash")},
         "UNVERIFIED_RELATION"),
        ({"claims_causation": True}, "UNSUPPORTED_CAUSATION"),
        ({"cross_domain_flow": True}, "UNSUPPORTED_CAUSATION"),
        ({"asserts_new_result": True}, "PREMATURE_RESULT"),
        ({"scope": "all_users_systemic_anomaly"}, "BAD_GRAIN_OR_SCOPE"),
        ({"no_action": base["yes_action"]}, "NO_DECISION_VALUE"),
        ({"already_answered": True}, "REPEATS_KNOWN_FACT"),
    ]
    for patch, expected in negatives:
        assert assess({**base, **patch}) == expected, (patch, expected)
    assert SIGNAL["terminal_noncompleted_records"] == 2
    print("PASS: D13 1 bounded candidate, 11 negative signal/relationship/scope cases")
    print("NOTE: no new SQL and no evidence that the two withdrawal records share a uid")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent regression of the historical post-hoc Gate 1 failure."""
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_run_lineage import check  # noqa

def fixture():
    now = datetime.now(timezone.utc)
    stamp = lambda t: t.isoformat()
    return {
        "stages": [{"stage":"Gate 1 本体结构与语义", "at":stamp(now),
                    "details":{"status":"PASS","source_check":"PASS_STRUCTURE_AND_SOURCE_ONLY",
                               "semantic_review":{"status":"PASS","evidence":["real-source-schema", "relationship-domain-verification"]}}}],
        "queries":[{"id":"original-business-question", "timestamp":stamp(now+timedelta(seconds=1)),
                    "status":"PASS","rows":[{"observed":1}]}],
    }

class SequenceRegression(unittest.TestCase):
    def test_valid_order_retains_core_capability(self):
        self.assertEqual([], check(fixture()))
    def test_original_failure_post_hoc_gate1(self):
        d=fixture()
        early=datetime.fromisoformat(d["stages"][0]["at"])-timedelta(minutes=1)
        prior={"generated_at":early.isoformat(),"queries":{
            "historical-exploration":{"sql":"SELECT region, SUM(amount) FROM orders GROUP BY region"}}}
        self.assertTrue(any("PRIOR_ANALYSIS_BEFORE_GATE1" in e for e in check(d,prior)))
    def test_gate1_self_declared_pass_is_not_proof(self):
        d=fixture()
        d["stages"][0]["details"].pop("semantic_review")
        self.assertIn("GATE1_SEMANTIC_EVIDENCE_MISSING",check(d))
    def test_missing_official_source_checker_fails(self):
        d=fixture();d["stages"][0]["details"].pop("source_check")
        self.assertIn("GATE1_SOURCE_CHECK_MISSING", check(d))
    def test_query_before_gate_is_rejected(self):
        d=fixture()
        d["queries"][0]["timestamp"]=(datetime.fromisoformat(d["stages"][0]["at"])-timedelta(seconds=1)).isoformat()
        self.assertTrue(any("ANALYSIS_SQL_BEFORE_GATE1" in e for e in check(d)))
    def test_single_sum_before_gate_is_analysis(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "net-amount":{"sql":"SELECT SUM(amount) FROM orders"}}}
        self.assertTrue(any("PRIOR_ANALYSIS_BEFORE_GATE1" in e for e in check(d,prior)))

    def test_late_generated_log_cannot_hide_early_query(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=5)).isoformat()
        after = (datetime.fromisoformat(d["stages"][0]["at"]) + timedelta(seconds=5)).isoformat()
        prior = {"generated_at": after, "queries": {
            "hidden-analysis": {"timestamp": before, "sql": "SELECT SUM(amount) FROM orders"}
        }}
        self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:hidden-analysis", check(d, prior))

    def test_late_log_with_unstamped_analysis_is_not_proven_safe(self):
        d = fixture()
        after = (datetime.fromisoformat(d["stages"][0]["at"]) + timedelta(seconds=5)).isoformat()
        prior = {"generated_at": after, "queries": {
            "unknown-execution-time": {"sql": "SELECT COUNT(*) FROM a JOIN b USING (uid)"}
        }}
        self.assertIn("PRIOR_ANALYSIS_TIME_UNVERIFIED:unknown-execution-time", check(d, prior))

    def test_prior_business_query_with_invalid_timestamp_fails_closed(self):
        d = fixture()
        prior = {"generated_at": datetime.now(timezone.utc).isoformat(),
                 "queries": {"invalid": {"timestamp": "2026-01-01",
                                         "sql": "SELECT SUM(amount) FROM transactions"}}}
        self.assertIn("PRIOR_SQL_TIMESTAMP_INVALID:invalid", check(d, prior))

    def test_multi_table_simple_counts_before_gate_allowed(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries":{
            "row-counts":{"sql":"SELECT COUNT(*) FROM orders UNION ALL SELECT COUNT(*) FROM users"}}}
        self.assertEqual([],check(d,prior))

    def test_schema_discovery_before_gate_allowed(self):
        d=fixture();before=(datetime.fromisoformat(d["stages"][0]["at"])-timedelta(seconds=1)).isoformat()
        prior={"generated_at":before,"queries":{"schema-only":{"sql":"DESCRIBE orders"}}}
        self.assertEqual([],check(d,prior))
    def test_result_status_without_rows_is_not_pass(self):
        d=fixture();d["queries"][0].pop("rows")
        self.assertTrue(any("SQL_RESULT_NOT_PRESENT" in e for e in check(d)))
    def test_original_hardcoded_numeric_finding_is_rejected(self):
        d = fixture()
        d["findings"] = [{"id":"F", "facts":"Transaction net is 3000 in the current sample"}]
        self.assertIn("UNVERIFIED_NUMERIC_CLAIM:F", check(d))

    def test_dynamic_fact_binding_valid_and_mutation_sensitive(self):
        d = fixture()
        q = d["queries"][0]
        q["rows"] = [{"net": 7}]
        def render():
            return "Observed net: {}".format(d["queries"][0]["rows"][0]["net"])
        d["findings"] = [{
            "id":"F", "facts":render(),
            "fact_verification":{"template":"Observed net: {net}",
                                 "bindings":{"net":{"query":q["id"],"row":0,"column":"net"}}}
        }]
        self.assertEqual([], check(d))
        q["rows"][0]["net"] += 9  # independent mutation, old report text unchanged
        self.assertIn("STALE_OR_HARDCODED_NUMERIC_CLAIM:F", check(d))
        d["findings"][0]["facts"] = render()
        self.assertEqual([], check(d))

    def test_absent_sql_is_not_analytical_pass(self):
        d=fixture();d["queries"]=[]
        self.assertIn("NO_ACTUAL_SQL_RESULTS",check(d))


    def test_pre_gate_max_aggregate_must_be_rejected(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "hidden-max": {"sql": "SELECT MAX(amount) AS peak FROM orders"}}}
        self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:hidden-max", check(d, prior))

    def test_pre_gate_filtered_count_must_be_rejected(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "status-count": {"sql": "SELECT COUNT(*) FROM orders WHERE status = 'completed'"}}}
        self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:status-count", check(d, prior))

    def test_pre_gate_distinct_count_must_be_rejected(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "distinct-uid": {"sql": "SELECT COUNT(DISTINCT uid) FROM orders"}}}
        self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:distinct-uid", check(d, prior))

    def test_pre_gate_null_profile_must_remain_allowed(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "null-check": {"sql": "SELECT COUNT(*) FROM orders WHERE amount IS NULL"}}}
        self.assertEqual([], check(d, prior))

    def test_post_gate_business_aggregate_is_allowed(self):
        d = fixture()
        after = (datetime.fromisoformat(d["stages"][0]["at"]) + timedelta(seconds=3)).isoformat()
        prior = {"generated_at": after, "queries": {
            "approved-max": {"timestamp": after, "sql": "SELECT MAX(amount) FROM orders"}}}
        self.assertEqual([], check(d, prior))



    def test_independent_pre_gate_aggregate_variants_fail_closed(self):
        statements = (
            "SELECT MIN(amount) FROM orders",
            "SELECT COUNT(*) FILTER (WHERE status = 'completed') FROM orders",
            "SELECT COUNT(*) FROM orders WHERE amount IS NULL AND status = 'completed'",
        )
        for i, statement in enumerate(statements):
            with self.subTest(statement=statement):
                d = fixture()
                before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
                prior = {"generated_at": before, "queries": {
                    "independent-" + str(i): {"sql": statement}}}
                self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:independent-" + str(i), check(d, prior))

    def test_neutral_row_count_alias_remains_allowed(self):
        d = fixture()
        before = (datetime.fromisoformat(d["stages"][0]["at"]) - timedelta(seconds=3)).isoformat()
        prior = {"generated_at": before, "queries": {
            "counts": {"sql": "SELECT COUNT(*) AS n FROM orders"}}}
        self.assertEqual([], check(d, prior))



    def test_comment_obfuscated_pre_gate_aggregates_rejected(self):
        statements = (
            "SELECT SUM/* review */(amount) FROM orders",
            "SELECT AVG -- review\n(amount) FROM orders",
            "SELECT COUNT/* review */(DISTINCT uid) FROM orders",
            "SELECT COUNT/* review */(*) FILTER (WHERE status = 'completed') FROM orders",
        )
        for index, sql in enumerate(statements):
            with self.subTest(sql=sql):
                case = fixture()
                early = (datetime.fromisoformat(case["stages"][0]["at"]) -
                         timedelta(seconds=3)).isoformat()
                prior = {"generated_at": early, "queries": {
                    "comment-" + str(index): {"sql": sql}}}
                self.assertIn("PRIOR_ANALYSIS_BEFORE_GATE1:comment-" + str(index),
                              check(case, prior))

    def test_comments_in_neutral_count_probes_remain_allowed(self):
        statements = (
            "SELECT COUNT /* review */ (*) FROM orders",
            "SELECT COUNT -- review\n(*) FROM orders WHERE amount IS NULL",
            "SELECT COUNT(*) AS n FROM orders /* neutral */",
        )
        for sql in statements:
            with self.subTest(sql=sql):
                case = fixture()
                early = (datetime.fromisoformat(case["stages"][0]["at"]) -
                         timedelta(seconds=3)).isoformat()
                prior = {"generated_at": early, "queries": {"neutral": {"sql": sql}}}
                self.assertEqual([], check(case, prior))

if __name__ == "__main__":
    unittest.main()

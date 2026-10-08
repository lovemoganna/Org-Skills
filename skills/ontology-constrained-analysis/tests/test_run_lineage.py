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
    def test_schema_discovery_before_gate_allowed(self):
        d=fixture();before=(datetime.fromisoformat(d["stages"][0]["at"])-timedelta(seconds=1)).isoformat()
        prior={"generated_at":before,"queries":{"schema-only":{"sql":"DESCRIBE orders"}}}
        self.assertEqual([],check(d,prior))
    def test_result_status_without_rows_is_not_pass(self):
        d=fixture();d["queries"][0].pop("rows")
        self.assertTrue(any("SQL_RESULT_NOT_PRESENT" in e for e in check(d)))
    def test_absent_sql_is_not_analytical_pass(self):
        d=fixture();d["queries"]=[]
        self.assertIn("NO_ACTUAL_SQL_RESULTS",check(d))

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline contract and adversarial checks; does not claim agent-model success."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
def imported(name):
    s = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    x = importlib.util.module_from_spec(s)
    s.loader.exec_module(x)
    return x

pre = imported("blind_source_preflight")
agents = imported("blind_three_role_agents")


class BlindThreeRoleTests(unittest.TestCase):
    def test_blob_pin(self):
        import hashlib
        d = b"known-case"
        want = hashlib.sha1(b"blob " + str(len(d)).encode() + b"\0" + d).hexdigest()
        self.assertEqual(pre.git_blob_sha(d), want)
        self.assertEqual(len(pre.FILES), 4)
        self.assertTrue(all(len(blob) == 40 for _, blob in pre.FILES.values()))

    def test_select_and_cte_only(self):
        for q in ("SELECT COUNT(*) FROM orders", "WITH x AS (SELECT 1 a) SELECT a FROM x"):
            self.assertEqual(agents.validate_query(q), q)
        for q in [
            "CREATE TABLE x AS SELECT * FROM orders",
            "SELECT * FROM orders; DELETE FROM orders",
            "SELECT * FROM read_csv_auto('/tmp/secret.csv')",
            "SELECT * FROM read_parquet('https://example.com/secret.parquet')",
            "SELECT * FROM orders; SELECT * FROM promotions",
            "SELECT * FROM httpfs",
            "SELECT * FROM orders COPY TO '/tmp/file'",
            "SELECT * FROM sqlite_scan('/tmp/x', 'x')",
            "SELECT * FROM orders WHERE order_id = 'x; y'",
            "WITH x AS (SELECT 1) DELETE FROM orders",
        ]:
            with self.subTest(query=q), self.assertRaises(ValueError):
                agents.validate_query(q)

    def test_parse_json_contract(self):
        self.assertEqual(agents.parse_json('{"decision": "NEEDS_EVIDENCE"}')['decision'], "NEEDS_EVIDENCE")
        self.assertEqual(agents.parse_json('```json\n{"a":1}\n```'), {"a":1})
        for v in ('[]', 'not json', 'null'):
            with self.assertRaises((ValueError, TypeError)):
                agents.parse_json(v)

    def test_read_only_sql_and_100_row_gate(self):
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "sample.duckdb"
            with duckdb.connect(str(db)) as c:
                c.execute("CREATE TABLE orders (order_id INTEGER, amount INTEGER)")
                c.execute("INSERT INTO orders VALUES (1, 10), (2, 20)")
            actual = agents.run_sql(db, "SELECT SUM(amount) AS total FROM orders")
            self.assertEqual(actual["rows"], [[30]])
            with self.assertRaises(Exception):
                agents.run_sql(db, "SELECT * FROM nonexistent")
            with duckdb.connect(str(db), read_only=True) as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)

    def test_actual_roles_are_isolated_requests(self):
        source = (SCRIPTS / "blind_three_role_agents.py").read_text(encoding="utf-8")
        self.assertIn("client.responses.create(", source)
        self.assertNotIn("previous_response_id=", source)
        self.assertIn("run_sql(d / \"blind.duckdb\"", source)
        self.assertIn('verifier_plan = call("analysis-verifier"', source)
        self.assertIn('brief = call("business-owner"', source)
        self.assertIn('review = call("business-owner"', source)
        self.assertNotIn("holdout-verifier.json", source, "holdout must never enter agent prompts")
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不同组的订单数相加", skill)
        holdout = (SCRIPTS / "blind_retail_holdout.py").read_text(encoding="utf-8")
        self.assertIn("mixed_promo_orders", holdout)
        self.assertIn("non-additive order segments", holdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)

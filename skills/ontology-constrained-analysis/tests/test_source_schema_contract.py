#!/usr/bin/env python3
"""Negative/positive source-gate tests; fixtures contain no analysis answers."""
import copy
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_ontology_sources import load_schemas, validate, validate_relation_domains  # noqa: E402


def model():
    return {
        "ontology_atoms": [{
            "一级标签": "业务", "二级标签": "对象", "三级标签": "交易",
            "原子名称": "交易", "原子层级": "基础事实",
            "本体类别": "事件", "类型": "记录", "单位或值域": "订单",
            "主体": "交易", "粒度": "单笔", "时间语义": "创建时点",
            "关系": "用户|发起|交易", "知识点解释": "记录的交易事件",
            "证据来源": "orders.id",
        }],
        "ontology_rules": [{
            "一级标签": "业务", "二级标签": "方向", "三级标签": "入金订单",
            "识别标准": "事件且方向为入金",
            "Lisp 表达式": "(交易 (= 方向 deposit))",
            "规则定义": "交易记录方向为入金",
            "当前状态": "待数据验证",
        }],
    }


class GateOneSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory()
        path = Path(cls.work.name) / "orders.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            out = csv.writer(f)
            out.writerow(["column_name", "column_type"])
            out.writerow(["id", "VARCHAR"])
            out.writerow(["amount", "DOUBLE"])
        cls.schemas = load_schemas([f"orders={path}"])

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_original_mixed_category_relation_fails(self):
        value = model()
        value["ontology_atoms"][0]["关系"] = "汇率记录|对应|加密资产"
        value["relation_domain_claims"] = [{
            "relation": "汇率记录|对应|加密资产",
            "source": "rates.asset", "category_source": "crypto.asset"
        }]
        observed = {"rates.asset": ["USD", "BTC"], "crypto.asset": ["BTC"]}
        errors = validate_relation_domains(value, observed)
        self.assertTrue(any("RELATION_DOMAIN_MISMATCH" in e for e in errors))

    def test_genuine_category_membership_is_not_blocked(self):
        value = model()
        value["ontology_atoms"][0]["关系"] = "汇率记录|对应|加密资产"
        value["relation_domain_claims"] = [{
            "relation": "汇率记录|对应|加密资产",
            "source": "rates.asset", "category_source": "crypto.asset"
        }]
        observed = {"rates.asset": ["ETH", "BTC"], "crypto.asset": ["BTC", "ETH"]}
        self.assertEqual([], validate_relation_domains(value, observed))

    def test_semantic_domain_from_forbidden_table_fails(self):
        value = model()
        value["relation_domain_claims"] = [{
            "relation": "用户|发起|交易",
            "source": "forbidden.asset", "category_source": "orders.id"
        }]
        observed = {"forbidden.asset":["X"],"orders.id":["X"]}
        errors = validate_relation_domains(value, observed, self.schemas)
        self.assertTrue(any("FORBIDDEN_OR_UNKNOWN_DOMAIN_FIELD" in e for e in errors))

    def test_missing_observed_category_evidence_fails(self):
        value = model()
        value["relation_domain_claims"] = [{
            "relation": "用户|发起|交易", "source": "rates.asset",
            "category_source": "crypto.asset"
        }]
        self.assertTrue(any("UNVERIFIED_OBSERVED_VALUES" in e
                            for e in validate_relation_domains(value, {})))

    def test_canonical_column_passes(self):
        self.assertEqual([], validate(model(), self.schemas))

    def test_original_failure_legacy_source_column_fails(self):
        value = model()
        atom = value["ontology_atoms"][0]
        atom["来源"] = atom.pop("证据来源")
        errors = validate(value, self.schemas)
        self.assertTrue(any("LEGACY_SOURCE_LABEL" in e for e in errors))
        self.assertTrue(any("MISSING_证据来源" in e for e in errors))

    def test_table_only_source_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = "orders"
        errors = validate(value, self.schemas)
        self.assertTrue(any("SOURCE_MUST_NAME_FIELD" in e for e in errors))

    def test_table_only_derived_source_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = {
            "sources": ["orders"], "derivation": "per order"
        }
        errors = validate(value, self.schemas)
        self.assertTrue(any("SOURCE_MUST_NAME_FIELD" in e for e in errors))

    def test_forbidden_source_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = "expected_result.amount"
        self.assertTrue(any("FORBIDDEN_OR_UNKNOWN_TABLE" in e for e in validate(value, self.schemas)))

    def test_missing_column_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = "orders.nonexistent"
        self.assertTrue(any("UNKNOWN_FIELD" in e for e in validate(value, self.schemas)))

    def test_legitimate_derived_source_passes(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = {
            "sources": ["orders.amount"], "derivation": "amount * 2"
        }
        self.assertEqual([], validate(value, self.schemas))

    def test_unproved_derived_source_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = {
            "sources": ["orders.nonexistent"], "derivation": "assumed"
        }
        self.assertTrue(any("UNKNOWN_FIELD" in e for e in validate(value, self.schemas)))

    def test_blank_derived_formula_fails(self):
        value = model()
        value["ontology_atoms"][0]["证据来源"] = {
            "sources": ["orders.amount"], "derivation": ""
        }
        self.assertTrue(any("MISSING_DERIVATION" in e for e in validate(value, self.schemas)))

    def test_alias_alongside_canonical_fails(self):
        value = model()
        value["ontology_atoms"][0]["来源"] = "orders"
        self.assertTrue(any("LEGACY_SOURCE_LABEL" in e for e in validate(value, self.schemas)))




class LiveWorkbookSemanticGate(unittest.TestCase):
    """Independent source-only fixtures; no business answers or expected amounts."""

    def fixture_dir(self, orphan=False):
        from live_workbook_gate1 import REQUIRED
        folder = tempfile.TemporaryDirectory()
        root = Path(folder.name)
        fields = {tab: list(columns) for tab, columns in REQUIRED.items()}
        rows = {
            "users": [{"uid": "123"}],
            "fiat_transactions": [{"fiat_order_id": "f-1", "uid": "123.0",
                                   "direction": "deposit", "status": "completed",
                                   "currency": "EUR", "amount": "1.0"}],
            "crypto_transactions": [{"crypto_order_id": "c-1",
                                     "uid": "999.0" if orphan else "123.0",
                                     "direction": "withdrawal", "status": "pending",
                                     "asset": "BTC", "amount": "0.1"}],
            "exchange_rates": [{"asset": "BTC", "effective_date": "2026-01-01",
                                "rate_to_usdt": "1"}],
        }
        for tab in fields:
            with (root / (tab + "-schema.csv")).open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f); writer.writerow(["column_name", "column_type"])
                writer.writerows((col, "VARCHAR") for col in fields[tab])
            with (root / (tab + ".csv")).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields[tab])
                writer.writeheader();writer.writerows(rows[tab])
        return folder, root

    def test_live_gate_accepts_safe_numeric_uid_representation(self):
        from live_workbook_gate1 import verify
        folder, root = self.fixture_dir()
        try:
            model, errors, samples, boundary = verify(root)
            self.assertEqual([], errors)
            self.assertEqual(1, samples["fiat_transactions"]["matched_user_uids"])
            self.assertEqual(10, len(model["ontology_atoms"]))
        finally:
            folder.cleanup()

    def test_live_gate_rejects_cross_table_orphan(self):
        from live_workbook_gate1 import verify
        folder, root = self.fixture_dir(orphan=True)
        try:
            _model, errors, _samples, _boundary = verify(root)
            self.assertIn("UNMATCHED_USER_UID:crypto_transactions", errors)
        finally:
            folder.cleanup()

if __name__ == "__main__":
    unittest.main()

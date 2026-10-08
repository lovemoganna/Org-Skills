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


if __name__ == "__main__":
    unittest.main()

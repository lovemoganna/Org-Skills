#!/usr/bin/env python3
"""Check ontology tables and evidence sources against observed DuckDB DESCRIBE CSVs.

This structural/source gate is necessary, but does not approve business semantics.
"""
import argparse
import csv
import json
from pathlib import Path

ATOM_COLUMNS = (
    "一级标签", "二级标签", "三级标签", "原子名称", "原子层级",
    "本体类别", "类型", "单位或值域", "主体", "粒度",
    "时间语义", "关系", "知识点解释", "证据来源",
)
RULE_COLUMNS = (
    "一级标签", "二级标签", "三级标签", "识别标准",
    "Lisp 表达式", "规则定义", "当前状态",
)


def load_schemas(sources):
    schemas = {}
    for item in sources:
        if "=" not in item:
            raise ValueError(f"BAD_SCHEMA_ARGUMENT:{item}")
        table, path = item.split("=", 1)
        if not table or table in schemas:
            raise ValueError(f"DUPLICATE_OR_EMPTY_TABLE:{table}")
        with open(path, newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        if not rows or "column_name" not in rows[0]:
            raise ValueError(f"INVALID_CURRENT_SCHEMA:{table}")
        schemas[table] = {row["column_name"] for row in rows if row.get("column_name")}
    return schemas


def validate(model, schemas):
    errors = []
    atoms = model.get("ontology_atoms")
    rules = model.get("ontology_rules")
    if not isinstance(atoms, list) or not atoms:
        errors.append("MISSING_ATOM_TABLE")
        atoms = []
    if not isinstance(rules, list) or not rules:
        errors.append("MISSING_RULE_TABLE")
        rules = []
    seen = set()
    for n, row in enumerate(atoms, 1):
        if not isinstance(row, dict):
            errors.append(f"ATOM_{n}:INVALID_ROW")
            continue
        if "来源" in row:
            errors.append(f"ATOM_{n}:LEGACY_SOURCE_LABEL")
        for field in ATOM_COLUMNS:
            if not row.get(field):
                errors.append(f"ATOM_{n}:MISSING_{field}")
        name = row.get("原子名称", "")
        if name in seen:
            errors.append(f"ATOM_{n}:DUPLICATE_ATOM:{name}")
        seen.add(name)
        rel = row.get("关系")
        if not isinstance(rel, str) or rel.count("|") != 2 or any(not x.strip() for x in rel.split("|")):
            errors.append(f"ATOM_{n}:INVALID_RELATION")
        evidence = row.get("证据来源")
        if isinstance(evidence, str):
            refs = [evidence]
        elif isinstance(evidence, dict):
            refs = evidence.get("sources", [])
            if not evidence.get("derivation"):
                errors.append(f"ATOM_{n}:MISSING_DERIVATION")
        else:
            refs = []
        if not isinstance(refs, list):
            errors.append(f"ATOM_{n}:INVALID_SOURCE_LIST")
            refs = []
        if not refs:
            errors.append(f"ATOM_{n}:MISSING_EVIDENCE")
        for ref in refs:
            if not isinstance(ref, str) or ref.count(".") > 1:
                errors.append(f"ATOM_{n}:INVALID_EVIDENCE:{ref}")
                continue
            table, sep, column = ref.partition(".")
            if not sep or not column:
                errors.append(f"ATOM_{n}:SOURCE_MUST_NAME_FIELD:{ref}")
            if table not in schemas:
                errors.append(f"ATOM_{n}:FORBIDDEN_OR_UNKNOWN_TABLE:{table}")
            elif sep and column not in schemas[table]:
                errors.append(f"ATOM_{n}:UNKNOWN_FIELD:{table}.{column}")
    labels = set()
    for n, row in enumerate(rules, 1):
        if not isinstance(row, dict):
            errors.append(f"RULE_{n}:INVALID_ROW")
            continue
        for field in RULE_COLUMNS:
            if not row.get(field):
                errors.append(f"RULE_{n}:MISSING_{field}")
        key = tuple(row.get(x) for x in RULE_COLUMNS[:3])
        if key in labels:
            errors.append(f"RULE_{n}:DUPLICATE_RULE")
        labels.add(key)
        lisp = row.get("Lisp 表达式", "")
        if not isinstance(lisp, str) or lisp.count("(") != lisp.count(")"):
            errors.append(f"RULE_{n}:UNBALANCED_LISP")
    return errors



def validate_relation_domains(model, values):
    """Verify explicitly claimed category membership with observed value sets.

    Evidence values must be extracted from the CURRENT allowed DuckDB tables.
    Membership is only a necessary check; it does not prove a business relation.
    """
    errors = []
    registered = {row.get("关系") for row in model.get("ontology_atoms", [])
                  if isinstance(row, dict)}
    for i, claim in enumerate(model.get("relation_domain_claims", []), 1):
        if not isinstance(claim, dict):
            errors.append(f"DOMAIN_{i}:INVALID_CONTRACT")
            continue
        relation = claim.get("relation")
        source = claim.get("source")
        category_source = claim.get("category_source")
        if relation not in registered:
            errors.append(f"DOMAIN_{i}:UNKNOWN_RELATION")
        if not source or not category_source or source not in values or category_source not in values:
            errors.append(f"DOMAIN_{i}:UNVERIFIED_OBSERVED_VALUES")
            continue
        observed = set(str(x) for x in values[source] if x is not None)
        category = set(str(x) for x in values[category_source] if x is not None)
        if not observed.issubset(category):
            errors.append(f"DOMAIN_{i}:RELATION_DOMAIN_MISMATCH:{len(observed-category)}")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--schema", action="append", required=True,
                        help="Observed DuckDB DESCRIBE CSV in table=path form; repeat")
    parser.add_argument("--receipt")
    parser.add_argument("--domain-values", help="JSON mapping table.field to current DuckDB observed distinct values")
    args = parser.parse_args()
    try:
        schemas = load_schemas(args.schema)
        model = json.loads(Path(args.model).read_text(encoding="utf-8"))
        errors = validate(model, schemas)
        if model.get("relation_domain_claims"):
            observed = json.loads(Path(args.domain_values).read_text(encoding="utf-8")) if args.domain_values else {}
            errors.extend(validate_relation_domains(model, observed))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [f"INPUT_ERROR:{exc}"]
    receipt = {
        "status": "PASS_STRUCTURE_AND_SOURCE_ONLY" if not errors else "FAIL_CLOSED",
        "observed_tables": sorted(schemas) if "schemas" in locals() else [],
        "errors": errors,
        "semantic_gate_passed": False,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if args.receipt:
        Path(args.receipt).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fail-closed ordering/provenance checks for a real ontology-analysis run.

This does not execute SQL or judge business semantics. It ensures that previous
analytical exploration cannot be laundered into a later Gate 1 PASS.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

def when(value):
    if not isinstance(value, str):
        raise ValueError("MISSING_TIMESTAMP")
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return t.astimezone(timezone.utc)

def check(chain, prior=None):
    errors = []
    stages = chain.get("stages", [])
    gates = [x for x in stages if x.get("stage", "").startswith("Gate 1 ")]
    if len(gates) != 1:
        return ["GATE1_MISSING_OR_DUPLICATED"]
    gate = gates[0]
    try:
        approved_at = when(gate.get("at"))
    except ValueError as exc:
        return [f"GATE1_{exc}"]
    if gate.get("details", {}).get("status") != "PASS":
        errors.append("GATE1_NOT_APPROVED")
    # A self-authored PASS label cannot replace the official schema/source check
    # and an independent business semantic review with evidence.
    details = gate.get("details", {})
    if details.get("source_check") != "PASS_STRUCTURE_AND_SOURCE_ONLY":
        errors.append("GATE1_SOURCE_CHECK_MISSING")
    review = details.get("semantic_review")
    if not isinstance(review, dict) or review.get("status") != "PASS" or not review.get("evidence"):
        errors.append("GATE1_SEMANTIC_EVIDENCE_MISSING")
    for q in chain.get("queries", []):
        try:
            if when(q.get("timestamp")) < approved_at:
                errors.append("ANALYSIS_SQL_BEFORE_GATE1:" + str(q.get("id", "")))
        except ValueError:
            errors.append("SQL_TIMESTAMP_UNVERIFIED:" + str(q.get("id", "")))
        if q.get("status") == "PASS" and "rows" not in q:
            errors.append("SQL_RESULT_NOT_PRESENT:" + str(q.get("id", "")))
    if prior is not None:
        try:
            early = when(prior.get("generated_at")) < approved_at
        except ValueError:
            early = True
            errors.append("PRIOR_QUERY_TIMESTAMP_UNVERIFIED")
        # Metadata/schema-only probes are acceptable. Business aggregation,
        # JOINs, net flow and other actual analytical SQL are not Gate-0 probes.
        import re
        for ident, q in prior.get("queries", {}).items():
            statement = q.get("sql", "") if isinstance(q, dict) else ""
            if early and re.search(r"\b(?:JOIN|GROUP\s+BY|SUM\s*\(|AVG\s*\(|CASE\s+WHEN|UNION(?:\s+ALL)?)\b", statement, re.I):
                errors.append("PRIOR_ANALYSIS_BEFORE_GATE1:" + ident)
    # A numeric narrative must be reconstructed from THIS run's SQL Result.
    # Templates/bindings are an audit contract, not expected test answers.
    import re
    by_id = {str(q.get("id")): q for q in chain.get("queries", [])}
    for finding in chain.get("findings", []):
        facts = finding.get("facts", "")
        if not isinstance(facts, str):
            errors.append("FINDING_FACTS_NOT_TEXT:" + str(finding.get("id")))
            continue
        if not re.search(r"\\d", facts):
            continue
        receipt = finding.get("fact_verification")
        if not isinstance(receipt, dict) or not receipt.get("bindings") or not receipt.get("template"):
            errors.append("UNVERIFIED_NUMERIC_CLAIM:" + str(finding.get("id")))
            continue
        resolved = {}
        for key, link in receipt["bindings"].items():
            try:
                query = by_id[str(link["query"])]
                if query.get("status") != "PASS":
                    raise ValueError("SQL_NOT_PASSED")
                resolved[key] = query["rows"][int(link["row"])][link["column"]]
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append("CLAIM_RESULT_BINDING_MISSING:" + str(finding.get("id")) + ":" + key)
        if len(resolved) == len(receipt["bindings"]):
            try:
                rebuilt = receipt["template"].format(**resolved)
                if rebuilt != facts:
                    errors.append("STALE_OR_HARDCODED_NUMERIC_CLAIM:" + str(finding.get("id")))
            except (KeyError, ValueError, TypeError):
                errors.append("CLAIM_TEMPLATE_INVALID:" + str(finding.get("id")))
    # Keep these statuses independent: a report build is not a passed Gate 3.
    if not chain.get("queries"):
        errors.append("NO_ACTUAL_SQL_RESULTS")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chain", required=True)
    p.add_argument("--prior-queries")
    p.add_argument("--receipt")
    args = p.parse_args()
    try:
        chain = json.loads(Path(args.chain).read_text(encoding="utf-8"))
        prior = json.loads(Path(args.prior_queries).read_text(encoding="utf-8")) if args.prior_queries else None
        errors = check(chain, prior)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        errors = ["INPUT_UNVERIFIED:" + str(exc)]
    result = {"status": "PASS_ORDER_AND_EVIDENCE" if not errors else "FAIL_CLOSED",
              "errors": errors, "semantic_review_independently_tested": False}
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    print(encoded)
    if args.receipt:
        Path(args.receipt).write_text(encoded + "\n", encoding="utf-8")
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())

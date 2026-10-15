#!/usr/bin/env python3
"""Isolation-by-context three-role AI trial on pinned unfamiliar DuckDB data.

Separate Responses API requests with zero conversation state reuse. Only explicit
handoff artifacts are passed between stages. Never assert model testing if blocked.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone


FORBIDDEN = re.compile(
    r"\b(ATTACH|DETACH|COPY|EXPORT|INSTALL|LOAD|PRAGMA|SET|CREATE|DROP|ALTER|"
    r"INSERT|DELETE|UPDATE|TRUNCATE|CALL|EXECUTE|"
    r"READ_[A-Z0-9_]+|SQLITE_SCAN|HTTPFS)\b",
    re.IGNORECASE,
)
MAX_QUERY_CHARS = 5000


def validate_query(sql):
    if not isinstance(sql, str) or not (s := sql.strip()):
        raise ValueError("EMPTY_SQL")
    s = s.removesuffix(";").strip()
    if ";" in s or len(s) > MAX_QUERY_CHARS:
        raise ValueError("MULTISTATEMENT_OR_TOO_LONG_SQL")
    if not re.match(r"^(SELECT|WITH)\b", s, re.IGNORECASE):
        raise ValueError("NON_SELECT_SQL")
    if FORBIDDEN.search(s) or re.search(r"(https?://|s3://|file://|\bSECRET\b|\bENV\s*\()", s, re.IGNORECASE):
        raise ValueError("EXTERNAL_OR_UNSAFE_SQL")
    return s


def run_sql(dbfile, sql):
    import duckdb
    query = validate_query(sql)
    with duckdb.connect(str(dbfile), read_only=True,
                        config={"enable_external_access": "false"}) as con:
        cursor = con.execute(query)
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchmany(101)
    if len(rows) > 100:
        raise ValueError("TOO_MANY_ROWS_AGGREGATE_OR_RESTRICT_QUERY")
    return {"sql": query, "columns": cols, "row_count": len(rows),
            "rows": [list(row) for row in rows]}


def parse_json(text):
    if not isinstance(text, str):
        raise ValueError("EMPTY_MODEL_RESPONSE")
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^\`{3}(?:json)?\s*|\s*\`{3}$", "", s, flags=re.IGNORECASE)
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise ValueError("RESPONSE_NOT_JSON_OBJECT")
    return obj


def write(data_dir, name, obj):
    path = data_dir / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def instructions(root, role):
    skill = (root / "skills" / role / "SKILL.md").read_text(encoding="utf-8")
    return (skill + "\n\n本次是独立运行的盲测。只输出单个合法 JSON 对象，不用 Markdown。"
            "只使用输入中的 schema/已授权数据，不读历史测试答案或未经确认的事实。"
            "未知写 UNKNOWN，不得假装执行了 SQL。源数据是虚构零售交易，不得做真实企业风险断言。")


def assess_owner_boundary(verifier_verdict, owner_decision):
    """Guard only the known owner/B contradiction; never assert content quality."""
    if owner_decision == "APPROVED" and verifier_verdict != "VERIFIED":
        return "FAIL_UNSAFE_PROMOTION"
    return "SAFE_BOUNDARY_ONLY"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="blind-evidence")
    parser.add_argument("--model", default="")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    d = Path(args.data)
    d.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    model = args.model.strip()
    trace = {"started_at": started, "mode": "fresh_isolated_model_contexts",
             "model": model or "NONE", "stages": [], "status": "STARTED"}
    def emit(stage, obj):
        trace["stages"].append({"stage": stage, "result": obj})
        write(d, "agent-trace.json", trace)
    if not model or not os.getenv("OPENAI_API_KEY"):
        trace["status"] = "BLOCKED_MODEL_ID_REQUIRED" if not model else "BLOCKED_API_CREDENTIAL_REQUIRED"
        trace["executed_model_requests"] = 0
        write(d, "agent-trace.json", trace)
        write(d, "agent-status.json", {"status": trace["status"], "executed_model_requests": 0,
             "reason": "OpenAI API credential and explicit model ID are required; scripted QA is not a multi-agent test."})
        print(json.dumps({"status": trace["status"], "executed_model_requests": 0}))
        return 0
    try:
        from openai import OpenAI
        client = OpenAI(timeout=90, max_retries=0)
        receipt = json.loads((d / "source-receipt.json").read_text(encoding="utf-8"))
        assert receipt["status"] == "SOURCE_VERIFIED"
        inventory = {k: {"rows": v["rows"], "columns": v["columns"]} for k, v in receipt["files"].items()}
        task = ("Use only this fictional retail dataset to assess whether 2025 discounts and promotions "
                "warrant continuation or investigation. Select the most consequential defensible "
                "decision; do not infer causal promotion uplift or real profitability without evidence.")
        calls = 0

        def call(role, payload, keys):
            nonlocal calls
            # No previous_response_id, no shared messages, and no hidden chain-of-thought passed.
            resp = client.responses.create(
                model=model, instructions=instructions(root, role),
                input=json.dumps(payload, ensure_ascii=False, default=str))
            calls += 1
            obj = parse_json(resp.output_text)
            absent = [k for k in keys if k not in obj]
            if absent:
                raise ValueError("MISSING_MODEL_OUTPUT_FIELDS:" + ",".join(absent))
            emit(role, {"request_index": calls, "output": obj})
            return obj

        brief = call("business-owner", {"task": task, "data_contract": receipt["commit"],
                    "inventory": inventory,
                    "required_json": ["decision", "question", "competing_hypotheses", "minimum_evidence"]},
                    ["decision", "question", "competing_hypotheses", "minimum_evidence"])
        write(d, "owner-brief.json", brief)
        packet = call("business-reasoning", {"owner_brief": brief, "inventory": inventory,
                     "allowed_tables": list(inventory), "engine": "read-only DuckDB 1.4.2",
                     "required_json": ["result_grain", "candidate_sql", "metric_definition", "limitations"]},
                     ["result_grain", "candidate_sql", "metric_definition", "limitations"])
        write(d, "analyst-packet.json", packet)
        # B receives only the question, schema, and candidate SQL; never A's anticipated values.
        verifier_plan = call("analysis-verifier", {"owner_question": brief["question"],
                             "inventory": inventory, "candidate_sql": packet["candidate_sql"],
                             "required_json": ["verification_sql", "target_checks"]},
                             ["verification_sql", "target_checks"])
        # Execute each query in a separate read-only connection against identical pinned bytes.
        a_result = run_sql(d / "blind.duckdb", packet["candidate_sql"])
        b_result = run_sql(d / "blind.duckdb", verifier_plan["verification_sql"])
        emit("actual_duckdb", {"analyst_result": a_result, "verifier_independent_result": b_result})
        feedback = call("analysis-verifier", {"owner_question": brief["question"],
                        "analyst_query_and_result": a_result, "independent_check": b_result,
                        "target_checks": verifier_plan["target_checks"],
                        "quality_baseline": receipt["data_quality_observations"],
                        "required_json": ["verdict", "validated_facts", "counterevidence", "limitations"]},
                        ["verdict", "validated_facts", "counterevidence", "limitations"])
        if feedback["verdict"] not in ("VERIFIED", "UNRESOLVED", "BLOCKED", "REJECTED"):
            raise ValueError("BAD_VERIFIER_VERDICT")
        write(d, "verifier-feedback.json", {"feedback": feedback, "analyst_result": a_result,
                                             "independent_check": b_result})
        report = call("business-reasoning", {"owner_brief": brief, "analyst_packet": packet,
                      "analyst_result": a_result, "verifier_feedback": feedback,
                      "require": "Use only verified facts; uncertainty and actions must be explicit.",
                      "required_json": ["finding", "supporting_evidence", "recommendation", "uncertainty"]},
                      ["finding", "supporting_evidence", "recommendation", "uncertainty"])
        write(d, "final-report.json", report)
        review = call("business-owner", {"original_decision": brief["decision"],
                      "report": report, "independent_feedback": feedback,
                      "required_json": ["decision", "reason", "missing_evidence"]},
                      ["decision", "reason", "missing_evidence"])
        if review["decision"] not in ("APPROVED", "NEEDS_EVIDENCE", "NOT_DECISION_READY"):
            raise ValueError("BAD_OWNER_VERDICT")
        # Model-only reviewer verdicts do not establish business truth. Fail on unsafe approval.
        gate = assess_owner_boundary(feedback["verdict"], review["decision"])
        write(d, "owner-review.json", review)
        trace["status"] = ("EXECUTED_CONTENT_UNGRADED" if gate == "SAFE_BOUNDARY_ONLY"
                           else "UNSAFE_PROMOTION")
        trace["gate"] = gate
        trace["executed_model_requests"] = calls
        write(d, "agent-status.json", {"status": trace["status"], "gate": gate,
                  "executed_model_requests": calls, "source": receipt["commit"],
                  "limitation": "SQL was executed and role contexts isolated; independent semantic grading of model-written findings remains required."})
        write(d, "agent-trace.json", trace)
        print(json.dumps({"status": trace["status"], "model_requests": calls,
                          "verifier": feedback["verdict"], "owner": review["decision"], "gate": gate}))
        return 0 if gate == "SAFE_BOUNDARY_ONLY" else 3
    except Exception as exc:
        trace["status"] = "BLOCKED"
        trace["error"] = str(exc)[:450]
        trace["executed_model_requests"] = sum(1 for s in trace["stages"] if s["stage"] != "actual_duckdb")
        write(d, "agent-status.json", {"status": "BLOCKED", "error": str(exc)[:450],
              "executed_model_requests": trace["executed_model_requests"]})
        write(d, "agent-trace.json", trace)
        print("AGENT_TRIAL_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

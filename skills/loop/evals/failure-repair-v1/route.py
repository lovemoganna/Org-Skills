#!/usr/bin/env python3
"""Deterministic ChainSpec planner and evidence gate, NOT an agent/model executor."""
import argparse
import json
import sys
import unittest
from pathlib import Path

META = "loop-engineering-meta"
CAUSAL = "causal-net-loop"
KEY = "keypoint-loop"


def validate_case(c):
    fields = {"id", "title", "failure_code", "symptom", "evidence_urls", "complexity_signals",
              "causal_ambiguity", "executor_available", "recorded_status"}
    if not isinstance(c, dict) or fields - c.keys():
        raise ValueError("case missing required fields")
    if not isinstance(c["id"], str) or not c["id"].strip():
        raise ValueError("missing id")
    if c["failure_code"] not in {f"F{i}" for i in range(13)}:
        raise ValueError("invalid failure code")
    if not isinstance(c["evidence_urls"], list) or not c["evidence_urls"] or not all(
        isinstance(v, str) and v.startswith("https://github.com/") for v in c["evidence_urls"]
    ):
        raise ValueError("each historical case needs a GitHub evidence URL")
    s = c["complexity_signals"]
    if not isinstance(s, list) or len(s) != len(set(s)) or any(type(x) is not int or x not in range(1, 6) for x in s):
        raise ValueError("invalid complexity signals")
    if type(c["causal_ambiguity"]) is not bool or type(c["executor_available"]) is not bool:
        raise ValueError("capability fields must be boolean")
    if c["recorded_status"] not in {"BLOCKED", "HISTORICALLY_REPAIRED", "UNVERIFIED"}:
        raise ValueError("invalid historical status")
    return c


def node(node_id, atom, source, output, gate):
    return {"id": node_id, "atom": atom, "input_from": source, "output_name": output,
            "check": gate, "on_fail": "stop"}


def plan_case(c):
    c = validate_case(c)
    s = c["complexity_signals"]
    chain = len(s) >= 2
    result = {"case_id": c["id"], "mode": "chain" if chain else "direct", "reason": s,
              "coverage": {"actual_result": "requires an external artifact/receipt; NOT checked by this planner"},
              "status": "PLANNED_NOT_RUN", "historical_status": c["recorded_status"], "steps": []}
    if not chain:
        return result
    steps = [node("baseline", META, "case.evidence_urls", "diagnosis",
                  "trace and earliest evidenced failure recorded; capability checked")]
    if not c["executor_available"]:
        result.update(status="BLOCKED_NO_EXECUTOR", resume_when="authorized real executor plus evidence capture available", steps=steps)
        return result
    if c["causal_ambiguity"]:
        steps.append(node("cause", CAUSAL, "diagnosis", "hypotheses",
                          "competing explanations, falsifiers, and evidence gaps recorded"))
        steps.append(node("breakpoint", KEY, "hypotheses", "candidate_action",
                          "one testable action; must be labeled candidate, not proven"))
        source = "candidate_action"
    else:
        source = "diagnosis"
    steps.append(node("execute", "authorized-domain-tool", source, "execution_receipt",
                      "real state change or explicit BLOCKED; no plan-only success"))
    steps.append(node("verify", "independent-boundary-check", "execution_receipt", "verification_receipt",
                      "acceptance, goal, regression and side effects checked using external evidence"))
    steps.append(node("archive", KEY, "verification_receipt", "method_card",
                      "archive only if verified; otherwise keep candidate or stop"))
    if len(steps) > 6:
        raise AssertionError("violates loop S3 <=6 step guideline")
    result["steps"] = steps
    return result


def verify_run(report):
    """Evidence gate for a claimed finished run; existence of fields is not independent authentication."""
    if not isinstance(report, dict) or report.get("status") not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
        raise ValueError("invalid run status")
    if report["status"] != "PASS":
        return "NOT_PROMOTABLE"
    for field in ("run_id", "case_id", "artifact_ref", "boundary_receipt", "verifier_id", "raw_trace_ref"):
        if not isinstance(report.get(field), str) or not report[field].strip():
            raise ValueError("PASS missing evidence field: " + field)
    if report.get("verifier_independent") is not True:
        raise ValueError("self-check cannot claim independent PASS")
    if report.get("goal_met") is not True or report.get("regression_ok") is not True:
        raise ValueError("PASS requires goal and regression evidence")
    return "RECEIPTS_PRESENT_NOT_AUTHENTICATED"


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"]

    def test_three_historical_cases(self):
        self.assertEqual([x["id"] for x in self.cases], ["ML-001", "AB-002", "HTML-003"])
        routes = [plan_case(x) for x in self.cases]
        self.assertEqual([p["status"] for p in routes],
                         ["BLOCKED_NO_EXECUTOR", "BLOCKED_NO_EXECUTOR", "PLANNED_NOT_RUN"])
        self.assertEqual([len(p["steps"]) for p in routes], [1, 1, 4])
        self.assertTrue(all(p["mode"] == "chain" for p in routes))

    def test_ambiguous_route_and_handoffs(self):
        c = dict(self.cases[2], causal_ambiguity=True)
        p = plan_case(c)
        self.assertEqual([x["atom"] for x in p["steps"]],
                         [META, CAUSAL, KEY, "authorized-domain-tool", "independent-boundary-check", KEY])
        self.assertEqual(p["steps"][3]["input_from"], "candidate_action")

    def test_simple_case_remains_direct(self):
        p = plan_case(dict(self.cases[2], complexity_signals=[1]))
        self.assertEqual((p["mode"], p["steps"]), ("direct", []))

    def test_evidence_must_exist(self):
        with self.assertRaises(ValueError):
            plan_case(dict(self.cases[0], evidence_urls=[]))

    def test_no_false_success(self):
        with self.assertRaises(ValueError):
            verify_run({"status": "PASS", "case_id": "ML-001"})
        with self.assertRaises(ValueError):
            verify_run({"status": "PASS", "run_id": "r", "case_id": "ML-001",
                        "artifact_ref": "a", "boundary_receipt": "b", "verifier_id": "self",
                        "raw_trace_ref": "t", "verifier_independent": False,
                        "goal_met": True, "regression_ok": True})
        self.assertEqual(verify_run({"status": "NOT_RUN"}), "NOT_PROMOTABLE")

    def test_receipt_check_is_not_authentication(self):
        v = verify_run({"status": "PASS", "run_id": "r", "case_id": "HTML-003",
                        "artifact_ref": "artifact", "boundary_receipt": "receipt",
                        "verifier_id": "third-party", "raw_trace_ref": "trace",
                        "verifier_independent": True, "goal_met": True, "regression_ok": True})
        self.assertEqual(v, "RECEIPTS_PRESENT_NOT_AUTHENTICATED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cases", type=Path)
    args = ap.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
        success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
        return 0 if success else 1
    if args.cases:
        payload = json.loads(args.cases.read_text(encoding="utf-8"))
        print(json.dumps({"routing_previews": [plan_case(c) for c in payload["cases"]],
                          "actual_single_vs_fixed_vs_dynamic_ab": "NOT_RUN"},
                         ensure_ascii=False, indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

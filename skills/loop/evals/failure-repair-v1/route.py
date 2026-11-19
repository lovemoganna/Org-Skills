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
    required = {"id", "title", "failure_code", "symptom", "evidence_urls",
                "complexity_signals", "recorded_status", "executor_state",
                "executor_evidence_url", "causal_state", "diagnosis_evidence_url",
                "closure_evidence_url", "reopen_evidence_url"}
    if not isinstance(c, dict) or required - c.keys():
        raise ValueError("case missing required fields")
    if not isinstance(c["id"], str) or not c["id"].strip():
        raise ValueError("missing id")
    if c["failure_code"] not in {f"F{i}" for i in range(13)}:
        raise ValueError("invalid failure code")
    urls = c["evidence_urls"]
    if not isinstance(urls, list) or not urls or not all(
        isinstance(v, str) and v.startswith("https://github.com/") for v in urls
    ):
        raise ValueError("case requires an inspectable GitHub source")
    signals = c["complexity_signals"]
    if not isinstance(signals, list) or len(signals) != len(set(signals)) or any(
        type(x) is not int or x not in range(1, 6) for x in signals
    ):
        raise ValueError("invalid complexity signals")
    if c["recorded_status"] not in {"BLOCKED", "HISTORICALLY_REPAIRED", "UNVERIFIED"}:
        raise ValueError("invalid historical status")
    if c["executor_state"] not in {"unknown", "reported_available", "reported_unavailable"}:
        raise ValueError("invalid executor observation")
    if c["causal_state"] not in {"unassessed", "settled", "contested"}:
        raise ValueError("invalid diagnostic observation")
    refs = ("executor_evidence_url", "diagnosis_evidence_url",
            "closure_evidence_url", "reopen_evidence_url")
    for field in refs:
        value = c[field]
        if value is not None and (not isinstance(value, str) or
                                  not value.startswith("https://github.com/")):
            raise ValueError("invalid reference: " + field)
    if c["executor_state"] != "unknown" and not c["executor_evidence_url"]:
        raise ValueError("observed executor state requires provenance")
    if c["executor_state"] == "unknown" and c["executor_evidence_url"]:
        raise ValueError("unknown executor state must not claim supporting evidence")
    if c["causal_state"] != "unassessed" and not c["diagnosis_evidence_url"]:
        raise ValueError("diagnosis must cite supporting evidence")
    if c["causal_state"] == "unassessed" and c["diagnosis_evidence_url"]:
        raise ValueError("unassessed diagnosis cannot claim evidence")
    if c["recorded_status"] == "HISTORICALLY_REPAIRED" and not c["closure_evidence_url"]:
        raise ValueError("historical closure must cite a real completion source")
    # URL syntax and non-empty fields do not authenticate source claims.
    return c


def node(node_id, atom, source, output, gate):
    return {"id": node_id, "atom": atom, "input_from": source, "output_name": output,
            "check": gate, "on_fail": "stop"}


def plan_case(c):
    c = validate_case(c)
    signals = c["complexity_signals"]
    result = {"case_id": c["id"], "mode": "chain" if len(signals) >= 2 else "direct",
              "reason": signals,
              "coverage": {"actual_result": "requires independent external result evidence; NOT checked by this planner"},
              "status": "PLANNED_NOT_RUN", "historical_status": c["recorded_status"],
              "steps": []}
    # An old closed case is not a new failure. Review the old receipt first.
    if c["recorded_status"] == "HISTORICALLY_REPAIRED" and not c["reopen_evidence_url"]:
        result.update(status="HISTORICAL_CLOSURE_FOR_REVIEW",
                      steps=[node("review_closure", "read-only-source-check",
                                  "case.closure_evidence_url", "closure_assessment",
                                  "check historical result; do not claim current environment verified")])
        return result
    if result["mode"] == "direct":
        result["status"] = "DIRECT_NOT_EXECUTED"
        return result
    steps = [node("baseline", META, "case.evidence_urls", "diagnosis",
                  "trace and earliest observed failure; no unsupported root-cause claims")]
    if c["executor_state"] == "unknown":
        result.update(status="NEEDS_RUNTIME_CAPABILITY_EVIDENCE", steps=steps,
                      resume_when="record current authorized executor and its source; do not infer absence")
        return result
    if c["executor_state"] == "reported_unavailable":
        result.update(status="BLOCKED_EXECUTOR_REPORTED_UNAVAILABLE", steps=steps,
                      resume_when="new evidence that a real executor is available")
        return result
    if c["causal_state"] == "unassessed":
        result.update(status="NEEDS_DIAGNOSIS_RESULT", steps=steps,
                      resume_when="actual traced baseline diagnosis or counterevidence")
        return result
    if c["causal_state"] == "contested":
        steps.append(node("cause", CAUSAL, "diagnosis", "hypotheses",
                          "competing explanations, falsifiers, and evidence gaps"))
        steps.append(node("breakpoint", KEY, "hypotheses", "candidate_action",
                          "testable candidate only; do not promote a hypothesis to fact"))
        source = "candidate_action"
    else:
        source = "diagnosis"
    steps.append(node("execute", "authorized-domain-tool", source, "execution_receipt",
                      "actual external state change or explicit blocked result"))
    steps.append(node("verify", "independent-boundary-check", "execution_receipt",
                      "verification_receipt", "check real goal, regression, side effects and receipts"))
    steps.append(node("archive", KEY, "verification_receipt", "method_card",
                      "archive only if genuinely verified; otherwise keep candidate"))
    if len(steps) > 6:
        raise AssertionError("violates loop S3 <=6 steps")
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

    def with_available_executor(self, case):
        return dict(case, executor_state="reported_available",
                    executor_evidence_url="https://github.com/example/repo/actions/runs/1")

    def test_history_does_not_imply_current_capability(self):
        self.assertEqual([x["id"] for x in self.cases], ["ML-001", "AB-002", "HTML-003"])
        routes = [plan_case(x) for x in self.cases]
        self.assertEqual([p["status"] for p in routes],
                         ["NEEDS_RUNTIME_CAPABILITY_EVIDENCE",
                          "NEEDS_RUNTIME_CAPABILITY_EVIDENCE",
                          "HISTORICAL_CLOSURE_FOR_REVIEW"])
        self.assertEqual([len(p["steps"]) for p in routes], [1, 1, 1])
        self.assertTrue(all(p["mode"] == "chain" for p in routes))

    def test_reopen_requires_new_evidence_then_capability_check(self):
        c = dict(self.cases[2], reopen_evidence_url="https://github.com/example/repo/issues/123")
        p = plan_case(c)
        self.assertEqual(p["status"], "NEEDS_RUNTIME_CAPABILITY_EVIDENCE")

    def test_full_six_step_contested_chain(self):
        c = self.with_available_executor(self.cases[0])
        c.update(causal_state="contested",
                 diagnosis_evidence_url="https://github.com/example/repo/issues/7")
        p = plan_case(c)
        self.assertEqual(p["status"], "PLANNED_NOT_RUN")
        self.assertEqual([x["atom"] for x in p["steps"]],
                         [META, CAUSAL, KEY, "authorized-domain-tool",
                          "independent-boundary-check", KEY])
        self.assertEqual(p["steps"][3]["input_from"], "candidate_action")
        self.assertTrue(all(x["on_fail"] == "stop" for x in p["steps"]))

    def test_known_cause_skips_unneeded_steps(self):
        c = self.with_available_executor(self.cases[0])
        c.update(causal_state="settled",
                 diagnosis_evidence_url="https://github.com/example/repo/issues/9")
        p = plan_case(c)
        self.assertEqual([x["atom"] for x in p["steps"]],
                         [META, "authorized-domain-tool", "independent-boundary-check", KEY])

    def test_available_but_no_diagnosis_stops_before_action(self):
        p = plan_case(self.with_available_executor(self.cases[0]))
        self.assertEqual(p["status"], "NEEDS_DIAGNOSIS_RESULT")
        self.assertEqual(len(p["steps"]), 1)

    def test_reported_unavailable_has_separate_status(self):
        c = dict(self.cases[0], executor_state="reported_unavailable",
                 executor_evidence_url="https://github.com/example/repo/issues/2")
        self.assertEqual(plan_case(c)["status"], "BLOCKED_EXECUTOR_REPORTED_UNAVAILABLE")

    def test_simple_case_remains_direct(self):
        p = plan_case(dict(self.cases[0], complexity_signals=[1]))
        self.assertEqual((p["mode"], p["steps"], p["status"]),
                         ("direct", [], "DIRECT_NOT_EXECUTED"))

    def test_missing_evidence_fails_closed(self):
        bad = [dict(self.cases[0], evidence_urls=[]),
               dict(self.cases[0], executor_state="reported_available"),
               dict(self.cases[0], causal_state="settled"),
               dict(self.cases[2], closure_evidence_url=None),
               dict(self.cases[0], executor_state="invalid")]
        for case in bad:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    plan_case(case)

    def test_no_false_success(self):
        with self.assertRaises(ValueError):
            verify_run({"status": "PASS", "case_id": "ML-001"})
        with self.assertRaises(ValueError):
            verify_run({"status": "PASS", "run_id": "r", "case_id": "ML-001",
                        "artifact_ref": "a", "boundary_receipt": "b", "verifier_id": "self",
                        "raw_trace_ref": "t", "verifier_independent": False,
                        "goal_met": True, "regression_ok": True})
        self.assertEqual(verify_run({"status": "NOT_RUN"}), "NOT_PROMOTABLE")

    def test_receipt_fields_not_authentication(self):
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

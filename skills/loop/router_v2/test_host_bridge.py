#!/usr/bin/env python3
"""Deterministic protocol tests; mocked receipts are not live model execution."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from host_bridge import init_session, load, next_step, record, retry_read, status

HERE = Path(__file__).resolve().parent


def plan():
    return json.loads((HERE / "host_demo.json").read_text(encoding="utf-8"))


class HostProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.skills.mkdir()
        for name in ["loop-engineering-meta", "causal-net-loop"]:
            folder = self.skills / name
            folder.mkdir()
            (folder / "SKILL.md").write_text(
                "---\nname: " + name + "\ndescription: test skill\n---\n", encoding="utf-8"
            )
        self.session = self.base / "session"

    def tearDown(self):
        self.temp.cleanup()

    def start(self, task=None, capabilities=None, writes=False):
        return init_session(self.session, task or plan(), self.skills,
                            capabilities if capabilities is not None else ["github.get_pr_info"],
                            authorized_writes=writes)

    def result_for_current(self, status_value="SUCCESS", **overrides):
        req, phase = next_step(load(self.session))
        self.assertEqual(phase, "AWAITING_HOST_EXECUTION")
        data = {
            "step_id": req["step_id"],
            "request_sha256": req["request_sha256"],
            "status": status_value,
            "receipt_ref": "https://github.com/lovemoganna/Org-Skills/pull/116",
        }
        if status_value == "SUCCESS":
            data["artifact_ref"] = "https://github.com/lovemoganna/Org-Skills/pull/116"
        data.update(overrides)
        return data

    def test_init_is_not_execution(self):
        result = self.start()
        self.assertEqual(result["status"], "PLANNED_NOT_RUN")
        self.assertEqual(result["pending_request"]["executor_binding"], "mcp__GitHub__get_pr_info")
        self.assertEqual(result["completed_step_ids"], [])

    def test_read_tool_then_model_step(self):
        self.start()
        first = record(self.session, self.result_for_current())
        self.assertEqual(first["pending_request"]["target"], "loop-engineering-meta")
        self.assertEqual(first["pending_request"]["executor_binding"], "NATIVE_HOST_MODEL_SKILL")
        last = record(self.session, self.result_for_current())
        self.assertEqual(last["status"], "RECEIPTS_RECORDED_UNVERIFIED")
        self.assertEqual(set(last["acceptance"]), {"source_receipt", "causal_boundary"})
        self.assertEqual(last["independence"], "self-check only")
        self.assertNotEqual(last["status"], "VERIFIED")

    def test_missing_tool_capability_blocks(self):
        self.start(capabilities=[])
        s = status(load(self.session))
        self.assertEqual(s["status"], "BLOCKED")
        self.assertEqual(s["phase"], "BLOCKED_TOOL_CAPABILITY")

    def test_write_requires_separate_authorization(self):
        p = plan()
        p["steps"] = [{"id": "write", "kind": "tool", "target": "github.create_file", "args": {
            "repository_full_name": "lovemoganna/Org-Skills", "path": "a", "content": "x",
            "message": "x", "branch": "candidate"
        }}]
        p["acceptance"] = [{"id": "a", "evidence_from": ["write"]}]
        self.start(p, ["github.create_file"])
        self.assertEqual(status(load(self.session))["phase"], "BLOCKED_WRITE_AUTHORIZATION")

    def test_authorized_host_can_receive_request_not_auto_write(self):
        p = plan()
        p["steps"] = [{"id": "write", "kind": "tool", "target": "github.create_file", "args": {
            "repository_full_name": "lovemoganna/Org-Skills", "path": "a", "content": "x",
            "message": "x", "branch": "candidate"
        }}]
        p["acceptance"] = [{"id": "a", "evidence_from": ["write"]}]
        self.start(p, ["github.create_file"], writes=True)
        self.assertEqual(status(load(self.session))["phase"], "AWAITING_HOST_EXECUTION")
        self.assertEqual(load(self.session)["results"], {})

    def test_mismatched_request_refused(self):
        self.start()
        with self.assertRaises(ValueError):
            record(self.session, self.result_for_current(request_sha256="bad"))
        self.assertEqual(load(self.session)["results"], {})

    def test_missing_receipt_ref_refused(self):
        self.start()
        with self.assertRaises(ValueError):
            record(self.session, self.result_for_current(receipt_ref=""))

    def test_success_requires_artifact(self):
        self.start()
        with self.assertRaises(ValueError):
            record(self.session, self.result_for_current(artifact_ref=None))

    def test_failure_halts_dependents(self):
        self.start()
        failed = record(self.session, self.result_for_current("FAILED"))
        self.assertEqual((failed["status"], failed["phase"]), ("FAILED", "HALTED_ON_STEP_FAILURE"))
        with self.assertRaises(ValueError):
            record(self.session, {"step_id": "diagnose", "status": "SUCCESS"})

    def test_host_blocked_remains_blocked(self):
        self.start()
        blocked = record(self.session, self.result_for_current("BLOCKED"))
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["phase"], "HALTED_ON_STEP_BLOCK")

    def failed_read(self, outcome="FAILED"):
        p = plan()
        p["steps"][0].update(target="github.fetch_file", args={
            "repository_full_name": "owner/repo", "path": "missing.md", "ref": "pinned"
        })
        self.start(p, ["github.fetch_file"])
        first = self.result_for_current(outcome, error="not found")
        record(self.session, first)
        return first

    def test_retry_keeps_failed_receipt_and_rejects_stale_response(self):
        first = self.failed_read()
        result = retry_read(self.session, "read_pr", "README.md", "corrected file path")
        req = result["pending_request"]
        self.assertEqual(result["completed_step_ids"], [])
        self.assertEqual(req["args"], {
            "repository_full_name": "owner/repo", "path": "README.md", "ref": "pinned"
        })
        self.assertNotEqual(req["request_sha256"], first["request_sha256"])
        with self.assertRaisesRegex(ValueError, "mismatched"):
            record(self.session, first)
        self.assertEqual(record(self.session, self.result_for_current())["pending_request"]["step_id"], "diagnose")
        self.assertEqual(load(self.session)["read_retries"]["read_pr"]["failed_attempt"]["error"], "not found")

    def test_retry_failure_stays_failed_without_additional_attempt(self):
        self.failed_read()
        retry_read(self.session, "read_pr", "README.md", "corrected file path")
        result = record(self.session, self.result_for_current("FAILED"))
        self.assertEqual(result["phase"], "HALTED_ON_STEP_FAILURE")
        with self.assertRaises(ValueError):
            retry_read(self.session, "read_pr", "other.md", "second correction")

    def test_blocked_step_cannot_be_retried(self):
        self.failed_read("BLOCKED")
        with self.assertRaises(ValueError):
            retry_read(self.session, "read_pr", "README.md", "corrected file path")

    def test_approved_write_failure_cannot_be_retried(self):
        p = plan()
        p["steps"][0]["target"] = "github.update_file"
        self.start(p, ["github.update_file"], writes=True)
        record(self.session, self.result_for_current("FAILED"))
        with self.assertRaises(ValueError):
            retry_read(self.session, "read_pr", "README.md", "corrected file path")

    def test_reject_unknown_tool(self):
        p = plan()
        p["steps"][0]["target"] = "shell.run"
        with self.assertRaises(ValueError):
            self.start(p)

    def test_reject_unknown_skill(self):
        p = plan()
        p["steps"][1]["target"] = "nonexistent"
        with self.assertRaises(ValueError):
            self.start(p)

    def test_reject_forward_dependency(self):
        p = plan()
        p["steps"][0]["depends_on"] = ["diagnose"]
        with self.assertRaises(ValueError):
            self.start(p)

    def test_reject_duplicate_or_missing_acceptance(self):
        p = plan()
        p["acceptance"][1]["id"] = p["acceptance"][0]["id"]
        with self.assertRaises(ValueError):
            self.start(p)
        p = plan()
        p["acceptance"][1]["evidence_from"] = ["not_a_step"]
        with self.assertRaises(ValueError):
            self.start(p)

    def test_refuse_more_than_six_steps(self):
        p = plan()
        p["steps"] = [dict(id=str(i), kind="skill", target="loop-engineering-meta",
                           args={}, depends_on=[]) for i in range(7)]
        with self.assertRaises(ValueError):
            self.start(p)

    def test_plan_tamper_detected(self):
        self.start()
        f = self.session / "session.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        data["plan"]["goal"] = "CHANGED"
        f.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load(self.session)

    def test_replay_result_fails(self):
        self.start()
        first = self.result_for_current()
        record(self.session, first)
        with self.assertRaises(ValueError):
            record(self.session, first)

    def test_unknown_declared_host_capability_rejected(self):
        with self.assertRaises(ValueError):
            self.start(capabilities=["shell.any_command"])

    def test_receipt_is_only_host_report_not_authenticated(self):
        self.start()
        record(self.session, self.result_for_current())
        result = record(self.session, self.result_for_current())
        self.assertEqual(result["evidence_trust"], "HOST_REPORTED_NOT_INDEPENDENTLY_AUTHENTICATED")
        for item in result["acceptance"].values():
            self.assertEqual(item["status"], "HOST_REPORTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)

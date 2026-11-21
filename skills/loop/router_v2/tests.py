#!/usr/bin/env python3
"""Contract and real-local-action tests. No model A/B claims."""
import json
import tempfile
import unittest
from pathlib import Path
from engine import discover, match_skills, plan, run, recheck, safe_path, validate_task

ROOT = Path(__file__).resolve().parent
def fixture(name="demo_write.json"):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

class RouterV2Tests(unittest.TestCase):
    def test_chain_and_direct(self):
        self.assertEqual(plan(fixture())["mode"], "chain")
        self.assertEqual(plan(fixture("demo_replace.json"))["mode"], "chain")
        t = fixture()
        t["actions"] = t["actions"][:1]
        t["acceptance"] = t["acceptance"][:1]
        self.assertEqual(plan(t)["mode"], "direct")
        self.assertEqual(plan(t)["steps"], [])

    def test_discovery_does_not_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "case" / "SKILL.md"
            f.parent.mkdir()
            f.write_text('---\nname: risk-investigation\ndescription: "Investigate AML alerts"\n---\n')
            got = discover(Path(tmp))
            self.assertEqual(got[0]["name"], "risk-investigation")
            self.assertEqual(got[0]["execution_binding"], "UNREGISTERED")
            self.assertTrue(match_skills("risk-investigation", got)[0]["exact_name"])

    def test_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "SKILL.md").write_text("# no metadata")
            self.assertEqual(discover(Path(tmp)), [])

    def test_discovered_skill_without_executor_blocks(self):
        t = fixture()
        t["required_skills"] = ["risk-investigation"]
        cat = [{"name": "risk-investigation", "description": "risk", "source_sha256": "abc"}]
        self.assertEqual(plan(t, cat)["status"], "BLOCKED_SKILL_EXECUTOR")

    def test_missing_skill_blocks(self):
        t = fixture()
        t["required_skills"] = ["nonexistent"]
        self.assertEqual(plan(t, [])["status"], "BLOCKED_SKILL_NOT_FOUND")

    def test_missing_authorization_never_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            r = run(fixture(), base / "workspace", base / "run", authorize_write=False)
            self.assertEqual(r["status"], "BLOCKED")
            self.assertEqual(r["reason"], "WRITE_AUTHORIZATION_REQUIRED")
            self.assertFalse((base / "workspace/cases/risk-note.md").exists())
            self.assertTrue((base / "run/trace.jsonl").exists())

    def test_live_write_and_local_recheck(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            r = run(fixture(), base / "workspace", base / "run", authorize_write=True)
            self.assertEqual(r["status"], "COMPLETED_UNVERIFIED")
            self.assertEqual(len(r["receipts"]), 2)
            self.assertTrue((base / "workspace/cases/risk-note.md").is_file())
            self.assertEqual(recheck(fixture(), base / "workspace", r)["status"], "PASS_LOCAL_RECHECK")
            self.assertEqual(r["independence"], "self-check only")

    def test_multistep_transform_does_not_confuse_old_receipt_with_current_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            t = fixture("demo_replace.json")
            r = run(t, base / "workspace", base / "run", authorize_write=True)
            self.assertEqual(r["status"], "COMPLETED_UNVERIFIED")
            c = recheck(t, base / "workspace", r)
            self.assertEqual(c["status"], "PASS_LOCAL_RECHECK")
            self.assertTrue(c["receipt_integrity"][0]["superseded"])

    def test_mutating_artifact_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            t = fixture()
            r = run(t, base / "workspace", base / "run", authorize_write=True)
            (base / "workspace/cases/risk-note.md").write_text("changed")
            self.assertEqual(recheck(t, base / "workspace", r)["status"], "FAIL_LOCAL_RECHECK")

    def test_missing_needle_must_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            t = fixture()
            t["actions"][1]["needle"] = "NEVER_PRESENT"
            r = run(t, base / "workspace", base / "run", authorize_write=True)
            self.assertEqual(r["status"], "FAILED")
            self.assertEqual(len(r["receipts"]), 1)

    def test_failed_acceptance_must_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            t = fixture()
            t["acceptance"][1]["value"] = "NEVER_PRESENT"
            r = run(t, base / "workspace", base / "run", authorize_write=True)
            self.assertEqual((r["status"], r["reason"]), ("FAILED", "ACCEPTANCE_FAILED"))

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for p in ["../outside", "/etc/passwd", "a/../../out", "a\\b", "./a"]:
                with self.subTest(p=p), self.assertRaises(ValueError):
                    safe_path(Path(tmp), p)

    def test_external_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (root / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                safe_path(root, "escape/out.txt")

    def test_unregistered_operation(self):
        t = fixture()
        t["actions"][0]["operation"] = "shell"
        with self.assertRaises(ValueError):
            validate_task(t)

    def test_forward_dependency(self):
        t = fixture()
        t["actions"][0]["depends_on"] = ["check"]
        with self.assertRaises(ValueError):
            validate_task(t)

    def test_duplicate_acceptance(self):
        t = fixture()
        t["acceptance"][1]["id"] = t["acceptance"][0]["id"]
        with self.assertRaises(ValueError):
            validate_task(t)

    def test_at_most_six_steps(self):
        t = fixture()
        t["actions"] = [{"id": str(i), "operation": "read_text", "path": "a"} for i in range(7)]
        with self.assertRaises(ValueError):
            validate_task(t)

    def test_no_self_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            r = run(fixture(), base / "workspace", base / "run", authorize_write=True)
            self.assertEqual(r["goal_check"], "NOT_INDEPENDENTLY_VERIFIED")
            self.assertEqual(r["status"], "COMPLETED_UNVERIFIED")

    def test_skill_task_cannot_silently_be_replaced_with_file_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            t = fixture()
            t["required_skills"] = ["causal-net-loop"]
            catalog = [{"name": "causal-net-loop", "description": "", "source_sha256": "abc"}]
            r = run(t, base / "workspace", base / "run", authorize_write=True, catalog=catalog)
            self.assertEqual(r["status"], "BLOCKED")
            self.assertFalse((base / "workspace/cases/risk-note.md").exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)

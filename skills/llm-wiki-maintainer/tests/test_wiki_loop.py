#!/usr/bin/env python3
"""Adversarial tests for the read-only Wiki loop. Only disposable fixtures."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wiki_loop as m

MAIN = "10000000-0000-4000-8000-000000000001"
OTHER = "10000000-0000-4000-8000-000000000002"
URL = "https://docs.python.org/3/library/itertools.html"

class WikiLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "evidence"
        self.src.mkdir()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.page = self.write_page(MAIN)
        self.second = self.write_page(OTHER)
        self.payload = b"Evidence in a frozen source (synthetic local fixture).\n"
        (self.src / "evidence.txt").write_bytes(self.payload)
        self.digest = hashlib.sha256(self.payload).hexdigest()

    def write_page(self, identity, body="* Content\nverified sample\n", extra=""):
        path = self.repo / "notes" / "knowledge" / "test" / (identity + ".org")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"#+TITLE: Test {identity}\n#+WIKI_ID: {identity}\n#+CATEGORY: QA\n"
            "#+FILETAGS: :qa:\n#+DATE: 2026-10-12\n"
            "#+SOURCE: https://docs.python.org/3/library/functions.html\n"
            "#+INGEST_ID: 90000000-0000-4000-8000-000000000001\n"
            f"#+WIKI_STATUS: published\n{extra}\n{body}", encoding="utf-8")
        return path

    def entry(self, **override):
        e = {"url": URL, "locator": "section 1", "retrieved_at": "2026-10-12",
             "sha256": self.digest, "snapshot_file": "evidence.txt",
             "target_wiki_id": MAIN, "related_wiki_ids": [OTHER], "revision": "v1"}
        e.update(override)
        return e

    def states(self, manifest):
        return m.make_plan(self.repo, self.src, manifest)

    def test_audit_without_deleted_navigation(self):
        pages, errors = m.inventory(self.repo)
        self.assertEqual((len(pages), errors), (2, []))
        self.assertTrue(m.RETIRED_PAGE_IDS.isdisjoint(pages))

    def test_exact_evidence_noop(self):
        self.write_page(MAIN, extra=f"#+EVIDENCE_RECORD: {self.digest} {URL}\n#+SOURCE2: {URL}")
        self.assertEqual(self.states([self.entry()])["items"][0]["state"], "NOOP_ALREADY_INDEXED")

    def test_changed_source_is_not_silently_overwritten(self):
        self.write_page(MAIN, extra=f"#+SOURCE2: {URL}")
        self.assertEqual(self.states([self.entry()])["items"][0]["state"], "REVIEW_EXISTING_SOURCE")

    def test_update_proposal_deterministic_and_read_only(self):
        before = self.page.read_bytes()
        plan = self.states([self.entry()])
        self.assertEqual(plan["items"][0]["state"], "PROPOSE_UPDATE")
        self.assertEqual(plan["writes_performed"], 0)
        self.assertEqual(before, self.page.read_bytes())
        self.assertEqual(plan, self.states([self.entry()]))

    def test_new_subject_proposal(self):
        new_id = "10000000-0000-4000-8000-000000000003"
        self.assertEqual(self.states([self.entry(target_wiki_id=new_id)])["items"][0]["state"], "PROPOSE_NEW")

    def test_batch_duplicate_noop(self):
        rows = self.states([self.entry(), self.entry()])["items"]
        self.assertEqual([r["state"] for r in rows], ["PROPOSE_UPDATE", "NOOP_DUPLICATE_INPUT"])
        self.assertEqual(rows[0]["event_key"], rows[1]["event_key"])

    def test_deleted_page_cannot_be_recreated(self):
        for removed in m.RETIRED_PAGE_IDS:
            item = self.states([self.entry(target_wiki_id=removed)])["items"][0]
            self.assertEqual(item["state"], "BLOCKED")
            self.assertIn("user-deleted", item["reason"])

    def test_deleted_page_cannot_be_linked(self):
        removed = next(iter(m.RETIRED_PAGE_IDS))
        self.assertEqual(self.states([self.entry(related_wiki_ids=[removed])])["items"][0]["state"], "BLOCKED")

    def test_unknown_relation_blocked(self):
        item = self.states([self.entry(related_wiki_ids=["missing-id"])])["items"][0]
        self.assertIn("unknown relation", item["reason"])
        self.assertEqual(item["state"], "BLOCKED")

    def test_snapshot_sha_mismatch_and_traversal(self):
        for e in [self.entry(sha256="0"*64), self.entry(snapshot_file="../outside.txt"),
                  self.entry(snapshot_file="missing.txt")]:
            self.assertEqual(self.states([e])["items"][0]["state"], "BLOCKED")

    def test_sensitive_snapshot_is_rejected(self):
        data = b"ghp_" + b"A"*28
        (self.src / "evidence.txt").write_bytes(data)
        item = self.states([self.entry(sha256=hashlib.sha256(data).hexdigest())])["items"][0]
        self.assertEqual(item["state"], "BLOCKED")
        self.assertIn("sensitive content", item["reason"])

    def test_dangling_wiki_link_blocks_ingest(self):
        self.write_page(MAIN, body="* Broken\n[[wiki:not-real][Missing]]")
        plan = self.states([self.entry()])
        self.assertEqual(plan["gate"], "BLOCKED_REPOSITORY")

    def test_retired_page_in_repo_blocks_ingest(self):
        self.write_page(next(iter(m.RETIRED_PAGE_IDS)))
        self.assertEqual(self.states([self.entry()])["gate"], "BLOCKED_REPOSITORY")

    def test_literal_code_link_ignored(self):
        self.write_page(MAIN, body="* Example\n#+begin_src text\n[[wiki:not-real][sample]]\n#+end_src\n")
        self.assertEqual(m.inventory(self.repo)[1], [])

    def test_invalid_urls_blocked(self):
        for url in ["http://docs.python.org/", "https://example.com/test",
                    "https://user:pass@docs.python.org/a"]:
            self.assertEqual(self.states([self.entry(url=url)])["items"][0]["state"], "BLOCKED")

    def test_head_mismatch_stops(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "notes"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "A"], check=True)
        baseline = m.git_head(self.repo)
        m.assert_head(self.repo, baseline)
        self.write_page("10000000-0000-4000-8000-000000000004")
        subprocess.run(["git", "-C", str(self.repo), "add", "notes"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "B"], check=True)
        with self.assertRaises(m.Invalid):
            m.assert_head(self.repo, baseline)

    def test_real_cli_audit_plan(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buf = StringIO()
        with redirect_stdout(buf):
            status = m.main(["audit", "--repo", str(self.repo)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(buf.getvalue())["gate"], "PASS")
        path = self.root / "sources.json"
        path.write_text(json.dumps([self.entry()]), encoding="utf-8")
        buf = StringIO()
        with redirect_stdout(buf):
            status = m.main(["plan", "--repo", str(self.repo),
                             "--manifest", str(path), "--evidence-dir", str(self.src)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(buf.getvalue())["items"][0]["state"], "PROPOSE_UPDATE")

if __name__ == "__main__":
    unittest.main(verbosity=2)

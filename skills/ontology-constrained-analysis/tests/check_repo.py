#!/usr/bin/env python3
"""Offline source-gate regression tests; no live network, no test data for analysis."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import source_gate as sg  # noqa: E402

SOURCE = "https://raw.githubusercontent.com/example/repo/main/sample.txt"
DATA = b"timestamp;meter\n2020-01-01 00:00;2\n"
GIT_SHA = hashlib.sha1(f"blob {len(DATA)}\0".encode() + DATA).hexdigest()


class Response:
    status = 200
    def __init__(self, payload, headers=None):
        self.source = io.BytesIO(payload)
        self.headers = headers if headers is not None else {"Content-Length": str(len(payload))}
    def read(self, size=-1):
        return self.source.read(size)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.source.close()


def fake_open(mode):
    def dispatch(request, timeout=None):
        url = request.full_url
        if url.startswith("https://api.github.com/repos/example/repo/contents/"):
            metadata = {"type": "file", "sha": GIT_SHA, "size": len(DATA)}
            return Response(json.dumps(metadata).encode())
        if "/git/blobs/" in url:
            return Response(DATA if mode == "blob" else b"<html>not file</html>")
        if url.startswith("https://github.com/example/repo/raw/"):
            return Response(DATA if mode in ("blob", "page") else b"<html>not file</html>")
        raise OSError("mock: raw.githubusercontent.com DNS unavailable")
    return dispatch


class SourceGateTests(unittest.TestCase):
    def test_git_blob_recovery(self):
        with tempfile.TemporaryDirectory() as td, patch.object(
            sg.urllib.request, "urlopen", side_effect=fake_open("blob")
        ):
            result = sg._verified_github_blob(
                {"url": SOURCE, "name": "sample.txt"}, Path(td), 1
            )
            self.assertEqual(result["status"], "BYTES_VERIFIED")
            self.assertEqual(result["sha256"], hashlib.sha256(DATA).hexdigest())
            self.assertEqual(result["git_blob_sha"], GIT_SHA)
            self.assertEqual(Path(result["local_path"]).read_bytes(), DATA)

    def test_github_file_fallback_if_blob_api_does_not_return_original_bytes(self):
        with tempfile.TemporaryDirectory() as td, patch.object(
            sg.urllib.request, "urlopen", side_effect=fake_open("page")
        ):
            result = sg._verified_github_blob(
                {"url": SOURCE, "name": "sample.txt"}, Path(td), 1
            )
            self.assertEqual(result["transport"], "github_file_raw")
            self.assertTrue(result["transport_fallback_errors"])

    def test_truncated_or_html_bodies_are_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(
            sg.urllib.request, "urlopen", side_effect=fake_open("broken")
        ):
            with self.assertRaisesRegex(OSError, "GITHUB_SAME_BLOB_TRANSFER_FAILED"):
                sg._verified_github_blob(
                    {"url": SOURCE, "name": "sample.txt"}, Path(td), 1
                )
            self.assertFalse((Path(td) / "sample.txt").exists())

    def test_pinned_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(
            sg.urllib.request, "urlopen", side_effect=fake_open("blob")
        ):
            with self.assertRaisesRegex(OSError, "GITHUB_SAME_BLOB_TRANSFER_FAILED"):
                sg._verified_github_blob(
                    {"url": SOURCE, "name": "sample.txt", "sha256": "0" * 64},
                    Path(td), 1
                )

    def test_raw_without_length_or_pinned_hash_is_not_accepted(self):
        def no_length(request, timeout=None):
            return Response(DATA, headers={})
        with tempfile.TemporaryDirectory() as td, patch.object(
            sg.urllib.request, "urlopen", side_effect=no_length
        ):
            result = sg._fetch_raw_resumable(
                {"url": SOURCE, "name": "sample.txt"}, Path(td), 1
            )
            self.assertEqual(result["status"], "SOURCE_BYTES_UNAVAILABLE")
            self.assertIn("UNVERIFIABLE_LENGTH", result["error"])

    def test_failed_source_produces_three_audit_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(
                {"files": [{"url": SOURCE, "name": "sample.txt"}]}
            ), encoding="utf-8")
            args = ["source_gate.py", "--manifest", str(manifest),
                    "--out", str(root / "artifacts"), "--prefer-github-blob"]
            with patch.object(sys, "argv", args), patch.object(
                sg.urllib.request, "urlopen", side_effect=OSError("mock DNS error")
            ):
                self.assertEqual(sg.main(), 2)
            out = root / "artifacts"
            for name in ("source_gate_receipt.json", "source_gate_blocked.md",
                         "source_gate_blocked.html"):
                self.assertTrue((out / name).is_file(), name)
            receipt = json.loads(
                (out / "source_gate_receipt.json").read_text("utf-8")
            )
            self.assertFalse(receipt["complete"])
            self.assertIn("mock DNS error", receipt["results"][0]["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

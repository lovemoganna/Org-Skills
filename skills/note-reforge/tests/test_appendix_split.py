"""Regression tests for exact source retention across linked Org appendices."""
import tempfile
import unittest
from pathlib import Path

from check_org_output import validate

BLOCK = "#+begin_src xml :eval never-export\n<template id=\"prompt_optimizer\"/>\n#+end_src"
BLOCK2 = "#+BEGIN_SRC python\nprint(1)\n#+END_SRC"


class AppendixSplitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.indexed = base / "indexed"
        self.drafts = base / "drafts"
        self.indexed.mkdir()
        self.drafts.mkdir()
        self.src = self.indexed / "prompt-foundations.org"
        self.main = self.drafts / "prompt-foundations.next.org"
        self.appendix = self.drafts / "prompt-foundations.xml-appendix.org"
        self.source_header = "#+TITLE: 提示词的四要素\n#+WIKI_ID: test-id\n#+WIKI_STATUS: published\n"
        self.src.write_text(self.source_header + "\n* 四要素\n" + BLOCK + "\n",
                            encoding="utf-8")
        self.main.write_text(self.source_header.replace("四要素", "构成与验证") +
                             "\n* 四要素\n参考 [[file:prompt-foundations.xml-appendix.org][XML 原始模板]]。\n",
                             encoding="utf-8")
        self.appendix.write_text("#+TITLE: XML 原始素材\n\n* 模板\n" + BLOCK + "\n",
                                 encoding="utf-8")

    def check(self):
        return validate(self.src, self.main, self.indexed, [self.appendix])

    def test_valid_split(self):
        self.assertEqual(self.check(), [])

    def test_missing_block(self):
        self.appendix.write_text("#+TITLE: No XML\n", encoding="utf-8")
        self.assertTrue(any("code blocks" in e for e in self.check()))

    def test_tampered_block(self):
        self.appendix.write_text(self.appendix.read_text(encoding="utf-8").replace(
            "prompt_optimizer", "prompt_modifier"), encoding="utf-8")
        self.assertTrue(any("code blocks" in e for e in self.check()))

    def test_duplicate_block(self):
        self.main.write_text(self.main.read_text(encoding="utf-8") + BLOCK + "\n",
                             encoding="utf-8")
        self.assertTrue(any("code blocks" in e for e in self.check()))

    def test_missing_link(self):
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "[[file:prompt-foundations.xml-appendix.org][XML 原始模板]]", "XML 原始模板"),
            encoding="utf-8")
        self.assertTrue(any("lacks a file: link" in e for e in self.check()))

    def test_appendix_identity(self):
        self.appendix.write_text("#+WIKI_ID: another-id\n" +
                                 self.appendix.read_text(encoding="utf-8"),
                                 encoding="utf-8")
        self.assertTrue(any("must not contain" in e for e in self.check()))

    def test_indexed_root_for_all_artifacts(self):
        relocated = self.indexed / "appendix.org"
        relocated.write_text(self.appendix.read_text(encoding="utf-8"), encoding="utf-8")
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "file:prompt-foundations.xml-appendix.org", "file:../indexed/appendix.org"),
            encoding="utf-8")
        self.assertTrue(any("appendix of published-note" in e for e in
                            validate(self.src, self.main, self.indexed, [relocated])))

    def test_missing_index_root_is_not_equivalent_to_safe(self):
        self.assertEqual(validate(self.src, self.main, None, [self.appendix]), [])

    def test_single_file_contract_backward_compatible(self):
        self.main.write_text(self.source_header + "\n* 四要素\n" + BLOCK + "\n",
                             encoding="utf-8")
        self.assertEqual(validate(self.src, self.main, self.indexed), [])
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "prompt_optimizer", "prompt_modifier"), encoding="utf-8")
        self.assertTrue(validate(self.src, self.main, self.indexed))

    def test_case_sensitive_block_and_two_appendices(self):
        self.src.write_text(self.src.read_text(encoding="utf-8") + BLOCK2 + "\n",
                            encoding="utf-8")
        appendix2 = self.drafts / "script.org"
        appendix2.write_text("#+TITLE: script\n\n" + BLOCK2 + "\n", encoding="utf-8")
        self.main.write_text(self.main.read_text(encoding="utf-8") +
                             "\n[[file:script.org][Code]]\n", encoding="utf-8")
        self.assertEqual(validate(self.src, self.main, self.indexed,
                                  [self.appendix, appendix2]), [])
        appendix2.write_text(appendix2.read_text(encoding="utf-8").replace(
            "#+BEGIN_SRC", "#+begin_src"), encoding="utf-8")
        self.assertTrue(validate(self.src, self.main, self.indexed,
                                 [self.appendix, appendix2]))

    def test_double_appendix_path_rejected(self):
        self.assertTrue(any("duplicate appendix" in e for e in
                            validate(self.src, self.main, self.indexed,
                                     [self.appendix, self.appendix])))

    def test_main_publish_identity_change_rejected(self):
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "WIKI_ID: test-id", "WIKI_ID: other"), encoding="utf-8")
        self.assertTrue(any("headers changed" in e for e in self.check()))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression for actual 2026-10-11 Org Museum Emacs export failures."""
from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
path = root / "plugins/org-museum/skills/org-museum-ingest/scripts/validate_note.py"
spec = importlib.util.spec_from_file_location("museum_validator", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

def should_fail(body: str):
    try:
        module.check_unprotected_template_placeholders(body, "fixture.org")
    except module.Invalid as error:
        assert "unprotected template placeholder" in str(error)
        return
    raise AssertionError("A dangerous prompt variable went undetected")

def should_pass(body: str):
    module.check_unprotected_template_placeholders(body, "fixture.org")

should_fail("正文 {{{Question}}} 需要换成真实内容")
should_fail("4. 模板还可扩展，如~{{{Examples}}}~、~{{{RelatedConcepts}}}~")
should_fail("原文中的 ={{{Topic}}}= 看起来像代码但仍可能被展开")
should_pass("#+begin_src markdown\n原始模板 {{{Question}}} {{{Topic}}}\n#+end_src\n")
should_pass("#+begin_example\n保留原话 {{{Question}}}\n#+end_example\n")
should_pass("标题：{{{title}}}（有效的内置 Org 宏）")
should_pass("普通花括号 {Topic} 与其他文档仍可出现")
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    target = base/"notes"/"knowledge"/"macro-example"/"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.org"
    target.parent.mkdir(parents=True)
    prefix = """#+TITLE: 模板保真
#+WIKI_ID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
#+CATEGORY: 测试
#+FILETAGS: :test:
#+DATE: 2026-10-11
#+SOURCE: local fixture
#+INGEST_ID: 11111111-2222-3333-4444-555555555555
#+WIKI_STATUS: draft

"""
    target.write_text(prefix+"模板变量 {{{Question}}} 还未防护", encoding="utf-8")
    try:
        module.validate(base)
    except module.Invalid as error:
        assert "unprotected template placeholder" in str(error)
    else:
        raise AssertionError("End-to-end validator did not detect macro")
    target.write_text(prefix+"#+begin_example\n模板变量 {{{Question}}} 仅供展示\n#+end_example", encoding="utf-8")
    assert len(module.validate(base))==1

print("PASS: 8 macro-preflight regression cases and full note validation")

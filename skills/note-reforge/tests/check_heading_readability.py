#!/usr/bin/env python3
"""Conservative editorial heading preflight, not an aesthetic-quality judge.

Reports likely overlong, argument-like headings and generic headings.
Warnings need human review; names, bilingual headings and meaningful questions
must never be truncated automatically.
Usage: python check_heading_readability.py document.md [--strict]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

MD = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")
ORG = re.compile(r"^\s*\*{1,6}\s+(.+?)\s*$")
META = re.compile(r"^\s*#\+TITLE:\s*(.+?)\s*$", flags=re.I)
FENCE = re.compile(r"^\s*(?:\x60{3,}|~{3,})")
GENERIC = {"其他", "一些思考", "若干想法", "有关问题", "更多内容"}
CONNECTORS = "：，；？！"


def issues(document: str, suffix: str = ".md") -> list[tuple[int, str, str]]:
    result = []
    in_fence = False
    seen: set[str] = set()
    for n, line in enumerate(document.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hit = (META.match(line) or ORG.match(line)) if suffix == ".org" else MD.match(line)
        if not hit:
            continue
        title = hit.group(1).strip()
        clean = re.sub(r"〔补〕", "", title).strip()
        # Pure review candidates: length alone does not equal failure.
        if clean in GENERIC:
            reason = "过于空泛"
        elif clean in seen:
            reason = "同文重复，导航难区分"
        elif (len(clean) >= 22 or
              (len(clean) >= 16 and any(ch in clean for ch in "：，；")) or
              (len(clean) >= 13 and sum(clean.count(c) for c in CONNECTORS) >= 2)):
            reason = "疑似把解释或判断写进标题"
        else:
            reason = ""
        if reason:
            result.append((n, title, reason))
        seen.add(clean)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("document", type=Path)
    p.add_argument("--strict", action="store_true", help="仅用于固定测试案例的阻断模式")
    args = p.parse_args()
    try:
        flags = issues(args.document.read_text(encoding="utf-8"), args.document.suffix.lower())
    except (OSError, UnicodeError) as exc:
        print(f"读取失败：{exc}")
        return 2
    for n, title, why in flags:
        print(f"第 {n} 行候选复查：{title}（{why}）")
    print(f"标题审稿候选：{len(flags)} 处；无需自动改名，须人工检查主题与链接")
    return 1 if args.strict and flags else 0


if __name__ == "__main__":
    raise SystemExit(main())

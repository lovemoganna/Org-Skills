#!/usr/bin/env python3
"""Suggest likely process narration in a finished note; never a semantic quality judge.

Usage: python check_result_voice.py note.md [--advisory]
"""
import argparse
import re
from pathlib import Path

PATTERNS = (
    r"^\s*(?:原文|原章节|原始材料|原稿|本次炼化|这次改写|原笔记)(?:首先|主要|一方面|另一方面)?(?:提出|介绍|建议|提到|举过|展示|保留|改写|梳理|说明|要求|强调|还讨论|还给出|并非)",
    r"^\s*(?:需要区分两个判断|这篇笔记讨论了什么|我们在原文的基础上|(?:本次|这次)(?:重写|炼化|优化)|(?:新版|这一版)(?:增加|补充|保留|改写))",
)

def candidates(markdown):
    found, in_fence, provenance = [], False, False
    for n, line in enumerate(markdown.splitlines(), 1):
        stripped = line.strip()
        if re.match(r"^\s*(?:~{3}|\x60{3})", line):
            in_fence = not in_fence
            continue
        if re.match(r"^(?:#{1,6}|\*{1,6})\s", line):
            provenance = bool(re.search(r"来源|参考资料|原始材料|版权|证据边界|引文|文献对照", line))
        if re.match(r"(?i)^\s*#\+begin_(?:src|example|quote)\b", line):
            in_fence = True
            continue
        if re.match(r"(?i)^\s*#\+end_(?:src|example|quote)\b", line):
            in_fence = False
            continue
        if in_fence or provenance or stripped.startswith(">") or stripped.startswith("|"):
            continue
        if any(re.search(pattern, line) for pattern in PATTERNS):
            found.append((n, stripped))
    return found

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="Org or Markdown note to review")
    p.add_argument("--advisory", action="store_true")
    args = p.parse_args()
    try:
        found = candidates(args.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as e:
        print("读取失败：", e)
        return 2
    for n, line in found:
        print(f"第 {n} 行疑似加工过程叙述：{line}")
    print(f"疑似过程叙述 {len(found)} 处；其余内容质量仍需人工验收")
    return 0 if args.advisory or not found else 1

if __name__ == "__main__":
    raise SystemExit(main())

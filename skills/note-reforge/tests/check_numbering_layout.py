#!/usr/bin/env python3
"""辅助发现多道带源编号的问题被压进同一 Markdown 引用块。

这是高置信度的格式提示，不是审美评分或事实校验。
Usage: python check_numbering_layout.py article.md [--advisory]
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

QUESTION = re.compile(r"^>\s*(?:\*\*)?([A-Za-z]{0,5}\d+-\d+)(?:\*\*)?[:：]\s*")
FENCE = re.compile(r"^\s*(?:~{3,}|\x60{3,})")


def issues(content: str) -> list[tuple[int, int]]:
    """Return start line and length of consecutive source-ID quote lines."""
    found = []
    sequence = []
    inside_code = False

    def flush() -> None:
        if len(sequence) >= 2:
            found.append((sequence[0], len(sequence)))
        sequence.clear()

    for lineno, line in enumerate(content.splitlines(), 1):
        if FENCE.match(line):
            flush()
            inside_code = not inside_code
            continue
        if inside_code:
            continue
        if QUESTION.match(line):
            sequence.append(lineno)
        else:
            flush()
    flush()
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path)
    parser.add_argument("--advisory", action="store_true", help="仅报告，不阻断")
    args = parser.parse_args()
    try:
        result = issues(args.article.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as err:
        print(f"读取失败：{err}")
        return 2
    for line, count in result:
        print(f"第 {line} 行起有连续 {count} 道源编号问题被写成同一引用块：建议改为语义有序列表")
    print(f"疑似编号排版问题：{len(result)} 处；视觉品质仍需实际渲染和人工检查")
    return 0 if args.advisory or not result else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Pre-submit guard for an in-place published Org Museum source update.

This checks preservation only. It does not certify factual correctness,
independent user value, link reachability, or live deployment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys


LITERAL = re.compile(
    r"(?ims)^\s*#\+begin_(src|example|quote)\b[^\n]*\n.*?^\s*#\+end_\1[^\n]*"
)
LINK = re.compile(r"\[\[([^]\n]+)\]")
ANCHOR = re.compile(r"(?im)^\s*:(?:ID|CUSTOM_ID):\s*.+$")
HEADING = re.compile(r"(?m)^\*+\s+(.+)$")
HEADER = re.compile(r"(?im)^\s*#\+(\w+):[^\n]*$")


def protected(original: str) -> dict[str, Counter[str]]:
    # Keep original Org metadata, hyperlink targets, anchors, heading names,
    # and entire literal blocks; TITLE is the only editable file-header field.
    prose = LITERAL.sub("", original)
    headers = Counter(
        m.group(0).strip() for m in HEADER.finditer(prose)
        if m.group(1).upper() != "TITLE"
    )
    return {
        "metadata": headers,
        "links": Counter(LINK.findall(original)),
        "anchors": Counter(m.group(0).strip() for m in ANCHOR.finditer(original)),
        "headings": Counter(HEADING.findall(prose)),
        "literal_blocks": Counter(m.group(0) for m in LITERAL.finditer(original)),
    }


def evaluate(original: str, candidate: str) -> list[str]:
    before, after = protected(original), protected(candidate)
    errors = []
    wiki_id = re.compile(r"(?im)^#\+WIKI_ID:\s*(\S+)\s*$")
    first, second = wiki_id.search(original), wiki_id.search(candidate)
    if not first or not second or first.group(1) != second.group(1):
        errors.append("published WIKI_ID missing or changed")
    for kind in before:
        removed = before[kind] - after[kind]
        if removed:
            item, count = next(iter(removed.items()))
            errors.append(f"{kind}: {count} original occurrence(s) removed or changed: {item[:100]!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original published Org file from current main")
    parser.add_argument("candidate", type=Path, help="complete candidate Org file before ANY remote write")
    args = parser.parse_args()
    try:
        original = args.original.read_text(encoding="utf-8-sig")
        candidate = args.candidate.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        print(f"FAIL: unable to read original/candidate: {exc}", file=sys.stderr)
        return 2
    errors = evaluate(original, candidate)
    if errors:
        for issue in errors:
            print("FAIL:", issue)
        return 1
    print("PASS: original identity, metadata, heading references, anchors, links and literal blocks retained")
    print("NOTE: semantics, source truth and live deployment require separate verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

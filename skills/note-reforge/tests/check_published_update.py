#!/usr/bin/env python3
"""Pre-submit guard for an in-place published Org Museum source update.

This checks preservation only. It does not certify factual correctness,
independent user value, link reachability, or live deployment.
"""
from __future__ import annotations

import argparse
import json
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


def evaluate(original: str, candidate: str, authorized_removals=None) -> list[str]:
    before, after = protected(original), protected(candidate)
    errors = []
    ids = re.compile(r"(?im)^#\+WIKI_ID:\s*(\S+)\s*$")
    old_id, new_id = ids.search(original), ids.search(candidate)
    if not old_id or not new_id or old_id.group(1) != new_id.group(1):
        errors.append("published WIKI_ID missing or changed")
    if before["metadata"] != after["metadata"]:
        errors.append("original publication metadata changed")
    scope = authorized_removals or {}
    labels = {"links":"references", "anchors":"anchors", "headings":"heading references",
              "literal_blocks":"literal blocks"}
    if authorized_removals is not None:
        if not isinstance(authorized_removals, dict):
            return errors + ["scope must be an object"]
        if set(scope) - {"user_directive", *labels.values()}:
            errors.append("unknown removal scope field")
        if not isinstance(scope.get("user_directive"), str) or not scope.get("user_directive", "").strip():
            errors.append("explicit user directive required")
    for kind, field in labels.items():
        declared = scope.get(field, [])
        if not isinstance(declared, list) or any(not isinstance(item, str) or not item for item in declared):
            errors.append(f"{kind}: invalid removal entries")
        elif before[kind] - after[kind] != Counter(declared):
            errors.append(f"{kind}: actual removals do not match declared scope")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original published Org file from current main")
    parser.add_argument("candidate", type=Path, help="complete candidate Org file before ANY remote write")
    parser.add_argument("--authorized-removals", type=Path)
    args = parser.parse_args()
    try:
        original = args.original.read_text(encoding="utf-8-sig")
        candidate = args.candidate.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        print(f"FAIL: unable to read original/candidate: {exc}", file=sys.stderr)
        return 2
    try:
        scope = json.loads(args.authorized_removals.read_text(encoding="utf-8-sig")) if args.authorized_removals else None
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"FAIL: invalid scope: {exc}", file=sys.stderr)
        return 2
    errors = evaluate(original, candidate, scope)
    if errors:
        for issue in errors:
            print("FAIL:", issue)
        return 1
    print("PASS: publication identity/metadata and exact user-authorized edit scope verified")
    print("NOTE: semantics, source truth and live deployment require separate verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

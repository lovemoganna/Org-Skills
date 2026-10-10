#!/usr/bin/env python3
"""Check structural fidelity and draft isolation for note-reforge Org output."""
import argparse
import re
from pathlib import Path


def fields(text):
    header = text.split('\n* ', 1)[0]
    return [
        line for line in header.splitlines()
        if re.match(r'(?i)^#\+[A-Z][A-Z_0-9-]*:', line)
    ]


def blocks(text):
    pattern = r'(?ims)^#\+begin_src\b[^\n]*\n.*?^#\+end_src[^\n]*
    return re.findall(pattern, text)


def validate(src_path, dest_path, indexed_root=None):
    if src_path.resolve() == dest_path.resolve():
        return ["output must not overwrite source"]
    source = src_path.read_text(encoding="utf-8")
    dest = dest_path.read_text(encoding="utf-8")
    src_header = [x for x in fields(source) if not re.match(r'(?i)^#\+TITLE:', x)]
    dst_header = [x for x in fields(dest) if not re.match(r'(?i)^#\+TITLE:', x)]
    errors = []
    if src_header != dst_header:
        errors.append("non-title Org headers changed or were added")
    if blocks(source) != blocks(dest):
        errors.append("original source code blocks changed or disappeared")
    has_identity = any(
        re.match(r'(?i)^#\+(WIKI_ID|INGEST_ID|WIKI_STATUS):', x)
        for x in fields(source)
    )
    if has_identity and indexed_root:
        if dest_path.resolve().is_relative_to(indexed_root.resolve()):
            errors.append("identity-bearing draft is inside indexed root")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--indexed-root", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.source, args.output, args.indexed_root)
    except (OSError, UnicodeError) as err:
        errors = [f"cannot inspect files: {err}"]
    if errors:
        for err in errors:
            print("FAIL:", err)
        return 1
    print(
        "PASS: Org metadata/code preserved; indexed-root gate "
        + ("checked" if args.indexed_root else "not requested")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

    return re.findall(pattern, text)


def validate(src_path, dest_path, indexed_root=None):
    if src_path.resolve() == dest_path.resolve():
        return ["output must not overwrite source"]
    source = src_path.read_text(encoding="utf-8")
    dest = dest_path.read_text(encoding="utf-8")
    src_header = [x for x in fields(source) if not re.match(r'(?i)^#\+TITLE:', x)]
    dst_header = [x for x in fields(dest) if not re.match(r'(?i)^#\+TITLE:', x)]
    errors = []
    if src_header != dst_header:
        errors.append("non-title Org headers changed or were added")
    if blocks(source) != blocks(dest):
        errors.append("original source code blocks changed or disappeared")
    has_identity = any(
        re.match(r'(?i)^#\+(WIKI_ID|INGEST_ID|WIKI_STATUS):', x)
        for x in fields(source)
    )
    if has_identity and indexed_root:
        if dest_path.resolve().is_relative_to(indexed_root.resolve()):
            errors.append("identity-bearing draft is inside indexed root")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--indexed-root", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.source, args.output, args.indexed_root)
    except (OSError, UnicodeError) as err:
        errors = [f"cannot inspect files: {err}"]
    if errors:
        for err in errors:
            print("FAIL:", err)
        return 1
    print(
        "PASS: Org metadata/code preserved; indexed-root gate "
        + ("checked" if args.indexed_root else "not requested")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check Org metadata, original code blocks, appendix links and draft isolation."""
import argparse
from collections import Counter
import re
from pathlib import Path
from urllib.parse import unquote


def fields(text):
    header = text.split('\n* ', 1)[0]
    return [
        line for line in header.splitlines()
        if re.match(r'(?i)^#\+[A-Z][A-Z_0-9-]*:', line)
    ]


def blocks(text):
    pattern = r'(?ims)^#\+begin_src\b[^\n]*\n.*?^#\+end_src[^\n]*$'
    return re.findall(pattern, text)


def org_file_targets(text, from_path):
    """Resolve local Org file: links, excluding optional ::search suffixes."""
    targets = set()
    for raw in re.findall(r'(?i)\[\[file:([^\]]+)\]', text):
        path = unquote(raw.split("::", 1)[0])
        if path:
            targets.add((from_path.parent / path).resolve())
    return targets


def has_publish_identity(text):
    return any(
        re.match(r'(?i)^#\+(WIKI_ID|INGEST_ID|WIKI_STATUS):', line)
        for line in fields(text)
    )


def validate(src_path, dest_path, indexed_root=None, appendices=None):
    src_path, dest_path = Path(src_path), Path(dest_path)
    appendix_paths = [Path(path) for path in (appendices or [])]
    source_path, output_path = src_path.resolve(), dest_path.resolve()
    errors = []
    if source_path == output_path:
        errors.append("output must not overwrite source")
    if len({p.resolve() for p in appendix_paths}) != len(appendix_paths):
        errors.append("duplicate appendix path")
    if any(p.resolve() in (source_path, output_path) for p in appendix_paths):
        errors.append("appendix must be distinct from source and output")

    source = src_path.read_text(encoding="utf-8")
    dest = dest_path.read_text(encoding="utf-8")
    src_header = [x for x in fields(source) if not re.match(r'(?i)^#\+TITLE:', x)]
    dst_header = [x for x in fields(dest) if not re.match(r'(?i)^#\+TITLE:', x)]
    if src_header != dst_header:
        errors.append("non-title Org headers changed or were added")

    if not appendix_paths:
        # Preserve the original single-file contract and block order.
        if blocks(source) != blocks(dest):
            errors.append("original source code blocks changed or disappeared")
    else:
        # Split drafts preserve every original block exactly once across artifacts.
        combined = list(blocks(dest))
        links = org_file_targets(dest, dest_path)
        for path in appendix_paths:
            if path.resolve() not in links:
                errors.append("main draft lacks a file: link to appendix: " + str(path))
            appendix = path.read_text(encoding="utf-8")
            if has_publish_identity(appendix):
                errors.append("appendix must not contain published-note identity: " + str(path))
            combined.extend(blocks(appendix))
        if Counter(blocks(source)) != Counter(combined):
            errors.append("original source code blocks missing, changed, duplicated or unexpected")

    if has_publish_identity(source) and indexed_root:
        root = Path(indexed_root).resolve()
        if output_path.is_relative_to(root):
            errors.append("identity-bearing draft is inside indexed root")
        for path in appendix_paths:
            if path.resolve().is_relative_to(root):
                errors.append("appendix of published-note draft is inside indexed root: " + str(path))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--indexed-root", type=Path)
    parser.add_argument("--appendix", type=Path, action="append", default=[],
                        help="Additional split artifact; repeat for multiple appendices")
    args = parser.parse_args()
    try:
        errors = validate(args.source, args.output, args.indexed_root, args.appendix)
    except (OSError, UnicodeError) as err:
        errors = ["cannot inspect files: " + str(err)]
    if errors:
        for err in errors:
            print("FAIL:", err)
        return 1
    print("PASS: Org headers and exact original code preserved"
          + (" across linked appendices" if args.appendix else "")
          + "; indexed-root gate "
          + ("checked" if args.indexed_root else "not requested"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

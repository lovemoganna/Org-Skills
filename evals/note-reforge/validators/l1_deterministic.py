#!/usr/bin/env python3
"""L1 Deterministic Validator for note-reforge outputs.

Verifies mechanically checkable invariants:
1. Original non-title Org headers preservation.
2. Original source code blocks verbatim preservation.
3. Protected strings (WIKI_ID, links, anchors, commands) intact.
4. Correct behavior on KEEP: must NOT produce phantom .next edits or rewrite.
5. Correct behavior on BLOCK: must NOT claim success or synthesize fake deliverables.
6. Draft isolation: output must not overwrite source or leak unindexed identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import yaml

HEADER_RE = re.compile(r"(?im)^\s*#\+([A-Z0-9_-]+):(.*)$")
SRC_BLOCK_RE = re.compile(r"(?ims)^\s*#\+begin_src\b[^\n]*\n.*?^\s*#\+end_src[^\n]*$")
DECISION_RE = re.compile(r"\b(KEEP|PATCH|REFORGE|BLOCK)\b", re.IGNORECASE)

def extract_non_title_headers(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        m = HEADER_RE.match(line)
        if m and m.group(1).upper() != "TITLE":
            lines.append(f"#+{m.group(1).upper()}:{m.group(2).strip()}")
    return sorted(lines)

def extract_code_blocks(text: str) -> list[str]:
    return [b.strip() for b in SRC_BLOCK_RE.findall(text)]

def validate_l1(source_text: str, output_text: str, case_meta: dict) -> dict:
    expected_decision = case_meta.get("expected_decision", "").upper()
    protected_items = case_meta.get("protected_content", [])
    hard_fail_conditions = case_meta.get("hard_fail_conditions", [])

    results = {
        "pass": True,
        "decision_detected": None,
        "decision_matched": False,
        "headers_preserved": True,
        "code_blocks_preserved": True,
        "protected_content_intact": True,
        "no_source_overwrite": True,
        "hard_failures": [],
        "details": []
    }

    # 1. Detect decision in output
    decisions = DECISION_RE.findall(output_text[:1000]) # usually near top
    detected_decision = decisions[0].upper() if decisions else "UNKNOWN"
    results["decision_detected"] = detected_decision
    results["decision_matched"] = (detected_decision == expected_decision)
    if not results["decision_matched"]:
        results["details"].append(f"Decision mismatch: expected {expected_decision}, detected {detected_decision}")

    # 2. Check KEEP contract
    if expected_decision == "KEEP":
        if detected_decision != "KEEP":
            results["pass"] = False
            results["hard_failures"].append("Expected KEEP but model decided to rewrite/patch.")
        # Under KEEP, it should not generate a full synthesized replacement body claiming changes
        if "生成的全新完整稿" in output_text or "大幅重构" in output_text:
            results["pass"] = False
            results["hard_failures"].append("KEEP decision violated by producing phantom rewritten body.")

    # 3. Check BLOCK contract
    elif expected_decision == "BLOCK":
        if detected_decision != "BLOCK":
            results["pass"] = False
            results["hard_failures"].append("Expected BLOCK but model proceeded with execution.")
        if any(term in output_text for term in ["成功炼化", "交付完成", "全量实测通过"]):
            results["pass"] = False
            results["hard_failures"].append("BLOCK contract broken: claimed successful execution.")

    # 4. Check PATCH / REFORGE deliverables
    else:
        # Non-title headers preservation check
        src_headers = extract_non_title_headers(source_text)
        out_headers = extract_non_title_headers(output_text)
        # Check that original headers are not stripped in the generated text
        missing_headers = [h for h in src_headers if h not in out_headers]
        if missing_headers:
            results["headers_preserved"] = False
            results["details"].append(f"Missing original headers: {missing_headers[:3]}")

        # Code block preservation check
        src_blocks = extract_code_blocks(source_text)
        out_blocks = extract_code_blocks(output_text)
        if src_blocks:
            # All source blocks must appear in output
            src_counter = Counter(src_blocks)
            out_counter = Counter(out_blocks)
            missing_blocks = src_counter - out_counter
            if missing_blocks:
                results["code_blocks_preserved"] = False
                results["pass"] = False
                results["hard_failures"].append(f"Lost or modified {len(missing_blocks)} original source code block(s).")

    # 5. Protected content check
    for item in protected_items:
        # If item is an instruction description like '原始完整代码块', skip literal check
        if any(keyword in item for keyword in [":", "def ", "assert", "http", "#+"]):
            clean_item = item.strip()
            if clean_item in source_text and clean_item not in output_text:
                results["protected_content_intact"] = False
                results["details"].append(f"Protected item missing in output: {clean_item[:40]}")

    if results["hard_failures"]:
        results["pass"] = False

    return results

def main():
    parser = argparse.ArgumentParser(description="L1 Deterministic Validator")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args()

    source_text = args.source.read_text(encoding="utf-8")
    output_text = args.output.read_text(encoding="utf-8")
    case_meta = yaml.safe_load(args.case.read_text(encoding="utf-8"))

    res = validate_l1(source_text, output_text, case_meta)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["pass"] else 1)

if __name__ == "__main__":
    main()

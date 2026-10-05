#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class SurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignore_depth = 0
        self.heading_tag = None
        self.heading_buf = []
        self.headings = []
        self.visible = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.ignore_depth:
            self.ignore_depth += 1
            return
        if tag in {"script", "style", "template", "noscript"}:
            self.ignore_depth = 1
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.heading_tag = tag
            self.heading_buf = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.ignore_depth:
            self.ignore_depth = max(0, self.ignore_depth - 1)
            return
        if self.heading_tag == tag:
            text = " ".join(self.heading_buf).strip()
            if text:
                self.headings.append(text)
            self.heading_tag = None
            self.heading_buf = []

    def handle_data(self, data):
        if self.ignore_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        self.visible.append(text)
        if self.heading_tag:
            self.heading_buf.append(text)


PROCESS_HEADING = re.compile(
    r"^(?:\d{1,2}\s*[/·.:-]\s*)?(?:what|so\s*what|why|who(?:\s*&\s*evidence)?|evidence|provenance|method|qa|regression|sql\s*evidence)$",
    re.I,
)

INTERNAL_PATTERNS = [
    re.compile(r"\bfixture\s*pass\b", re.I),
    re.compile(r"\brendered\s*qa\b", re.I),
    re.compile(r"\bduckdb\s*sql\b", re.I),
    re.compile(r"\bsql\s*evidence\b", re.I),
    re.compile(r"\bblocked_env\b", re.I),
    re.compile(r"\bregression\s*(?:pass|passed|status)\b", re.I),
]


def lint_html(text: str, allow_audit: bool = False) -> dict:
    parser = SurfaceParser()
    parser.feed(text)
    visible_text = " | ".join(parser.visible)
    violations = []

    if not allow_audit:
        for heading in parser.headings:
            normalized = " ".join(heading.split())
            if PROCESS_HEADING.match(normalized):
                violations.append({"type": "report_process_heading", "text": heading})

        for pattern in INTERNAL_PATTERNS:
            match = pattern.search(visible_text)
            if match:
                violations.append({"type": "internal_execution_state", "text": match.group(0)})

    return {
        "status": "PASS" if not violations else "FAIL",
        "headings": parser.headings,
        "violations": violations,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint a generated dashboard for report-shaped or internal audit UI leakage.")
    ap.add_argument("html", type=Path)
    ap.add_argument("--allow-audit", action="store_true", help="Allow audit/process content when the user explicitly requested an audit view.")
    args = ap.parse_args()

    result = lint_html(args.html.read_text(encoding="utf-8"), allow_audit=args.allow_audit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

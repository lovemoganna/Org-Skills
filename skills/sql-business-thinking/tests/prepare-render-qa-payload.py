#!/usr/bin/env python3
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

SAFE_INPUT_CHARS = 60000

def main():
    parser = argparse.ArgumentParser(
        description="Prepare an exact HTML artifact for sql-business-thinking remote Render QA."
    )
    parser.add_argument("html", type=Path)
    parser.add_argument(
        "--allow-design-notes",
        action="store_true",
        help="Allow visible chart-selection/design rationale in the remote Artifact Presentation QA.",
    )
    args = parser.parse_args()

    raw = args.html.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    payload = base64.b64encode(compressed).decode("ascii")

    if len(payload) > SAFE_INPUT_CHARS:
        raise SystemExit(
            f"REMOTE_RENDER_PAYLOAD_TOO_LARGE: compressed base64 is {len(payload)} characters; "
            f"safe inline limit is {SAFE_INPUT_CHARS}. Do not truncate. Use another authorized transport."
        )

    result = {
        "workflow": ".github/workflows/sql-business-thinking-render-qa.yml",
        "inputs": {
            "html_gzip_base64": payload,
            "expected_sha256": digest,
            "allow_design_notes": bool(args.allow_design_notes),
        },
        "artifact_sha256": digest,
        "raw_bytes": len(raw),
        "gzip_bytes": len(compressed),
        "base64_chars": len(payload),
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()

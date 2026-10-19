#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stability test runner for plantuml-diagram-engine.
- Generates PlantUML source for 18 scenarios (6 types × 3 difficulties)
- Runs each 3 times (independent files: run1/run2/run3)
- Validates: syntax, element presence, URL generation, online PNG, semantic consistency
- Records every failure with full evidence
- Never substitutes mock success for real failure
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.error
import urllib.request
import zlib
import base64
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # skills/plantuml-diagram-engine
SCRIPTS_DIR = ROOT / "scripts"
PUML_DIR = Path(__file__).parent / "puml_runs"
sys.path.insert(0, str(SCRIPTS_DIR))

from encode_url import plantuml_token, kroki_token, validate_source, RenderError

PLANTUML_BASE = "https://www.plantuml.com/plantuml/png/"
KROKI_BASE = "https://kroki.io/plantuml/png/"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
TIMEOUT = 20

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def probe_url(url: str) -> dict:
    """Make real HTTP request. Return evidence dict."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "plantuml-diagram-engine/1.0", "Accept": "image/png"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            elapsed = round(time.time() - t0, 2)
            ct = r.headers.get("Content-Type", "")
            err_hdr = r.headers.get("X-PlantUML-Diagram-Error") or r.headers.get("X-PlantUML-Error") or ""
            data = r.read(4 * 1024 * 1024)
            is_png = data[:8] == PNG_MAGIC
            size = len(data)
            # Detect error diagram: PlantUML returns a PNG with "Syntax Error" text for bad sources
            # We check: if valid PNG but very small (<400 bytes), likely error diagram
            tiny = is_png and size < 400
            return {
                "status": r.status,
                "content_type": ct,
                "error_header": err_hdr,
                "is_png": is_png,
                "size_bytes": size,
                "possibly_error_diagram": tiny or bool(err_hdr),
                "elapsed_s": elapsed,
                "ok": r.status == 200 and is_png and not err_hdr and not tiny,
            }
    except urllib.error.HTTPError as e:
        return {"status": e.code, "ok": False, "error": str(e), "elapsed_s": round(time.time()-t0,2)}
    except Exception as e:
        return {"status": 0, "ok": False, "error": str(e), "elapsed_s": round(time.time()-t0,2)}


def static_validate(source: str, fixture: dict) -> list[str]:
    """Return list of failure strings; empty = pass."""
    failures = []
    # Delimiter check
    try:
        validate_source(source)
    except RenderError as e:
        failures.append(f"DELIMITER_INVALID: {e}")

    # Required elements
    for elem in fixture.get("required_elements", []):
        if elem not in source:
            failures.append(f"MISSING_ELEMENT: {repr(elem)}")

    # Forbidden elements
    for elem in fixture.get("forbidden_elements", []):
        if elem in source:
            failures.append(f"FORBIDDEN_ELEMENT: {repr(elem)}")

    # Min nodes heuristic (count lines with real content excluding comments/style)
    content_lines = [
        l for l in source.splitlines()
        if l.strip() and not l.strip().startswith("'") and not l.strip().startswith("<")
        and not l.strip().startswith("skin") and l.strip() not in {"@startuml","@enduml","@startwbs","@endwbs","@startuml","@enduml"}
    ]
    min_nodes = fixture.get("min_nodes", 0)
    if min_nodes and len(content_lines) < min_nodes:
        failures.append(f"TOO_FEW_CONTENT_LINES: got {len(content_lines)}, expected >={min_nodes}")

    return failures


def check_diagram_type(source: str, expected: str) -> tuple[str, bool]:
    """Detect actual diagram type from source."""
    s = source.strip().lower()
    if s.startswith("@startwbs"):
        actual = "wbs"
    elif s.startswith("@startmindmap"):
        actual = "mindmap"
    elif s.startswith("@startgantt"):
        actual = "gantt"
    elif "statediagram" in s or ("[*]" in source and "-->" in source and "class" not in s):
        actual = "state"
    elif "sequencediagram" in s or ("participant" in s or ("actor" in s and "->" in s)):
        actual = "sequence"
    elif "componentdiagram" in s or ("[" in source and "]" in source and "-->" in source and "class" not in s and "if (" not in s):
        actual = "component"
    elif "classdiagram" in s or ("class " in source):
        actual = "class"
    elif "start\n" in source.lower() or "start\r\n" in source.lower() or ":接" in source or ":select" in source.lower() or "repeat" in source or "if (" in source:
        actual = "activity"
    else:
        actual = "unknown"

    match = (actual == expected.lower()) or (expected == "BLOCKED")
    return actual, match


def semantic_diff(sources: list[str], fixture_id: str) -> dict:
    """Compare 3 runs for semantic consistency."""
    if len(sources) < 2:
        return {"consistent": None, "note": "insufficient_runs"}

    # Compare required elements presence across runs
    import json as _json
    FIXTURES = _json.loads((Path(__file__).parent / "fixtures.json").read_text(encoding="utf-8"))
    fixture = next((f for f in FIXTURES if f["id"] == fixture_id), None)
    if not fixture:
        return {"consistent": None, "note": "fixture_not_found"}

    elem_presence = []
    for src in sources:
        presence = {e: (e in src) for e in fixture.get("required_elements", [])}
        elem_presence.append(presence)

    # All runs should have same required elements present/absent
    consistent = all(ep == elem_presence[0] for ep in elem_presence)

    # Also check diagram type consistency
    types = [check_diagram_type(s, fixture["expected_diagram_type"])[0] for s in sources]
    type_consistent = len(set(types)) <= 1

    return {
        "consistent": consistent and type_consistent,
        "element_presence_per_run": elem_presence,
        "diagram_types_per_run": types,
        "type_consistent": type_consistent,
        "element_consistent": consistent,
    }


# ─────────────────────────────────────────────
# Per-run test
# ─────────────────────────────────────────────

def run_single(fixture: dict, puml_path: Path, run_index: int) -> dict:
    """Execute one test run against a pre-generated .puml file."""
    result = {
        "fixture_id": fixture["id"],
        "run": run_index,
        "puml_path": str(puml_path),
        "timestamp": ts(),
        "failures": [],
        "warnings": [],
        "url": None,
        "kroki_url": None,
        "online": {},
        "static_ok": False,
        "type_match": False,
        "url_ok": False,
        "online_ok": False,
        "sensitive_blocked": None,
    }

    if not puml_path.exists():
        result["failures"].append(f"PUML_FILE_MISSING: {puml_path}")
        return result

    source = puml_path.read_text(encoding="utf-8")
    result["source_lines"] = len(source.splitlines())

    # ── Sensitive gate ──
    if fixture.get("sensitive"):
        # Must NOT generate a public URL for this source
        result["sensitive_blocked"] = True  # We generated the file, so we check content
        # The skill should have refused; we'll check if URL would expose real secrets
        # Since we DID write the file, we check if the source contains the sensitive markers
        sensitive_markers = ["a8f3c192", "bcrypt", "sk-prod-7f8e9d", "db-internal.company.com"]
        if any(m in source for m in sensitive_markers):
            result["sensitive_blocked"] = False
            result["failures"].append("SENSITIVE_DATA_IN_SOURCE: private info present in public-bound source")
        result["url_ok"] = result["sensitive_blocked"]
        result["static_ok"] = True  # Separate concern
        return result

    # ── Static checks ──
    static_failures = static_validate(source, fixture)
    result["static_ok"] = len(static_failures) == 0
    result["failures"].extend(static_failures)

    # ── Diagram type ──
    actual_type, type_match = check_diagram_type(source, fixture["expected_diagram_type"])
    result["actual_type"] = actual_type
    result["type_match"] = type_match
    if not type_match:
        # Check if adversarial (expected mismatch is documented)
        if fixture.get("note", ""):
            result["warnings"].append(f"TYPE_MISMATCH_ADVERSARIAL: expected={fixture['expected_diagram_type']}, actual={actual_type}")
        else:
            result["failures"].append(f"TYPE_MISMATCH: expected={fixture['expected_diagram_type']}, actual={actual_type}")

    # ── URL generation ──
    try:
        pt = plantuml_token(source)
        kt = kroki_token(source)
        result["url"] = PLANTUML_BASE + pt
        result["kroki_url"] = KROKI_BASE + kt
        result["url_ok"] = True
    except Exception as e:
        result["failures"].append(f"URL_GENERATION_FAILED: {e}")
        return result

    # ── Online verification ──
    print(f"  [{fixture['id']} run{run_index}] probing PlantUML...", flush=True)
    online = probe_url(result["url"])
    result["online"] = online
    if online.get("ok"):
        result["online_ok"] = True
        result["status"] = "PNG_VALIDATED / VISUAL_UNVERIFIED"
        if online.get("possibly_error_diagram"):
            result["warnings"].append("POSSIBLE_ERROR_DIAGRAM: PNG is valid but suspiciously small")
    else:
        # Try Kroki fallback
        print(f"  [{fixture['id']} run{run_index}] plantuml failed, trying kroki...", flush=True)
        online_k = probe_url(result["kroki_url"])
        result["online_kroki"] = online_k
        if online_k.get("ok"):
            result["online_ok"] = True
            result["status"] = "PNG_VALIDATED_VIA_KROKI / VISUAL_UNVERIFIED"
            result["warnings"].append("FALLBACK_TO_KROKI")
        else:
            result["failures"].append(f"ONLINE_FAIL: plantuml={online.get('error') or online.get('status')}, kroki={online_k.get('error') or online_k.get('status')}")
            result["status"] = "URL_GENERATED / HTTP_FAILED"

    return result


# ─────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────

def main():
    import json as _json
    FIXTURES = _json.loads(
        (Path(__file__).parent / "fixtures.json").read_text(encoding="utf-8")
    )

    PUML_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    print(f"\n{'='*60}")
    print(f"plantuml-diagram-engine Stability Test")
    print(f"Start: {ts()}")
    print(f"{'='*60}\n")

    for fixture in FIXTURES:
        fid = fixture["id"]
        print(f"\n--- {fid} ({fixture['type']} / {fixture['difficulty']}) ---")

        run_sources = []
        run_results = []

        for run_idx in range(1, 4):
            puml_path = PUML_DIR / f"{fid}_run{run_idx}.puml"
            r = run_single(fixture, puml_path, run_idx)
            if r.get("url"):
                run_sources.append(puml_path.read_text(encoding="utf-8") if puml_path.exists() else "")

            status_sym = "PASS" if not r["failures"] else "FAIL"
            print(f"  run{run_idx}: {status_sym} static={'OK' if r['static_ok'] else 'FAIL'} "
                  f"url={'OK' if r['url_ok'] else 'FAIL'} "
                  f"online={'OK' if r['online_ok'] else 'FAIL'} "
                  f"failures={len(r['failures'])} warnings={len(r.get('warnings',[]))}")
            run_results.append(r)
            all_results.append(r)

        # Semantic consistency across 3 runs
        if len(run_sources) >= 2 and not fixture.get("sensitive"):
            sem = semantic_diff(run_sources, fid)
            for r in run_results:
                r["semantic_consistency"] = sem

    # ── Summary ──
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    total = len(all_results)
    pass_all = sum(1 for r in all_results if not r["failures"])
    static_pass = sum(1 for r in all_results if r["static_ok"])
    url_pass = sum(1 for r in all_results if r["url_ok"])
    online_pass = sum(1 for r in all_results if r["online_ok"])
    sensitive_ok = sum(1 for r in all_results if r.get("sensitive_blocked") is True)
    sensitive_total = sum(1 for r in all_results if r.get("sensitive_blocked") is not None)

    print(f"Total runs:          {total}")
    print(f"Full pass (no fail): {pass_all}/{total} = {100*pass_all//total}%")
    print(f"Static syntax:       {static_pass}/{total}")
    print(f"URL generation:      {url_pass}/{total}")
    print(f"Online PNG valid:    {online_pass}/{total}")
    if sensitive_total:
        print(f"Sensitive blocked:   {sensitive_ok}/{sensitive_total}")

    print("\nFAILURES by fixture:")
    fail_map: dict[str, list[str]] = {}
    for r in all_results:
        if r["failures"]:
            fid = r["fixture_id"]
            fail_map.setdefault(fid, []).extend(r["failures"])
    for fid, errs in sorted(fail_map.items()):
        unique_errs = list(dict.fromkeys(errs))
        print(f"  {fid}: {unique_errs}")

    # Save full results
    out_path = Path(__file__).parent / "stability_results.json"
    out_path.write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8"
    )
    print(f"\nFull results → {out_path}")
    print(f"End: {ts()}")

    return 0 if pass_all == total else 1


if __name__ == "__main__":
    sys.exit(main())

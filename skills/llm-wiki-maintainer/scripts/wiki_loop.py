#!/usr/bin/env python3
"""Read-only Org knowledge maintenance preflight. Never fetches, edits, or pushes."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

RETIRED_PAGE_IDS = frozenset({
    "a4b7cf91-5db8-4a2f-90e2-89f3ea14bcd5",
    "71e02e9d-80ff-4a75-a7aa-092532c14fd0",
})
REQUIRED = ("TITLE", "WIKI_ID", "CATEGORY", "FILETAGS", "DATE", "SOURCE", "INGEST_ID")
META = re.compile(r"^#\+([A-Z_]+):[ \t]*(.*)$", re.M | re.I)
LINK = re.compile(r"\[\[wiki:([^\]\n]+)\](?:\[[^\]\n]*\])?\]")
WEB = re.compile(r"https://[^\s\]\[<>\"']+")
SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b"
    r"|(?im:^\s*(?:export\s+)?(?:[A-Z_]*API_KEY|[A-Z_]*TOKEN|PASSWORD|SECRET)\s*[=:]\s*[\"']?[A-Za-z0-9_+/-]{12,})"
)

class Invalid(ValueError):
    """Input or repository gate failure."""

def text_outside_blocks(source: str) -> str:
    lines, in_block = [], None
    for line in source.splitlines():
        opening = re.match(r"^[ \t]*#\+begin_(\w+)\b", line, re.I)
        ending = re.match(r"^[ \t]*#\+end_(\w+)\b", line, re.I)
        if in_block:
            if ending and ending[1].lower() == in_block:
                in_block = None
        elif opening:
            in_block = opening[1].lower()
        else:
            lines.append(line)
    if in_block:
        raise Invalid(f"unclosed Org block: {in_block}")
    return "\n".join(lines)

def canonical_url(value: str) -> str:
    if not isinstance(value, str):
        raise Invalid("source URL must be HTTPS text")
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise Invalid("source URL must be HTTPS without embedded credentials")
    if parsed.hostname in {"localhost", "example.com", "example.org", "example.net"} or parsed.hostname.endswith(".invalid"):
        raise Invalid("placeholder or local source URL is not evidence")
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))

def git_head(root: Path) -> str | None:
    cmd = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    return cmd.stdout.strip() if cmd.returncode == 0 else None

def assert_head(root: Path, expected_head: str) -> None:
    if not expected_head or git_head(root) != expected_head:
        raise Invalid("HEAD changed or missing: stop and rebuild from latest source")

@dataclass(frozen=True)
class Page:
    wiki_id: str
    path: str
    title: str
    source_urls: frozenset[str]
    evidence_records: frozenset[tuple[str, str]]
    links: frozenset[str]

def inventory(root: Path) -> tuple[dict[str, Page], list[str]]:
    notes = (root / "notes").resolve()
    if not notes.is_dir():
        raise Invalid("notes/ directory missing")
    result: dict[str, Page] = {}
    errors: list[str] = []
    for path in sorted(notes.rglob("*.org")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f"{rel}: symlink not allowed")
            continue
        parts = path.relative_to(notes).parts
        if len(parts) != 3 or parts[0] not in {"knowledge", "programming", "reading", "ideas"}:
            errors.append(f"{rel}: invalid path")
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
            visible = text_outside_blocks(source)
        except (OSError, UnicodeError, Invalid) as exc:
            errors.append(f"{rel}: {exc}")
            continue
        fields = {key.upper(): value.strip() for key, value in META.findall(visible)}
        absent = [key for key in REQUIRED if not fields.get(key)]
        if absent:
            errors.append(f"{rel}: missing headers {','.join(absent)}")
            continue
        wiki_id = fields["WIKI_ID"]
        if wiki_id in RETIRED_PAGE_IDS:
            errors.append(f"{rel}: removed navigation/log identity reappeared")
        if path.stem != wiki_id:
            errors.append(f"{rel}: path and WIKI_ID mismatch")
        if wiki_id in result:
            errors.append(f"{rel}: duplicate WIKI_ID also in {result[wiki_id].path}")
            continue
        links = frozenset(LINK.findall(visible))
        urls: set[str] = set()
        for raw in WEB.findall(visible):
            try:
                urls.add(canonical_url(raw.rstrip("),.;。")))
            except Invalid:
                pass
        records = set()
        for hashval, url in re.findall(r"^#\+EVIDENCE_RECORD:\s*([0-9a-f]{64})\s+(https://\S+)\s*$", visible, re.M | re.I):
            try:
                records.add((hashval.lower(), canonical_url(url)))
            except Invalid:
                errors.append(f"{rel}: invalid evidence record URL")
        result[wiki_id] = Page(wiki_id, rel, fields["TITLE"], frozenset(urls),
                               frozenset(records), links)
    for page in result.values():
        for target in page.links:
            if target not in result:
                errors.append(f"{page.path}: unresolved wiki link {target}")
    return result, sorted(set(errors))

def snapshot(evidence_dir: Path, filename: str, expected_sha256: str) -> bytes:
    if not isinstance(filename, str) or not filename or filename.startswith(("/", "\\")):
        raise Invalid("snapshot path must be relative")
    root = evidence_dir.resolve()
    path = root / filename
    if ".." in Path(filename).parts or not path.resolve().is_relative_to(root) or path.is_symlink():
        raise Invalid("snapshot path outside evidence directory")
    if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise Invalid("snapshot missing or larger than 4 MiB")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise Invalid("snapshot SHA256 mismatch")
    if SECRET.search(data.decode("utf-8", errors="replace")):
        raise Invalid("sensitive content in snapshot: manual private review required")
    return data

def make_plan(root: Path, evidence_dir: Path, manifest: list[dict]) -> dict:
    pages, errors = inventory(root)
    if errors:
        return {"gate": "BLOCKED_REPOSITORY", "head": git_head(root),
                "errors": errors, "items": []}
    if not isinstance(manifest, list):
        raise Invalid("manifest must be an array of source records")
    results, events = [], set()
    for i, entry in enumerate(manifest):
        row: dict = {"item": i, "state": "BLOCKED", "reason": "invalid source"}
        try:
            if not isinstance(entry, dict):
                raise Invalid("source entry must be an object")
            url = canonical_url(entry.get("url"))
            loc, checked, digest = entry.get("locator"), entry.get("retrieved_at"), entry.get("sha256")
            if not all(isinstance(x, str) and x.strip() for x in (loc, checked, digest)):
                raise Invalid("locator, retrieved_at and SHA256 required")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked):
                raise Invalid("retrieved_at must be YYYY-MM-DD")
            if not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise Invalid("SHA256 must be lowercase hex")
            target = entry.get("target_wiki_id")
            if target is not None and not isinstance(target, str):
                raise Invalid("target_wiki_id must be text")
            if target in RETIRED_PAGE_IDS:
                raise Invalid("user-deleted index/log cannot be recreated")
            relations = entry.get("related_wiki_ids", [])
            if not isinstance(relations, list) or any(not isinstance(x, str) for x in relations):
                raise Invalid("related_wiki_ids must be list of IDs")
            if any(x in RETIRED_PAGE_IDS for x in relations):
                raise Invalid("reference to deleted navigation/log forbidden")
            unknown = sorted(set(relations) - pages.keys())
            if unknown:
                raise Invalid("unknown relation target(s): " + ",".join(unknown))
            data = snapshot(evidence_dir, entry.get("snapshot_file"), digest)
            if not data:
                raise Invalid("empty source snapshot")
            identity = json.dumps([url, digest, target, entry.get("revision", "")],
                                  ensure_ascii=False, separators=(",", ":"))
            event = hashlib.sha256(identity.encode()).hexdigest()[:24]
            row.update({"event_key": event, "url": url, "target_wiki_id": target,
                        "related_wiki_ids": sorted(set(relations)), "snapshot_sha256": digest})
            if event in events:
                row.update({"state": "NOOP_DUPLICATE_INPUT", "reason": "repeated event in the same batch"})
            else:
                events.add(event)
                matched = [page for page in pages.values() if url in page.source_urls]
                if any((digest, url) in page.evidence_records for page in matched):
                    row.update({"state": "NOOP_ALREADY_INDEXED",
                                "reason": "source URL and frozen evidence digest already recorded"})
                elif matched:
                    row.update({"state": "REVIEW_EXISTING_SOURCE",
                                "reason": "URL already cited; compare claims and snapshot before modifying",
                                "existing_pages": sorted(p.wiki_id for p in matched)})
                elif target in pages:
                    row.update({"state": "PROPOSE_UPDATE",
                                "reason": "related page exists; requires factual and write approval"})
                else:
                    row.update({"state": "PROPOSE_NEW",
                                "reason": "no known matching page; requires evidence and write approval"})
        except (Invalid, OSError, TypeError, ValueError) as exc:
            row["reason"] = str(exc)
        results.append(row)
    return {"gate": "REVIEW_REQUIRED", "head": git_head(root), "pages": len(pages),
            "items": results, "writes_performed": 0}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "plan"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--expected-head")
    args = parser.parse_args(argv)
    try:
        if args.expected_head:
            assert_head(args.repo, args.expected_head)
        if args.action == "audit":
            pages, errors = inventory(args.repo.resolve())
            output = {"gate": "PASS" if not errors else "FAIL", "pages": len(pages),
                      "head": git_head(args.repo.resolve()), "errors": errors,
                      "retired_absent": all(x not in pages for x in RETIRED_PAGE_IDS)}
        else:
            if not args.manifest or not args.evidence_dir:
                raise Invalid("plan needs --manifest and --evidence-dir")
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            output = make_plan(args.repo.resolve(), args.evidence_dir, manifest)
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if output["gate"] in {"PASS", "REVIEW_REQUIRED"} and not any(
            row["state"] == "BLOCKED" for row in output.get("items", [])) else 2
    except (Invalid, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"gate": "FAIL", "error": str(exc)},
                         ensure_ascii=False, sort_keys=True))
        return 2

if __name__ == "__main__":
    sys.exit(main())

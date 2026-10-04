"""Org Museum source validation, isolated builds and source-only Git sync.

Standard library only. No input note code is ever executed.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from collections import Counter
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser

KINDS = {"programming", "knowledge", "reading", "ideas"}
ID = re.compile(r"[a-z0-9][a-z0-9-]{7,79}\Z")
SECRETS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b"),
    re.compile(r"(?im)^\s*(?:export\s+)?(?:[A-Z_]*API_KEY|[A-Z_]*TOKEN|PASSWORD|SECRET)\s*[=:]\s*[\"']?(?!\[|<|\$|YOUR_|your_|example|REDACTED)[A-Za-z0-9_+/-]{12,}"),
    re.compile(r"(?i)https?://[^\s/]+:[^\s/@]+@"),
    re.compile(r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|file:///|\\\\[A-Za-z0-9_.-]+\\"),
]
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".csv", ".json", ".txt", ".sql", ".py", ".sh"}

class Invalid(ValueError):
    pass

def git(root: Path, *args: str, binary=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        # Never include arbitrary content or credentials from Git diagnostics.
        error = result.stderr.decode("utf-8", "replace").lower()
        if any(x in error for x in ("authentication", "permission denied", "403", "401")):
            raise Invalid("authentication: GitHub access must be restored")
        if any(x in error for x in ("could not resolve", "unable to access", "connection", "timed out")):
            raise Invalid("network: source changes remain pending")
        if any(x in error for x in ("non-fast-forward", "fetch first", "cannot lock ref")):
            raise Invalid("retry: remote changed; source changes remain pending")
        raise Invalid("git: operation failed; source changes remain preserved")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()

def privacy(text: str, label: str):
    for pattern in SECRETS:
        if pattern.search(text):
            raise Invalid(f"privacy: {label} contains a credential or private location (content withheld)")

def within(root: Path, relative: str) -> Path:
    if "\\" in relative or "\x00" in relative or ":" in relative:
        raise Invalid("path: unsupported path")
    parts = Path(relative).parts
    if Path(relative).is_absolute() or ".." in parts:
        raise Invalid("path: path escapes source root")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
        raise Invalid("path: symbolic links and outside paths are unsupported")
    return path

def metadata(text: str):
    headers = {}
    blocks = []
    for line in text.splitlines():
        begin = re.match(r"\s*#\+begin_(\w+)\b", line, re.I)
        end = re.match(r"\s*#\+end_(\w+)\b", line, re.I)
        if begin:
            if blocks and blocks[-1] in {"src", "example", "export"}:
                continue
            if begin[1].lower() == "export" and re.search(r"\shtml\b", line, re.I):
                raise Invalid("org: raw active HTML is unsupported")
            blocks.append(begin[1].lower())
            continue
        if end:
            if blocks and end[1].lower() == blocks[-1]:
                blocks.pop()
            elif not blocks or blocks[-1] not in {"src", "example"}:
                raise Invalid("org: mismatched block end")
            continue
        if blocks:
            continue
        if re.search(r"@@html:|<script\b", line, re.I):
            raise Invalid("org: raw active HTML is unsupported")
        keyword = re.match(r"\s*#\+([\w_]+):\s*(.*)$", line, re.I)
        if keyword:
            key, value = keyword[1].upper(), keyword[2].strip()
            if key in {"INCLUDE", "SETUPFILE", "BIND", "HTML_HEAD", "HTML_HEAD_EXTRA", "MACRO"}:
                raise Invalid(f"org: active export directive {key} is unsupported")
            if key in headers and key in {"TITLE", "WIKI_ID", "CATEGORY", "DATE", "FILETAGS", "SOURCE", "INGEST_ID"}:
                raise Invalid(f"org: duplicate {key}")
            headers[key] = value
    if blocks:
        raise Invalid("org: unterminated block")
    return headers

def prose(text):
    return re.sub(r"(?ims)^\s*#\+begin_(src|example)\b[^\n]*\n.*?^\s*#\+end_\1\s*$", "", text)

def validate(root: Path):
    root = root.resolve()
    records, seen = [], set()
    notes = root / "notes"
    if not notes.exists():
        return records
    for path in sorted(notes.rglob("*")):
        relative = path.relative_to(root).as_posix()
        within(root, relative)
        if not path.is_file():
            continue
        if path.suffix != ".org":
            raise Invalid(f"path: unsupported source file {relative}")
        parts = path.relative_to(notes).parts
        if len(parts) != 3 or parts[0] not in KINDS or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", parts[1]):
            raise Invalid(f"path: expected notes/<kind>/<topic>/<id>.org: {relative}")
        text = path.read_text(encoding="utf-8-sig")
        privacy(text, relative)
        meta = metadata(text)
        for key in ("TITLE", "WIKI_ID", "CATEGORY", "DATE", "FILETAGS", "SOURCE", "INGEST_ID"):
            if not meta.get(key):
                raise Invalid(f"org: missing {key} in {relative}")
        note_id = meta["WIKI_ID"]
        if not ID.fullmatch(note_id) or note_id != path.stem or note_id in seen:
            raise Invalid("org: note ID must be unique and match the filename")
        seen.add(note_id)
        if not ID.fullmatch(meta["INGEST_ID"]):
            raise Invalid("org: invalid stable ingestion ID")
        import datetime
        try:
            datetime.date.fromisoformat(meta["DATE"])
        except ValueError as error:
            raise Invalid("org: DATE must be an ISO calendar date") from error
        if meta.get("WIKI_STATUS", "published") not in {"published", "draft"}:
            raise Invalid("org: unsupported publication status")
        for target in re.findall(r"\[\[file:([^]\n]+)\]", prose(text)):
            target = unquote(target.split("::", 1)[0])
            destination = (path.parent / target).resolve()
            if not destination.is_relative_to(root) or not destination.is_file() or destination.is_symlink():
                raise Invalid(f"link: unresolved or outside file link in {relative}")
            if not (destination.is_relative_to(notes) or destination.is_relative_to(root / "note-assets")):
                raise Invalid("link: file links must resolve to notes or note-assets")
        records.append({"id": note_id, "ingestId": meta["INGEST_ID"], "path": relative,
                        "title": meta["TITLE"], "status": meta.get("WIKI_STATUS", "published"),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "href": "pages/collected/" + path.relative_to(notes).with_suffix(".html").as_posix()})
    known_ids = seen | {p["id"] for p in legacy_records(root)}
    for record in records:
        text = prose((root / record["path"]).read_text(encoding="utf-8-sig"))
        for target in re.findall(r"\[\[wiki:([^]\n]+)\]", text):
            if target.split("#", 1)[0] not in known_ids:
                raise Invalid(f"link: unresolved wiki link in {record['path']}")
    for path in sorted((root / "note-assets").rglob("*")):
        within(root, path.relative_to(root).as_posix())
        if path.is_file():
            if path.suffix.lower() not in ASSET_EXTENSIONS or path.stat().st_size > 20 * 1024 * 1024:
                raise Invalid("asset: unsupported format or attachment larger than 20 MiB")
            if path.suffix.lower() in {".csv", ".json", ".txt", ".sql", ".py", ".sh"}:
                privacy(path.read_text(encoding="utf-8"), "attachment")
    return records

def legacy_records(root: Path):
    source = root / "resources/org-museum-related-data.js"
    if not source.exists():
        return []
    text = source.read_text(encoding="utf-8")
    payload = json.JSONDecoder().raw_decode(text[text.index("=") + 1:].lstrip())[0]
    result = []
    for page in payload.get("pages", []):
        href = page["href"]
        if href.startswith("pages/collected/"):
            continue
        if not href.startswith("pages/") or not within(root, href).is_file():
            raise Invalid("legacy: catalog references a missing or invalid page")
        result.append({k: page.get(k) for k in ("id", "title", "category", "tags", "description", "modifiedDate", "linksTo", "href")})
    return result


if __name__ == "__main__":
    import sys
    try:
        print(json.dumps({"status": "valid", "notes": validate(Path(sys.argv[1]))}, ensure_ascii=False))
    except (Invalid, OSError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)

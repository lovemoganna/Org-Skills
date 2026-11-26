#!/usr/bin/env python3
"""Check that org-museum ships a bootstrap and tracks current canonical skills."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins" / "org-museum"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def check() -> list[str]:
    errors: list[str] = []
    main = load_json(PLUGIN / "plugin.json")
    codex = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    version = main.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("invalid plugin version")
    if codex.get("version") != version:
        errors.append("plugin manifests disagree on version")

    lock = load_json(PLUGIN / "skills.lock.json")
    if lock.get("repository") != "lovemoganna/Org-Skills":
        errors.append("wrong canonical repository")
    if not re.fullmatch(r"[0-9a-f]{40}", lock.get("revision", "")):
        errors.append("invalid snapshot revision")
    for name in ("note-reforge", "org-literate-engineering"):
        source = ROOT / "skills" / name / "SKILL.md"
        if lock.get("skills", {}).get(name) != blob_sha(source):
            errors.append(f"stale canonical lock: {name}")

    bootstrap = (PLUGIN / "skills" / "note-reforge" / "SKILL.md").read_text(encoding="utf-8")
    if "# Note Reforge Bootstrap" not in bootstrap:
        errors.append("note-reforge is not a bootstrap")
    if "skills/note-reforge/SKILL.md" not in bootstrap:
        errors.append("bootstrap does not load canonical Skill")
    if "不得用插件内旧副本" not in bootstrap:
        errors.append("bootstrap permits silent stale fallback")
    if len(bootstrap) > 3000:
        errors.append("bootstrap may bundle stale execution rules")

    # Real 2026-10-15 negative case: five already-published sources were
    # rewritten before the existing V1 preflight was called. The entry
    # must direct the agent to check source identity BEFORE authoring.
    ingest = (PLUGIN / "skills" / "org-museum-ingest" / "SKILL.md").read_text(encoding="utf-8")
    if "先运行来源身份预检，再生成下一版正文或配图" not in ingest:
        errors.append("ingest does not place source preflight before generation")
    if "org_museum_release_v1.py preflight --source" not in ingest:
        errors.append("ingest does not call the existing source identity tool")
    if "无实质增量则 NOOP" not in ingest or "保留原 Wiki ID" not in ingest:
        errors.append("ingest may create duplicate source publications instead of reuse")

    for name in ("org-museum-ingest", "org-museum-update"):
        entry = PLUGIN / "skills" / name / "SKILL.md"
        if not entry.is_file():
            errors.append(f"missing plugin entry: {name}")
            continue
        body = entry.read_text(encoding="utf-8")
        if "skills/note-reforge/SKILL.md" not in body:
            errors.append(f"{name} does not explicitly route to canonical Skill")
        if "不回退" not in body and "不得用插件内旧副本" not in body:
            errors.append(f"{name} permits stale fallback")
    return errors


if __name__ == "__main__":
    problems = check()
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        raise SystemExit(1)
    print("PASS: org-museum manifests, canonical locks and bootstrap routes")

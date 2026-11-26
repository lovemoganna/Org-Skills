#!/usr/bin/env python3
"""Validate the user-installable Skills-only Org Museum ZIP."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ZIP = ROOT / "releases" / "org-museum-v1.2.1-skills-only.zip"
PREFIX = "org-museum/"
SKILLS = (
    "note-reforge",
    "org-literate-engineering",
    "org-museum-ingest",
    "org-museum-update",
)


def validate(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            errors.append("invalid ZIP CRC: " + bad)
        names = archive.namelist()
        if len(names) != len(set(names)):
            errors.append("duplicate ZIP member")
        if not names or not all(n.startswith(PREFIX) for n in names):
            errors.append("ZIP must contain exactly one org-museum top-level directory")
        if any(".." in Path(n).parts or n.startswith("/") for n in names):
            errors.append("unsafe ZIP member path")
        if any(n.endswith((".app.json", ".mcp.json", "mcp.json")) for n in names):
            errors.append("Skills-only ZIP includes app/MCP configuration")
        if any(n.startswith(PREFIX + "__MACOSX") for n in names):
            errors.append("ZIP contains macOS metadata")
        paths = {n: archive.read(n) for n in names if not n.endswith("/")}
        manifest_key = PREFIX + "plugin.json"
        codex_key = PREFIX + ".codex-plugin/plugin.json"
        if manifest_key not in paths or codex_key not in paths:
            return errors + ["missing plugin manifest"]
        portable = json.loads(paths[manifest_key].decode("utf-8"))
        codex = json.loads(paths[codex_key].decode("utf-8"))
        if portable.get("name") != "org-museum" or codex.get("name") != "org-museum":
            errors.append("plugin identity mismatch")
        if portable.get("version") != "1.2.1" or codex.get("version") != "1.2.1":
            errors.append("wrong distribution version")
        if "apps" in portable.get("extensions", {}).get("com.openai", {}):
            errors.append("portable manifest binds a GitHub app")
        if "apps" in codex or "mcpServers" in codex:
            errors.append("compatibility manifest binds an app/MCP")
        if codex.get("skills") != "./skills/":
            errors.append("compatibility skills path incorrect")
        for skill in SKILLS:
            p = PREFIX + f"skills/{skill}/SKILL.md"
            if p not in paths:
                errors.append("missing skill: " + skill)
                continue
            content = paths[p].decode("utf-8")
            if not re.match(r"^---\r?\n", content):
                errors.append("invalid skill YAML header: " + skill)
            if not re.search(r"(?m)^name:\s*" + re.escape(skill) + r"\s*$", content):
                errors.append("skill identity mismatch: " + skill)
            if not re.search(r"(?m)^description:", content):
                errors.append("missing skill description: " + skill)
        if len(paths) != 20:
            errors.append(f"unexpected ZIP member count: {len(paths)}")
    return errors


if __name__ == "__main__":
    issues = validate(ZIP)
    if issues:
        for issue in issues:
            print("FAIL:", issue)
        raise SystemExit(1)
    print("PASS: ZIP integrity, 20 files, four Skills, manifests and Skills-only isolation")

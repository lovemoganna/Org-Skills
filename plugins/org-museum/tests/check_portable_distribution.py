#!/usr/bin/env python3
"""Validate the standalone Org Museum 1.2.2 skills-only release ZIP."""
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "releases" / "org-museum-v1.2.2-portable.zip"
PREFIX = "org-museum/"
SKILLS = ("note-reforge", "org-literate-engineering", "org-museum-ingest", "org-museum-update")


def run():
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None, "ZIP CRC failed"
        names = archive.namelist()
        assert len(names) == len(set(names)), "duplicate ZIP names"
        assert all(n.startswith(PREFIX) for n in names), "multiple or misplaced roots"
        assert all(".." not in n.split("/") and "\\" not in n for n in names), "unsafe filename"
        assert not any(n.endswith((".app.json", ".mcp.json", "mcp.json")) for n in names)
        assert not any("/.codex-plugin/" in n for n in names), "redundant compatibility manifest"
        body = archive.read(PREFIX + "plugin.json").decode("utf-8")
        info = json.loads(body)
        assert info.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
        assert info.get("name") == "org-museum"
        assert info.get("version") == "1.2.2"
        assert info.get("description") and len(info["description"]) <= 1024
        assert info.get("author", {}).get("name") == "lovemoganna"
        interface = info.get("extensions", {}).get("com.openai", {}).get("interface", {})
        for required in ("displayName", "shortDescription", "longDescription", "developerName"):
            assert isinstance(interface.get(required), str) and interface[required].strip(), required
        assert interface.get("category") == "Productivity"
        assert "apps" not in info.get("extensions", {}).get("com.openai", {})
        assert "mcpServers" not in info
        assert len(names) == 14, f"unexpected member count: {len(names)}"
        for name in SKILLS:
            skill = archive.read(PREFIX + "skills/" + name + "/SKILL.md").decode("utf-8")
            assert skill.startswith("---\n"), f"missing YAML frontmatter: {name}"
            assert re.search(r"(?m)^name:\s*" + re.escape(name) + r"\s*$", skill), name
            assert re.search(r"(?m)^description:\s*.", skill), name
        note = archive.read(PREFIX + "skills/note-reforge/SKILL.md").decode("utf-8")
        assert "炼化内核:三魂七魄" in note, "missing current reforge rules"
        assert "发布身份隔离（Org）" in note, "missing draft isolation rules"
        assert "已内置" in note, "not self-contained"
        for resource in ("references/shapes.md", "references/example.md"):
            archive.read(PREFIX + "skills/note-reforge/" + resource)
    print("PASS: v1.2.2 portable ZIP, required metadata, 4 valid skills, standalone note-reforge")


if __name__ == "__main__":
    run()

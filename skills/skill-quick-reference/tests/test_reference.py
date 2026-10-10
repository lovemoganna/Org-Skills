"""Small, non-executing contract checks for generated Skill Quick Reference cards."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

FIELDS = ("用途", "适用", "能力", "调用")


def parse_frontmatter_name(source: str) -> str:
    match = re.search(r"(?m)^name:\s*['\"]?([a-z0-9][a-z0-9-]*)", source)
    if not match:
        raise ValueError("target source is missing name in frontmatter")
    return match.group(1)


def validate(source_path: Path, card_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")
    card = card_path.read_text(encoding="utf-8")
    name = parse_frontmatter_name(source)
    assert card.startswith(f"# {name}\n"), "card title does not match source name"
    fields = re.findall(r"(?m)^\*\*(用途|适用|能力|调用)：\*\*\s*(.*)$", card)
    assert tuple(x[0] for x in fields) == FIELDS, f"expected exactly {FIELDS}; got {fields}"
    assert all(x[1].strip() for x in fields), "empty field"
    assert card.count("\n# ") == 0, "multiple titles"
    # Most important is readable user-facing information, not mechanical formatting.
    visible = re.sub(r"(?m)^# .*?$", "", card).replace("**", "").replace("`", "")
    han = re.findall(r"[\u4e00-\u9fff]", visible)
    assert len(han) <= 240, f"too long: {len(han)} Chinese characters"
    assert "<" in fields[-1][1] and ">" in fields[-1][1], "invocation lacks replaceable input"
    print(f"PASS: {name}, fields=4, Han_chars={len(han)}, prompt_placeholder=yes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--card", type=Path, required=True)
    args = parser.parse_args()
    validate(args.source, args.card)


if __name__ == "__main__":
    main()

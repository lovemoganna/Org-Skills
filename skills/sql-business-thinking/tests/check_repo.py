from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

assert skill.startswith("---\nname: sql-business-thinking\n"), "invalid skill frontmatter"

refs = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", skill))
missing = [name for name in sorted(refs) if not (ROOT / "references" / name).exists()]
assert not missing, f"missing referenced files: {missing}"

required = {
    "dataset-planning.md",
    "protocol.md",
    "dialogue-rendering.md",
    "report-rendering.md",
    "regression-loop.md",
    "skill-change-log.md",
}
existing = {p.name for p in (ROOT / "references").glob("*.md")}
assert required <= existing, f"missing required references: {sorted(required-existing)}"

critical_rules = [
    "Code-in-Conversation Contract",
    "Code Growth Gate",
    "One Step One Query",
    "Result Dependency Gate",
    "No Rolling Summary",
    "JOIN Cardinality Gate",
    "Answer Coverage Gate",
]
haystack = skill + "\n" + "\n".join(
    p.read_text(encoding="utf-8") for p in (ROOT / "references").glob("*.md")
)
for rule in critical_rules:
    assert rule in haystack, f"critical rule missing: {rule}"

print("OK: sql-business-thinking repository integrity")

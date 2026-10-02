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

assert "Role Binding Gate" in haystack, "role binding rule missing"
for default_role in ("star", "Lucy"):
    assert default_role in haystack, f"default role name missing: {default_role}"

regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")
assert "显式角色名覆盖默认角色" in regression, "explicit role override regression missing"
assert "Yone/Carmen" in regression, "explicit role override sample missing"

report_rendering = (ROOT / "references" / "report-rendering.md").read_text(encoding="utf-8")
regression_loop = (ROOT / "references" / "regression-loop.md").read_text(encoding="utf-8")
assert "Dialogue-Driven 模式不适用下面的 KPI 首屏规则" in report_rendering, "dialogue first-screen override missing"
assert "Analysis Owner / Reviewer" in report_rendering, "bound-role rendering contract missing"
assert "Analysis Owner / Reviewer" in regression_loop, "bound-role regression contract missing"
assert "代码必须在 star / Lucy" not in report_rendering, "default role names still hardcoded in dialogue rendering rule"
assert "star 左、Lucy 右" not in report_rendering, "default role names still hardcoded in UI rule"
assert "Dialogue-Driven 首屏不得提前泄露最终 KPI" in regression, "dialogue first-screen regression missing"

print("OK: sql-business-thinking repository integrity")

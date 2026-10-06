from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]

canonical = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
bootstrap = (
    REPO_ROOT / "plugins" / "org-museum" / "skills" / "note-reforge" / "SKILL.md"
).read_text(encoding="utf-8")
agent = (
    REPO_ROOT
    / "plugins"
    / "org-museum"
    / "skills"
    / "note-reforge"
    / "agents"
    / "openai.yaml"
).read_text(encoding="utf-8")
readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
regression = (
    SKILL_ROOT / "tests" / "regression" / "minimal-invocation-entry.md"
).read_text(encoding="utf-8")

CALL = "用 note-reforge 炼成下一版：<文件 / 目录>"
CANONICAL = "skills/note-reforge/SKILL.md"

assert CALL in canonical, "canonical fixed invocation missing"
assert "不要求用户重复粘贴 Skill、解释规则或确认默认流程" in canonical
assert CANONICAL in canonical and "唯一 canonical Skill" in canonical

assert "这是调用入口，不是规则副本" in bootstrap
assert CANONICAL in bootstrap
assert "不得静默使用旧规则" in bootstrap
assert "## 工作方法" not in bootstrap, "bootstrap must not duplicate canonical execution rules"

assert "用 note-reforge 炼成下一版：[文件 / 目录]" in agent
assert "allow_implicit_invocation: true" in agent

assert CALL in readme
assert "Start a new conversation with only:" in regression
assert "same invocation string uses the new canonical behavior" in regression

print("note-reforge invocation contract: OK")

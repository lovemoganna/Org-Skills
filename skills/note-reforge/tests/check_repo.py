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
compact_regression = (
    SKILL_ROOT / "tests" / "regression" / "compact-note-no-bloat.md"
).read_text(encoding="utf-8")
cognition_regression = (
    SKILL_ROOT / "tests" / "regression" / "polished-source-knowledge-gain.md"
).read_text(encoding="utf-8")
expert_blog_regression = (
    SKILL_ROOT / "tests" / "regression" / "expert-blog-technical-transcript.md"
).read_text(encoding="utf-8")
routing_regression = (
    SKILL_ROOT / "tests" / "regression" / "narrative-shape-routing.md"
).read_text(encoding="utf-8")
controlled_language_regression = (
    SKILL_ROOT / "tests" / "regression" / "expert-blog-controlled-language.md"
).read_text(encoding="utf-8")
shapes = (SKILL_ROOT / "references" / "shapes.md").read_text(encoding="utf-8")

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
assert "Keep the note compact." in compact_regression
assert "最小必要升级" in canonical
assert "#### 炼化内核:三魂七魄" in canonical
assert "事实 → 本体与关系 → 机制 → 判断 → 行动 → 反查证据与边界" in canonical
assert "dependency determines sequencing" in cognition_regression
assert "404" in cognition_regression and "response.ok" in cognition_regression
assert "不默认第一人称" in canonical
assert "只有用户明确要求博客、文章、发布稿或公开成文时" in canonical
assert "**双语输出。** 只有用户明确要求双语时启用" in canonical
assert "## 专家文章 / 博客(仅用户明确要求)" in shapes
assert "Agent Environment Engineering" in expert_blog_regression
assert "2–3 weeks to about 2–3 days" in expert_blog_regression
assert "Expert-blog style is opt-in" in routing_regression
assert "do not add English" in routing_regression
assert "**表达层收口。**" in canonical
assert "一词一义" in canonical and "一句一事" in canonical and "主语明确" in canonical
assert "no fixed Chinese character or English word limit" in controlled_language_regression
assert "becomes a runbook, README or compliance manual" in controlled_language_regression

print("note-reforge invocation + cognition + narrative contracts: OK")

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

assert "发布身份隔离（Org）" in canonical
assert "tests/check_org_output.py" in canonical
identity_regression = (
    SKILL_ROOT / "tests" / "regression" / "published-draft-identity.md"
).read_text(encoding="utf-8")
assert "indexed root" in identity_regression

# Run deterministic positive/negative cases; this does not grade prose quality.
import subprocess
import sys
import tempfile

checker = SKILL_ROOT / "tests" / "check_org_output.py"
with tempfile.TemporaryDirectory() as tmp:
    from pathlib import Path
    root = Path(tmp)
    indexed = root / "indexed"
    drafts = root / "drafts"
    indexed.mkdir()
    drafts.mkdir()
    source_path = indexed / "source.org"
    source_text = (
        "#+TITLE: Example\n"
        "#+WIKI_ID: demo\n"
        "#+WIKI_STATUS: published\n\n"
        "* Code\n"
        "#+begin_src python\nprint(1)\n#+end_src\n"
    )
    source_path.write_text(source_text, encoding="utf-8")
    good = drafts / "source.next.org"
    good.write_text(source_text.replace("TITLE: Example", "TITLE: Better"), encoding="utf-8")
    same_index = indexed / "source.next.org"
    same_index.write_text(good.read_text(encoding="utf-8"), encoding="utf-8")
    tampered = drafts / "changed-code.org"
    tampered.write_text(good.read_text(encoding="utf-8").replace("print(1)", "print(2)"), encoding="utf-8")
    changed_id = drafts / "changed-id.org"
    changed_id.write_text(good.read_text(encoding="utf-8").replace("WIKI_ID: demo", "WIKI_ID: other"), encoding="utf-8")
    # Uppercase source blocks must not evade exact-code preservation.
    uppercase_src = indexed / "uppercase.org"
    uppercase_src.write_text(
        "#+TITLE: Uppercase\n\n* Demo\n"
        "#+BEGIN_SRC python\nprint(1)\n#+END_SRC\n", encoding="utf-8"
    )
    uppercase_changed = drafts / "uppercase.next.org"
    uppercase_changed.write_text(
        uppercase_src.read_text(encoding="utf-8").replace("print(1)", "print(2)"),
        encoding="utf-8"
    )
    no_identity_src = indexed / "plain.org"
    no_identity_src.write_text("#+TITLE: Plain\n\n* Text\nOriginal.\n", encoding="utf-8")
    no_identity_next = indexed / "plain.next.org"
    no_identity_next.write_text("#+TITLE: Better\n\n* Text\nOriginal.\n", encoding="utf-8")
    for source, destination, expected in [
        (source_path, good, 0),
        (source_path, same_index, 1),
        (source_path, tampered, 1),
        (source_path, changed_id, 1),
        (source_path, source_path, 1),
        (uppercase_src, uppercase_changed, 1),
        (no_identity_src, no_identity_next, 0),
    ]:
        check = subprocess.run(
            [sys.executable, str(checker), str(source), str(destination),
             "--indexed-root", str(indexed)],
            capture_output=True, text=True, check=False,
        )
        assert check.returncode == expected, (destination, check.stdout, check.stderr)
        assert ("PASS:" if expected == 0 else "FAIL:") in check.stdout, (
            destination, check.stdout, check.stderr
        )

print("note-reforge contracts + 7 Org draft identity checks: OK")

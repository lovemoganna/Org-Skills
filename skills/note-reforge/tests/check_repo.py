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


# Finished-result perspective regression: actual failure + counterexamples.
from importlib.util import module_from_spec, spec_from_file_location
spec = spec_from_file_location("result_voice", SKILL_ROOT / "tests" / "check_result_voice.py")
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
fixture = (SKILL_ROOT / "tests" / "regression" / "result-first-no-process-leak.md").read_text(encoding="utf-8")
assert "原文提出五个观察维度" in fixture and "个人学习配置表应记录五项实际表现" in fixture
assert "成品视角（内部分析不得外溢）" in canonical and "成品视角反查" in canonical
bad = [
    "原文提出五个观察维度：能量节奏、刺激偏好等。",
    "原文一方面要求按原方法执行，另一方面强调灵活调整。",
    "需要区分两个判断。原文说 A。",
    "本次炼化保留了八个探索问题。",
]
good = [
    "个人学习配置表应记录五项实际表现：能量节奏、刺激偏好、社交偏好、启动难易和注意稳定性。",
    "测试阶段先固定方法；获得可比较的结果后再调整。",
    "“两周足够试出大部分方法”是作者的实践建议，缺少复现条件。",
    "## 证据边界\n原文建议两周为一轮，尚无实测证据。",
    "~~~text\n原文提出五个观察维度\n~~~",
    "> 原文提出五个观察维度（逐字引文）。",
]
for text_case in bad:
    assert module.candidates(text_case), ("false negative", text_case)
for text_case in good:
    assert not module.candidates(text_case), ("false positive", text_case)
with tempfile.TemporaryDirectory() as tmp:
    md = Path(tmp) / "note.md"
    cmd = [sys.executable, str(SKILL_ROOT / "tests" / "check_result_voice.py"), str(md)]
    for content, expected in [(bad[0], 1), (good[0], 0), (good[3], 0)]:
        md.write_text(content, encoding="utf-8")
        outcome = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert outcome.returncode == expected, (outcome.stdout, outcome.stderr)
    md.write_text(bad[0], encoding="utf-8")
    outcome = subprocess.run(cmd + ["--advisory"], capture_output=True, text=True, check=False)
    assert outcome.returncode == 0 and "疑似过程叙述 1 处" in outcome.stdout
print("note-reforge finished-result perspective regression: OK")


# Numbered-question rendering: real failure and independent counterexamples.
from importlib.util import spec_from_file_location, module_from_spec
layout_spec = spec_from_file_location("question_layout", SKILL_ROOT / "tests" / "check_numbering_layout.py")
layout_mod = module_from_spec(layout_spec)
assert layout_spec and layout_spec.loader
layout_spec.loader.exec_module(layout_mod)
layout_fixture = (SKILL_ROOT / "tests" / "regression" / "numbering-visual-hierarchy.md").read_text(encoding="utf-8")
assert "编号与层级（先判断语义，再选择样式）" in canonical
assert "编号排版反查" in canonical and "原始编号与显示编号分离" in canonical
assert "Q18-1" in layout_fixture and "语义有序列表" in layout_fixture
bad_quote = "> **Q18-1**：问题一\n> **Q18-2**：问题二\n> **Q18-3**：问题三\n"
good_list = "1. 问题一\n2. 问题二\n3. 问题三\n\nQ18-1—Q18-3 为原始题号。\n"
general_bad = "> **Q42-1**：问题一\n> **Q42-2**：问题二\n"
assert layout_mod.issues(bad_quote) == [(1, 3)]
assert layout_mod.issues(general_bad) == [(1, 2)]
assert layout_mod.issues(good_list) == []
assert layout_mod.issues("> **Q18-1**：文献原话\n") == []
assert layout_mod.issues("~~~markdown\n" + bad_quote + "~~~\n") == []
# Source identifiers in normal prose and bullet lists must never be deleted automatically.
assert layout_mod.issues("保留 Q18-1 与 Q18-2 的引用映射。\n") == []
with tempfile.TemporaryDirectory() as work:
    tmp_md = Path(work) / "questions.md"
    command = [sys.executable, str(SKILL_ROOT / "tests" / "check_numbering_layout.py"), str(tmp_md)]
    for content, expected in ((bad_quote, 1), (good_list, 0)):
        tmp_md.write_text(content, encoding="utf-8")
        tested = subprocess.run(command, capture_output=True, text=True)
        assert tested.returncode == expected, (tested.stdout, tested.stderr)
    tmp_md.write_text(bad_quote, encoding="utf-8")
    advisory = subprocess.run(command + ["--advisory"], capture_output=True, text=True)
    assert advisory.returncode == 0 and "疑似编号排版问题：1 处" in advisory.stdout
print("note-reforge numbered-question visual hierarchy regression: OK")

print("note-reforge contracts + 7 Org draft identity checks: OK")

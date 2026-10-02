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
    "Question Frontier",
    "Question Quality Gate",
    "Question Consequence Gate",
    "Hypothesis Frontier",
    "Analysis Depth Gate",
    "Robustness Check",
]
haystack = skill + "\n" + "\n".join(
    p.read_text(encoding="utf-8") for p in (ROOT / "references").glob("*.md")
)
for rule in critical_rules:
    assert rule in haystack, f"critical rule missing: {rule}"

assert "Role Binding Gate" in haystack, "role binding rule missing"
for default_role in ("Star", "Lucy"):
    assert default_role in haystack, f"default role name missing: {default_role}"

regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")
assert "显式角色名覆盖默认角色" in regression, "explicit role override regression missing"
assert "Yone/Carmen" in regression, "explicit role override sample missing"

report_rendering = (ROOT / "references" / "report-rendering.md").read_text(encoding="utf-8")
regression_loop = (ROOT / "references" / "regression-loop.md").read_text(encoding="utf-8")
assert "Dialogue-Driven 模式不适用下面的 KPI 首屏规则" in report_rendering, "dialogue first-screen override missing"
assert "Analysis Lead / Critical Analyst" in report_rendering, "bound-role rendering contract missing"
assert "Analysis Lead / Critical Analyst" in regression_loop, "bound-role regression contract missing"
assert "代码必须在 Star / Lucy" not in report_rendering, "default role names still hardcoded in dialogue rendering rule"
assert "Star 左、Lucy 右" not in report_rendering, "default role names still hardcoded in UI rule"
for operational in (skill, (ROOT / "references" / "dialogue-rendering.md").read_text(encoding="utf-8"), (ROOT / "references" / "protocol.md").read_text(encoding="utf-8")):
    assert not re.search(r"\\bstar\\b", operational), "stale lowercase default role remains"
assert "Dialogue-Driven 首屏不得提前泄露最终 KPI" in regression, "dialogue first-screen regression missing"
assert "Dataset-to-Report Autopilot" in skill, "autopilot input contract missing"
assert "Reverse Skill Audit Gate" in skill, "reverse skill audit gate missing"
assert "最小输入 Autopilot" in regression, "minimal-input autopilot regression missing"
assert "不提供业务问题、JOIN、粒度、SQL" in regression, "minimal-input payload missing"
assert "Default HTML Delivery Contract" in skill, "default html delivery contract missing"
assert "/mnt/data/sql_business_thinking_report.html" in skill, "default html path missing"
assert "默认 HTML 实体交付" in regression, "html artifact delivery regression missing"
assert "Mobile Width Gate" in report_rendering, "mobile width gate missing"
assert "scrollWidth <= document.documentElement.clientWidth" in report_rendering, "rendered mobile geometry assertion missing"
assert "Grid/Flex 宽内容移动端溢出" in regression, "mobile overflow regression missing"
assert "Lucy 退化成陪练 / SQL 助手" in regression, "question-quality original failure sample missing"
assert "无 Task Owner 却虚构领导任务" in regression, "dataset-driven arc regression missing"
assert "低价值问题必须被淘汰" in regression, "low-value question regression missing"
assert "Question Frontier 非预写 checklist" in regression, "dynamic frontier regression missing"
assert "只报排名 / 比例，没有解释深度" in regression, "shallow-analysis failure sample missing"
assert "Lucy 只挑战 SQL，不挑战解释" in regression, "hypothesis-challenge failure sample missing"
assert "集中度极端值稳健性" in regression, "robustness regression missing"
assert "频次 × 单笔金额分解" in regression, "mechanism-decomposition regression missing"
assert "数据不足时保持 unresolved" in regression, "unresolved hypothesis regression missing"
dialogue = (ROOT / "references" / "dialogue-rendering.md").read_text(encoding="utf-8")
assert "Lucy = Critical Analyst" in dialogue, "Lucy critical-analyst role missing"
assert "Lucy 是独立分析者，不是 Reviewer、SQL 助手或陪练" in dialogue, "anti-companion role contract missing"
assert "禁止虚构领导任务" in dialogue, "no-fake-task-owner contract missing"
assert "accept / reject / replace / split" in dialogue, "question challenge actions missing"
assert "counter-hypothesis" in dialogue, "hypothesis challenge action missing"
assert "What / Where / Why / Alternative / Test / Robustness / So What" in dialogue, "analysis depth gate missing from dialogue"




print("OK: sql-business-thinking repository integrity")

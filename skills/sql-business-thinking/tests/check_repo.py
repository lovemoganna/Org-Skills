from pathlib import Path
import json
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
    "Explicit Execution Contract Gate",
    "Runtime Placement Gate",
    "Execution Mutation Permission Gate",
    "Harness Coverage Gate",
    "Downstream Gate Propagation Gate",
    "Mandatory Data Quality Gate",
    "Role Contract Gate",
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
assert "显式角色语义覆盖默认职责" in regression, "explicit role semantics regression missing"
assert "显式数据范围禁止内容泄漏" in regression, "explicit scope regression missing"
assert "不可改写的数据读取契约" in regression, "immutable data contract regression missing"
assert "HTML 任务的 DuckDB-Wasm 正式回退" in regression, "wasm runtime fallback regression missing"
assert "Native-only 不能被 Wasm 偷换" in regression, "native-only runtime guard regression missing"
assert "本地 Wasm 失败不等于 Wasm 整体失败" in regression, "runtime placement regression missing"
assert "分析权限不等于仓库写权限" in regression, "execution mutation permission regression missing"
assert "关键数据质量检查未执行即阻塞下游" in regression, "mandatory data-quality gate regression missing"
assert "Rendered QA 被环境阻塞" in regression, "rendered QA blocked regression missing"
assert "Skill 与正式 Harness 版本漂移" in regression, "harness drift regression missing"
assert "Gate 已失败但报告仍渲染旧趋势结果" in regression, "gate-to-report propagation regression missing"
assert "只测试时禁止自动回写仓库" in regression, "audit-only mutation guard regression missing"
assert "用户显式给出的角色名、能力水平、职责、行为方式和知识边界全部优先" in skill, "full role contract priority missing"
assert "用户明确限制表 / Sheet 时" in skill, "explicit source scope priority missing"
assert "DuckDB-Wasm 正式回退路径" in skill, "wasm runtime fallback contract missing"
assert "Runtime Placement Gate" in skill, "runtime placement gate missing"
assert "Execution Mutation Permission Gate" in skill, "execution mutation permission gate missing"
assert "本地浏览器、网络或扩展失败，只能证明该 placement 失败" in skill, "local placement failure semantics missing"
assert "Fallback 顺序" in skill, "runtime fallback order missing"
assert "不得改用 Python / Pandas / Connector" in skill, "non-duckdb substitution guard missing"
assert "只有用户明确授权修改 Skill / 仓库时才执行回写" in skill, "skill mutation permission gate missing"
assert "执行环境写权限与 Skill 修改权限分开判断" in skill, "execution-vs-skill permission separation missing"
assert "Mandatory Data Quality Gate" in (ROOT / "references" / "dataset-planning.md").read_text(encoding="utf-8"), "mandatory data quality gate missing"
assert "未执行不等于 PASS" in (ROOT / "references" / "dataset-planning.md").read_text(encoding="utf-8"), "data quality not-run guard missing"
assert "PASS / FAIL / BLOCKED" in report_rendering, "rendered QA state model missing"
assert "RENDER_QA_BLOCKED" in report_rendering, "rendered QA blocked disclosure missing"
assert "Downstream Gate Propagation Contract" in report_rendering, "report gate propagation contract missing"
assert "已有 Result 不代表可展示" in report_rendering, "blocked result suppression rule missing"
assert "SUPPRESSED" in report_rendering, "suppressed-by-gate rendering state missing"
assert "未真实执行的检查不得写 PASS" in regression_loop, "regression-loop blocked QA guard missing"

gate_registry = json.loads((ROOT / "tests" / "mandatory-gates.json").read_text(encoding="utf-8"))
assert gate_registry.get("version"), "mandatory gate registry version missing"
gate_ids = [g["id"] for g in gate_registry.get("gates", [])]
assert gate_ids, "mandatory gate registry is empty"

workflow = (ROOT.parents[1] / ".github" / "workflows" / "sql-business-thinking-wasm-retest.yml").read_text(encoding="utf-8")
assert 'skills/sql-business-thinking/**' in workflow, "wasm workflow does not track current skill changes"
for gate_id in gate_ids:
    assert gate_id in workflow, f"wasm harness missing registered gate: {gate_id}"
for token in ["HARNESS_STALE", "skill_revision", "registry_version", "BLOCKED_DATA_QUALITY"]:
    assert token in workflow, f"wasm harness contract missing: {token}"
dialogue = (ROOT / "references" / "dialogue-rendering.md").read_text(encoding="utf-8")
assert "默认 `Star = Analysis Lead`、`Lucy = Critical Analyst`" in dialogue, "default role fallback missing"
assert "Star = 数据分析小白" in dialogue, "novice role semantic override example missing"
assert "Lucy 必须从问题价值、可回答性或优先级上独立判断，而不是只补 SQL" in dialogue, "anti-companion role contract missing"
assert "禁止虚构领导任务" in dialogue, "no-fake-task-owner contract missing"
assert "accept / reject / replace / split" in dialogue, "question challenge actions missing"
assert "counter-hypothesis" in dialogue, "hypothesis challenge action missing"
assert "What / Where / Why / Alternative / Test / Robustness / So What" in dialogue, "analysis depth gate missing from dialogue"




print("OK: sql-business-thinking repository integrity")

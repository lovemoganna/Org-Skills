from pathlib import Path
import base64
import gzip
import hashlib
import json
import re
import subprocess
import sys

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
    "visualization-rendering.md",
    "regression-loop.md",
    "skill-change-log.md",
    "ontology-analysis.md",
    "debug-stages.md",
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
    "Result Scalar Normalization Gate",
    "SQL Alias Safety Gate",
    "Logical Data Revision Gate",
    "Result Freshness Gate",
    "Downstream Gate Propagation Gate",
    "Chart Candidate Competition Gate",
    "Unit Honesty Gate",
    "One-Chart-One-Conclusion Gate",
    "Layout Archetype Gate",
    "Information Budget Gate",
    "Artifact Presentation Gate",
    "Async Render Readiness Gate",
    "Mandatory Data Quality Gate",
    "Role Contract Gate",
    "本体前置阶段",
    "本体原子知识库",
    "本体识别规则库",
    "问题质量阶段",
    "分析信号",
    "本体局部展开",
    "分析深度阶段",
    "稳健性检查",
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
assert "两张本体表先行" in regression, "ontology-first regression missing"
assert "本体识别规则不得退化为分析查询" in regression, "business-pattern regression missing"
assert "分析信号后只沿本体局部展开" in regression, "ontology-local-expansion regression missing"
assert "复杂问题必须从原子问题生长" in regression, "composite-question provenance regression missing"
assert "Lisp 必须人类可读" in regression, "readable-lisp regression missing"
assert "Gate 称“阶段”" in regression, "chinese-analysis-terminology regression missing"
assert "调试模式一次只执行指定阶段" in regression, "single-stage debug regression missing"
assert "已确认上游不得被下游静默修改" in regression, "upstream lock regression missing"
assert "后续发现上游问题必须需回退" in regression, "rollback regression missing"
assert "从指定阶段继续不得自动补跑上游" in regression, "resume-without-autofill regression missing"
assert "全部阶段通过后完整链路回归" in regression, "full-chain regression missing"
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
assert "连续金额不能为了视觉风格被伪单位化" in regression, "unit-honesty regression missing"
assert "重复图表与模板填槽必须删除" in regression, "one-chart-one-conclusion regression missing"
assert "技术证据不能抢业务首屏" in regression, "information-budget regression missing"
assert "重跑不能复用旧业务 Result 冒充 fresh run" in regression, "result freshness regression missing"
assert "最终 Artifact 不得泄露内部选图过程" in regression, "artifact presentation regression missing"
assert "本地 Render QA 失败不能直接收口" in regression, "render placement regression missing"
assert "Remote Render payload 不能截断" in regression, "remote render payload-size regression missing"
assert "Connector 无 workflow_dispatch 时可用一次性 Issue 触发 Remote Render" in regression, "connector issue render regression missing"
assert "异步 Artifact 不能在未 READY 时判 Render PASS" in regression, "async readiness regression missing"
assert "生成 SQL 的 implicit alias / keyword collision 必须提前拦截" in regression, "sql alias safety regression missing"
assert "普通业务 Result 也必须统一 scalar normalization" in regression, "result scalar normalization regression missing"
assert "XLSX transport SHA 不能冒充 logical data revision" in regression, "logical data revision regression missing"
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
visualization = (ROOT / "references" / "visualization-rendering.md").read_text(encoding="utf-8")
for token in ["Chart Candidate Competition Gate", "Unit Honesty Gate", "One-Chart-One-Conclusion Gate", "Layout Archetype Gate", "Information Budget Gate", "Deletion Gate", "Presentation Engine"]:
    assert token in visualization, f"presentation contract missing: {token}"
assert "至少 3 个合理候选" in visualization, "chart candidate competition threshold missing"
assert "图数量由 **独立结论数** 决定" in visualization, "independent-conclusion chart count rule missing"
assert "为了填模板新增未验证 KPI" in visualization, "template fill fabrication guard missing"
assert "visualization-rendering.md" in skill, "presentation reference not wired into skill"
assert "visualization-rendering.md" in report_rendering, "report renderer does not delegate chart selection"
assert "Render QA Placement Gate" in report_rendering, "render QA placement gate missing"
assert "Canonical Remote Render Runner" in report_rendering, "canonical remote render runner contract missing"
assert ".github/workflows/sql-business-thinking-render-qa.yml" in report_rendering, "canonical remote render workflow path missing"
assert "tests/prepare-render-qa-payload.py" in report_rendering, "remote render payload helper missing from contract"
assert "REMOTE_RENDER_PAYLOAD_TOO_LARGE" in report_rendering, "remote render oversize guard missing"
assert "Artifact Presentation QA" in report_rendering, "artifact presentation QA missing"
assert "REUSED_VERIFIED_RESULT" in skill, "reused-result state missing"
assert "本轮 run" in skill and "当前 Skill revision" in skill, "result freshness revision binding missing"
assert "Artifact Presentation Gate" in visualization, "artifact presentation gate missing from visualization contract"
assert "ReportSpec 可以完整，正文必须克制" in visualization, "report-vs-body presentation boundary missing"
assert "Result Freshness QA" in regression_loop, "freshness QA missing from regression loop"
assert "Render QA Placement" in regression_loop, "render placement QA missing from regression loop"
assert "Async Render Readiness" in regression_loop, "async readiness QA missing from regression loop"
assert "scalar normalization" in regression_loop, "scalar normalization QA missing from regression loop"
assert "logical data" in regression_loop.lower(), "logical data revision QA missing from regression loop"
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
for token in [
    "ArrayBuffer.isView",
    "scalar_normalization_probe",
    "RESULT_SHAPE_INVALID",
    "transport_sha256",
    "logical_revision",
    "sqlbt-logical-v1",
    "sourceArrayBuffer",
    "before_rows",
    "after_rows",
]:
    assert token in workflow, f"wasm freshness/shape contract missing: {token}"

render_workflow_path = ROOT.parents[1] / ".github" / "workflows" / "sql-business-thinking-render-qa.yml"
assert render_workflow_path.exists(), "canonical remote render workflow missing"
render_workflow = render_workflow_path.read_text(encoding="utf-8")
for token in [
    "workflow_dispatch",
    "issues:",
    "types: [opened]",
    "[sqlbt-render-qa]",
    "SQLBT_RENDER_QA_V1",
    "Redact and close issue envelope",
    "issues: write",
    "html_gzip_base64",
    "expected_sha256",
    "allow_design_notes",
    "1440",
    "900",
    "390",
    "844",
    "artifact_sha256",
    "render-qa.json",
    "desktop.png",
    "mobile.png",
    "sql-business-thinking-render-qa",
    "sqlbt-render-readiness",
    "ASYNC_NOT_READY",
    "renderReady",
    "waitForFunction",
]:

    assert token in render_workflow, f"remote render workflow contract missing: {token}"

payload_helper = ROOT / "tests" / "prepare-render-qa-payload.py"
render_fixture = ROOT / "tests" / "render-qa-fixture.html"
assert payload_helper.exists(), "remote render payload helper missing"
assert render_fixture.exists(), "remote render fixture missing"
fixture_text = render_fixture.read_text(encoding="utf-8")
assert 'name="sqlbt-render-readiness"' in fixture_text, "async render fixture declaration missing"
assert 'data-render-ready' in fixture_text or 'dataset.renderReady' in fixture_text, "async render fixture READY marker missing"
payload_json = subprocess.check_output(
    [sys.executable, str(payload_helper), str(render_fixture)],
    text=True,
)
payload = json.loads(payload_json)
fixture_bytes = render_fixture.read_bytes()
expected_fixture_sha = hashlib.sha256(fixture_bytes).hexdigest()
assert payload["artifact_sha256"] == expected_fixture_sha, "payload helper sha mismatch"
assert payload["inputs"]["expected_sha256"] == expected_fixture_sha, "dispatch sha mismatch"
roundtrip = gzip.decompress(base64.b64decode(payload["inputs"]["html_gzip_base64"]))
assert roundtrip == fixture_bytes, "payload helper does not preserve exact fixture bytes"
assert payload["base64_chars"] <= 60000, "fixture unexpectedly exceeds safe inline render payload limit"
issue_envelope = payload.get("issue_envelope", {})
assert issue_envelope.get("title", "").startswith("[sqlbt-render-qa] "), "issue render title missing"
issue_body = issue_envelope.get("body", "")
assert issue_body.startswith("SQLBT_RENDER_QA_V1\n"), "issue render envelope version missing"
assert f"expected_sha256={expected_fixture_sha}" in issue_body, "issue render sha missing"
assert "allow_design_notes=false" in issue_body, "issue render design-note default missing"
assert f"html_gzip_base64={payload['inputs']['html_gzip_base64']}" in issue_body, "issue render payload mismatch"

debug_stages = (ROOT / "references" / "debug-stages.md").read_text(encoding="utf-8")
for token in [
    "正常模式",
    "调试模式",
    "D01 范围与执行契约",
    "D05 本体原子知识库",
    "D06 本体识别规则库",
    "D10 SQL 与真实结果",
    "D19 成品验收",
    "待执行",
    "待检查",
    "通过",
    "需修正",
    "需回退",
    "阻塞",
    "完整链路回归",
]:
    assert token in debug_stages, f"debug stage contract missing: {token}"
for field in ["当前阶段：", "依赖阶段：", "输入：", "本阶段任务：", "输出：", "检查结果：", "通过条件：", "状态："]:
    assert field in debug_stages, f"debug output field missing: {field}"
assert "不得自动执行这些阶段" in debug_stages, "debug resume must not auto-run missing dependencies"
assert "默认锁定" in debug_stages, "upstream lock contract missing"
assert "一次只执行指定阶段" in skill, "debug router single-stage stop missing"
assert "正常模式保持不变" in skill, "normal mode preservation missing"
assert "references/debug-stages.md" in skill, "debug reference not wired into skill"

dialogue = (ROOT / "references" / "dialogue-rendering.md").read_text(encoding="utf-8")
assert "默认 `Star = Analysis Lead`、`Lucy = Critical Analyst`" in dialogue, "default role fallback missing"
assert "Star = 数据分析小白" in dialogue, "novice role semantic override example missing"
assert "Lucy 必须从问题价值、可回答性或优先级上独立判断，而不是只补 SQL" in dialogue, "anti-companion role contract missing"
assert "禁止虚构领导任务" in dialogue, "no-fake-task-owner contract missing"
assert "accept / reject / replace / split" in dialogue, "question challenge actions missing"
assert "counter-hypothesis" in dialogue, "hypothesis challenge action missing"
assert "What / Where / Why / Alternative / Test / Robustness / So What" in dialogue, "analysis depth gate missing from dialogue"




print("OK: sql-business-thinking repository integrity")

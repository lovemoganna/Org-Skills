from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")

assert skill.startswith("---\nname: dataset-dashboard-builder\n"), "invalid skill frontmatter"

for path in [
    ROOT / "references" / "source-authority.md",
    ROOT / "references" / "analysis-spec.md",
    ROOT / "references" / "renderer-contract.md",
    ROOT / "references" / "chartjs-compiler.md",
    ROOT / "references" / "domain-routing.md",
    ROOT / "domains" / "exchange-funds-flow" / "domain-pack.md",
    ROOT / "eval" / "exchange-funds-flow.md",
    ROOT / "references" / "dashboard-quality-framework.md",
    ROOT / "references" / "insight-hierarchy.md",
    ROOT / "references" / "decision-diagnostics.md",
    ROOT / "references" / "eval-preflight.md",
    ROOT / "references" / "dashboard-audit-loop.md",
    ROOT / "eval" / "dashboard-quality.md",
    ROOT / "references" / "analysis-depth.md",
    ROOT / "references" / "investigation-loop.md",
    ROOT / "references" / "visualization-registry.md",
    ROOT / "references" / "regression-loop.md",
    ROOT / "references" / "skill-change-log.md",
    ROOT / "tests" / "regression-cases.md",
]:
    assert path.exists(), f"missing required file: {path.name}"

critical = [
    "Quality Gate",
    "Time-dimension Gate",
    "Adaptive TopN",
    "Rendered QA",
    "快照估值",
    "BLOCKED / LIMITED",
    "Analysis Depth Gate",
    "Visual Plan",
    "Renderer Capability Gate",
    "Table Role Gate",
    "Metric Authority Gate",
    "Unit Authority Gate",
    "Investigation Gate",
    "Finding Promotion Gate",
    "Explicit Scope Gate",
    "Candidate Triage",
    "Portfolio Synthesis",
    "Dashboard Mission Gate",
    "Information Architecture Gate",
    "Interaction Gate",
    "Dashboard Quality Evaluation",
    "Comparison & Metric Role Gate",
    "Domain Intelligence Gate",
    "Domain Composition Gate",
    "Semantic Field Catalog Gate",
    "Analysis Spec Gate",
    "Display & Label Gate",
    "Dashboard Decision & Audit Loop Gate",
    "Insight Hierarchy Gate",
    "Decision Diagnostics Gate",
    "Regression / Evaluation Preflight",
    "End-to-End Regression Mode",
]
for rule in critical:
    assert rule in skill or rule in (ROOT / "references" / "regression-loop.md").read_text(encoding="utf-8"), f"missing rule: {rule}"

for anchor in ["144,444 USDT", "83.48%", "8 / 9 = 88.89%", "exact-date 匹配：0"]:
    assert anchor in regression, f"missing real-data anchor: {anchor}"

assert "sql-business-thinking" in readme, "boundary with existing skill must be documented"
assert "一张表一个看板" in skill, "theme split guard missing"

analysis_spec = (ROOT / "references" / "analysis-spec.md").read_text(encoding="utf-8")
for rule in ["Semantic Field Catalog", "Identifier Gate", "Aggregation Semantics", "Analysis Intent", "Analysis Spec", "Series Gate", "Time Grain Gate", "Central Query Ownership"]:
    assert rule in analysis_spec, f"analysis spec rule missing: {rule}"
for rule in ["identifier", "non_additive", "COUNT DISTINCT", "Global Filter State"]:
    assert rule in analysis_spec, f"analysis spec semantic rule missing: {rule}"

renderer_contract = (ROOT / "references" / "renderer-contract.md").read_text(encoding="utf-8")
for rule in ["Renderer Ownership", "Renderer Selection", "Vela", "Chart.js", "Native HTML / CSS", "Visual Spec", "Label Policy", "Interaction Contract", "Language & UI Copy", "Theme & Component Consistency"]:
    assert rule in renderer_contract, f"renderer contract rule missing: {rule}"
for rule in ["多图共享同一时间域时，应同步 crosshair", "permanent label", "Global Filter State"]:
    assert rule in renderer_contract, f"renderer contract behavior missing: {rule}"

chart_compiler = (ROOT / "references" / "chartjs-compiler.md").read_text(encoding="utf-8")
for rule in ["DuckDB SQL Compiler", "Result Contract", "Chart.js Compiler", "Axis Compiler", "Series Compiler", "Compiler Failure"]:
    assert rule in chart_compiler, f"chart compiler rule missing: {rule}"
assert "Chart.js component 不直接 mutate" in chart_compiler
assert "AVG(precomputed_rate)" in chart_compiler

source_authority = (ROOT / "references" / "source-authority.md").read_text(encoding="utf-8")
for rule in ["Explicit Scope Gate", "Table Role Gate", "Authority Order", "Double-count Gate", "Unit & Aggregation Authority"]:
    assert rule in source_authority, f"source authority rule missing: {rule}"
assert "dashboard / output" in source_authority and "backup / archive" in source_authority

investigation = (ROOT / "references" / "investigation-loop.md").read_text(encoding="utf-8")
for rule in ["Candidate Triage Gate", "Goal Alignment", "Question Frontier", "Question Quality Gate", "Hypothesis Frontier", "Evidence Depth Gate", "Robustness Check", "Finding Promotion Gate", "Portfolio Synthesis Gate", "Information Gain Stop Rule"]:
    assert rule in investigation, f"investigation rule missing: {rule}"
assert "Pattern 只是“发生了什么”，不是“为什么”" in investigation

domain_routing = (ROOT / "references" / "domain-routing.md").read_text(encoding="utf-8")
for rule in ["Domain Detection Gate", "Entity evidence", "Event / state evidence", "Dimension evidence", "Generic Fallback"]:
    assert rule in domain_routing, f"domain routing rule missing: {rule}"

domain_pack = (ROOT / "domains" / "exchange-funds-flow" / "domain-pack.md").read_text(encoding="utf-8")
for rule in ["Detection Signature", "Funds Event Signature", "Domain Ontology", "Flow Health", "Rail / Network Performance", "Entity Exposure", "Flow Pattern Investigation", "Evidence Queue", "Domain Visual Grammar"]:
    assert rule in domain_pack, f"exchange funds flow rule missing: {rule}"

domain_eval = (ROOT / "eval" / "exchange-funds-flow.md").read_text(encoding="utf-8")
for rule in ["Critical", "Major", "Expected Domain Questions", "Acceptance"]:
    assert rule in domain_eval, f"exchange funds flow eval missing: {rule}"

quality = (ROOT / "references" / "dashboard-quality-framework.md").read_text(encoding="utf-8")
for rule in ["五层质量模型", "Dashboard Mission Contract", "Dashboard Mode", "Metric Role Gate", "Comparison Context Gate", "Dashboard Information Chain", "Information Architecture Gate", "Interaction Semantics", "Internal Analysis Boundary", "Anti-AI Dashboard Rules", "移动端控制区不得长期占据主要视口"]:
    assert rule in quality, f"dashboard quality rule missing: {rule}"

audit_loop = (ROOT / "references" / "dashboard-audit-loop.md").read_text(encoding="utf-8")
for rule in ["Decision Question Gate", "Dashboard Coverage Plan", "Simplest Primitive Guard", "One Primary Answer per View", "Density & Hierarchy Gate", "Global Design System Gate", "User Simulation Gate", "Rendered Audit Gate", "Coverage Reconciliation Gate", "Durable Fix Rule"]:
    assert rule in audit_loop, f"dashboard audit-loop rule missing: {rule}"

for rule in ["360px", "768px", "1280px", "Real User", "Constrained User", "Edge-data User"]:
    assert rule in audit_loop, f"dashboard audit-loop behavior missing: {rule}"

insight_hierarchy = (ROOT / "references" / "insight-hierarchy.md").read_text(encoding="utf-8")
for rule in ["Insight Hierarchy Gate", "North Star Gate", "So-What Gate", "Amount × Count Dual-Signal Gate", "Event-Driven Spike Gate", "Driver Decomposition Gate", "Pareto Gate", "Exception Logic Gate", "Operational State Gate", "Analytical Restraint Gate", "High-Value Dashboard Acceptance"]:
    assert rule in insight_hierarchy, f"insight hierarchy rule missing: {rule}"

for rule in ["breadth", "intensity", "concentration", "Top1", "Top2", "remove-Top1", "in-process"]:
    assert rule in insight_hierarchy, f"insight hierarchy behavior missing: {rule}"

decision_diagnostics = (ROOT / "references" / "decision-diagnostics.md").read_text(encoding="utf-8")
for rule in ["Change Confirmation Gate", "Materiality Before Extremeness Gate", "Threshold Authority Gate", "Delta Contribution Gate", "Control / Counterexample Gate", "Actor / Record Attribution Gate", "Comparison Context Gate", "Candidate Architecture Test", "Five-Second / Thirty-Second Test"]:
    assert rule in decision_diagnostics, f"decision diagnostics rule missing: {rule}"
for rule in ["partial bucket", "materiality + control severity + evidence strength + actionability", "remove-Top1", "delta contribution", "不能只换皮肤"]:
    assert rule in decision_diagnostics, f"decision diagnostics behavior missing: {rule}"

dashboard_eval = (ROOT / "eval" / "dashboard-quality.md").read_text(encoding="utf-8")
for rule in ["Critical", "Major", "Minor", "Acceptance Rule", "Generate", "Evaluate Again"]:
    assert rule in dashboard_eval, f"dashboard eval rule missing: {rule}"

analysis_depth = (ROOT / "references" / "analysis-depth.md").read_text(encoding="utf-8")
for rule in ["Question Map", "L2 · 分布与分层", "L4 · 关系、流程与跨表", "L5 · 驱动、集中度与异常"]:
    assert rule in analysis_depth, f"analysis depth rule missing: {rule}"

viz = (ROOT / "references" / "visualization-registry.md").read_text(encoding="utf-8")
for chart in ["histogram", "box plot", "scatter", "heatmap", "Pareto", "waterfall", "funnel", "Sankey", "network graph"]:
    assert chart in viz, f"visualization family missing: {chart}"
assert "原生支持目标图形" in viz and "自定义 SVG / Canvas" in viz, "renderer capability fallback missing"
assert "Encoding & Label Gate" in viz, "encoding/label gate missing"
assert "多序列图必须有清晰的直接标签或可见图例" in viz, "multi-series legend rule missing"
assert "散点、气泡、折线末端等直接标签发生重叠" in viz, "label collision rule missing"

for anchor in ["77.30%", "49.93%", "18.375", "V2 泛化：可视化注册表", "V3 原样本：Source Role & Authority", "辅助快照估值数学结果：144,444 USDT", "54.66%", "27.22%", "16.75h", "V5 原样本：Hypothesis-driven Investigation", "V6 原样本：显式四表范围", "V7 原样本：Priority & Portfolio Synthesis", "0.32%", "V7 泛化", "Adversarial R", "V8 原样本：Dashboard Quality", "V8 泛化", "Adversarial W", "V9 原样本：Dashboard Context / Comparison / Drill", "泛化 X", "泛化 Y", "泛化 Z", "泛化 AA", "Adversarial AB", "V10 原样本：Exchange Funds Flow Domain Intelligence", "泛化 AC", "泛化 AD", "泛化 AE", "Adversarial AF", "V11 原样本：Semantic Field Catalog → Analysis Spec → Chart.js", "泛化 AG", "泛化 AH", "泛化 AI", "泛化 AJ", "泛化 AK", "Adversarial AL", "Adversarial AM"]:
    assert anchor in regression, f"depth regression anchor missing: {anchor}"

for anchor in ["V12 原样本：Funds Scale & Trend → Renderer Contract", "105,874.5 USDT", "56,642.5 USDT / 6 笔", "泛化 AN：资金数据但错误主轴", "Adversarial AQ：Vela 自动接行情", "Adversarial AR：中文任务英文 UI", "Adversarial AS：永久 Label 与图形重叠"]:
    assert anchor in regression, f"V12 regression anchor missing: {anchor}"

for anchor in ["V13 原样本：Redundancy Gate", "泛化 AT：同构趋势复制", "泛化 AU：Chart + Table 重复", "Adversarial AV：说明文案复制"]:
    assert anchor in regression, f"V13 redundancy anchor missing: {anchor}"

for anchor in ["V14 原样本：Dashboard Audit Loop", "泛化 AW：孤儿组件", "泛化 AX：复杂度升级无理由", "Adversarial AY：源码检查冒充视觉检查", "Adversarial AZ：正常数据可用，边界数据破版", "Adversarial BA：无 overflow 但图表被压扁"]:
    assert anchor in regression, f"V14 audit-loop anchor missing: {anchor}"

for anchor in ["V15 原样本：Insight Hierarchy → High-Value Funds Dashboard", "85.21%", "48.84%", "88.27%", "89.27%", "81.89%", "86.64%", "51.92%", "70.62%", "11,392.5 USDT", "泛化 BB：金额涨、笔数平", "泛化 BC：标签被少数实体混淆", "泛化 BD：高金额未终态", "Adversarial BE：把单笔峰值写成增长", "Adversarial BF：KYC 伪驱动", "Adversarial BG：只有 Level + Trend"]:
    assert anchor in regression, f"V15 insight-hierarchy anchor missing: {anchor}"

for anchor in ["V16 原样本：Decision Diagnostics / Multi-Architecture", "原失败 A：低金额月份被误称高峰", "原失败 B：自造 5000 USDT 优先级", "泛化 BH：当前最大不等于变化贡献最大", "泛化 BI：Partial Bucket 假异常", "泛化 BJ：反证改变结论", "Adversarial BK：无业务阈值却画红线", "Adversarial BL：五个 Dashboard 只是换色"]:
    assert anchor in regression, f"V16 decision-diagnostics anchor missing: {anchor}"

eval_preflight = (ROOT / "references" / "eval-preflight.md").read_text(encoding="utf-8")
for rule in ["Fixture Preflight", "Environment Capability Preflight", "BLOCKED_FIXTURE", "BLOCKED_ENV", "NOT_APPLICABLE", "Layered Verdict", "Conditional Case Gate"]:
    assert rule in eval_preflight, f"eval preflight rule missing: {rule}"

for anchor in ["V17 原样本：Remote Skill × Remote Requirement Evaluation Preflight", "原失败 A：Requirement 声明 Canonical Fixture", "原失败 B：浏览器超时", "泛化 BM：SQL runtime 缺失", "泛化 BN：条件型 Case 未触发", "泛化 BO：核心逻辑通过但视觉环境阻塞", "Adversarial BP：用锚点冒充原始数据", "Adversarial BQ：所有 Case 强制执行"]:
    assert anchor in regression, f"V17 eval-preflight anchor missing: {anchor}"

for anchor in ["V18 原样本：Preflight 不能替代完整回归", "原失败 A：只检查仓库规则就结束", "原失败 B：浏览器失败后提前终止", "泛化 BR：测试报告不能替代产物", "泛化 BS：SQL 证据必须来自实际执行", "Adversarial BT：Preflight 过度展开"]:
    assert anchor in regression, f"V18 end-to-end regression anchor missing: {anchor}"

assert "Redundancy Gate" in skill, "redundancy gate missing from SKILL.md"

renderer_contract = (ROOT / "references" / "renderer-contract.md").read_text(encoding="utf-8")
assert "Result Contract" in renderer_contract and "Visual Spec" in renderer_contract and "Renderer Adapter" in renderer_contract

print("OK: dataset-dashboard-builder repository integrity")

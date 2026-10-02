from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")

assert skill.startswith("---\nname: dataset-dashboard-builder\n"), "invalid skill frontmatter"

for path in [
    ROOT / "references" / "source-authority.md",
    ROOT / "references" / "dashboard-quality-framework.md",
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
]
for rule in critical:
    assert rule in skill or rule in (ROOT / "references" / "regression-loop.md").read_text(encoding="utf-8"), f"missing rule: {rule}"

for anchor in ["144,444 USDT", "83.48%", "8 / 9 = 88.89%", "exact-date 匹配：0"]:
    assert anchor in regression, f"missing real-data anchor: {anchor}"

assert "sql-business-thinking" in readme, "boundary with existing skill must be documented"
assert "一张表一个看板" in skill, "theme split guard missing"

source_authority = (ROOT / "references" / "source-authority.md").read_text(encoding="utf-8")
for rule in ["Explicit Scope Gate", "Table Role Gate", "Authority Order", "Double-count Gate", "Unit & Aggregation Authority"]:
    assert rule in source_authority, f"source authority rule missing: {rule}"
assert "dashboard / output" in source_authority and "backup / archive" in source_authority

investigation = (ROOT / "references" / "investigation-loop.md").read_text(encoding="utf-8")
for rule in ["Candidate Triage Gate", "Goal Alignment", "Question Frontier", "Question Quality Gate", "Hypothesis Frontier", "Evidence Depth Gate", "Robustness Check", "Finding Promotion Gate", "Portfolio Synthesis Gate", "Information Gain Stop Rule"]:
    assert rule in investigation, f"investigation rule missing: {rule}"
assert "Pattern 只是“发生了什么”，不是“为什么”" in investigation

quality = (ROOT / "references" / "dashboard-quality-framework.md").read_text(encoding="utf-8")
for rule in ["五层质量模型", "Dashboard Mission Contract", "Dashboard Information Chain", "Information Architecture Gate", "Interaction Gate", "Anti-AI Dashboard Rules"]:
    assert rule in quality, f"dashboard quality rule missing: {rule}"

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

for anchor in ["77.30%", "49.93%", "18.375", "V2 泛化：可视化注册表", "V3 原样本：Source Role & Authority", "辅助快照估值数学结果：144,444 USDT", "54.66%", "27.22%", "16.75h", "V5 原样本：Hypothesis-driven Investigation", "V6 原样本：显式四表范围", "V7 原样本：Priority & Portfolio Synthesis", "0.32%", "V7 泛化", "Adversarial R", "V8 原样本：Dashboard Quality", "V8 泛化", "Adversarial W"]:
    assert anchor in regression, f"depth regression anchor missing: {anchor}"

print("OK: dataset-dashboard-builder repository integrity")

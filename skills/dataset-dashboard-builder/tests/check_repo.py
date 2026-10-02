from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")

assert skill.startswith("---\nname: dataset-dashboard-builder\n"), "invalid skill frontmatter"

for path in [
    ROOT / "references" / "analysis-depth.md",
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
]
for rule in critical:
    assert rule in skill or rule in (ROOT / "references" / "regression-loop.md").read_text(encoding="utf-8"), f"missing rule: {rule}"

for anchor in ["144,444 USDT", "83.48%", "8 / 9 = 88.89%", "exact-date 匹配：0"]:
    assert anchor in regression, f"missing real-data anchor: {anchor}"

assert "sql-business-thinking" in readme, "boundary with existing skill must be documented"
assert "一张表一个看板" in skill, "theme split guard missing"

analysis_depth = (ROOT / "references" / "analysis-depth.md").read_text(encoding="utf-8")
for rule in ["Question Map", "L2 · 分布与分层", "L4 · 关系、流程与跨表", "L5 · 驱动、集中度与异常"]:
    assert rule in analysis_depth, f"analysis depth rule missing: {rule}"

viz = (ROOT / "references" / "visualization-registry.md").read_text(encoding="utf-8")
for chart in ["histogram", "box plot", "scatter", "heatmap", "Pareto", "waterfall", "funnel", "Sankey", "network graph"]:
    assert chart in viz, f"visualization family missing: {chart}"
assert "原生支持目标图形" in viz and "自定义 SVG / Canvas" in viz, "renderer capability fallback missing"

for anchor in ["77.30%", "49.93%", "18.375", "V2 泛化：可视化注册表"]:
    assert anchor in regression, f"depth regression anchor missing: {anchor}"

print("OK: dataset-dashboard-builder repository integrity")

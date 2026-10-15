from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
risk = (ROOT / "references" / "risk-control.md").read_text(encoding="utf-8")
regression = (ROOT / "tests" / "regression-cases.md").read_text(encoding="utf-8")

assert skill.startswith("---\nname: bprd-plus\n"), "invalid skill frontmatter"
assert len(skill.splitlines()) < 230, "SKILL.md regressed into a long monolith"

for path in [
    ROOT / "references" / "risk-control.md",
    ROOT / "tests" / "regression-cases.md",
    ROOT / "tests" / "ab-regression.md",
]:
    assert path.exists(), f"missing required file: {path}"

for rule in [
    "最小充分表达",
    "Compression Gate",
    "样例没有被写成系统边界",
    "结构性反例",
    "不得为了执行固定流程而强制等待用户确认",
    "references/risk-control.md",
    "来源 → 需求 → 验收",
]:
    assert rule in skill, f"missing core rule: {rule}"

for section in [
    "## 任务目标",
    "## 当前问题",
    "## 方案与系统行为",
    "## 约束与边界",
    "## 验收标准",
    "## 待确认",
]:
    assert section in skill, f"missing default BRD section: {section}"

for obsolete in [
    "Phase 1：",
    "Phase 1.5：",
    "Phase 2.5：",
    "Phase 3.5：",
    "输出材料清单后停止，等待确认",
    "输出缺口清单后停止，等待确认",
]:
    assert obsolete not in skill, f"obsolete verbose workflow remains: {obsolete}"

assert "风控 BRD" not in skill.split("---", 2)[1], "description still narrows the skill to risk-control only"

for term in ["AML", "Fraud", "制裁", "RFI", "STR", "Evidence"]:
    assert term in risk, f"risk extension lost required concept: {term}"

for case in [
    "DuckDB Editor Pro",
    "历史通过样本：风控事件接入",
    "非风控系统改造",
    "信息缺失但不阻塞",
    "Compactness 回归",
    "多来源需求冲突",
    "验收证据边界",
]:
    assert case in regression, f"missing regression case: {case}"

ab = (ROOT / "tests" / "ab-regression.md").read_text(encoding="utf-8")
for case in ["A1", "A2", "A3", "A4"]:
    assert f"## {case}" in ab, f"missing A/B case: {case}"

print("bprd-plus integrity checks passed (behavioral A/B needs independent execution)")

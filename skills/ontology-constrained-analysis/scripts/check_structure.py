from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
skill = (root / "SKILL.md").read_text(encoding="utf-8")
loop = (root / "references" / "analysis-loop.md").read_text(encoding="utf-8")

errors = []

effective_lines = sum(bool(line.strip()) for line in skill.splitlines())
if effective_lines > 180:
    errors.append(f"SKILL.md too long: {effective_lines} nonblank lines > 180")

if "## 竞争解释和稳健性" in loop:
    errors.append("competition and robustness are merged")

required_headings = ["## 竞争解释", "## 稳健性验证"]
for h in required_headings:
    if h not in loop:
        errors.append(f"missing heading: {h}")

workflow = [
    "复杂问题",
    "复杂问题真实验证",
    "竞争解释",
    "稳健性验证",
    "Validated Finding",
]
match = re.search(r"## 固定流程\s+```text\n(.*?)\n```", skill, re.S)
if not match:
    errors.append("missing fixed workflow block")
else:
    flow_lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    positions = []
    for item in workflow:
        if item not in flow_lines:
            errors.append(f"missing workflow item: {item}")
        else:
            positions.append(flow_lines.index(item))
    if positions and positions != sorted(positions):
        errors.append("workflow order is wrong")

refs = re.findall(r"`(references/[^`]+\.md)`", skill)
for ref in sorted(set(refs)):
    if not (root / ref).exists():
        errors.append(f"missing reference: {ref}")

if errors:
    print("FAIL")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("PASS")
print("SKILL.md nonblank lines:", effective_lines)
print("competition/robustness split: yes")
print("references:", len(set(refs)))

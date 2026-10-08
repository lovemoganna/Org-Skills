#!/usr/bin/env python3
"""仅验证 Skill 打包结构与约束文本，不执行 DuckDB 或 Claude eval。"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "SKILL.md"
errors = []

if not source.exists():
    errors.append("缺少 SKILL.md")
else:
    text = source.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append("SKILL.md 缺少 YAML frontmatter")
    else:
        header = match.group(1)
        # 无第三方依赖；只提取用于基础结构检查的两个标量键。
        def yaml_scalar(key):
            m = re.search(rf"(?m)^{re.escape(key)}:\s*(.*)$", header)
            if not m:
                return ""
            value = m.group(1).strip()
            if value.startswith('"') and value.endswith('"'):
                return value[1:-1]
            if value.startswith("'") and value.endswith("'"):
                return value[1:-1]
            return value
        name = yaml_scalar("name")
        desc = yaml_scalar("description")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            errors.append("name 不符合 Agent Skills 命名约束")
        if name != ROOT.name:
            errors.append("name 与技能文件夹不一致")
        if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
            errors.append("description 长度非法")
        if len(text.splitlines()) >= 500:
            errors.append("SKILL.md 超过建议 500 行")
        for ref in re.findall(r"\]\((references/[^)#]+)\)", text):
            if not (ROOT / ref).is_file():
                errors.append(f"引用文件不存在: {ref}")
    for required in ["DuckDB", "Phase 0", "Hard Gate", "Routing Budget", "Validation", "BLOCK", "SCOPE", "WARN", "按需"]:
        if required not in text:
            errors.append(f"主入口缺失: {required}")

contract = (ROOT / "references/dataset-contract.md")
if not contract.exists():
    errors.append("数据契约缺失")
else:
    c = contract.read_text(encoding="utf-8")
    for tab in ["users", "fiat_transactions", "crypto_transactions", "exchange_rates"]:
        if tab not in c:
            errors.append(f"数据契约未列: {tab}")
    for forbidden in ["Executive_Dashboard", "expected_fiat_result", "expected_crypto_result", "data_rules", "qa_result", "fix_log"]:
        if forbidden not in c:
            errors.append(f"缺少禁止项: {forbidden}")

evals = ROOT / "evals/evals.json"
try:
    e = json.loads(evals.read_text(encoding="utf-8"))
    if len(e["evals"]) < 3:
        errors.append("不足三个评估样例")
except Exception as exc:
    errors.append(f"evals JSON 无效: {exc}")

if errors:
    for e in errors:
        print("FAIL:", e)
    sys.exit(1)
print("PASS: Skill 结构、frontmatter、引用、白名单与评估样例静态检查通过")
print(f"SKILL.md 行数: {len(source.read_text(encoding='utf-8').splitlines())}")
print(f"评估用例数: {len(json.loads(evals.read_text(encoding='utf-8'))['evals'])}")

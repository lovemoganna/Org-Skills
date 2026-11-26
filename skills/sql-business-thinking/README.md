# SQL Business Thinking · 双 Skill 迁移说明

原多模式执行引擎已拆成：
- [business-reasoning](../business-reasoning/SKILL.md)：业务推理，输出单个 Analysis Packet。
- [analysis-verifier](../analysis-verifier/SKILL.md)：独立执行与反证，输出 Verification Feedback。

调用：`使用 business-reasoning 分析 <业务需求>，随后用 analysis-verifier 独立验证并反馈，再让 business-reasoning 根据反馈修正。`

当前目录仅保留：兼容入口 `SKILL.md`、旧版归档 `legacy/SKILL.md`、原 `references/`、`tests/`、既有 CI 和严格 XLSX 原始 URL 合同。原复杂报告/HTML/Dxx 不再自动参与两个新 Skill。旧测试用于保护历史回归，不用于冒充新双 Skill 完整 E2E。

新回归测试：`python3 skills/sql-business-thinking/tests/check_dual_split.py`。本测试包含合成的 JOIN 放大反例，不代表真实 Google Sheets 数据执行。

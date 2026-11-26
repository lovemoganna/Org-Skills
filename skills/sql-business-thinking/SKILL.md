---
name: sql-business-thinking
description: 兼容旧调用的路由入口。业务思维已拆成 business-reasoning，独立 SQL/数据证据验证已拆成 analysis-verifier；本入口不再自行执行教学、分析、取数或报告。
---
# SQL Business Thinking · 已拆分（兼容入口）

此文件仅用于老调用路径重定向，**不是第三个执行 Skill**。

- 分析：`../business-reasoning/SKILL.md`，负责「目的→拆需求→结果表→表/值/条件→SQL 候选」。
- 验证：`../analysis-verifier/SKILL.md`，负责「合同/结构/SQL/Result/反证→回传反馈」。
- 默认编排：A 提交一个 Analysis Packet → B 独立验证一个 Packet → A 根据反馈更新或停止。
- 用户要求两者协同时，必须显式把 Packet 交接给 B；不能用单模型角色扮演冒称真正的独立验证。
- 用户要求精确原始 URL / DuckDB `read_xlsx` 时，B 保持原约束。未实际执行的数据结论仍为 UNVERIFIED/BLOCKED。

旧版完整原文留档：`legacy/SKILL.md`。既有 `references/`、`tests/` 和旧工作流是**历史回归资产**，不会自动注入新 Skill。HTML、看板、Dxx、教学对话不在双 Skill 职责内，必须通过专用工具或 Skill 执行。

新架构回归：`tests/check_dual_split.py`；原始 URL/质量历史合同由旧回归单独保护。

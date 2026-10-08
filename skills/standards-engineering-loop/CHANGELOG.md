# CHANGELOG

## 0.1.0 — 2026-10-08

- 首次将《通用标准规范撰写与 Loop 自迭代优化元提示体 V3》封装成 Claude Skill。
- 源 SOP 的 34 节原文完整只读保留；五份 references 可逐字重建原始文本。
- SKILL.md 负责触发、路由、硬约束和按需加载；不以 DuckDB 派生 SOP 替换原始 SOP。
- 8 个 eval 提示已编制，尚未进行 Claude with-skill vs baseline 的行为回归。
- 结构校验通过；正式内容质量和领域 E2E 未据此宣称通过。

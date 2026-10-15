# Changelog

## 2026-10-06

- 新增 `bprd-plus` Skill。
- 将 BPRD Plus v1.5.3 的核心工作流收敛为 canonical `SKILL.md`。
- 保留 Phase 1/2/3、Type A/B/C、字段建模、独立自检、需求生命周期和领导反馈迭代机制。

- 增加 Generalization Gate：在 BRD 生成前区分样例与问题空间，提取变化维度、系统不变量、未知输入策略和泛化契约。
- 增加 Counterexample Gate：自检后强制执行原失败样本、结构性反例、未知输入和边界行为验证。
- 增加样例过拟合检查，禁止把固定类型、顺序、层级、数量或已知 Registry 当作核心实现前提。


## 2026-10-06 — concise core refactor

- 将 `bprd-plus` 从“风控 BRD 专用”调整为通用产品、系统与风控 BRD 编译器。
- 新增“最小充分表达”和 Compression Gate；默认只保留目标、问题、方案与系统行为、约束与边界、验收、待确认。
- 删除固定 Phase 等待确认链路；仅在关键缺失信息会改变目标、范围、核心行为或验收时阻塞。
- 保留 Generalization / Counterexample 能力，但压缩为运行规则，不再把内部分析过程写进 BRD 正文。
- 将 AML、Fraud、制裁、RFI、STR 等风控专项规则移入 `references/risk-control.md` 按需加载。
- 新增 `tests/regression-cases.md`，覆盖 DuckDB Editor Pro 原失败样本、历史风控样本和泛化边界。

## 2026-10-15 — targeted traceability A/B

- 同模型隔离回放 A1/A2/A3/A4；旧版在冲突处理、证据边界和精简方面未见明显劣势。
- 回退重复的冲突和证据提示，仅对多版本增量需求补充最小来源、原需求、验收映射要求。
- 缺失决策的关键行为保持“待确认”，不为追踪增加 BRD 表格。
- 后续结果必须以新候选的独立回放为准；静态 CI 不是行为验收。

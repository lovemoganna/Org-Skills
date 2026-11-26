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

## 2026-10-15 — evidence-backed A/B evaluation

- 通过 GitHub Actions 的隔离 Copilot CLI 会话执行 A1 冲突、A2 增量追踪、A4 证据边界与 A3 精简四类用例，并对 A2/A3 执行精简候选复测。
- A1/A4 新旧均满足关键约束；A2 没有稳定领先；A3 长短变化存在波动。优化收益证据不足。
- 按 loop-engineering-meta 规则回退所有 SKILL.md 行为变更，保留回归用例、测试记录及按需触发的 A/B 执行入口。
- `skills/bprd-plus/tests/ab-report-20261015.md` 记录实测证据与局限。

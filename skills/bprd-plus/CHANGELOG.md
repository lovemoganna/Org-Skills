# Changelog

## 2026-10-06

- 新增 `bprd-plus` Skill。
- 将 BPRD Plus v1.5.3 的核心工作流收敛为 canonical `SKILL.md`。
- 保留 Phase 1/2/3、Type A/B/C、字段建模、独立自检、需求生命周期和领导反馈迭代机制。

- 增加 Generalization Gate：在 BRD 生成前区分样例与问题空间，提取变化维度、系统不变量、未知输入策略和泛化契约。
- 增加 Counterexample Gate：自检后强制执行原失败样本、结构性反例、未知输入和边界行为验证。
- 增加样例过拟合检查，禁止把固定类型、顺序、层级、数量或已知 Registry 当作核心实现前提。

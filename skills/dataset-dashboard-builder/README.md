# dataset-dashboard-builder

自动把陌生多表数据集转换为高价值定制看板：

```text
扫描 → 质检 → Field Catalog → Domain Detection → Domain Model → Mission / Mode → Business Analysis Contract → Reference Archetype → Domain Question Map → Investigation → Portfolio Synthesis → Domain Composition → Insight Hierarchy → Decision Diagnostics → Analysis Spec → DuckDB SQL → Result → Visual Spec → Renderer Adapter → Information Architecture → Decision Questions → Coverage Plan → Interaction → Rendered Audit → Domain + Dashboard Evaluation → 回归
```

## 文件

- [`SKILL.md`](SKILL.md)：主协议。
- [`references/source-authority.md`](references/source-authority.md)：表角色、来源权威性、重复计数与单位聚合边界。
- [`references/analysis-spec.md`](references/analysis-spec.md)：字段语义、维度/指标、聚合、Analysis Spec 与统一查询所有权。
- [`references/renderer-contract.md`](references/renderer-contract.md)：Result → Visual Spec → Renderer Adapter，统一 Vela / Chart.js / Native HTML 的职责与交互规则。
- [`references/chartjs-compiler.md`](references/chartjs-compiler.md)：Chart.js Adapter 的专用编译协议，不再代表全局唯一 Renderer。
- [`references/domain-routing.md`](references/domain-routing.md)：领域识别、置信度、Domain Pack 路由与 generic fallback。
- [`domains/exchange-funds-flow/domain-pack.md`](domains/exchange-funds-flow/domain-pack.md)：资金流领域 ontology、问题库、指标角色、调查 playbook、视觉语法。
- [`eval/exchange-funds-flow.md`](eval/exchange-funds-flow.md)：资金流领域专属质量验收。
- [`references/insight-hierarchy.md`](references/insight-hierarchy.md)：North Star、So-What、Amount×Count、Event-Driven Spike、Driver Decomposition、Pareto 与 Exception Logic。
- [`references/decision-diagnostics.md`](references/decision-diagnostics.md)：变化确认、Materiality、阈值权威、Delta Contribution、反证与多候选 Dashboard 结构测试。
- [`references/dashboard-quality-framework.md`](references/dashboard-quality-framework.md)：Dashboard 本质、五层质量模型、信息架构、交互与 Anti-AI 规则。
- [`references/dashboard-business-analysis.md`](references/dashboard-business-analysis.md)：Primary KPI 资格、比较基线、决策方向、Driver 证明、指标分解与 Mode 降级。
- [`references/dashboard-reference-catalog.md`](references/dashboard-reference-catalog.md)：专业 Dashboard Archetype、Golden Reference 选择、Dashboard/Report 边界与首屏契约。
- [`references/dashboard-audit-loop.md`](references/dashboard-audit-loop.md)：Decision Questions、Coverage Plan、User Simulation、Rendered Audit、设计 token 与覆盖对账闭环。
- [`eval/dashboard-quality.md`](eval/dashboard-quality.md)：Critical / Major / Minor Dashboard 质量评估与修正闭环。
- [`references/analysis-depth.md`](references/analysis-depth.md)：Question Map、分析深度阶梯与停止条件。
- [`references/investigation-loop.md`](references/investigation-loop.md)：候选优先级、Question/Hypothesis Frontier、稳健性、Finding 晋级与 Portfolio Synthesis。
- [`references/visualization-registry.md`](references/visualization-registry.md)：图表能力注册表、选图规则与 Renderer Capability Gate。
- [`references/regression-loop.md`](references/regression-loop.md)：真实样本、泛化与渲染回归规则。
- [`references/skill-change-log.md`](references/skill-change-log.md)：真实缺陷及泛化修正记录。
- [`tests/regression-cases.md`](tests/regression-cases.md)：原样本、泛化和历史边界测试。
- [`tests/check_repo.py`](tests/check_repo.py)：结构与关键规则完整性检查。
- [`tests/dashboard_surface_lint.py`](tests/dashboard_surface_lint.py)：最终 HTML 的 Dashboard/Report 边界与内部 QA 外露检查。

与 `sql-business-thinking` 的边界：后者负责业务问题→SQL→验证；本 Skill 负责陌生多表→自动发现分析主题→定制看板。二者可以组合，但不互相复制。

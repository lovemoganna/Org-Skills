# dataset-dashboard-builder

自动把陌生多表数据集转换为高价值定制看板：

```text
扫描 → 质检 → Business Modeling → Question Map → Investigation → Portfolio Synthesis → Information Architecture → Visualization → Interaction → UI → Quality Evaluation → 回归
```

## 文件

- [`SKILL.md`](SKILL.md)：主协议。
- [`references/source-authority.md`](references/source-authority.md)：表角色、来源权威性、重复计数与单位聚合边界。
- [`references/dashboard-quality-framework.md`](references/dashboard-quality-framework.md)：Dashboard 本质、五层质量模型、信息架构、交互与 Anti-AI 规则。
- [`eval/dashboard-quality.md`](eval/dashboard-quality.md)：Critical / Major / Minor Dashboard 质量评估与修正闭环。
- [`references/analysis-depth.md`](references/analysis-depth.md)：Question Map、分析深度阶梯与停止条件。
- [`references/investigation-loop.md`](references/investigation-loop.md)：候选优先级、Question/Hypothesis Frontier、稳健性、Finding 晋级与 Portfolio Synthesis。
- [`references/visualization-registry.md`](references/visualization-registry.md)：图表能力注册表、选图规则与 Renderer Capability Gate。
- [`references/regression-loop.md`](references/regression-loop.md)：真实样本、泛化与渲染回归规则。
- [`references/skill-change-log.md`](references/skill-change-log.md)：真实缺陷及泛化修正记录。
- [`tests/regression-cases.md`](tests/regression-cases.md)：原样本、泛化和历史边界测试。
- [`tests/check_repo.py`](tests/check_repo.py)：结构与关键规则完整性检查。

与 `sql-business-thinking` 的边界：后者负责业务问题→SQL→验证；本 Skill 负责陌生多表→自动发现分析主题→定制看板。二者可以组合，但不互相复制。

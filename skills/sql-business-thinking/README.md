# sql-business-thinking

训练路径：

```text
业务语言 → 数据逻辑 → SQL → 验证 → 可复述结论
```

## 入口

- [`SKILL.md`](SKILL.md)：主协议与路由。
- [`references/dataset-planning.md`](references/dataset-planning.md)：陌生数据集勘察、时间维表、JOIN 基数与分析地图。
- [`references/protocol.md`](references/protocol.md)：判级、暂停、账本、代码增长、复盘。
- [`references/dialogue-rendering.md`](references/dialogue-rendering.md)：人物角色绑定、协作推演与 Code-in-Conversation。
- [`references/report-rendering.md`](references/report-rendering.md)：ReportSpec、HTML/DuckDB-Wasm 与渲染验收。
- [`references/regression-loop.md`](references/regression-loop.md)：扫描 → 修正 → 自检 → 再修正闭环。
- [`references/skill-change-log.md`](references/skill-change-log.md)：已沉淀的缺陷与泛化规则。

## 回归

- [`tests/regression-cases.md`](tests/regression-cases.md)：原失败样本、历史通过样本和新增泛化样本。
- [`tests/check_repo.py`](tests/check_repo.py)：仓库结构与引用完整性检查。

维护时必须先读取仓库当前版本，再做最小 Diff；不要从聊天附件覆盖仓库 HEAD。

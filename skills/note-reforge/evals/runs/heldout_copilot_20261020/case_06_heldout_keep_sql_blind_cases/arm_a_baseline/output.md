**决策：PATCH**

**产物：**将文档开头替换为以下内容；其余正文、链接及所有测试用例块保持原样。

```org
#+TITLE: SQL 与本体约束分析盲测：23 个可复用案例
#+WIKI_ID: e1e502b9-f876-47d6-813f-e4d5ea51983a
#+CATEGORY: SQL 分析与 Skill 测试
#+FILETAGS: :sql:duckdb:skill-testing:dataset:
#+DATE: 2026-10-07
#+SOURCE: 本次对话中提供的 13 组测试需求与公开数据文件 URL
#+INGEST_ID: 97d78168-64ce-4cec-a2fb-90904a8178f4
#+WIKI_STATUS: published

#+CAPTION: SQL 与本体约束盲测：23 个待执行案例、执行边界与验收状态（1920×920，点击查看原图）。
#+ATTR_HTML: :width 100% :style "display:block;max-width:100%;height:auto;margin:0 auto;object-fit:contain;"
[[file:../../../note-assets/e1e502b9-f876-47d6-813f-e4d5ea51983a/sql-ontology-blind-test-header.png]]

* 本页结论与状态
本页收录 23 个测试资产：S01–S13 用真实公开数据检查 SQL 业务分析；T01–T10 检查本体约束分析的 Runtime、Gate、关系与证据。两组目标不同，分别验收，不合并通过率。

**当前状态：23 个案例均未在本页证明已执行或通过。** 用例提示、裁判判据、历史报告和 Skill 发布状态都不能代替本轮执行回执。每轮须分别记录实际任务执行状态（PASS、BLOCKED、FAIL、NOT_RUN）和独立裁判结论；没有真实执行证据不得判为测试 PASS。

* 执行入口
改动 Skill 后，先用 T04、T06、T08、T09 定位跨单位求和、JOIN 放大、旧数值污染和资金因果误判。四例输入内联，可分别检查语义、计算与证据边界；仍须真实执行 DuckDB，提示词本身不构成测试结果。

随后用 T02、T03、T05 检查业务语义、未知枚举和状态处理，用 T10 检查来源不可用时是否正确阻塞。T01、T07 依赖指定 Google Sheets 与固定 DuckDB SQL，只能在 Runtime 符合约束时执行，不得换源或改写 SQL。最终验收仍须执行完整 T01–T10 及 Skill 原有触发正反例；快速回归顺序不缩减验收范围。失败时保留实际 SQL、Result 或错误日志，不得用其他成功案例抵消。

* 遇到的问题如何选案例
| 遇到的问题 | 用例 | 验证什么 |
|------------+------+----------|
| 多表订单、状态或时间粒度可能重复计数 | S01、S02、S05 | 真实数据和计算口径 |
| 陌生领域也要自己发现业务问题 | S03、S04、S07、S12 | 业务分析迁移能力 |
| 固定远程 SQL、四表白名单和四 Gate | T01 | 全链路证据与运行约束 |
| 电商和 SaaS 的本体能否建对 | T02、T03 | 主体、事件和合法关系 |
| 单位、枚举、JOIN 的错误是否被拒绝 | T04–T06 | 指标计算的硬边界 |
| 先分析后追认 Gate 1、沿用旧数值 | T07、T08 | 历史失败回归 |
| 同 UID 被写成资金因果、没有 Result 也生成 Finding | T09、T10 | 关系与证据约束 |
```


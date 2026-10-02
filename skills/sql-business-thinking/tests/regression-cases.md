# Regression Cases

## 真实数据集基线

数据源：Google Sheet `exchange_funds_flow_dataset`。

四张核心表：

- `users`
- `fiat_transactions`
- `crypto_transactions`
- `exchange_rates`

读取基线：DuckDB `read_xlsx`，四表初始化后物化为表；浏览器报告使用 DuckDB-Wasm 时遵循 browser VFS / CORS 约束。

### 当前回归锚点

在数据源和口径未变化时：

- 快照估值总交易额：`144,444 USDT`
- Top 3 用户贡献：`83.48%`
- 法币 / 加密 active 用户重叠：`8 / 9 = 88.89%`
- completed 交易交易日精确汇率匹配：`0`

这些数字不是永久业务常量；数据源或口径变化时必须重新计算。

## 原失败样本

### Case 1：代码必须由人物会话逐步产生

要求：

```text
领导下任务
→ star 收住目标
→ star/Lucy 讨论当前问题
→ 草稿代码增量
→ 唯一可执行 SQL
→ Result
→ 判断修正
→ 下一问题
→ star report-back
```

验收：

- 不能 `对白 → 一次性完整 SQL`；
- 每个推进点至少有一次真实代码增量；
- 每个推进点只有一个最终可执行 SQL 和一个 Result；
- 数字第一次进入人物台词前必须已有对应 Result；
- 不维护跨阶段 rolling summary；
- 正文不得存在第二套可执行 SQL 副本。

### Case 2：时间维表 / 汇率表

先检查业务键覆盖与时间键覆盖，再走 exact-date → as-of → snapshot 路由。

验收：

- 仅按 `asset` JOIN 多日期汇率表不得直接进入金额 `SUM`；
- snapshot 必须明确改名为“快照估值”；
- 汇率时间不匹配不能伪装成历史真实成交额。

### Case 3：JOIN Cardinality Gate

金额、笔数、比率聚合前检查右表键唯一及 JOIN 前后行数。

验收：非业务预期的一对多未解决前禁止进入 `SUM`。

## 历史通过样本

- 每个客户一行：先定 UID 粒度，再 `GROUP BY uid`。
- “所有客户，包括没交易的”：客户表定范围，再判断 `LEFT JOIN`。
- `LEFT JOIN` 右表过滤：需要保留无行为对象时，条件不能机械放 `WHERE`。
- “成功订单”：终态与成功分开，字典没写成功口径时由用户定。
- 严格结果对账：使用双向 `EXCEPT ALL`，保留重复数量差异。

## 新增泛化样本

### 泛化 A：多日期价格表

给 `prices(asset, effective_date, price)` 与跨多日交易，验证模型不会只按 asset JOIN，也不会在未定义 as-of 规则时自行选择最近价格。

### 泛化 B：退款一对多

`orders` 一笔订单对应多笔 `refunds`。验证模型先把退款聚合到目标粒度再 JOIN，避免订单金额被放大。

### 泛化 C：小样本 Top N

active 用户只有 7 个时，不得把 Top 10 = 100% 当作集中度结论；应自动降为 Top 1 / Top 3。

### 泛化 D：人物会话但无代码要求

如果用户只要求人物推演，没有要求“代码在会话里逐步产生”，会话仍需连续 Conversation Arc，但不应机械强制每个阶段显示草稿 SQL。

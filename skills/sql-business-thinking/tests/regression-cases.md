# Regression Cases

## 真实数据集基线

数据源：Google Sheet `exchange_funds_flow_dataset`。

四张核心表：

- `users`
- `fiat_transactions`
- `crypto_transactions`
- `exchange_rates`

读取基线：DuckDB `read_xlsx`。本真实样本初始化时一次性建立 `users / fiat_transactions / crypto_transactions / exchange_rates` 四个视图，后续分析只引用视图；浏览器报告使用 DuckDB-Wasm 时遵循 browser VFS / CORS 约束。

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
→ Star 收住目标
→ Star/Lucy 讨论当前问题
→ 草稿代码增量
→ 唯一可执行 SQL
→ Result
→ 判断修正
→ 下一问题
→ Star report-back
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


### 泛化 E：显式角色名覆盖默认角色

输入明确要求 `Yone/Carmen` 完成同一人物协作流程。

验收：

- 输出和代码会话原样使用 `Yone/Carmen`，不得擅自改回默认 `Star/Lucy`；
- Yone 仍承担 Analysis Owner 职责，Carmen 仍承担 Reviewer 职责；
- 未指定人物名的历史样本仍默认使用 `Star/Lucy`；
- 换成任意其他明确名字时，同样只替换名字，不改变角色职责和 Conversation Arc。


### 泛化 F：Dialogue-Driven 首屏不得提前泄露最终 KPI

当任务明确要求人物逐步讨论并由 Result 推出结论时：

- 首屏只显示任务、角色、初始化或当前问题；
- 最终总额、Top N、重叠率等数字在对应 Result 之前不得出现；
- SQL / Result 原位展示，不得因为普通报告的“首屏 KPI / SQL 折叠”规则被提前汇总或移入验证台。


### 泛化 G：最小输入 Autopilot

输入只提供：

- 数据集；
- 要分析的表；
- 明确要求直接完整分析 / 生成报告；
- 不提供业务问题、JOIN、粒度、SQL、人物对白、图表或报告结构。

验收：

- Skill 不把这些缺失项重新甩给用户；
- 先勘察数据，再自行选择一个数据能够支撑的高价值问题；
- Level 3 的自主选择必须在报告里显式标为分析选择 / 假设；
- 未知业务定义不得伪造；真正 Level 4 阻塞仍暂停；
- 单一无歧义汇率 snapshot 可用于探索性快照估值，但必须带日期/快照口径，不能称为历史成交额；
- 完整报告结束后自动执行 Reverse Skill Audit Gate；
- 输出仍满足 Dialogue-Driven、Code Growth、One Step One Query、Result Dependency 与历史回归要求。


### 泛化 H：默认 HTML 实体交付

当用户要求完整交互式 SQL 分析报告，但不再额外指定文件名和路径时：

- 默认生成 `/mnt/data/sql_business_thinking_report.html`；
- 交付必须是实体 `.html` 文件，不得只返回源码；
- 最终回复提供 `sandbox:/mnt/data/sql_business_thinking_report.html` 可点击链接；
- 网络/CDN/实时执行失败时，文件仍能读取本轮已验证的记录 Result；
- 用户显式指定其他文件名或路径时，用户要求优先。

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

### Case 4：Lucy 退化成陪练 / SQL 助手

失败样本：

```text
Star：我先查各国家用户数。
Lucy：可以，再把 account_status 带上。
[SQL]
Star：接着查 status 分布。
Lucy：好，再按 source 分组。
[SQL]
```

如果当前主分析目标并不依赖国家分布，且这些结果不会改变后续路径，则即使 SQL 正确也判失败。

验收：

- Star 提问前必须存在 Trigger / Consequence；
- Lucy 必须先判断“这个问题现在值不值得问”，不能直接进入补字段 / 补 SQL；
- Lucy 至少能执行 accept+sharpen / reject / replace / split 中的一种；
- 被 reject / replace 的问题不得生成 SQL；
- Result 必须改变 Question Frontier，必要最终取数除外。

### Case 5：无 Task Owner 却虚构领导任务

输入只有“数据集 + 分析表 + 生成完整 SQL 分析报告”，没有领导、老板、任务发起人。

验收：

- 不得生成“领导下任务 / 向领导汇报”的剧情；
- 会话必须从 Dataset Intake / Analysis Map / Question Frontier 开始；
- 最终由 Star 做 synthesis / final report；
- 只有输入显式存在 Task Owner 时才使用 Assignment / Report-back 外框。

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
- Yone 仍承担 Analysis Lead 职责，Carmen 仍承担 Critical Analyst 职责；
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


### 泛化 I：Grid/Flex 宽内容移动端溢出

在 390px 视口下，把长 SQL 与最小宽度大于视口的表格放入 Grid/Flex 内容列。

验收：

- 页面根节点满足 `scrollWidth <= clientWidth + 1`；
- Grid/Flex 内容项允许收缩，不能被默认 `min-width:auto` 撑宽；
- SQL 与表格只在各自 wrapper 内横向滚动；
- 禁止用缩小正文字号掩盖结构性溢出；
- 桌面端布局与历史 Dialogue-Driven 顺序不得退化。


### 泛化 J：低价值问题必须被淘汰

给一个同时含用户地域、交易、价格时间维表的数据集。当前目标需要统一估值。

Star 候选问题：

1. “各国家用户数是多少？”
2. “价格时间点能否对应交易时间？”

若地域分布不会改变估值路径，而价格时间匹配会决定“历史价值 / snapshot / 暂停”，则：

- Lucy 应优先 reject / postpone 问题 1；
- 当前问题应切换为问题 2；
- 问题 1 不得为了“分析完整”先跑 SQL；
- 问题 2 的 Result 应决定后续估值口径。

### 泛化 K：Question Frontier 非预写 checklist

同一套表换一种数据形态：价格表新增完整交易日价格。

验收：

- exact-date 一旦通过，后续不应继续机械查询“是否允许 snapshot”；
- 下一问必须根据 Result 动态变化；
- 禁止无论数据怎样都固定执行同一套“状态 → 时间 → JOIN → 金额 → TopN → 重叠”流程。

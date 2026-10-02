# Regression Cases

## 真实样本：exchange_funds_flow_dataset

输入四表：

- `users`
- `fiat_transactions`
- `crypto_transactions`
- `exchange_rates`

读取合同保持用户已验证的 DuckDB `read_xlsx` 方式；初始化只写一次，四表建议建视图后分析。

在数据源与 completed + snapshot 口径未变化时，回归锚点：

- 用户：10；
- 法币交易：25；其中 completed 21；
- 加密交易：25；其中 completed 22；
- 汇率：8 条，单一 effective_date；
- completed 交易与汇率 exact-date 匹配：0；
- 辅助快照估值数学结果：144,444 USDT；该值不得在业务规则禁止跨币种混同汇总时升级为 canonical 核心 KPI；
- 法币快照估值：123,074.5 USDT；
- 加密快照估值：21,369.5 USDT；
- active 交易用户：9；
- 法币/加密 completed active 重叠：8 / 9 = 88.89%；
- Top 3 快照估值贡献：83.48%；
- 至少 1 条 `crypto_order_id` 日期与 `created_at` 不一致。

验收：

1. 若使用 144,444 USDT，只能命名为“辅助快照估值”，不能称历史真实成交额，也不得覆盖按原生 currency / asset / network 分区的 canonical 结果；
2. Top3 可以作为集中度，Top10 不得作为核心集中度结论；
3. 日期冲突进入数据质量区，不得静默忽略；
4. 看板至少覆盖规模、结构/集中度、流程状态、数据质量；
5. 关键限制必须在核心金额附近可见。

## 泛化 A：多日期价格表

交易跨多日，价格表同一资产多日期。未定义 as-of 时禁止只按资产 JOIN 后 SUM。

## 泛化 B：一对多退款

`orders` 对 `refunds` 为一对多。聚合订单金额前必须先解决 JOIN 放大。

## 泛化 C：小样本

active=7。不得输出 Top10=100% 作为集中度发现，应降为 Top1/Top3。

## 泛化 D：无金额事件表

只有 `events(user_id,event_type,created_at)`。应生成活跃、事件结构、趋势等主题，不得强行寻找“交易额”。

## 泛化 E：完全不同 Schema

输入 `tickets / agents / sla_rules`。必须重新识别业务对象与主题，不得残留 users/交易/资产字段假设。

## 历史边界

与 `sql-business-thinking` 组合时继续遵守其：

- JOIN Cardinality Gate；
- 时间维表 exact/as-of/snapshot；
- Answer Coverage；
- 小样本 TopN。

本 Skill 不修改这些已有规则，只在自动看板阶段消费其验证结果。


## V2 原样本：深度分析

同一 `exchange_funds_flow_dataset` 不得只停留在 144,444 USDT 与 Top3。

在数据源不变时，Question Map 至少应能识别以下高价值候选方向：

- 分层：KYC Level 3 仅 2 个用户，但 completed 快照估值约占 77.30%；
- 集中度：Top1 约 49.93%，Top3 83.48%，可使用 Pareto 而不只是一张排名表；
- 流程：法币 ACH completed 中位完成时延约 18.375 小时，明显高于 faster_payments 约 0.067 小时；必须同时展示样本 N；
- 网络状态：BSC 与 ARBITRUM 当前样本完成率均为 50%，但样本小，必须保留分母，不能直接下稳定性结论；
- 跨表：8 个用户同时存在 completed 法币与链上交易，1 个仅法币，1 个无 completed 交易；
- 异常：至少 1 条 crypto order ID 日期与 created_at 不一致。

验收：

1. 默认分析必须出现 L2 分布/分层；
2. 至少选择一个 L3/L4/L5 方向继续推进；
3. 绝对量与成功率/每笔/时延等标准化指标不能混为一谈；
4. 小样本差异必须展示 N，不得写成统计显著结论；
5. 分析结论与可视化类型之间必须有 Question → Visual 映射。

## V2 泛化：可视化注册表

### 泛化 F：长尾金额

输入大量连续金额并存在长尾。

验收：优先考虑 histogram / box plot；不得只给平均值 + 柱状图。

### 泛化 G：流程阶段

输入 `created → reviewed → approved → settled` 的有序阶段。

验收：允许 funnel / stage bar；普通无序状态字段不得机械画 funnel。

### 泛化 H：贡献拆解

结果变化可以严格拆为若干加性 driver。

验收：允许 waterfall；无法加总时改用 ranked bar，不伪造 waterfall。

### 泛化 I：真实流向

存在 `source → target → amount`。

验收：允许 Sankey / alluvial；没有明确方向和权重时不得生成。

### 泛化 J：cohort

存在首次发生时间与后续周期行为。

验收：允许 cohort heatmap；没有 cohort 起点时不得硬造 retention。

### 泛化 K：Renderer 不支持目标图

验收：按“原生 → 等价变体 → 自定义 → 表格”降级，并保证分析语义不变。


## V3 原样本：Source Role & Authority

完整工作簿包含 11 个 Sheet：

- `users / fiat_transactions / crypto_transactions` → entity / fact；
- `exchange_rates` → reference；
- `expected_fiat_result / expected_crypto_result` → canonical aggregate / reconciliation target；
- `data_rules` → rule / dictionary；
- `qa_result` → QA；
- `fix_log` → fix / audit log；
- `Executive_Dashboard` → dashboard / output；
- `_backup_*` → backup / archive。

验收：

1. dashboard / backup 不得进入业务人口或 KPI；
2. expected 结果只用于对账，不得与原始交易再次累计；
3. `data_rules / qa_result / fix_log` 可以改变口径或可信度，但其记录数不得作为业务指标；
4. `fix_log` 已明确跨币种混同汇总属于历史缺陷，因此原生 currency / asset / network 汇总是 canonical；
5. `144,444 USDT` 仅保留为辅助 snapshot 检查值，不能替代原生单位结果。

## V3 泛化：混合工作簿

输入：

`orders / customers / expected_orders / qa_result / dashboard / _backup_20260101`

验收：

- `orders / customers` 进入业务分析；
- `expected_orders` 用于对账；
- `qa_result` 用于验证；
- `dashboard / backup` 默认排除；
- 不发生重复计数。


## V4 渲染泛化：图例与标签

### 多序列图

两条以上 series 同图时，验收必须有可见图例或直接标签；不得仅靠颜色区分。

### 密集散点

多个点坐标接近时，验收不得出现直接标签覆盖。允许只标关键点，其余通过 tooltip / hover detail 查看。

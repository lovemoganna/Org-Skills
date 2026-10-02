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
- 快照估值：144,444 USDT；
- 法币快照估值：123,074.5 USDT；
- 加密快照估值：21,369.5 USDT；
- active 交易用户：9；
- 法币/加密 completed active 重叠：8 / 9 = 88.89%；
- Top 3 快照估值贡献：83.48%；
- 至少 1 条 `crypto_order_id` 日期与 `created_at` 不一致。

验收：

1. 总金额必须命名为“快照估值”，不能称历史真实成交额；
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

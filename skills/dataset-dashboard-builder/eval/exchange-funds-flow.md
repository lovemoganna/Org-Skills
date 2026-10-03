# Exchange Funds Flow Domain Evaluation

只有在 Exchange Funds Flow Domain Pack 被加载时执行。

## Detection

自动加载本 Pack 时先检查：

- Funds Event Signature 是否成立；
- 是否至少有两类 supporting evidence；
- 是否仅因 `network / asset / channel / status` 等重名字段误判。

Detection 不通过则应回退 generic，而不是进入下面的 Domain Evaluation。

## Critical

任一出现即失败：

- Fiat / Crypto 原生单位被无依据混加；
- processing / confirming 被当作 failed；
- snapshot FX 被称为历史真实成交额；
- 不存在的 address / balance / case / counterparty 被补造；
- flow pattern 被直接定性为 fraud / laundering；
- drill evidence 指向错误订单或错误用户。

## Major

必须修正：

- 页面只有通用 KPI / trend / TopN，看不出资金流领域工作流；
- 当前 Schema 存在 amount + direction + time，却没有 Funds Scale & Trend；
- 只展示状态、channel / network，而没有 amount / count 随时间变化；
- deposit / withdrawal 没有同时检查金额与笔数；
- 未区分 Fiat rail 与 Crypto network；
- rail / network 比较不显示 denominator；
- latency 差异没有 N 或稳健性上下文；
- entity concentration 没有 extreme-driver / confounding 检查；
- investigation mode 没有 Evidence Queue；
- rapid in-out 等序列信号没有落到相关订单；
- 状态结构被压成一个 completion rate，导致 failed 与 in-process 语义丢失；
- 领域问题被当前图表模板反向决定。

## Expected Domain Questions

根据当前 Schema 支持情况，至少判断这些问题是否 applicable：

- Funds Scale & Trend；
- Flow Health；
- Deposit / Withdrawal Structure；
- Entity Exposure；
- Rail / Network Diagnostics；
- Flow Pattern Investigation；
- Evidence Queue。

不 applicable 可以跳过，但必须是因为缺字段 / 缺证据，而不是遗漏。

## Acceptance

通过时必须满足：

1. Domain confidence 有证据；
2. Domain Ontology 与实际 Schema 对齐；
3. 至少一个领域专属工作流真实改变 Dashboard 结构；
4. 通用 Analysis / Investigation 仍然执行；
5. Critical = 0；
6. Major = 0；
7. 所有领域专属异常都能回到真实证据或明确 unavailable；
8. amount + direction + time 存在时，默认视图能直接看到资金规模与时间变化；
9. channel / network 仅在有解释价值时进入主页面。

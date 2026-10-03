# Exchange Funds Flow Domain Pack

适用：中心化交易平台、钱包、支付或类似系统中的法币 / 加密资产资金流分析。

此 Pack 只在 Domain Detection Gate 证明当前数据与该领域匹配时加载。

## 1. Domain Ontology

核心对象候选：

```text
User / Account
├─ identity / KYC / country / account status
├─ Fiat Flow
│  ├─ order
│  ├─ direction: deposit / withdrawal
│  ├─ currency
│  ├─ channel / rail
│  ├─ status
│  ├─ amount / fee
│  └─ created → completed latency
└─ Crypto Flow
   ├─ order
   ├─ direction: deposit / withdrawal
   ├─ asset
   ├─ network
   ├─ status
   ├─ amount / fee
   └─ created → confirmation / completion
```

可能存在但不得假设存在：

- address；
- tx_hash；
- counterparty；
- risk score；
- case / alert；
- source / destination exchange；
- blockchain labels；
- balance；
- account-status effective time。

## 2. Event / State Model

### Fiat

默认事件链：

```text
Created
→ Processing / Pending
→ Completed | Failed | Cancelled
```

只有字段真实支持时才扩展阶段。

### Crypto

默认区分：

```text
Created
→ Confirming / Processing
→ Completed | Failed
```

不得把 confirming / processing 与 failed 混成同一“未完成失败”。

## 3. Domain Question Library

按价值优先考虑，而不是机械全部执行。

### A. Flow Health

- Fiat / Crypto 的处理完成状态如何？
- 未完成记录是失败，还是仍在处理中？
- 哪些 rail / network 出现明显处理摩擦？
- 时延差异是否由单一用户 / 单笔异常驱动？
- 是否存在 backlog 迹象？

### B. Rail / Network Performance

对 channel / network 联合观察：

- N；
- completed share；
- failed / processing / confirming；
- settlement latency；
- amount / frequency（仅单位兼容时）；
- fee / effective fee（数据支持时）。

必须同时保留 denominator 与状态结构。

### C. Entity Exposure

- 资金活动是否集中于少数用户？
- 集中是金额、频率、方向还是资产 / rail 造成？
- 去除 Top1 / Top2 后结论是否成立？
- KYC / country / account status 与集中是否混杂？
- 某群体高占比是否只是少数大实体造成？

### D. Flow Pattern Investigation

仅基于当前数据能证明的事件序列检查：

- rapid in-out；
- same-amount deposit → withdrawal；
- repeated deposits / withdrawals；
- unusual direction imbalance；
- unusual fee ratio；
- cross-rail / cross-network pattern（必须存在可关联语义）；
- temporal burst。

这些只是 investigation patterns，不自动等于欺诈 / 洗钱 / 风险事件。

### E. Evidence Queue

任何重要 Signal 最终应能落到：

```text
Signal
→ Affected entity
→ Relevant order(s)
→ Timeline / context
→ Raw evidence
```

如果缺少 record key，不强制伪造 drill-through。

## 4. Metric Roles

### Primary / Health

数据支持时优先考虑：

- completion / terminal-state mix；
- settlement latency；
- unresolved / in-process count；
- affected users。

### Driver

- channel / network；
- direction；
- currency / asset；
- user / segment；
- amount band；
- time window。

### Guardrail

- sample N / denominator；
- missing / invalid timestamps；
- exact/as-of FX coverage；
- data-quality conflicts；
- unit compatibility。

### Diagnostic

- concentration；
- Top contribution；
- fee ratio；
- rapid reversal interval；
- order-level state timeline。

不要把 snapshot valuation 自动当 Primary KPI。

## 5. Investigation Playbooks

### Rail Friction

```text
Low completion / high latency
→ status mix
→ denominator N
→ user mix
→ direction mix
→ amount distribution
→ remove slowest / largest
→ compare peer rails
→ evidence queue
```

### Entity Concentration

```text
Top share high
→ Top1 / Top2
→ remove extremes
→ frequency vs ticket size
→ asset / currency / rail composition
→ user attributes
→ confounding check
→ entity drill
```

### Rapid In-Out

```text
Deposit → Withdrawal close in time
→ same user?
→ same currency / asset?
→ equal / similar amount?
→ completed states?
→ compare with other reversal intervals
→ materiality
→ raw order evidence
```

结论只能描述 observed flow pattern。没有外部证据不得升级为 laundering / fraud。

### Data-Time Conflict

```text
ID / timestamp / reference-date conflict
→ confirm reproducibility
→ measure affected records
→ identify impacted metric / chart
→ block or annotate affected interpretation
→ evidence record
```

## 6. Domain Composition

不是固定页面模板。

当前数据支持时，优先组合以下工作区：

### Flow Health

适合回答“资金处理是否健康”。

推荐一个紧凑矩阵，而不是大量独立 KPI。

### Rail / Network Performance

推荐：

- performance matrix；
- ranked latency / completion；
- status mix；
- sample N。

### Entity Exposure

推荐：

- concentration curve / ranking；
- entity table；
- composition breakdown；
- robustness note。

### Flow Pattern Investigation

推荐：

- event sequence table / timeline；
- exception queue；
- interval / amount comparison。

### Evidence Queue

用于操作性下钻。

如果 Domain Mission 是 investigation，Evidence Queue 通常比额外一张汇总图更有价值。

## 7. Domain Visual Grammar

优先：

- Status mix: stacked bar / matrix；
- Rail performance: matrix / ranked bar / conditional table；
- Latency: distribution / box / dot / ranked median + N；
- Concentration: Pareto / ranked bar + cumulative share；
- User exposure: sortable table；
- Event sequence: timeline / sequence table；
- Exception evidence: operational table / drawer；
- Flow relation: Sankey 仅在真实 source → target + weight 存在时。

避免：

- 默认 Pie；
- “总资金 USDT”大卡（若 FX 不满足历史估值）；
- 没有 stage semantics 的 funnel；
- 没有 address relation 的 network graph；
- 用地图展示 country 但空间关系无业务意义。

## 8. Action Model

当前数据若只有历史事实，默认动作是：

- inspect；
- compare；
- drill；
- flag for further review；
- request missing context。

除非数据包含 owner / case / workflow 字段，不得伪造：

- assign case；
- freeze user；
- block withdrawal；
- escalate alert；
- close investigation。

## 9. Domain Boundaries

该 Pack 不是 AML / fraud detection engine。

禁止：

- 根据快速进出直接认定洗钱；
- 根据 KYC level 推断风险；
- 根据单个 network completion 差异认定网络故障；
- 根据 frozen 当前状态推断历史交易发生在冻结后；
- 根据 snapshot FX 做历史真实资金规模结论。

所有异常必须继续遵守 Investigation Gate。

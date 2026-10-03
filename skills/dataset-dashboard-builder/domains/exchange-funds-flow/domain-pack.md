# Exchange Funds Flow Domain Pack

适用：中心化交易平台、钱包、支付或类似系统中的法币 / 加密资产资金流分析。

此 Pack 只在 Domain Detection Gate 证明当前数据与该领域匹配时加载。

## 0. Detection Signature

自动识别时，除非用户显式指定本领域，至少满足：

### 必须命中：Funds Event Signature

事实数据中存在真实资金事件语义，至少符合其一：

- `direction = deposit / withdrawal`；或
- 明确的 transfer / deposit / withdrawal event type，并存在 amount + currency / asset。

仅有 `network / channel / asset / status` 字段名不够。

### 并且至少命中两类 Supporting Evidence

- User / account entity；
- currency / asset；
- fiat rail / payment channel；
- blockchain network；
- fee；
- confirmation；
- transaction / order / tx hash / address；
- created → completed lifecycle。

若 Funds Event Signature 不成立，默认不自动加载本 Pack。

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

### A. Funds Scale & Trend

只要存在 `amount + direction + time`，且数据质量允许，这一层默认是资金流看板的第一主轴：

- 完成资金的总金额 / 总笔数是多少？
- 金额与笔数随时间如何变化？
- deposit / withdrawal 分别贡献多少？
- Fiat / Crypto 分别贡献多少？
- 原生 currency / asset 的金额结构是什么？
- 是否存在明显时间段变化，需要继续下钻？
- 高峰是 count 广泛上升，还是少数大额交易导致？
- amount 与 count 是否给出同一信号？
- 典型单笔（median ticket）是否发生变化？
- Top transaction / Top entity 是否主导时间高峰？

**硬规则：**

- 资金看板不能只有状态、channel、network，而缺失 amount / count 的时间变化；
- channel / network 属于诊断维度，不能默认替代资金规模主轴；
- 原生单位不兼容时，金额趋势按 currency / asset 分层；
- 只有通过 Time-dimension Gate 时才允许跨单位汇总；
- 单日 reference FX 只能生成“参考汇率折算 / 快照估值趋势”，不得命名为历史真实成交额；
- snapshot valuation 可以作为辅助比较，不得掩盖原生单位明细。

### B. Flow Health

- Fiat / Crypto 的处理完成状态如何？
- 未完成记录是失败，还是仍在处理中？
- unresolved / in-process 是否影响资金规模解释？
- 状态结构是否随时间变化？

### C. Deposit / Withdrawal Structure

- 入金金额 / 笔数与出金金额 / 笔数如何比较？
- deposit / withdrawal 的时间趋势是否不同？
- 方向差异来自 Fiat、Crypto、currency、asset 还是少数实体？
- amount 与 count 是否给出一致信号？

### D. Rail / Network Diagnostics

只有当主问题需要解释处理性能时再进入：

- channel / network 的 N；
- completed share；
- failed / processing / confirming；
- settlement latency；
- fee / effective fee；
- amount / frequency（仅单位兼容时）。

Rail / Network 默认是 Driver / Diagnostic，不是资金流看板的第一主轴。

### E. Entity Exposure

优先执行 Pareto / concentration，而不是只做 TopN 排名。

- 资金活动是否集中于少数用户？
- 集中是金额、频率、方向还是资产 / rail 造成？
- 去除 Top1 / Top2 后结论是否成立？
- KYC / country / account status 与集中是否混杂？
- 某群体高占比是否只是少数大实体造成？
- Top1 / Top2 / Top5 share 是多少？
- 去掉 Top1 后结论是否仍成立？
- Top transaction share 是否解释了实体集中或月度峰值？

### F. Flow Pattern Investigation

仅基于当前数据能证明的事件序列检查：

- rapid in-out；
- same-amount deposit → withdrawal；
- repeated deposits / withdrawals；
- unusual direction imbalance；
- unusual fee ratio；
- cross-rail / cross-network pattern（必须存在可关联语义）；
- temporal burst。

这些只是 investigation patterns，不自动等于欺诈 / 洗钱 / 风险事件。

### G. Evidence Queue

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

### Primary

数据支持时优先考虑：

- completed amount；
- completed count；
- deposit amount / count；
- withdrawal amount / count；
- amount / count trend over time；
- Fiat / Crypto split。

如果单位不兼容：

- 原生 currency / asset 分层趋势优先；
- 可用 snapshot valuation 时必须显式写“参考汇率折算 / 快照估值”。

### Health / Guardrail

- completion / terminal-state mix；
- unresolved / in-process count；
- affected users；
- settlement latency；
- sample N / denominator；
- missing / invalid timestamps；
- exact/as-of FX coverage；
- data-quality conflicts；
- unit compatibility。

### Driver

- direction；
- Fiat / Crypto；
- currency / asset；
- user / segment；
- channel / network；
- amount band；
- time window。

### Diagnostic

- concentration；
- Top contribution；
- fee ratio；
- rapid reversal interval；
- order-level state timeline；
- rail / network performance。

snapshot valuation 不得冒充 historical actual amount。

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

如果当前数据支持 `amount + direction + time`，默认优先级：

### Funds Scale & Trend

第一主轴。

推荐：

- total amount / count；
- deposit / withdrawal amount / count；
- time trend；
- Fiat / Crypto split；
- native currency / asset amount table；
- snapshot valuation 只作为明确标记的辅助层。

### Flow Health

适合回答“资金处理是否健康”。

优先把 materially large 的 in-process / failed / cancelled 记录转为 Exception Queue，而不是默认画状态构成图。

只有状态分布本身改变业务判断时，才保留紧凑 status structure。

### Deposit / Withdrawal Structure

推荐：

- amount + count 成对出现；
- direction comparison；
- direction trend；
- 必要时继续拆 Fiat / Crypto / currency / asset。

### Entity Exposure

推荐：

- Pareto / cumulative share；
- Top1 / Top2 concentration；
- entity ranking / bar-in-cell table；
- remove-Top1 robustness；
- confounding note。

### Rail / Network Diagnostics

只有主问题需要解释处理性能时再展示。

推荐：

- performance matrix；
- latency / completion；
- sample N。

不得在已有 amount + time 的资金数据上，用 rail / network performance 替代 Funds Scale & Trend。

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

- Funds amount + count over time: 允许一张混合图，但必须确保双轴不制造虚假相关；资金方向分析优先 deposit / withdrawal bars + count line；
- Funds amount over time: line / area；
- Funds count over time: line；
- Deposit vs withdrawal: diverging / grouped bars；
- Native currency / asset amount: table / ranked bar；
- Status mix: 100% stacked / compact status bar / matrix；
- Concentration: Pareto / ranked bar + cumulative share；
- User exposure: sortable table；
- Rail performance: matrix / ranked bar / conditional table（诊断层）；
- Latency: distribution / box / dot / ranked median + N；
- Event sequence: timeline / sequence table；
- Exception evidence: operational table / drawer；
- Flow relation: Sankey 仅在真实 source → target + weight 存在时。

避免：

- 默认 Pie；
- 只有状态和 channel/network、却缺少 amount/count time trend；
- 把不同 currency / asset 直接相加；
- 单日 FX 快照生成“历史真实总额”；
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

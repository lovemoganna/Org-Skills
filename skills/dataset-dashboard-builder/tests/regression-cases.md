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


## V5 原样本：Hypothesis-driven Investigation

### Case：集中度不能停在 Top1 / Top3

Observed Pattern：

- Top1 = 49.93%；
- Top3 = 83.48%。

失败行为：

```text
Top3 很高
→ 结论：用户高度集中
→ 画 Pareto
```

验收：

1. 至少建立两个解释：
   - H1：整体结构性集中；
   - H2：少数极端实体造成表面集中。
2. 去掉 Top1 后重新计算：
   - 剩余第一名仍约占 54.66%。
3. 去掉 Top2 后：
   - 剩余第一名约占 27.22%。
4. 结论不能写成“由单一大户造成”；应收紧为“当前样本主要由前两名实体驱动，前两名移除后集中度明显下降”或同义事实表达。
5. Pareto 只能表达 Pattern，不能替代 Robustness。

### Case：KYC3 占 77.30% 不能直接解释成 KYC 效应

Observed Pattern：

- KYC Level 3 两个用户贡献约 77.30%。

验收：

- 必须检查这两个用户是否本身就是 Top1/Top2；
- 如果 KYC3 与大户身份完全重合，状态保持“entity concentration 与 KYC level 混杂”；
- 禁止写“KYC3 用户价值更高”；
- 若没有更大样本或可比用户，Hypothesis 保持 unresolved。

### Case：ACH 时延必须排除单点异常

Observed Pattern：

- ACH completed median ≈ 18.375h，N=4。

验收：

- 检查分布与最慢记录；
- 去掉最慢一笔后，中位时延仍约 16.75h；
- 按用户拆分：两个用户都表现出较高时延，但样本仍小；
- 结论只能写“当前 ACH 样本持续偏慢，且不完全由单一最慢订单解释”；不得写“ACH 渠道导致慢”。

## V5 泛化

### 泛化 L：Pattern 不能直接晋级

任意 TopN、成功率差异、群体占比或趋势峰值第一次出现时：

- 只能标 Pattern；
- 必须建立 H1/H2；
- 没有 Diagnostic Test / Robustness 时不得进首屏 Finding。

### 泛化 M：Result 必须改变 Frontier

如果一条查询只是增加一个新的描述切片，但不会改变解释、口径、优先级或下一步：

- 默认淘汰；
- 不得为了“分析完整”执行并画图。

### 泛化 N：数据不足保持 unresolved

只有聚合结果，没有明细支撑竞争解释时：

- 保留 Pattern；
- 明确缺少什么数据；
- 不得为了通过 Finding Promotion Gate 编造 Why。


## V6 原样本：显式四表范围

工作簿实际包含额外 expected / rule / qa / dashboard / backup Sheet。

用户明确要求：

`只使用 users / fiat_transactions / crypto_transactions / exchange_rates`

验收：

1. 可以读取 workbook metadata 确认 Sheet 名；
2. 只读取四张指定表的内容；
3. 不得读取或引用 `data_rules / expected_* / qa_result / fix_log / Executive_Dashboard / _backup_*` 的内容；
4. 历史 regression 中已知这些表存在，也不得把其规则偷偷带入当前分析；
5. 若四表本身不足以定义某项口径，只能标记 LIMITED / MISSING INPUT，不得擅自扩表。

## V6 泛化：显式子集覆盖 Full-dataset Scan

输入工作簿：

`orders / users / prices / qa / expected / dashboard`

用户只允许：

`orders / users`

验收：

- 分析只消费 orders / users；
- prices 缺失造成的估值问题应标记 missing input；
- 不得因为 prices 实际存在就越界读取；
- qa / expected / dashboard 不参与分析。


## V7 原样本：Priority & Portfolio Synthesis

### Case：稀有不等于首屏重要

当前四表中：

- Gabriel 的 2,500 BRL completed deposit → withdrawal 间隔约 0.5h；
- 按 2024-09-01 reference-rate snapshot，2,500 BRL ≈ 455 USDT；
- 约占 144,444 USDT 辅助 snapshot 总观察量的 0.32%。

验收：

- 可以识别为异常序列；
- 因影响窄、动机 unresolved，默认归为 P2 Secondary Lead；
- 不得仅因“唯一 / 30 分钟 / 等额”就排在集中度、处理摩擦或数据可信度之前；
- 如果另一个数据集中的小金额异常会阻塞合规/控制或使核心指标失真，允许按 Decision Dependency / Control Severity 升级，不能机械按金额降级。

### Case：集中度与 KYC 表象必须综合

当前样本：

- Top2 reference-rate snapshot share ≈ 77.30%；
- Top2 两个用户恰好都是 KYC3；
- 因此 KYC3 share ≈ 77.30%。

验收：

- 不得生成“集中度高”和“KYC3 用户价值高”两张独立核心卡片；
- 必须综合为同一主线：当前 KYC3 高占比与 Top2 实体集中完全混杂；
- KYC effect 保持 unresolved；
- Executive Thesis 的主语应是 entity concentration，而不是未经识别的 KYC effect。

### Case：首屏必须形成 Thesis

当前样本至少应区分：

1. P0/P1：数据可信度 / 核心趋势依赖；
2. P1：实体集中与混杂；
3. P1：ACH 样本内处理摩擦；
4. P2：快速 BRL 回转等窄影响线索。

验收：

- 首屏不是 4 个同权 Finding；
- 默认压缩为少量 Executive Thesis；
- Secondary Lead 下沉。

## V7 泛化

### 泛化 O：小而醒目的异常 vs 广泛但不醒目的问题

数据同时存在：

- 1 条极端异常，占总体 0.1%，证据弱；
- 一个影响 40% 对象的流程问题，证据强。

验收：流程问题优先；极端异常保留 Secondary Lead。除非极端异常具有阻塞性/高控制严重性。

### 泛化 P：同一驱动产生多个 Finding

某地区占比高、某产品占比高，但两者完全由同一批 3 个大客户驱动。

验收：

- 合并为“少数客户驱动的结构表象”；
- 地区 / 产品只作为 supporting evidence；
- 不得重复占用首屏。

### 泛化 Q：小样本但阻塞分析正确性

只有 1 条日期错误，却单独制造一个新月份峰值。

验收：

- 虽然行数少，因其改变趋势判断，可按 Decision Dependency 提升为 P0/P1；
- Candidate Triage 不能退化成纯金额/行数排序。


### Adversarial R：显式目标不能被全局 Materiality 覆盖

用户明确要求：

`只调查某个小额异常序列是否成立及其解释`

同时数据中存在一个影响范围更大的无关流程问题。

验收：

- Candidate Triage 先服从用户显式目标；
- 小额异常不能仅因全局金额/覆盖面较小被跳过；
- Materiality 用于该目标内部判断调查深度与措辞；
- 无关的大范围问题可作为旁注，不得抢走主分析路径。


## V8 原样本：Dashboard Quality

当前四表样本存在稳定对象键 `uid / fiat_order_id / crypto_order_id`，且核心任务包括异常识别、原因解释和对象验证。

失败基线：

- HTML 有 Thesis / Evidence / Context / Secondary Lead；
- 但主要是长滚动阅读；
- 没有用户可用的筛选、对象定位、跨模块联动或下钻；
- Supporting Evidence 更像报告章节，不形成“总览 → 解释 → 对象 → 明细”工作路径。

验收：

1. 先建立 Dashboard Mission Contract；
2. 首屏必须同时出现：
   - 当前状态；
   - 1–3 个最高优先级问题；
   - 明确的继续分析入口；
3. Information Architecture 必须形成 `What → So What → Why → Who/Where → Evidence`；
4. 至少提供一个有分析价值的筛选或对象选择；
5. 至少提供从核心问题到用户 / 订单 / 交易证据的下钻路径；
6. 筛选后相关 KPI / 图 / 表使用一致范围；
7. 长篇解释不得成为主要交互方式；
8. Dashboard Quality Evaluation 必须达到 Critical=0 / Major=0。

## V8 泛化

### 泛化 S：有稳定对象键的调查型数据集

输入：

`customers / orders / events`

存在 `customer_id / order_id`，用户目标是定位异常订单。

验收：

- 静态汇总不足；
- 必须支持至少一种对象定位 / drill-down；
- 详情必须回到原始订单或事件。

### 泛化 T：纯静态汇报任务

用户明确要求：

`生成一页静态管理层汇报，不需要交互`

验收：

- 不强制筛选 / drill-down；
- 仍必须满足信息架构与数据真实性；
- Interaction Gate 正确豁免。

### 泛化 U：漂亮但无业务链路

页面有渐变、卡片、动画、8 个图，但无法说明主要业务问题或下一步动作。

验收：

- 评为 Major；
- 不能因视觉完成度高而通过。

### 泛化 V：长报告不是 Dashboard

页面有正确结论和图表，但需要连续滚动阅读大量解释才能理解，且没有状态→异常→定位路径。

验收：

- 评为 Major；
- 必须重构 Information Architecture，而不是只改颜色和间距。

### Adversarial W：不要固定六模块模板

数据只有简单 SLA 监控，无可用实体层级，也没有合理的“原因→对象”链。

验收：

- 不强行生成状态 / 趋势 / 异常 / 解释 / 定位 / 下钻全部模块；
- 只保留任务真正需要的模块；
- Dashboard Framework 是功能语义，不是页面模板。


### V8 Rendered QA：移动端控制区

当桌面使用 sticky filter bar 时：

- 390px 等窄屏不得让完整筛选区长期固定并挤压主要分析内容；
- 应折叠、收起或取消 sticky；
- 允许筛选区在页面顶部正常占位；
- 禁止用缩小字体来掩盖控制区过高问题。


## V9 原样本：Dashboard Context / Comparison / Drill

当前 V8 HTML 暴露以下失败：

1. 页面使用“当前状态”，但四表数据横跨历史日期，且没有当前 as-of；
2. `Dashboard Quality Evaluation` 被直接展示给最终用户；
3. 点击“定位异常记录”后，只选中对应用户，详情默认仍停在 Fiat，未落到异常 crypto record；
4. 点击“查看 ACH 明细”后，只选中一个用户，详情展示该用户全部 Fiat，而不是 ACH evidence；
5. Fiat completed / Crypto completed 作为两个独立 KPI Card，比较语境不够明确。

验收：

- Mission Contract 包含 Audience / Mode / Decision / Population / Period / Comparison / Cadence；
- 页面把无当前语义的数据称为 scope snapshot / 范围状态，并显示日期范围；
- Quality Evaluation / Hypothesis / Regression 不作为最终页面模块；
- 日期异常 drill-through 直接进入对应 crypto record 或包含该记录的正确证据视图；
- ACH drill-through 保留 `channel=ach` 与 `status=completed` 上下文；
- Completed 比较在同一视图中同时可见，显示差异；不要求用户切 Filter 比较；
- Context / Diagnostic 指标不得与 Primary KPI 自动同权。

## V9 泛化

### 泛化 X：跨 tab drill-through

Dashboard 发现一条 payment 失败，但用户详情默认打开 profile tab。

验收：

- 点击失败信号后直接进入 payment / failure evidence；
- 不得只打开该用户 profile。

### 泛化 Y：Filter 不能替代核心比较

用户任务是比较 Region A 与 Region B conversion。

验收：

- A/B conversion 同时可见；
- 不能只提供 region 下拉框让用户来回切换记忆。

### 泛化 Z：没有当前语义

输入历史离线样本，用户未声明 as-of / refresh cadence。

验收：

- 不使用“实时 / 当前 / 今日”作为无依据语义；
- 明确数据覆盖期或 scope snapshot。

### 泛化 AA：内部评价不外露

生成流程包含 QA / evaluation / regression。

验收：

- 最终 Dashboard 默认不出现 “Quality Evaluation / Regression Passed / Hypothesis Frontier” 等内部模块；
- 只有用户明确要求审计时才展示。

### Adversarial AB：显式审计模式

用户明确要求：

`把 Dashboard 的质量评估和失败项也展示在页面里`

验收：

- Internal Analysis Boundary 正确豁免；
- 可以展示 Evaluation，但必须与业务 Dashboard 主区分开。


## V10 原样本：Exchange Funds Flow Domain Intelligence

当前四表：

- `users`；
- `fiat_transactions`；
- `crypto_transactions`；
- `exchange_rates`。

### Domain Detection

支持证据：

- Entity：user / KYC / country / account status；
- Event / State：fiat / crypto orders，deposit / withdrawal，completed / failed / processing / confirming；
- Dimension：currency / channel / asset / network / fee / completion time。

验收：

- Domain = `exchange-funds-flow`；
- Confidence = high；
- 加载 `domains/exchange-funds-flow/domain-pack.md`；
- 不把该领域自动升级成 AML / fraud。

### Domain Composition

原 generic 失败行为：

```text
Completed KPI
+ concentration
+ latency
+ trend
+ user detail
```

V10 必须至少重组为当前数据支持的领域工作区：

1. **Flow Health**：Fiat / Crypto 状态结构，不只显示 completed rate；
2. **Rail / Network Performance**：channel / network 的 N、状态、latency 等同屏；
3. **Entity Exposure**：Top concentration + user attributes / composition；
4. **Flow Pattern Investigation**：rapid in-out 等已验证序列候选；
5. **Evidence Queue**：Signal → User → Order evidence。

不是所有工作区必须同等权重。

### Domain Accuracy

验收：

- processing / confirming 与 failed 分开；
- Fiat channel 与 Crypto network 分开；
- snapshot FX 不作为历史真实成交额；
- rapid in-out 不写成洗钱 / 欺诈；
- 当前存在 address / tx_hash，可在订单 Evidence 中展示；但没有明确 address-to-address 关系图数据时，不生成链上 network graph；
- 没有 case / owner 时，不生成 assign / freeze / close 等动作。

## V10 泛化

### 泛化 AC：客服 SLA 数据

输入：

`tickets / agents / sla_rules`

具有 ticket state / priority / agent / SLA duration，但没有 payment / asset / network。

验收：

- 不加载 exchange-funds-flow；
- generic 或未来 support domain；
- 不残留 rail / network / KYC / flow pattern。

### 泛化 AD：只有 crypto-like 字段但缺资金事件语义

输入：

`events(id,user_id,network,status,created_at)`

没有 deposit / withdrawal、amount、currency / asset，也没有明确资金流任务。

验收：

- Funds Event Signature 不成立；
- 不自动加载 exchange-funds-flow；
- 不机械生成 rapid in-out / concentration / fee analysis。

### 泛化 AE：用户明确指定 generic

即使 Schema 很像资金流，用户要求：

`只做通用数据探索，不使用行业假设`

验收：

- 不加载 Domain Pack；
- generic pipeline 正常工作。

### Adversarial AF：字段名伪装

输入：

`marketing_network / asset_name / channel_name`

但事实表实际是广告 campaign performance。

验收：

- 不能仅凭 network / asset / channel 字段名判定 exchange funds flow；
- Entity + Event-State + Dimension 证据不足时回退 generic。


## V11 原样本：Semantic Field Catalog → Analysis Spec → Chart.js

当前四表必须先生成统一字段语义。

### Field Catalog

至少识别：

- `uid / fiat_order_id / crypto_order_id` → identifier；
- `created_at / completed_at / effective_date` → temporal；
- `channel / network / direction / country_code` → categorical；
- `status` → state；
- `currency / asset` → unit / categorical；
- `amount / fee` → continuous_numeric；
- `confirmations` → discrete_numeric。

验收：

- `uid` 虽为数值，也不得生成 `SUM(uid)`；
- order id 不得进入 Y axis；
- amount 只有在单位兼容时才允许 SUM；
- rate / percentage / snapshot 不得机械 SUM。

### Spec A：时间 + 指标

问题：

`Fiat 记录量如何随时间变化？`

预期：

- intent = `trend`；
- temporal dimension = `created_at`；
- measure = `COUNT(fiat_order_id)`；
- time grain 根据当前跨度动态选择，不写死在组件；
- Chart.js = `line`；
- X = time bucket；
- Y = order count；
- 不出现“异常 / 风险”作为 chart intent。

### Spec B：分类 + 指标

问题：

`不同 channel 的 completed settlement latency 如何比较？`

预期：

- intent = `category_comparison`；
- dimension = `channel`；
- filters = `status = completed`；
- measure = median latency；
- aggregation = `MEDIAN`；
- Chart.js = horizontal `bar`；
- 排序按 median latency DESC；
- N 必须可同时查询或作为 tooltip / table context。

### Spec C：两个连续数值

问题：

`Fiat amount 与 fee 的关系如何？`

预期：

- intent = `relationship`；
- X = amount；
- Y = fee；
- point identity = `fiat_order_id`；
- optional Series = direction；
- Chart.js = `scatter`；
- 禁止先 SUM(amount) / SUM(fee) 再画一个点。

### Spec D：数值分布

问题：

`Completed Fiat amount 如何分布？`

预期：

- intent = `distribution`；
- measure = amount；
- 在单位不兼容时必须先按 currency 分层或选择单一 currency；
- SQL 层生成 histogram bin；
- Chart.js 使用 bar 渲染 bins；
- Renderer 不得自己重新分箱。

### Spec E：实体 / 原始记录

问题：

`查看 Crypto 原始订单明细`

预期：

- intent = `detail`；
- 使用 table；
- `crypto_order_id` 作为 identifier；
- 不生成数值轴；
- 记录排序按业务时间；
- table 与 chart 共用统一 Filter State。

### Query Ownership

验收：

```text
Analysis Spec
→ DuckDB SQL
→ Result Contract
→ Chart.js Spec
```

- KPI / Chart / Table 不得自行拼 SQL；
- 全局筛选必须 patch Analysis Spec 后重新执行；
- X/Y/Series/TopN/time grain 不能写死在组件；
- Chart.js config 不能从原始 Schema 临时猜列。

## V11 泛化

### 泛化 AG：数值 ID

输入：

`customer_id BIGINT / order_id BIGINT / revenue DOUBLE / segment VARCHAR`

验收：

- customer_id / order_id = identifier；
- 允许 COUNT DISTINCT；
- 禁止 SUM / AVG ID；
- revenue 才是 measure。

### 泛化 AH：Series 基数过高

输入：

`date / revenue / product_id`，product_id 有 500 个值。

验收：

- 不自动生成 500 条折线；
- Planner 必须选择 TopN / filter / small multiples / no series；
- Renderer 不得自行截断到任意前 10 个。

### 泛化 AI：Non-additive Rate

输入：

`region / conversion_rate / converted / eligible`

验收：

- 优先 `SUM(converted) / SUM(eligible)`；
- 禁止 `SUM(conversion_rate)`；
- 除非 metric definition 明确，否则不得简单 AVG conversion_rate。

### 泛化 AJ：动态时间粒度

输入 A：3 天分钟级事件。
输入 B：5 年月度业务数据。

验收：

- 两者不能都写死 month 或 day；
- time grain 根据跨度、自然 cadence、数据密度与问题生成；
- 用户明确粒度时优先用户要求。

### 泛化 AK：同一指标跨组件

一个 KPI、趋势图和明细表都引用 `completed_share`。

验收：

- 三者引用同一 measure definition；
- 不允许 KPI 用 completed/total、图表用 AVG(row_rate)、表格又用另一状态集合。

### Adversarial AL：组件自行查询

某 Chart.js 组件内部出现：

`duckdb.query(...)` 或自行拼 `SELECT ...`

验收：

- 判失败；
- 查询必须上收 Analysis Engine；
- 组件只消费 Result Contract。

### Adversarial AM：伪数值字段

输入：

`postal_code INTEGER / sku_code BIGINT / risk_level_code INTEGER`

验收：

- 不能仅凭 numeric type 当 continuous measure；
- 根据语义识别为 categorical / identifier / ordinal / unknown；
- 未确认语义时不得 SUM。


## V12 原样本：Funds Scale & Trend → Renderer Contract

同一 `exchange_funds_flow_dataset`，只要 `amount + direction + created_at` 可用，资金流看板默认主轴必须先回答资金规模与时间变化。

当前四表在 completed + reference FX snapshot 口径下，数学锚点：

- completed 总笔数：43；
- 参考汇率折算总额：144,444 USDT；
- 入金参考折算：105,874.5 USDT，24 笔；
- 出金参考折算：38,569.5 USDT，19 笔；
- 月度时间序列至少覆盖 2024-12 → 2026-01；
- 2025-01：56,642.5 USDT / 6 笔；
- 2025-06：30,530 USDT / 3 笔；
- 2026-01：500 USDT / 1 笔。

注意：这些跨币种结果仍然只是 `reference-rate / snapshot valuation`，不是历史真实成交额。

### Primary Axis 验收

默认页面至少能直接看到：

1. total amount；
2. deposit amount；
3. withdrawal amount；
4. completed count；
5. amount over time；
6. count over time；
7. deposit / withdrawal split；
8. native currency / asset amount detail。

失败条件：

- 有 amount + time，却只展示 completion / status / channel / network；
- Rail / Network Performance 占据主位，而 Funds Scale & Trend 缺失；
- 只有笔数趋势，没有金额趋势；
- 只有总额，没有随时间变化；
- 只有统一 USDT，没有原生 currency / asset 明细。

### Snapshot 口径验收

- 单日 exchange_rates 可以用于“参考汇率折算趋势 / 快照估值趋势”；
- 不得命名为历史真实成交额；
- 标题、KPI、tooltip / data window 必须保持 reference / snapshot 限制；
- 若业务规则禁止跨单位汇总，则 canonical 主结果仍按原生单位分层。

### Renderer Contract 验收

唯一链路：

```text
Analysis Spec
→ DuckDB SQL
→ Result Contract
→ Visual Spec
→ Renderer Adapter
```

- Renderer 不得直接查 DuckDB；
- Renderer 不得修改 aggregation / time grain / TopN；
- 用户明确指定 Vela 时，资金时间序列可使用 Vela；
- Vela 默认消费离线 Result，不自动连接 Binance / Coinbase / Hyperliquid；
- 业务单值时间序列不得伪装成真实 OHLC K 线；
- amount / count 两图共享时间域时应支持 crosshair sync；
- range / zoom / pan 只改变视图，不改变业务口径；
- Vela 不适合的 status / table / simple ranking 可以使用 Native HTML / CSS；
- generic category / distribution / relationship 可使用 Chart.js Adapter。

### 中文与 UI Copy 验收

中文任务：

- UI 主语言为中文；
- 允许 ACH / USDT / Tx Hash / UID 等必要术语；
- 不显示 `Analysis Spec / Compiler / Regression / Generated by` 等开发文案；
- 不在每个 Panel 重复“点击可筛选”等教程式废话；
- 统一交互说明只保留最小必要信息。

### Label 验收

如果用户要求 permanent Label：

- vertical bar → 柱顶外侧；
- horizontal bar → 柱尾外侧；
- line / point → 点位上方；
- label 不得与 mark / axis / legend 重叠；
- 必须有 padding / collision avoidance；
- Tooltip 不能替代 permanent Label。

### Interaction 验收

- 点击同一筛选值可取消；
- selected state 可见；
- 图表、KPI、表格共享 Global Filter State；
- table row selection 与 chart selection 语义一致；
- crosshair sync 不应偷偷变成 filter。

## V12 泛化

### 泛化 AN：资金数据但错误主轴

输入：

`payments(id, user_id, direction, currency, amount, status, created_at, channel)`

验收：

- amount + count + time 为一级候选；
- channel 只能作为 driver / diagnostic；
- 不得默认生成“Channel Performance Dashboard”取代资金规模趋势。

### 泛化 AO：多币种无可用 FX

输入多个 currency / asset，但没有合法 exact / as-of / snapshot 规则。

验收：

- amount trend 按原生单位分层；
- count 可以跨单位汇总；
- 不生成 fake unified amount total。

### Adversarial AP：Renderer 偷算业务口径

Vela / Chart.js / HTML component 内出现原始 rows 聚合或 `SUM` 等重新计算。

验收：失败。必须回到 Analysis Engine / Result Contract。

### Adversarial AQ：Vela 自动接行情

用户数据是离线业务资金流水，但 Vela Adapter 自动连接 Binance / Coinbase / Hyperliquid。

验收：失败。除非 Mission 明确需要市场行情，否则必须使用离线 Result。

### Adversarial AR：中文任务英文 UI

最终页面大量出现 `Flow Health / Activity Trend / Evidence Queue / Completed share`，而用户未要求英文。

验收：失败。业务 UI 应中文优先。

### Adversarial AS：永久 Label 与图形重叠

用户明确要求永久 Label，但柱体 / 点位与文字重叠或被 canvas 边缘裁切。

验收：失败。必须外置、避让或更换同语义表达。


## V13 原样本：Redundancy Gate

基于同一 exchange_funds_flow_dataset，已知 V12 曾出现以下冗余：

- 总额 / 入金 / 出金先在 KPI 出现，又在双趋势图、永久 Label 条、逐月明细表重复；
- amount trend 与 count trend 使用两张同构 Vela 图；
- 用户集中度同时出现 ranking bar 与相同实体 table；
- Flow Pattern Signal 卡片与 Evidence Queue 表达同一异常。

### 验收

默认页面应压缩为不超过 5–6 个主要工作区，并优先形成：

```text
概览
→ 单一主趋势（metric / direction 可切换）
→ 资金结构
→ 用户集中
→ 核查队列
```

要求：

- amount / count 可以在一个趋势视图切换，不要求并排双图；
- total / deposit / withdrawal 可以在同一趋势视图切换；
- permanent label 已提供逐期数值时，不额外生成重复 totals table；
- 用户 ranking 与 exact lookup 能合并成 bar-in-cell table 时，不保留第二张 ranking 图；
- anomaly signal 与 evidence detail 合并到同一 Queue；
- status 只保留一个主组件，不同时堆叠 status KPI + summary + bar。

### 泛化 AT：同构趋势复制

输入 revenue / orders / date，两个指标可以通过 metric selector 在同一时间图查看。

验收：默认不因为“两个指标”就生成两张完全同构图；只有需要同时比较、不同单位同屏有明确价值时才保留多图。

### 泛化 AU：Chart + Table 重复

一张 Top10 bar 和一张同字段、同排序、同数值的 Top10 table。

验收：判重复；除非 table 增加 entity attributes、exact lookup 或操作入口，否则删除其中一个。

### Adversarial AV：说明文案复制

每个 panel 都写“点击图表可筛选”。

验收：失败；统一为一处必要交互提示或通过显著 hover/selected state 自解释。


## V14 原样本：Dashboard Audit Loop

基于 exchange_funds_flow_dataset 与前序多轮 Dashboard 调试，新增生成前 / 生成后的自动审查契约。

### Decision Questions

默认页面必须先压缩成 2–5 个问题，例如：

1. 范围内资金规模是多少？
2. 资金规模与笔数随时间如何变化？
3. 资金集中在哪些实体？
4. 哪些记录值得继续核查？

验收：

- 每个 section 只能对应一个主 job；
- 每个主组件必须服务至少一个问题；
- 组件不能说明回答哪个问题 → 删除；
- 一个问题默认只有一个 Primary View。

### Coverage Plan

至少覆盖：

- kpi-turnover
- kpi-net
- trend-funds
- filter-date
- filter-direction
- entity-concentration
- queue-evidence

要求：

- required 项必须全部渲染；
- 未计划组件必须回写新问题或删除；
- 不允许“AI 顺手加的图”。

### Simplest Primitive

- 单一水平优先 KPI；
- 精确明细优先 table；
- 简单排名可 bar-in-cell；
- 普通业务趋势无需伪装 K 线；
- advanced visual 必须证明新增分析价值。

### User Simulation

必须至少覆盖：

- Real User：默认打开 → 判断资金规模 → 看趋势 → 定位实体 → 查看证据；
- Constrained：360px 或 keyboard-only；
- Edge Data：empty / long label / extreme value 至少一种。

### Rendered Audit

能渲染时检查 360 / 768 / 1280：

- 无整页横向 overflow；
- filter 不长期占满视口；
- KPI baseline 一致；
- input / select / button 同行高度一致；
- section left edge / gutter 一致；
- chart label 无裁切 / 重叠；
- dark / light 状态连续。

不能渲染时必须标记 rendered visual check unavailable，不得只跑 node --check 就声称 UI 已验收。

### 泛化 AW：孤儿组件

计划只有 KPI / trend / entity table，最终 HTML 多出 donut 与“智能洞察”卡片。

验收：失败。除非新增 Decision Question 并证明独立价值，否则删除。

### 泛化 AX：复杂度升级无理由

3 个分类值用 3D donut / custom WebGL visual。

验收：失败。Simplest Primitive Guard 应选择简单 bar / compact status / table。

### Adversarial AY：源码检查冒充视觉检查

只执行 HTML parse + node --check，最终声称“视觉验收通过”。

验收：失败。必须明确区分 source/static QA 与 rendered visual QA。

### Adversarial AZ：正常数据可用，边界数据破版

默认数据正常，但 empty / long label / 360px 时控件溢出或页面断裂。

验收：失败。Edge-data + constrained simulation 是 required。


### Adversarial BA：无 overflow 但图表被压扁

360px 下页面没有整页横向 overflow，但 12 个时间点被强行缩放到 300px 宽，tick / label 无法读取。

验收：失败。响应式检查必须同时验证 plot 可读性；优先使用组件内部横向滚动、减少可见点数或提高时间粒度，而不是把图整体缩小到不可读。


## V15 原样本：Insight Hierarchy → High-Value Funds Dashboard

同一 exchange_funds_flow_dataset，目标不再只是“生成正确看板”，而是验证看板是否能从规模进入驱动、集中度、例外与证据。

### North Star

completed + reference FX snapshot 口径：

- 总流水：144,444 USDT；
- 净流入：+67,305 USDT；
- completed：43 / 50；
- 入金：105,874.5 USDT；
- 出金：38,569.5 USDT。

### Amount × Count Dual Signal

Fiat：

- 金额：123,074.5 USDT；
- 金额份额：85.21%；
- completed count：21；
- count share：48.84%；
- median ticket：1,542 USDT。

Crypto：

- 金额：21,369.5 USDT；
- completed count：22；
- median ticket：650 USDT。

验收：

- 不能只写“Fiat 流水更高”；
- 必须指出 Fiat 的金额份额明显高于笔数份额，并继续检查 ticket size；
- 当前样本支持“Fiat 大额单笔驱动更多”的描述，不支持由 flow type 本身导致的因果结论。

### Event-Driven Spike

重要高峰月：

- 2025-01：56,642.5 USDT / 6 笔；Top1 transaction share = 88.27%；
- 2025-02：13,442.5 USDT / 4 笔；Top1 transaction share = 89.27%；
- 2025-06：30,530 USDT / 3 笔；Top1 transaction share = 81.89%；
- 2025-09：11,542.5 USDT / 4 笔；Top1 transaction share = 86.64%。

验收：

- 不得把这些峰值写成“广泛增长 / 活跃度提升”；
- 应写成“少数大额交易 / 单笔事件驱动的金额峰值”；
- 必须保留对应 transaction / user 的 evidence path。

### Pareto / Concentration

- Top1 user：49.93%；
- Top2 users：77.30%；
- Top2 transactions：51.92%；
- Top5 transactions：70.62%。

验收：

- 用户集中度必须至少展示 Top1 / Top2 或 Pareto cumulative share；
- KYC3 高占比若主要来自两个 Top 用户，不能写成“KYC3 用户整体更高价值”；
- 应表达为“资金集中于两个用户；这两个用户恰好都是 KYC3，当前数据不能证明 KYC 等级驱动高金额”。

### Operational Exceptions

in-process = pending / processing / confirming：

- 4 笔；
- 参考快照估值合计：11,392.5 USDT；
- 其中 10,000 USD pending deposit 为 materially large 单笔。

terminal non-completion = failed / cancelled：

- 3 笔；
- 参考快照估值合计：825.5 USDT。

验收：

- in-process 与 failed / cancelled 必须分开；
- 10,000 pending 应进入 Exception / Queue 或 Guardrail；
- 不能只把 4 笔未终态压成一个状态百分比。

### High-Value Acceptance

默认看板必须能回答：

1. North Star 是多少；
2. 金额 / 笔数如何变化；
3. 峰值来自 breadth、intensity 还是 concentration；
4. 哪些用户 / 交易贡献最大；
5. 哪些 exception 值得继续查；
6. 能否下钻到真实记录。

如果只能回答 1–2，V15 判失败。

### 泛化 BB：金额涨、笔数平

输入：

- amount 明显上涨；
- count 基本不变；
- 少数 top transaction 增大。

验收：

- 必须继续检查 ticket size / top transaction share；
- 不得直接写“业务活动全面增长”。

### 泛化 BC：标签被少数实体混淆

输入：

某 segment 占 75% 金额，但该 segment 的金额几乎由 2 个实体贡献。

验收：

- 先表达 entity concentration；
- segment 只能作为 confounded context；
- 不得把 segment 标签写成驱动因素。

### 泛化 BD：高金额未终态

输入：

总订单 100 笔，只有 2 笔 pending，但 pending amount 占 completed turnover 的 25%。

验收：

- 不能因为 count 低就降级；
- 必须按 material amount 进入 Guardrail / Exception；
- next check 要落到具体记录。

### Adversarial BE：把单笔峰值写成增长

月度 turnover 暴增，但 top1 transaction share > 80%，count 未同步增加。

验收：失败。必须改为 event-driven spike / concentration 表达。

### Adversarial BF：KYC 伪驱动

KYC3 占比高，但去掉 Top2 用户后差异消失。

验收：失败。不得写“KYC3 驱动高流水”。

### Adversarial BG：只有 Level + Trend

页面只有 KPI + 时间趋势，虽然数字都正确，但没有 driver / concentration / exception / evidence。

验收：不能称为 high-value dashboard。


## V16 原样本：Decision Diagnostics / Multi-Architecture

### 原失败 A：低金额月份被误称高峰

若某时间桶流水很小，但最大单笔占该桶 90%+：

- 不得仅因 Top1 share 高进入“高峰月”；
- 必须先比较该桶 turnover / count 对 North Star 的 materiality；
- 只有 materially important 的候选时间桶再进入 Event-Driven Spike。

验收：低金额高占比只可写“桶内高度集中”，不得写“重要高峰”。

### 原失败 B：自造 5000 USDT 优先级

没有用户规则 / policy / SLA / benchmark 时：

```text
> 5000 USDT → 优先
< 5000 USDT → 关注
```

验收：失败。

正确：按 relative materiality + control severity + evidence strength + actionability 排序，并解释依据。

### 泛化 BH：当前最大不等于变化贡献最大

某 Segment A 当前金额最大，但本期 vs 上期几乎不变；Segment B 规模较小但贡献了 80% 的增长。

验收：变化解释必须把 B 作为主要 delta contributor，不能只展示 A 的 TopN。

### 泛化 BI：Partial Bucket 假异常

最后一个日 / 周 / 月时间桶尚未完整，数值显著低于上一完整桶。

验收：不得写“暴跌”；必须标记 partial / incomplete 或排除不可比桶。

### 泛化 BJ：反证改变结论

“金额上涨”由单一 Top1 entity 驱动；remove-Top1 后上涨消失。

验收：结论必须改为 entity-concentrated / event-dependent，不得写 broad-based growth。

### Adversarial BK：无业务阈值却画红线

模型为了“专业”自行生成 10k / 20% / 3σ 作为业务风险线。

验收：失败。统计阈值最多标 analytical trigger，不能伪装 business rule。

### Adversarial BL：五个 Dashboard 只是换色

五个候选拥有相同 section order / primary view / decision path，只改变 palette / 卡片 / chart theme。

验收：失败。

正确候选必须共享 metric definitions，但至少在 audience / primary job / question ordering / exploration depth / evidence placement / interaction model 中一项结构性不同。


## V17 原样本：Remote Skill × Remote Requirement Evaluation Preflight

### 原失败 A：Requirement 声明 Canonical Fixture，但仓库只有数学锚点

输入：

- Requirement 要求 users / fiat_transactions / crypto_transactions / exchange_rates；
- 仓库只有 144,444 / 77.30% 等数学结果，没有原始行。

验收：

- Real-data Case = `BLOCKED_FIXTURE`；
- 不得把锚点直接写进 Dashboard 后声称真实回归通过；
- 缺陷 Owner = Requirement / Fixture，不是 Skill 分析逻辑。

### 原失败 B：浏览器超时

输入：

- HTML parse / JS syntax PASS；
- Chromium / screenshot 无法运行。

验收：

- Static QA 可 PASS；
- Rendered QA = `BLOCKED_ENV`；
- Overall 不能 Full PASS；
- 不得把浏览器环境问题标成 Skill FAIL。

### 泛化 BM：SQL runtime 缺失

Requirement 明确要求验证 DuckDB SQL chain，但环境没有 DuckDB。

验收：

- DuckDB execution Case = `BLOCKED_ENV`；
- 可以独立重算数学结果作为辅助 evidence；
- 不得声称 DuckDB SQL 已执行。

### 泛化 BN：条件型 Case 未触发

Requirement 包含 Multi-Architecture Test，但本轮用户只要求生成一个 Dashboard。

验收：

- Case = `NOT_APPLICABLE`；
- 不计入 PASS / FAIL 分母；
- 不得标为 UNVERIFIED 或 FAIL。

### 泛化 BO：核心逻辑通过但视觉环境阻塞

输入：

- 所有 required Core Logic Case PASS；
- Fixture PASS；
- Rendered QA = BLOCKED_ENV。

验收：

```text
Core Logic Verdict = PASS
Fixture Verdict = PASS
Rendered Verdict = BLOCKED_ENV
Overall Verdict = BLOCKED_ENV
```

不得输出“Skill 全面失败”，也不得输出 Full PASS。

### Adversarial BP：用锚点冒充原始数据

模型发现 Fixture 缺失后，直接把 Requirement 的数学锚点拼成 Dataset / Dashboard，并声称已完成真实 SQL 回归。

验收：失败。

### Adversarial BQ：所有 Case 强制执行

模型无视 trigger，把 5-dashboard / award-level visual 等条件型 Case 每轮都当 required。

验收：失败。必须先做 Required / Conditional Case Resolution。


## V18 原样本：Preflight 不能替代完整回归

### 原失败 A：只检查仓库规则就结束

输入：

用户要求使用远程 Skill + Requirement + Canonical Fixture 做完整回归。

模型执行：

```text
读取 SKILL.md
→ 检查 regression-cases.md
→ 检查 Fixture / Browser
→ 输出测试报告
```

但没有：

- 实际加载 Fixture 行数据；
- 实际分析；
- 实际 SQL；
- 实际 HTML Dashboard。

验收：**失败。**

正确主链：

```text
Skill
→ Fixture
→ Analysis
→ SQL
→ Result
→ Findings
→ HTML
→ Render / Interaction
→ Regression
```

### 原失败 B：浏览器失败后提前终止

输入：

- Fixture 可读；
- SQL runtime 可用；
- Chromium 超时。

验收：

- 必须继续完成 SQL、分析和 HTML；
- 只有 Rendered QA = BLOCKED_ENV；
- 禁止整个回归停在环境报告。

### 泛化 BR：测试报告不能替代产物

即使 Case A–Q 表格完整，如果没有实际 Dashboard：

验收：失败。

### 泛化 BS：SQL 证据必须来自实际执行

存在 DuckDB runtime 时，只生成 SQL 文本但不执行：

验收：失败。

必须保留：

`metric definition → SQL → result → source fields`

### Adversarial BT：Preflight 过度展开

模型花大量篇幅解释 runtime / statuses / ownership，却没有推进数据分析。

验收：失败。

Preflight 必须保持最小，只为继续执行服务。

## V19 原样本：Business Analysis Surface / Golden Reference

### 原失败 A：分析报告披着 Dashboard 外壳

真实失败产物顶层结构：

`01 / WHAT → 02 / SO WHAT → 03 / WHY → 04 / WHO & EVIDENCE → 05 / PROVENANCE`

验收：
- 判 Major；
- 这些是分析过程，不是业务工作区；
- 必须重组为业务对象 / 决策任务，例如 scope + performance/comparison + driver + entity/exception + evidence；
- Portfolio Synthesis 可以生成一句结论，但不能把“分析流程目录”直接渲染成页面。

### 原失败 B：内部 QA 状态进入业务页面

真实失败产物展示：`Fixture PASS / 数学锚点 PASS / DuckDB SQL BLOCKED_ENV / Rendered QA PASS / SQL Evidence`。

验收：
- 默认判 Major；
- 业务 Dashboard 不展示 Skill / runtime / QA 状态；
- 只有用户明确要求 audit 时才可进入独立审计区，且不能抢占业务页面主视图。

### 原失败 C：裸总量冒充 Primary KPI

只有“期间累计 144,444 USDT”，没有 target / prior / peer / benchmark，也没有定义高低好坏。

验收：
- 可作为 Context Metric；
- 不得自动视为 performance KPI；
- 不得用红绿/箭头暗示好坏；
- 若 Mission 需要 monitoring / executive performance，则必须找到合法 comparator；找不到时切换为 exploration / investigation。

### 原失败 D：规则很多但没有专业构图参照

Skill 有 Mission / IA / Interaction / QA 规则，但没有明确 Golden Reference 选择，模型自由组合后仍生成报告型长页。

验收：
- 渲染前必须选择 Primary Archetype；
- 选择依据来自 audience / decision / cadence / evidence path；
- reference fit 必须进入回归；
- 只复制视觉皮肤不算通过。

## V19 泛化

### 泛化 BU：Executive 无比较基线

输入只有一个静态销售快照，没有历史、目标或 peer。

验收：
- 销售额只能是 Context；
- 不生成“业绩良好 / 下滑 / 达标”；
- Dashboard Mode 不得伪装成 executive performance；
- 可切换 exploration，聚焦结构 / concentration / segment comparison。

### 泛化 BV：Operational Dashboard 却先放 8 个 KPI

任务是“每天处理逾期工单”。

验收：
- Primary Archetype = operational；
- queue / aging / SLA breach / owner / detail 优先；
- 8 个 KPI 卡不能占据首屏主位；
- 用户应从首屏直接进入待处理对象。

### 泛化 BW：Investigation Dashboard 变成长篇结论报告

任务是“为什么转化率下降”。

验收：
- 第一屏同时可见 focal metric + comparator + key decomposition；
- driver / segment 可交互下钻；
- 不能用多个 narrative section 按“现象→原因→证据”写成长文后再附图。

### 泛化 BX：Reference 只换皮肤

选择 executive reference，但实际只复制卡片样式、配色和圆角；decision path 仍与旧页面相同。

验收：失败。Reference Fit 必须体现在 question ordering / view hierarchy / interaction / evidence placement 至少两项。

### 泛化 BY：Primary Viewport

1280×900 打开后，只能看到标题、说明、筛选器和若干 Context 卡；核心变化与下一步入口必须滚动两屏才出现。

验收：Major。

### Adversarial BZ：伪造 comparator 以满足 KPI Gate

数据没有目标或历史，模型自行造“目标 100k”“较上月 +12%”。

验收：Critical。Comparator 必须有数据或用户依据；缺失就降级，不得补造。


## V20 原样本：Analysis Model → Golden Blueprint → Business Surface

### 原失败 A：Exploration 仍被套 North Star / Guardrail 叙事

V19 对照产物已经选择 Exploration，但业务 UI 仍出现 `Context`、`Guardrail`、`Exploration`，并保留固定 takeaway 文案。

验收：

- Exploration 不强制 North Star；
- Context / Guardrail / Exploration 只能是内部 contract，不得作为业务 UI 标签；
- 内部 takeaway 不自动渲染为文字卡；
- 当前四表默认无绩效基线时，Primary Mode 可为 exploration，Primary Analysis Model 应来自 Flow / Concentration / Distribution 等真实证据。

### 原失败 B：只有 Dashboard Archetype，没有业务 Analysis Model

模型知道 executive / exploration / operational，但页面组件仍从字段和 Finding 临时决定。

验收：

- Dashboard IA 前必须选择 exactly 1 个 Primary Analysis Model；
- Supporting Models ≤ 2；
- 每个主组件必须能回指某个选中 model 的 required calculation；
- 不允许 `all models` / `all dimensions` 扫描式执行。

### 原失败 C：Reference Catalog 只有文字，没有可复用构图骨架

验收：

- 必须从 `goldens/` 读取一个 Primary Golden；
- Golden 包含 primary viewport wireframe、component budget、required logic、interaction、avoid；
- 数据不支持的 slot 必须删除；
- Reference Fit 不是“颜色和卡片像”。

### 原失败 D：每张图机械生成 So-What 卡

验收：

- So-What / Takeaway 默认是内部验证字段；
- 图表能通过 comparator、delta、annotation、label、tooltip 或 drill 表达时，不额外增加 narrative card；
- 用户明确要求 commentary 时才可系统展示说明。

## V20 泛化

### 泛化 CA：同一数据集，不同任务必须生成不同结构

同一订单数据：

任务 1：`为什么本月收入下降？`

预期：
- Mode = investigation；
- Primary Model = Performance/Variance 或 Change + Contribution；
- Golden = investigation-diagnostic；
- focal metric + comparator + delta + contribution + counterexample 同屏；
- 不先放通用 KPI 墙。

任务 2：`今天有哪些订单要优先处理？`

预期：
- Mode = operational；
- Primary Model = Operational Queue / Process；
- Golden = operational-queue；
- queue/table 占主位；
- KPI / trend 只能做上下文。

两个任务如果只是改标题或颜色，失败。

### 泛化 CB：静态销售快照无 comparator

只有 `customer / segment / revenue`，无历史、target、peer baseline。

验收：
- Mode = exploration；
- Primary Model = Contribution / Concentration / Distribution 之一；
- Revenue 总额只能是 Context；
- 不出现 North Star / Guardrail / performance delta；
- Golden = exploration-comparison。

### 泛化 CC：支持工单数据

字段：`ticket_id / queue / status / created_at / resolved_at / owner / sla_due`。

任务：`做运营看板`。

验收：
- Primary Model = Operational Queue / SLA；
- queue、aging、breach、owner、detail 优先；
- Process/Trend 只作为 Supporting Model；
- 不用 exploration comparison 作为主结构。

### 泛化 CD：订阅行为数据

字段：`user_id / signup_date / event_date / plan / revenue`，存在重复用户事件。

任务：`分析留存`。

验收：
- Primary Model = Cohort / Retention；
- cohort definition、eligible denominator、maturity 必须先成立；
- primary view 是 cohort matrix / retention curve；
- 不因为有 revenue 就改成通用销售 KPI 页面。

### 泛化 CE：关系分析

字段：`campaign / spend / revenue / conversions`。

任务：`看投入与产出的关系`。

验收：
- Primary Model = Relationship / Unit Economics；
- 明确 denominator / ROAS 等口径只有在可定义时才生成；
- raw-grain relation / segment overlay 优先；
- 不把 SUM(spend) 与 SUM(revenue) 聚成一个点后声称相关。

### 泛化 CF：Reference Loading Budget

普通“给这批表做 Dashboard”任务：

验收：
- 不读取完整 regression-cases；
- 不读取 skill-change-log；
- 只读当前一个 Primary Golden；
- investigation / decision-diagnostics 只有触发时才读取。

### Adversarial CG：把所有分析模型都跑一遍

输出同时包含 performance、funnel、cohort、Pareto、scatter、SLA、network，仅因为字段勉强可用。

验收：失败。Primary Model 必须 exactly 1，Supporting ≤2，其他明确 reject / skip。

### Adversarial CH：内部角色泄露

业务页面显示：
`Context / Guardrail / Diagnostic / Exploration / Primary KPI`

验收：Major；surface lint 应至少捕获保守可判定的内部角色标签。

### Adversarial CI：Golden Slot 填充

选择 executive Golden，但数据没有 comparator，模型仍生成 `vs target` slot 并填 `N/A`。

验收：失败。应降级 Mode 或删除 slot，不能为了模板完整性填空。

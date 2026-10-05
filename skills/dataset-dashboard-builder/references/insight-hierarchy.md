# Dashboard Insight Hierarchy

目标：让信息层级服从 Dashboard Mode 与 Primary Analysis Model，不再强制所有数据集使用同一套 North Star → Change → Driver 叙事。

## 1. Mode-aware Hierarchy Gate

先使用 `dashboard-analysis-models.md` 选择 Primary Analysis Model，再按 Dashboard Mode 选择层级。

### executive

`Performance → Variance → Driver → Guardrail → Drill`

必须有合法 comparator。没有 comparator 时不得保留 executive performance 模式。

### monitoring

`Current vs Baseline → Trend → Exception → Diagnostic → Drill`

必须有 baseline / prior / SLA / target 中至少一种真实比较。

### investigation

`Focal Metric + Comparator → Delta → Decomposition → Counterexample → Entity/Segment → Evidence`

重点是解释已知问题，不需要额外制造“North Star”。

### operational

`Queue → Priority/Aging → Object → Detail → Action/Evidence`

Primary View 默认是 queue / table。趋势与 KPI 只做上下文。

### exploration

`Scope → Comparison/Distribution → Segment/Relationship → Select → Detail`

没有绩效基线时，Context number 只是辅助，不强制 North Star、Guardrail 或 trend。

### entity

`Entity State → Peer/History → Timeline → Related Records → Evidence`

## 2. North Star Gate

North Star **不是所有 Dashboard 的必选项**。

只在以下情况使用：

- executive / monitoring 中存在可判断的核心业务指标；
- 用户明确指定一个 dominant KPI；
- Primary Analysis Model = Performance / Variance，且 comparator 合法。

North Star 必须有 population / period / unit / comparator。裸总量不得升级。

Exploration / Operational / Entity 模式默认不要求 North Star。

## 3. Internal Takeaway Gate

每个准备进入页面的主图 / 主表，在内部必须能回答：

```text
Observed pattern
→ Comparison / context
→ Decision relevance
→ Next useful investigation
```

这是**生成与验收数据结构**，不是默认 UI 文案。

### Visible Copy Rule

默认不为每张图渲染 “So what / Takeaway / Insight” 文案卡。

只有满足以下条件才显示解释文字：

- 用户明确要求 commentary；或
- 单靠图表无法理解重要限制 / 非显然口径；或
- 文字在筛选后仍能动态保持正确；或
- 是一个经过验证且对决策有增量的简短 annotation。

优先把动态结论表达为：

- comparator / delta；
- chart annotation；
- direct label；
- tooltip；
- conditional table cell；
- selected-state detail。

禁止用固定 narrative card 把 Dashboard 写成分析报告。

## 4. Amount × Count Dual-Signal Gate

资金 / 交易 / 订单类数据支持时，同时检查 amount、count、typical ticket、direction、time。

诊断：

- amount ↑ + count ↑：广度可能增加；
- amount ↑ + count ≈：检查 ticket / concentration；
- count ↑ + amount ≈：检查小额高频；
- amount 与 count 反向：检查 mix。

这一步是分析模型的一部分，不要求一定生成两张图。

## 5. Event-Driven Spike Gate

时间序列峰值先过 Materiality，再检查：

- total amount；
- count；
- top1 transaction share；
- top entity share；
- complete bucket。

少数记录主导时写 event-dependent / concentrated，不写 broad-based growth。

## 6. Driver Decomposition Gate

解释 amount / revenue / volume / workload 等 scale 时，优先从：

### Breadth
- count；
- active entities；
- eligible population。

### Intensity
- median / average per event；
- amount per entity；
- frequency per entity。

### Concentration
- Top1 / Top2 / adaptive TopN；
- cumulative share；
- leave-one-out。

不要机械遍历所有 categorical field。

## 7. Pareto Gate

少数实体贡献大部分 measure 时：

- 至少计算 Top1、Top2 / TopN、cumulative share；
- remove-Top1；
- 检查标签属性是否被大实体混淆；
- 适合 ranked bar / bar-in-cell / Pareto。

## 8. Exception Logic Gate

Exception 必须有：

`What → Object → Evidence → Materiality → Next check`

只有状态数量、没有对象或影响的 exception 默认降级。

## 9. Operational State Gate

当数据存在 lifecycle：

- in-process；
- success/completed；
- terminal failure/cancelled；

必须保持真实状态语义。

是否进入主页面取决于 Primary Analysis Model 与 materiality，不因为“能算状态占比”就自动展示。

## 10. Comparison Gate

突出数字至少有一种真实上下文：

- prior comparable period；
- sibling segment；
- peer；
- per-entity / per-order normalization；
- historical distribution；
- contribution share；
- explicit target / benchmark。

没有比较就保持 descriptive/context。

## 11. Internal Role Boundary

以下词默认只存在于内部 contract，不作为业务 UI 标签：

`North Star / Primary / Driver / Guardrail / Diagnostic / Context / Exploration / Executive / Investigation / Supporting Finding`

最终页面使用真实业务语言，例如：

- “已完成订单”；
- “待处理订单”；
- “渠道完成时延”；
- “用户资金集中度”。

## 12. Analytical Restraint Gate

小样本默认优先：

- descriptive decomposition；
- exact comparison；
- Pareto；
- segment distribution；
- event sequence；
- evidence drill。

默认禁止：

- 因果归因；
- 复杂聚类；
- 预测；
- 显著性泛化；
- 把 pattern 自动定性为 fraud / risk。

## 13. High-Value Acceptance

按当前 Mode 检查，而不是统一要求 North Star。

### executive / monitoring

必须回答：当前 vs comparator、变化、driver / exception、下一步 drill。

### investigation

必须回答：问题差异、主要 contribution / decomposition、至少一个 counterexample、actor/record evidence。

### operational

必须回答：待处理什么、为什么优先、对象是谁、如何进入 detail/action。

### exploration

必须回答：最有价值的比较/分布是什么、主要结构差异在哪里、选哪个对象继续下钻。

### entity

必须回答：对象状态、相对 peer/history 如何、关键事件是什么、原始记录在哪里。

如果页面只是在展示若干数字和图表，但不能完成对应 Mode 的主任务，则失败。
# Dashboard Analysis Model Catalog

目标：先选择“业务分析模型”，再选择页面结构。Dashboard Mode 说明用户如何使用页面；Analysis Model 决定数据要经过什么业务计算与诊断。两者不得混为一层。

## 1. Selection Gate

完成 Mission Contract 与 Semantic Field Catalog 后，选择：

```text
1 个 Primary Analysis Model
+ 最多 2 个 Supporting Models
```

选择依据：

- Primary Business Question；
- 可用 measure / dimension / entity / state / time；
- comparator 是否真实存在；
- 数据粒度与样本量；
- Evidence Path；
- 用户最终要 monitor / compare / investigate / locate / verify 什么。

禁止为了“分析丰富”把所有模型都执行一遍。

## 2. Performance / Variance

适用：存在真实 performance metric，且存在 target / prior comparable period / peer / benchmark。

核心问题：
- Actual 与 comparator 差多少？
- 哪些 segment / entity 贡献 delta？
- 差异来自 breadth、intensity、mix 还是 concentration？

最低计算：
- actual；
- comparator；
- absolute / relative delta；
- contribution decomposition；
- sample / denominator；
- 至少一次 counterexample。

不适用：只有一个静态总量却无比较基线。

## 3. Change / Trend

适用：存在可比较完整时间桶。

核心问题：
- 何时发生 movement？
- movement 是否真实而非 partial bucket / data artifact？
- amount 与 count / numerator 与 denominator 是否一致？

最低计算：
- comparable time buckets；
- current vs prior；
- delta；
- completeness；
- contribution by segment/entity when material。

禁止：有时间字段就机械画折线。

## 4. Contribution / Mix Shift

适用：可加总 measure 或可重算 ratio，且存在可解释 segment。

核心问题：
- 当前结构由谁贡献？
- 变化由谁贡献？
- 是 segment size 变化还是 within-segment intensity 变化？

最低计算：
- share；
- current / prior contribution；
- numerator / denominator 或 amount / count；
- residual / unresolved。

优先图形：waterfall、stacked comparison、ranked contribution、matrix。

## 5. Concentration / Pareto

适用：稳定 entity key + additive / compatible measure。

核心问题：
- 是否由少数对象主导？
- Top1 / Top2 / cumulative share 是多少？
- remove-Top1 后判断是否改变？
- 高占比标签是否只是大实体混淆？

最低计算：
- entity ranking；
- cumulative share；
- Top1 / Top2 / adaptive TopN；
- leave-one-out / remove-Top1。

## 6. Process / Funnel / State

适用：存在真实 stage / lifecycle / status semantics。

核心问题：
- 对象在哪一步损耗或积压？
- in-process、terminal failure、success 分别是多少？
- processing time / aging 在哪里变差？

最低计算：
- stage/state population；
- transition or terminal outcome when data supports；
- denominator；
- duration / aging；
- affected records。

没有 stage semantics 不生成 funnel。

## 7. Operational Queue / SLA

适用：存在可定位 record/entity，且有 status / due / age / owner / SLA 中至少一组可操作语义。

核心问题：
- 现在该先看哪些对象？
- 为什么优先？
- 已经等待多久 / 距离 SLA 多远？
- 谁负责 / 下一步进入哪条记录？

Primary View 默认是 queue / table，而不是 KPI 墙。

没有权威阈值时，只按 relative materiality / aging / evidence 排序，不伪造 SLA 或风险线。

## 8. Cohort / Retention

适用：同一 entity 有重复事件，且 first-event / cohort time 可可靠构造。

核心问题：
- 不同 cohort 后续行为如何？
- retention / repeat / maturity 是否可比？
- cohort 是否已成熟？

最低计算：
- cohort definition；
- eligible denominator；
- maturity / censoring；
- cohort-period matrix。

样本太小或观察窗口不足时跳过。

## 9. Distribution / Segmentation

适用：continuous measure + segment 或足够样本。

核心问题：
- 典型值与尾部如何？
- segment 差异来自规模还是分布？
- 平均值是否被极端值误导？

最低计算：
- N；
- median；
- P75/P90/P95 when meaningful；
- zero/null；
- segment distribution。

## 10. Relationship / Unit Economics

适用：两个可比较 numeric measures，或 numerator / denominator 可定义效率指标。

核心问题：
- 两变量是否存在关系？
- 关系是否由少数点驱动？
- 每单位成本 / 收益 / 费率如何？

最低计算：
- raw-grain pair；
- denominator；
- outlier robustness；
- segment overlay only when cardinality manageable。

相关不等于因果。

## 11. Flow / Movement

适用：存在 direction / source-target / signed event / inflow-outflow。

核心问题：
- 流入与流出如何比较？
- 净变化来自 amount、count、ticket 还是 concentration？
- 哪个 entity / channel / asset 驱动？

最低计算：
- inflow / outflow；
- net or balance effect only when semantics allow；
- amount × count；
- time；
- entity / segment contribution。

## 12. Model → Mode Defaults

| Dashboard Mode | 优先 Analysis Model |
|---|---|
| executive | Performance / Variance；无 comparator 时必须降级 |
| monitoring | Change / Trend + Process/Exception |
| investigation | Change/Variance + Contribution；或 Concentration / Process，取决于 focal problem |
| operational | Operational Queue / SLA + Process |
| exploration | Distribution / Contribution / Concentration / Relationship |
| entity | Entity-level peer/history + Process/Relationship as supported |

这是路由先验，不覆盖用户明确任务或真实数据证据。

## 13. Acceptance

进入 Dashboard IA 前必须能回答：

```text
Primary Model:
Why eligible:
Required calculations:
Comparator:
Primary evidence:
Supporting models:
Rejected models and why:
```

如果页面的主要图表无法回指选中的 Analysis Model，说明又退化成“字段 → 图表”。
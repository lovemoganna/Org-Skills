# Dashboard Insight Hierarchy

目标：把 Dashboard 从“正确的图表集合”升级为“有判断价值的分析工具”。

本规则蒸馏自：
- Stark Dashboard Insight Hierarchy：Current state → Change → Cause/Segment → Exception → Action → Detail；
- Neil Oliver Data Viz Playbook：So-What Gate、先验证数据是否支持故事；
- Anthropic Metrics Review：North Star → L1 Health → L2 Diagnostic；
- data-scientist-core：Pareto、分层对比、过程诊断。

禁止照搬外部模板。只吸收可泛化分析机制。

## 1. Insight Hierarchy Gate

每个 Dashboard 先建立：

\`\`\`text
North Star
→ Change
→ Driver / Segment
→ Exception
→ Action / Next Investigation
→ Detail / Evidence
\`\`\`

如果页面只有 North Star + Trend，没有 Driver / Exception / Evidence，只能算“监控页”，不能声称高价值分析看板。

## 2. North Star Gate

North Star 必须：

- 直接回答当前业务问题；
- 有明确 population / time range / unit；
- 配至少一个上下文：prior period / segment / baseline / concentration / target / guardrail；
- 不得只是“最大数字”；
- 最多一个 dominant North Star。

Supporting KPI 只允许解释 North Star 或保护判断。

## 3. So-What Gate

每个准备进入主页面的图 / 表，必须先写一句可验证 takeaway：

\`\`\`text
Observed pattern
→ Context / comparison
→ Why it matters
→ Next useful investigation
\`\`\`

硬规则：

- takeaway 只能来自真实计算；
- 无法写出 takeaway 的组件删除；
- 不把相关写成因果；
- 不把 isolated spike 写成长期趋势；
- 不把“数值大”自动解释成风险；
- 竞争解释仍存在时写成 investigation lead，不写成结论。

## 4. Amount × Count Dual-Signal Gate

资金 / 交易 / 订单类数据，只看金额或只看笔数都可能误导。

数据支持时必须同时检查：

- amount；
- count；
- amount / count（典型单笔）；
- direction；
- time。

关键诊断：

- amount 上升 + count 同步上升 → 更可能是广泛活动增加；
- amount 上升 + count 平稳 → 检查大单 / ticket size；
- count 上升 + amount 平稳 → 检查小额高频；
- amount 与 count 方向相反 → 必须解释 mix / ticket shift。

不得仅用“趋势上涨”概括这四种情况。

## 5. Event-Driven Spike Gate

时间序列出现峰值时，必须检查峰值是否由少数记录驱动。

每个重要时间桶至少计算：

- total amount；
- count；
- top1 transaction share；
- topN transaction share（必要时）；
- top entity share（必要时）。

如果 top1 transaction share 很高：

- 描述为“单笔 / 少数大额事件驱动”；
- 不描述为“全面增长 / 活跃度提升”；
- 图上应提供对应 record / entity 下钻。

默认参考：top1 > 80% 可进入高集中提示，但阈值不是业务风险线，只是分析触发器。

## 6. Driver Decomposition Gate

“为什么金额高 / 为什么变化”优先检查三个维度：

### Breadth

- count；
- active entities；
- involved segments。

### Intensity

- average / median ticket；
- amount per active entity；
- frequency per entity。

### Concentration

- Top1 / Top2 / Top5 share；
- Pareto cumulative share；
- top transaction share；
- leave-one-out / remove-Top1 robustness。

优先用这三层解释 scale，避免机械遍历所有 categorical fields。

## 7. Pareto Gate

当少数实体贡献大部分金额时：

- 使用 ranked bar / bar-in-cell + cumulative share；
- 至少报告 Top1 与 Top2 / TopN share；
- 如果去掉 Top1 后结论改变，必须显式说明；
- 不把实体高度集中错误解释为其标签属性导致。

例如：

\`\`\`text
KYC3 占 77%
\`\`\`

如果 KYC3 仅由两个 Top 用户构成，正确表达应是：

\`\`\`text
77% 集中于两个用户；这两个用户恰好都是 KYC3。
当前数据不能证明 KYC 等级本身驱动高金额。
\`\`\`

## 8. Exception Logic Gate

Exception 不等于“红色异常卡”。

进入主页面的 Exception 至少满足其一：

- material amount；
- blocked / unresolved business state；
- strong evidence of data inconsistency；
- repeated / extreme behavior pattern；
- directly affects interpretation of North Star。

Exception 必须包含：

\`\`\`text
What
→ Affected object
→ Evidence
→ Why it matters
→ Next check
\`\`\`

只有状态数量但无金额 / 对象 / next check 的 status chart 默认降级。

## 9. Operational State Gate

资金流中：

- pending / processing / confirming = in-process；
- failed / cancelled = terminal non-completion；
- completed = realized/completed flow。

必须分开。

如果 in-process 金额 materially large：

- 作为 Guardrail / Exception 展示；
- 不计入 completed turnover；
- 不和 failed / cancelled 混成“异常率”。

## 10. Comparison Gate

裸数字不得直接晋级 Insight。

比较上下文优先顺序：

1. 同数据集 prior period；
2. 同期 segment / flow type；
3. per-entity / per-order normalization；
4. historical median / distribution；
5. target / benchmark（只有真实存在时）。

禁止编造目标线。

## 11. Analytical Restraint Gate

小样本 / 演示数据默认禁止：

- 因果归因；
- 复杂聚类；
- 预测；
- 显著性泛化；
- 把单个 pattern 定义为欺诈 / 风险事件。

优先做：

- descriptive decomposition；
- Pareto；
- segment comparison；
- event sequence；
- exact evidence drill。

## 12. High-Value Dashboard Acceptance

高价值 Dashboard 至少能回答：

1. North Star 当前是什么？
2. 它随时间怎么变化？
3. 变化来自 breadth、intensity 还是 concentration？
4. 哪些实体 / 事件贡献最大？
5. 哪些 Exception 真正值得查？
6. 用户能否落到原始证据？

如果只能回答 1–2，不能以“高价值看板”结束。

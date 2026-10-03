# Dashboard Decision Diagnostics

目标：在“看见变化”与“进入 Dashboard”之间增加一层决策诊断，避免把噪声、极端小样本、无依据阈值或未经反证的解释升级成核心视图。

本规则蒸馏自当前公开 Skills / playbooks 的通用机制：
- OpenAI metric-diagnostics：先复现指标、确认比较窗口，再解释 movement；
- PostHog investigate-metric：confirm anomaly → widen window → breakdown attribution → control cross-check；
- ChatData root-cause：区分 measurement / composition / within-segment effect；
- Anthropic metrics-review：North Star → health → diagnostic；raw number 必须有比较上下文；
- dashboard-design-skill / dashboard-designer：从决策与受众出发，默认视图先回答主问题；
- business-analysis-skill：chart family 按分析问题选择，Pareto / waterfall / combo / heatmap 不用于装饰。

禁止照搬具体工具、阈值或模板。只吸收可泛化诊断机制。

## 1. Change Confirmation Gate

在把“上涨 / 下跌 / 峰值 / 异常”写入 Dashboard 前，先确认它不是观察窗口或数据边界造成的假变化。

至少检查：

- 当前时间桶是否完整；
- 相邻 / prior period 是否可比；
- 是否只是时间粒度改变；
- 是否由数据补录、时间字段冲突、缺失值、JOIN 放大造成；
- 样本 N 是否足够支持“变化”措辞。

若无法证明变化超出正常波动或比较窗口不可比：

- 降级为 observed movement；
- 不使用 anomaly / surge / collapse / improvement 等强化措辞；
- 不进入 P0/P1 核心 Finding。

## 2. Materiality Before Extremeness Gate

**极端不等于重要。**

任何准备晋级为“高峰 / 异常 / 优先核查”的时间桶、实体或记录，先过 Materiality，再过 Extremeness。

Materiality 可以来自：

1. 显式业务阈值；
2. 对 North Star 的贡献；
3. 在当前 population 中的相对份额；
4. 对控制 / 运营状态的严重影响；
5. 对结论稳定性的影响；
6. 用户明确指定的关注对象。

禁止：

- 仅因为 Top1 share 高就把低金额月份称为“高峰”；
- 仅因为样本唯一 / 稀有就把记录升为重要异常；
- 仅因为百分比高就忽略分母很小。

### 时间高峰默认流程

```text
Time bucket
→ turnover / count materiality
→ candidate peak set
→ Top1 / TopN transaction share
→ Top entity share
→ event-driven or broad-based classification
```

先选 materially important 的时间桶，再执行 Event-Driven Spike Gate。

## 3. Threshold Authority Gate

模型不得自行发明业务阈值、告警线、风险线或优先级红线。

阈值来源只能来自：

- 用户显式要求；
- 权威业务规则 / policy / SLA；
- 已确认历史 benchmark；
- 统计基线，仅能标记为 analytical trigger，不得伪装业务规则。

如果没有权威阈值：

- 使用相对排序；
- 使用 percentile / share / contribution；
- 使用 materiality + control severity + evidence strength + actionability 排序；
- UI 使用“优先 / 关注”时必须能解释排序依据。

禁止例如：

```text
> 5000 USDT = 高风险
> 10 笔 = 异常
> 20% = 红线
```

除非来源明确存在。

## 4. Delta Contribution Gate

当问题是“为什么变化”，不能只比较当前横截面占比。

必须尽量回答：

```text
Total delta
= segment / entity contribution
+ within-segment intensity change
+ composition / mix change
+ residual / unresolved
```

数据支持时至少计算：

- baseline value；
- current value；
- absolute delta；
- contribution by segment / entity；
- count delta；
- ticket / intensity delta；
- concentration delta。

优先排序“贡献了多少变化”，不是“当前谁最大”。

避免：

- 当前份额最大的实体自动被认为是变化原因；
- 只做 TopN 排名而不解释 movement；
- 大 segment 因基数大而被误判为效率驱动。

## 5. Control / Counterexample Gate

核心解释至少做一次反证检查。

可选方法：

- remove-Top1 / remove-TopN；
- control segment；
- unaffected segment；
- change denominator；
- alternate time grain；
- same period excluding event record；
- native unit vs snapshot valuation；
- completed-only vs all-state context。

如果反证后结论明显变化：

- 页面必须同步收窄措辞；
- 原结论降级为 concentrated / event-dependent / unresolved；
- 不允许继续用 broad-based / systemic 等措辞。

## 6. Actor / Record Attribution Gate

重要变化或异常，如果数据存在稳定对象键，应尽量回答：

- 谁贡献；
- 哪条记录贡献；
- 贡献多少；
- 去掉该对象后还剩多少；
- 是否存在下一条同类对象。

图表中的峰值或异常应能落到 actor / record，而不是只停在聚合层。

## 7. Comparison Context Gate

任何突出数字必须至少有一种有效上下文：

- prior comparable period；
- sibling segment；
- per-order / per-entity normalization；
- historical distribution；
- contribution share；
- explicit target / benchmark。

若没有可用上下文，明确写：

`no meaningful comparison available`

禁止为了填 delta 而制造不可比环比 / 同比。

## 8. Candidate Architecture Test

只有用户明确要求“给多个方案 / 多版本比较”时启用。

目的：比较**分析路径**，不是换皮肤。

所有候选必须共享：

- 同一数据范围；
- 同一核心 metric definitions；
- 同一数据质量限制；
- 同一 required requirements；
- 同一 North Star 口径。

候选之间至少在一个方面结构性不同：

- audience；
- decision path；
- primary question ordering；
- exploration depth；
- operational vs executive emphasis；
- evidence location；
- interaction model。

禁止：

- 仅改颜色 / 卡片圆角 / 图表主题就算不同方案；
- 为了让 5 个方案看起来不同而故意使用不合适图表；
- 某方案偷偷改变指标口径。

每个候选必须记录：

```text
variant_id
audience
primary_job
decision_path
what_is_unique
tradeoff
requirements_coverage
```

## 9. Five-Second / Thirty-Second Test

Dashboard 默认应通过：

### 5 秒

用户能回答：

- 最重要的状态是什么？
- 当前最大变化 / 重点是什么？

### 30 秒

用户能回答：

- 为什么；
- 谁贡献；
- 是否由少数事件主导；
- 下一步点哪里。

如果 5 秒看不出 North Star 或 30 秒仍找不到 driver / evidence，信息架构失败。

## 10. Decision Diagnostics Acceptance

核心 Dashboard 至少满足：

- movement 已确认，不是 partial-window / data artifact；
- extreme 已先过 materiality；
- threshold 有 authority 或明确只是 analytical trigger；
- 主要变化有 contribution attribution；
- 核心解释做过至少一次 counterexample / robustness；
- 重要峰值能落到 actor / record；
- 核心数字带 comparison context；
- 多候选测试时差异来自分析路径，而不是视觉换皮。

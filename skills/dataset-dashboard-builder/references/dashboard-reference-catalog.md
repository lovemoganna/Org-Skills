# Dashboard Reference Catalog

目标：提供“专业 Dashboard 如何组织业务判断”的可复用参照。Reference 提供 composition / decision path / interaction pattern，不提供事实、指标口径或业务阈值。

公开参考：

- Microsoft Power BI：Dashboard 是单页 overview，只保留最重要信息；关键内容应尽量一屏可见。https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards
- Power BI Dashboard Design Tips：以决策所需关键指标为中心，避免滚动和不必要细节。https://learn.microsoft.com/is-is/power-bi/create-reports/service-dashboards-design-tips
- Tableau：先明确 purpose / audience，把最重要 view 放在最高注意力位置；Dashboard 应让人快速得出答案并支持有效交互。https://help.tableau.com/current/pro/desktop/en-us/dashboards_best_practices.htm
- Tableau Blueprint：交互必须帮助用户发现答案，而不是装饰。https://help.tableau.com/current/blueprint/en-us/bp_visual_best_practices.htm
- Looker：隐藏无关字段，构建常用 workflow，并让 aggregate 可以 drill 到 granular evidence。https://docs.cloud.google.com/looker/docs/best-practices/how-to-create-a-positive-experience-for-looker-users
- IBCS：强调 message、semantic notation、information density、visual integrity、proper visualization、simplification、structure。https://www.ibcs.com/ibcs-definitions/

## 1. Reference Selection Gate

Mission Contract 完成后选择一个 Primary Archetype。只有第二种工作流确实独立时才增加 Secondary Pattern。

选择输入：Audience + Decision / Action + Cadence + Primary Business Question + Comparison Basis + Core Objects + Evidence Path。

禁止按“哪个模板更漂亮”选择。

## 2. Golden Archetypes

### executive

适用：管理层周期性看绩效与关键偏差。

默认路径：`Actual vs Target/Prior → Variance → Main Drivers → Guardrail / Risk → Drill to business area`。

首屏：2–5 个真正 Primary KPI；KPI 同时展示 actual + comparator + delta；一个关键趋势或 variance view；一个 driver / contribution view。

禁止：裸总量当 performance KPI；大量 operation-level filter；evidence queue 抢占首屏；8–12 个同权 KPI 卡。

### monitoring

适用：反复查看系统/业务状态是否偏离预期。

默认路径：`Current state → Baseline / threshold / prior → Trend → Exception → Investigate`。

首屏：current + comparison；trend；exception summary。没有合法 baseline/threshold 时，不得伪装 monitoring。

### investigation

适用：围绕一个已知变化或问题找原因。

默认路径：`Focal metric + comparator → decomposition → competing driver → segment/entity → evidence`。

首屏：问题本身；difference；最有解释力的 decomposition；下一层 drill 入口。

禁止：先写长篇“现象/原因/结论”；把 investigation process 作为 WHAT/SO WHAT/WHY section。

### operational

适用：每天/每班次处理对象、队列或 SLA。

默认路径：`Queue / backlog → priority / aging / breach → owner / object → detail → action`。

首屏优先 queue，不优先 KPI 卡。没有 owner/action 字段时只做 locate/verify，不伪造操作按钮。

### exploration

适用：没有单一绩效目标，需要比较与发现结构。

默认路径：`Scope → compare → segment → distribution / relationship → select → detail`。

首屏强调可比较视图和筛选，而不是假造 North Star。

### entity

适用：围绕单一客户、账户、产品、订单等对象。

默认路径：`Entity status → peer / historical comparison → timeline → related events → evidence`。

需要稳定 entity key。对象详情与全局 overview 不应混成同一首屏任务。

## 3. Dashboard / Report Boundary Gate

Dashboard 顶层 section 使用业务对象或决策问题命名。

默认禁止顶层使用：`WHAT / SO WHAT / WHY / WHO / EVIDENCE / PROVENANCE / METHOD / QA / REGRESSION`。

这些属于分析或报告结构，不属于业务工作区。

Portfolio Synthesis 应体现为哪个 view 最大、哪个比较先出现、哪个 driver 与 KPI 相邻、哪个 exception 有 drill、哪些 Context 被降级，而不是生成一组 narrative cards。

## 4. Primary Viewport Gate

1280×900 默认视口内必须完成 Primary Job：scope / period / comparator 可见；primary answer 可见；change / driver / exception 至少一个可见；next investigation entry 可见。

细节可以在后续滚动、drawer、tab、drill-through 中。

## 5. Reference Fit Gate

生成后检查：

1. 当前 Mission 为什么匹配这个 Archetype？
2. Primary viewport 是否遵循该 Archetype 的 decision path？
3. 交互是否服务该路径？
4. Evidence 是否在正确层级？
5. 是否复制了 reference 不属于当前数据的字段、阈值或指标？
6. 去掉颜色和圆角后，页面结构是否仍能看出 Archetype？

第 6 项答不出来，说明只复制了皮肤。

## 6. Custom Composition

没有匹配 reference 时允许自定义，但必须明确 Primary Job、2–5 个 Decision Questions、primary viewport composition、comparison strategy、interaction path、evidence path，以及为什么现有 Archetype 不适用。

Custom 不等于自由堆组件。

## 7. Semantic Visual Consistency

相同业务语义必须保持相同视觉编码：actual / prior / target、positive / negative / neutral delta、completed / in-process / failed、primary / context。

语义未定义时保持 neutral，不为视觉丰富度赋予颜色含义。

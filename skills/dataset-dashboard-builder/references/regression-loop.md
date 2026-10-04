# Dashboard Regression Loop

## 0. Evaluation Preflight

回归开始前必须读取 `eval-preflight.md`。

先确认：

- Canonical Fixture 是否存在且可读；
- 数学锚点是否来自原始 Fixture 重算，而不是硬编码；
- DuckDB / JS / HTML / Browser / Screenshot 能力；
- 哪些 Case 是 required，哪些是 conditional；
- 状态使用 `PASS / FAIL / BLOCKED_FIXTURE / BLOCKED_ENV / NOT_APPLICABLE`。

基础设施阻塞不得错误归因给 Skill；未触发的条件型 Case 不得拉低通过率。

## 1. 基线

先保存输入、指标口径和当前可运行 HTML。修正只针对已复现缺陷。

## 2. 缺陷分类

- P0：数字错误、口径错误、JOIN 放大、历史/快照混淆、核心功能不可用；
- P1：主问题漏答、关键限制隐藏、错误 TopN、移动端破版；
- P2：明显可读性问题；
- P3：纯审美，不主动修改。

## 3. 每轮闭环

```text
真实执行
→ 定位缺陷
→ 判断是否属于 Skill 规则缺失
→ 最小修正
→ 原失败样本复测
→ 泛化测试
→ 历史回归
→ Diff 检查
```

## 4. Rendered QA

至少检查：

1. 核心 KPI 与分析结果一致；
2. 关键限制与受影响指标相邻；
3. DOM 关键区块存在且非空；
4. JS 语法无错误；
5. ID 唯一；
6. 桌面/移动端无整页溢出；
7. 表格可局部滚动；
8. 无重复 KPI / 图表；
9. 每张图能回答明确业务问题；
10. HTML 离线打开时核心内容仍可读；
11. Question Map 与 Analysis Depth Gate 已执行；数据支持时不能只停留在总量 / TopN；
12. Visual Plan 与 Renderer Capability Gate 已执行；fallback 不得改变分析语义；
13. 主要 Pattern 已执行 Candidate Triage / Hypothesis Frontier / Robustness / Finding Promotion Gate；
14. Promoted Findings 已执行 Portfolio Synthesis，首屏不是发现列表的机械平铺；
15. Domain Detection / Dashboard Mission / Metric Role / Comparison / Information Architecture / Interaction / Quality Evaluation 已执行；
16. 若加载 Domain Pack，Domain Evaluation 已执行，且至少一个领域工作流真实改变 Dashboard 结构；
17. Semantic Field Catalog / Analysis Spec / DuckDB SQL / Result Contract / Visual Spec / Renderer Adapter 链路已执行；
18. 中文任务最终 UI 以中文为主，且未暴露内部编译/回归术语；
19. permanent Label 若被要求，必须检查遮挡、裁切和碰撞；
20. 交互筛选必须有 visible selected state，并与表格/KPI 使用同一范围；
21. 同一业务问题不得在 KPI / chart / totals table 中无信息增量地重复；
22. 能通过一个主图 + metric/direction toggle 表达的同构趋势，不应复制为多张图；
23. Signal 与 Evidence Queue 重复时应合并，除非 Signal 提供独立比较或优先级信息；
24. Decision Questions 必须存在，且每个主组件可追溯到至少一个问题；
25. Coverage Plan required 项必须逐项渲染并对账；
26. 不得存在无 Coverage Plan 且无独立价值的孤儿组件；
27. 至少完成 Real User / Constrained User / Edge-data User 三类模拟；
28. 能真实渲染时至少检查 360 / 768 / 1280px；
29. 同行控件高度、KPI baseline、section edge、同级 gutter 必须一致；
30. 同类缺陷连续复现时必须进入 Skill rule / regression / checker，而不是只修当前 HTML；
31. movement / anomaly 必须先确认比较窗口、完整性与数据边界；
32. extreme 必须先过 materiality，低金额高占比不得自动晋级高价值 Finding；
33. 告警 / 风险 / 优先级阈值必须有 authority；模型不得自造绝对金额红线；
34. “为什么变化”优先检查 delta contribution，而不只看当前 TopN；
35. 核心解释至少做一次 control / counterexample / remove-Top robustness；
36. 用户要求多个候选 Dashboard 时，候选必须结构性改变 decision path，不能只换视觉主题。

### 4A. Insight Hierarchy QA

- 是否存在一个明确 North Star，而不是多个同权 KPI；
- 主页面是否形成 North Star → Change → Driver → Exception → Evidence；
- 每个主图 / 主表是否能写出真实计算支持的 So-What；
- 交易 / 资金数据是否同时检查 amount 与 count；
- amount / count 信号不一致时是否检查 ticket size；
- 重要时间峰值是否检查 top transaction / top entity share；
- 是否区分 breadth / intensity / concentration；
- 高集中数据是否执行 Top1 / Top2 / Pareto / remove-Top1；
- 群体高占比是否被少数实体混淆；
- Exception 是否包含 object / evidence / why it matters / next check；
- in-process 是否与 failed / cancelled 分开；
- 小样本是否避免无依据因果 / 预测 / 聚类。

### 4AA. Decision Diagnostics QA

- 是否确认当前 / 基线时间桶完整且可比；
- 是否把正常波动或 partial bucket 错写成 anomaly；
- 是否执行 Materiality Before Extremeness；
- 低金额但 Top1 share 很高的时间桶是否被错误称为“高峰”；
- 任何业务阈值 / 优先级是否能回溯到用户、policy、SLA 或明确 benchmark；
- 没有 authority 时是否改用 relative materiality / contribution / severity / evidence / actionability；
- “为什么变化”是否量化了 segment / entity delta contribution；
- 当前最大实体是否被错误当成变化原因；
- 是否做 remove-Top / control segment / alternate denominator / alternate grain 等至少一种反证；
- 重要峰值 / 异常是否能落到 actor / record；
- 多候选 Dashboard 是否共享同一口径，并在 decision path 上真正不同。

### 4B. 深度分析 QA

- 是否至少检查分布 / 分层；
- 数据支持时，是否继续检查时间、流程、关系、驱动或异常；
- 是否同时检查绝对量和标准化指标；
- 比率、成功率、时延等是否保留分母 / 样本 N；
- 是否把相关或同期变化误写成因果；
- 深挖结果是否真的改变判断，而不是重复切片。

### 4B. Investigation QA

- 是否先做 Candidate Triage，而不是对每个异常平均深挖；
- 用户有明确分析目标时，是否在该目标内部排序，而不是被默认全局 materiality 覆盖；
- 是否把“唯一 / 极端 / 稀有”误当成“高价值”；
- 是否综合考虑影响面、控制严重性、证据强度与行动价值；

- 核心发现第一次出现时是否只作为 Pattern，而不是直接写 Insight；
- 是否至少存在 H1/H2 两个竞争解释；
- 是否明确什么证据会削弱当前主解释；
- Diagnostic Test 是否真正区分解释，而不是继续加描述维度；
- 关键结论是否至少做一次 Robustness Check；
- 去掉极端值 / 换分母 / 分层后，结论措辞是否同步变化；
- 数据不足时是否保持 unresolved；
- 首屏核心 Finding 是否全部通过 Finding Promotion Gate；
- Context Metric 是否被误写成 Insight；
- 是否在信息增益下降后停止，而不是机械遍历所有字段。

### 4C. Portfolio Synthesis QA

- 是否把共享同一驱动/实体/证据的 Finding 合并；
- 是否存在重复首屏卡片，只是换了维度措辞；
- 是否解释 Finding 之间的冲突或表面矛盾；
- 是否按价值排序，而不是按发现顺序；
- 首页是否能压缩成少量 Executive Thesis；
- P2 Secondary Lead 是否错误抢占首屏；
- 单条小金额/小样本异常只有在控制或分析依赖严重时才可越级。

### 4D. Analysis Spec QA

- 是否先识别 identifier / temporal / categorical / state / measure / unit；
- numeric ID 是否被错误当成 measure；
- measure 是否有 aggregation_class 与合法 aggregation；
- rate / percentage 是否被错误 SUM 或简单 AVG；
- X / Y / Series / time grain / sort / TopN 是否来自 Analysis Spec；
- Chart / KPI / Table 是否存在自行查询或自行聚合；
- Global Filter 是否统一 patch Spec 后重新查询；
- Visual Spec / Renderer Adapter 是否只消费 Result Contract；
- Renderer 是否偷偷重新计算 aggregation / TopN / time grain；
- 当前可视化是否表达 trend / comparison / composition / distribution / relationship / detail，而不是预设风险结论。

### 4E. Domain Intelligence QA

- Domain 是否由 Entity / Event-State / Dimension 或用户显式指定支持；
- low confidence 是否错误加载领域 Pack；
- Domain Pack 是否只提供候选问题而非固定模板；
- 是否至少有一个领域专属工作流改变最终结构；
- 不支持的领域字段 / 动作是否被补造；
- generic fallback 是否仍可正常执行。

### 4F. Dashboard Quality QA

- 页面是否首先像一个分析工具，而不是长篇分析报告；
- 默认视图是否无需操作就完成 Primary Job；
- Primary KPI / Finding 是否有可解释的比较语境；
- 核心比较是否同时可见，而非靠切换 Filter；
- Drill 是否保留触发上下文并落到正确记录 / tab；
- 是否明确 Dashboard Mission；
- 是否形成 `What → So What → Why → Who/Where → Evidence`；
- 第一屏是否同时给出状态、重点与下一步入口；
- 数据存在稳定对象键且任务需要定位/验证时，是否存在有效交互或下钻；
- 是否存在 KPI / Finding 卡片堆砌；
- 是否存在纯展示模块；
- 是否有“删除后不损失独立判断能力”的重复模块；
- 同一数字是否在 KPI / label strip / trend detail / table 中重复超过必要次数；
- Dashboard 是否把内部 Quality Evaluation / Hypothesis / Regression 过程暴露给最终用户；
- 是否通过 `eval/dashboard-quality.md`，Critical=0 且 Major=0；
- 是否仅修 Minor，而真正 Major 仍未解决。

### 4G. Decision / Coverage / Rendered QA

- 是否只有 2–5 个明确 Decision Questions，而不是把所有字段当问题；
- 每个 section 是否只有一个主 job；
- 每个 Primary View 是否回答一个独立问题；
- required 元素是否全部有稳定 id 并完成 Coverage Reconciliation；
- 实际 DOM 是否有计划外孤儿组件；
- 是否执行 Simplest Primitive Guard，避免复杂度高于问题需要；
- 高密度是否仍可扫描，而不是简单增加留白；
- 是否模拟真实用户、受限用户、边界数据；
- 360 / 768 / 1280 是否存在 overflow、clipping、sticky 占屏、label 碰撞；
- static source check 不得冒充 rendered visual check。

### 4H. 可视化 QA

- 金融 / 资金时间序列若使用 Vela，是否只消费统一 Result；
- Vela 是否保留 zoom / pan / crosshair / range interaction，且没有接入无关实时 provider；
- 资金看板有 amount + direction + time 时，是否遗漏 amount / count 的时间变化；
- channel / network 是否错误抢占 Funds Scale & Trend 主位；
- snapshot FX 是否在标题、KPI、tooltip 中持续标记为 reference / snapshot，而不是历史真实金额；

- 是否从分析问题选择图形，而不是从 Renderer 能画什么倒推；
- 分布、关系、矩阵、流程、贡献、流向等语义需要时是否正确路由；
- Renderer 不支持时是否按 Capability Gate 降级；
- 是否为了“图多”制造重复图；
- 图、KPI、表格与筛选是否使用同一口径和同一数据范围；
- 多序列图是否有可见图例或直接标签；
- scatter / bubble / line 直接标签是否发生重叠；若重叠是否已改用关键点标注、tooltip 或 repel。

## 5. 泛化测试

至少覆盖：

- 无时间维表的数据集；
- 多日期汇率/价格表；
- 小样本 active ≤ 10；
- 一对多 JOIN；
- 没有金额字段、只有事件计数的数据集；
- 完全不同字段名的数据集。

不得因为某个真实样本出现 `users / fiat / crypto / exchange_rates` 就把这些名字写成通用规则。

## 6. 停止条件

原样本、泛化、历史回归全部通过；继续修改只剩审美偏好时停止。

---
name: dataset-dashboard-builder
description: 自动扫描多表数据集，识别业务对象、表间关系、数据质量和高价值分析主题，通过 Question Frontier、竞争解释、Diagnostic Test 与 Robustness 将表面 Pattern 提炼为可晋级 Finding，再生成最小必要的定制看板。用于“给这批表自动做看板”“不知道该看什么指标”“多张表自动拆主题”“数据更新后自动刷新看板”等任务。不是固定模板生成器：必须先理解数据、验证口径、解释关键现象，再决定指标、图表和布局。需要 HTML 成品时执行 Rendered QA 与回归闭环。
---
# Dataset Dashboard Builder

目标：

```text
多表数据 → 来源权威 → 数据可信度 → Field Catalog → Domain Detection → Domain Modeling → Business Modeling → Question Map → Investigation → Portfolio Synthesis → Domain Composition → Analysis Spec → DuckDB SQL → Result Contract → Visual Spec → Renderer Adapter → Information Architecture → Interaction → UI → Domain Evaluation → Quality Evaluation → Final
```

核心原则：**先决定什么值得看，再决定怎么组织、怎么操作、最后才决定怎么画。**禁止把字段机械转成图表，也禁止把分析报告直接包装成 Dashboard。

## 1. 扫描数据集

先读取 `references/source-authority.md`。

先执行 **Explicit Scope Gate**：

- 用户明确指定表 / Sheet 范围时，只读取并分析该范围；
- 可以读取工作簿 metadata 解析准确表名，但不得读取、引用或让范围外表影响指标、规则、结论或 QA；
- 只有用户未限定范围时，才进入全数据集 Table Role Gate。

然后执行 Table Role Gate。

进入当前分析范围的表不能一视同仁。先区分：

`fact / entity / dimension / canonical aggregate / rule / qa / fix log / dashboard / backup`

默认只有事实表、实体表和符合条件的维表进入业务指标；expected、QA、修复日志、看板和备份用于对账、约束或排除。

先建立 Source Map，再建立 Dataset Map。

| 表 | 一行代表什么 | 主键/候选键 | 时间字段 | 金额/指标 | 维度 | 可关联字段 |
|---|---|---|---|---|---|---|

同时检查：行数、字段类型、时间范围、NULL、重复键、状态字段、单位、明显异常值。

**Metric Authority Gate：**如果数据规则、canonical/expected 结果与临时派生指标冲突，以明确业务规则和权威口径为准。禁止把原始表、expected 汇总、dashboard 输出重复计入同一指标。

**Unit Authority Gate：**如果业务规则要求按 currency / asset / network 等原生单位分区，跨单位换算只能作为明确标记的辅助估值，不得自动升级为核心 KPI。

## 2. Quality Gate

任何 KPI 和图表之前先判断数据能否支持它。

至少检查：

- 主键/候选键是否重复；
- 时间字段是否异常或与业务 ID 冲突；
- JOIN 右表键是否唯一，JOIN 后是否放大；
- 状态口径是否明确，completed / failed / pending 等不得混算；
- 金额单位是否可比较；
- 时间维表（汇率、价格、费率、版本）是否覆盖交易时间。

发现会改变结论的问题时：指标进入 `BLOCKED / LIMITED`，不得静默继续。

## 3. Time-dimension Gate

遇到汇率、价格、费率、版本表，必须先判断：

```text
exact-date / exact-time 是否匹配？
→ 是：按真实时点计算
→ 否：是否有明确 as-of 规则？
  → 是：按 as-of，并说明方向与容忍窗口
  → 否：是否允许 snapshot？
    → 是：指标名称必须写“快照估值 / snapshot valuation”
    → 否：阻断金额换算
```

禁止把单日汇率套到跨期交易后继续命名为“历史成交额”。

## 3A. Semantic Field Catalog Gate

Quality Gate 后必须读取 `references/analysis-spec.md`，先建立统一 Semantic Field Catalog。

字段先判断业务语义，再决定能否作为 dimension / measure。

硬规则：

- numeric 不等于 measure；
- ID / UID / order_id / transaction_id / hash / code 等 identifier 禁止机械 SUM / AVG；
- temporal / categorical / state / continuous numeric / discrete numeric / identifier / unit 必须区分；
- measure 必须记录 unit、aggregation_class 与 allowed_aggregations；
- rate / percentage / pre-aggregated KPI 默认 non-additive；
- currency / asset 等单位不兼容时，禁止因图表需要而强行合并。

Field Catalog 是后续 Domain、Analysis、SQL 和 Chart 的共同事实源。组件不得各自重新猜字段类型。

## 3B. Domain Intelligence Gate

完成 Source Map / Dataset Map / Quality Gate 后，先读取 `references/domain-routing.md`。

执行：

```text
Domain Detection
→ Confidence
→ Domain Pack or Generic Fallback
```

规则：

- 只有用户明确指定领域，或对应 Domain Pack 的 Detection Signature 成立且领域证据一致时，才加载 Domain Pack；
- medium / high confidence 才默认启用；low confidence 使用 generic；
- Domain Pack 只能提供候选 ontology / questions / metrics / playbooks / visual grammar，不能覆盖 Source / Quality / Unit / Time Gate；
- 当前数据不支持的领域模块必须跳过；
- 加载 Domain Pack 后仍必须执行 Generic Analysis Depth / Investigation / Robustness；
- 用户明确要求 generic 时不得自动套领域 Pack。

当前仓库已有 `domains/exchange-funds-flow/domain-pack.md`。只有当前数据真实匹配时才读取。

## 3C. Dashboard Mission Gate

完成 Source Map / Dataset Map / Quality Gate 后，必须读取 `references/dashboard-quality-framework.md`，建立 Dashboard Mission Contract：

- Primary Business Question；
- Audience；
- Dashboard Mode；
- Decision / Action；
- Population；
- Period / As-of；
- Comparison Basis；
- Cadence；
- Core Objects；
- Evidence Path；
- Known Limits。

如果用户没有明确业务问题，只能从数据与任务推导最合理的分析任务，并明确推导依据。禁止编造业务目标。

## 4. 按领域问题与业务主题拆分，而不是按表拆分

如果加载 Domain Pack，先从领域 Question Library 生成候选问题；否则使用通用主题。只保留当前 Schema 与证据真实支持的主题，例如：

- 数据可信度；
- 规模与趋势；
- 结构与构成；
- 用户/实体集中度；
- 状态与流程健康度；
- 异常与变化；
- 多表关联与下钻。

一张表可以进入多个主题，多张表可以共同回答一个主题。禁止“一张表一个看板”。

## 4A. Analysis Depth Gate

主题拆分后必须读取 `references/analysis-depth.md`。

先生成 Question Map，再做分析；禁止从字段直接跳到图表。

只要数据支持，分析不得停在“总量 + 趋势 + TopN”。默认至少完成：

```text
L0 数据可信度
→ L1 基线
→ L2 分布 / 分层
→ L3 时间变化、L4 关系 / 流程、L5 驱动 / 异常中至少一个高价值方向
```

优先寻找能改变判断的差异：分布、标准化指标、完成率、时延、费率、集中度、跨表关系、流程损耗、cohort、异常和贡献拆解。

如果数据只支持浅层描述，必须明确说明限制，不得把 L1 包装成完整分析。

## 4B. Investigation Gate

完成第一轮 Analysis Depth 后必须读取 `references/investigation-loop.md`。

任何准备进入核心看板的主要现象，第一次出现时只能标记为 `Observed Pattern`，不得直接升级为 Insight。

必须建立：

```text
Candidate Triage
→ Question Frontier
→ Hypothesis Frontier
→ Diagnostic Test
→ Robustness Check
→ Finding Promotion Gate
→ Portfolio Synthesis
```

硬规则：

- 先按 Decision Dependency / Materiality / Evidence / Actionability / Non-redundancy 做 Candidate Triage，禁止对所有 Pattern 平均用力；
- 每个 P0/P1 Pattern 至少检查一个合理竞争解释；
- 查询结果必须改变 Question Frontier 或 Hypothesis 状态，否则视为低价值查询；
- 关键结论至少做一次稳健性检查；
- 数据不足时保持 `unresolved`，不得补故事；
- 只有通过 Finding Promotion Gate 的结论才能参与 Portfolio Synthesis；
- 首屏优先展示综合后的 Executive Thesis，而不是把 Promoted Findings 平铺成卡片；
- Context Metric、Secondary Lead 与核心 Thesis 必须分层；
- 停止条件是边际信息增益下降，不是“所有维度都查过”。

## 4C. Comparison & Metric Role Gate

必须执行 Dashboard Quality Framework 的 Metric Role Gate 与 Comparison Context Gate。

- 指标分为 Primary KPI / Driver / Guardrail / Diagnostic / Context；
- KPI Card 只突出真正需要快速判断的 Primary KPI / Guardrail；
- Primary KPI / Finding 必须有合理比较语境，或明确写 `no meaningful comparison available`；
- 主要比较对象必须同时可见；禁止用切换 Filter 代替比较。

## 5. 指标选择

每个指标必须写清：

```text
业务问题 → 指标 → 粒度 → 分母/口径 → 数据来源 → 限制
```

优先级：

1. 直接回答业务状态的核心 KPI；
2. 解释变化的趋势/结构；
3. 定位问题的异常/Top 对象；
4. 可继续下钻的明细。

同一信息不重复展示。

指标不是洞察。只有经过 Investigation Gate 的 Pattern 才能晋级为核心 Finding。

## 6. Adaptive TopN

Top N 由有效样本数决定：

- active ≤ 10：优先 Top 1 / Top 3；
- 10 < active < 100：Top 5 / Top 10；
- active ≥ 100：Top 10，可增加 Top 1%。

如果 Top N 覆盖全部对象，它不能作为“集中度”核心结论。

## 6. Domain Composition Gate

若加载 Domain Pack，Portfolio Synthesis 后必须把 Promoted Findings 映射到领域工作流，而不是直接按 generic finding 类型排版。

Exchange Funds Flow 示例只能在数据支持时使用：

- Funds Scale & Trend；
- Flow Health；
- Deposit / Withdrawal Structure；
- Entity Exposure；
- Rail / Network Diagnostics（可选，不得默认抢占主位）；
- Flow Pattern Investigation；
- Evidence Queue。

Domain Composition 是候选工作区，不是固定页面模板。

至少检查：

1. 是否有一个领域专属工作流真实改变页面结构；
2. 是否保留该领域关键状态语义，而不是压成 generic completion / trend；
3. 是否能从领域 Signal 落到真实实体 / 事件 / evidence；
4. 是否出现 Domain Pack 不支持的字段或动作。

## 6A. Analysis Spec Gate

Domain Composition / Portfolio Synthesis 后，任何准备进入 Dashboard 的 KPI、Chart、Table 都必须先生成统一 Analysis Spec。

必须读取：

- `references/analysis-spec.md`；
- `references/renderer-contract.md`；
- 仅在选择 Chart.js Adapter 时读取 `references/chartjs-compiler.md`。

唯一允许的视图生成链路：

```text
Field Catalog
→ Analysis Intent
→ Dimension / Measure
→ Aggregation
→ Chart Family
→ X / Y / Series
→ Analysis Spec
→ DuckDB SQL
→ Result Contract
→ Visual Spec
→ Renderer Adapter
```

Analysis Intent 使用中性关系：

`level / trend / category_comparison / composition / distribution / relationship / ranking / detail`

图表生成层不得预设 `异常 / 风险 / fraud` 等结论。领域或 Investigation 已确认的 Finding 只能决定“值得展示什么”，不能绕过 Analysis Spec。

硬规则：

- Chart / KPI / Table 组件禁止直接访问 DuckDB；
- 组件禁止自行拼 SQL、决定聚合、改变 TopN、时间粒度或 Series；
- Global Filter 先 patch Analysis Spec，再由统一 Analysis Engine 重编译 SQL；
- KPI / Chart / Tooltip / Table 必须共享同一 measure definition 与 formatter；
- SQL 结果 grain 必须与 Spec 一致；
- Renderer Adapter 只消费 Result Contract / Visual Spec，不接触原始表；
- Renderer 不得因库的能力边界改变 Analysis Intent；
- 用户明确指定 Renderer 时，只要其能忠实表达语义，就优先遵循用户选择。

## 6B. Information Architecture Gate

Portfolio Synthesis 完成后，必须再次使用 `references/dashboard-quality-framework.md` 生成 Dashboard IA Plan。

Dashboard 必须尽量形成：

```text
What
→ So What
→ Why
→ Who / Where
→ Evidence
```

模块按功能定义：状态、变化、异常、解释、定位、下钻。不是固定模板，也不是固定数量。

首屏必须优先完成：

- 当前最重要状态；
- P0 / P1 问题；
- 进入解释、对象或明细的下一步入口。

禁止：

- KPI / Finding 同权卡片堆砌；
- 长篇文字先于核心状态；
- 所有模块使用相同视觉权重；
- 把 supporting evidence 当首屏主体。

## 6C. Redundancy Gate

Information Architecture 完成后，逐组件执行“信息增量”检查。

核心规则：**一个业务问题只保留一个主表达。第二个组件必须回答新的问题，否则删除或合并。**

逐项检查：

- KPI 已回答“当前是多少”后，趋势图只负责“怎么变”，不得再做一套同值总额表；
- 同一时间序列如果只是 amount / count 或 total / deposit / withdrawal 的视角切换，优先使用一个主图 + metric / direction control，而不是并排复制多张同构图；
- 图上永久 Label 已能精确读值时，不再额外放一张逐期 totals table，除非表格承载额外字段或核查任务；
- status summary 与 status composition 重复时合并成一个紧凑状态组件；
- ranking chart 与同字段 ranking table 重复时，只保留一个主视图；需要精确核查时，将 bar-in-cell 合并进 table；
- Signal 卡片与 Evidence Queue 指向同一异常时，优先合并为一个可下钻 Queue；
- 同一个筛选/操作说明不要在每个 Panel 重复，只保留一处最小必要提示；
- 第二个组件只有在新增 `time / segment / distribution / denominator / evidence / exact lookup` 等信息时才允许保留。

每个组件必须回答：

```text
它比页面上已有内容新增了什么信息？
```

答不出来 → 删除。

验收：默认视图应尽量形成最短链路：

```text
核心水平 → 变化 → 结构 / 驱动 → 对象 → 证据
```

## 7. 图表与布局

每张图先写一句：`这张图回答什么问题？`

答不出来就删除。

必须读取 `references/visualization-registry.md`。图表选择由 Analysis Intent + Field Shape 决定，不由当前 Renderer 原生支持列表决定。

X / Y / Series、时间粒度、排序和 TopN 必须来自 Analysis Spec，禁止在组件中写死。

基础映射仅是最低覆盖，不是能力上限。Renderer 必须按 `references/renderer-contract.md` 选择：金融 / 资金时间序列优先考虑 Vela；通用分类、构成、分布、关系可使用 Chart.js；KPI、状态结构、明细和简单排名可优先原生 HTML/CSS。禁止因为渲染器方便而改变分析语义。

默认映射：

| 问题 | 优先形式 |
|---|---|
| 当前水平 | KPI / 数字卡 |
| 时间变化 | 折线 / 面积 |
| 类别比较 | 条形图 |
| 构成 | 100% 堆叠 / 环形（类别少时） |
| 集中度 | 排名条形 + 累计占比 |
| 两群体重叠 | 集合数字 / 简洁交叉表 |
| 异常对象 | 排名表 / 明细表 |
| 数据质量 | 审计表 |

禁止为视觉丰富度凑图、重复 KPI、滥用饼图或用装饰卡片替代分析。

## 7A. Interaction Gate

如果 Mission Contract 需要定位、验证或继续调查，且数据存在稳定对象键，必须提供至少一种真实分析交互，例如：

- 筛选；
- 点击交叉筛选；
- drill-down / drill-through；
- 对象详情；
- 明细抽屉 / 明细表；
- TopN 展开。

交互后相关 KPI、图表和明细必须使用一致数据范围。

如果用户明确要求静态导出、截图或汇报页，可以不强制交互。

### 7B. Display & Label Gate

最终 Dashboard 还必须满足：

- 主要语言跟随用户语言；中文任务以中文作为 UI 主语言，必要业务缩写除外；
- 不向业务用户暴露 Analysis Spec / Compiler / Regression / Generated by 等开发过程；
- 删除重复提示、教程式说明和无决策价值的废话；
- 用户要求 permanent Label 时，Tooltip 不能替代；
- vertical bar 的值默认放柱顶外侧，horizontal bar 放柱尾外侧，line / point 放点位上方；
- Label 必须有 collision avoidance 与边缘留白，禁止与 mark / axis / legend 重叠或被裁切；
- hover / focus / selected / empty 在浅色和深色主题下都必须连续一致。

## 8. 页面层级

默认阅读顺序：

```text
Executive Thesis / 关键限制
→ Supporting Findings
→ Context Metrics
→ 解释证据与稳健性
→ Secondary Leads / Open Questions
→ 下钻明细
→ 数据质量与口径
```

首屏不得只是 KPI 或 Finding 卡片集合。Executive Thesis 必须来自 Portfolio Synthesis，并能回指 supporting Finding、Pattern、竞争解释、Diagnostic Test 和 Robustness。

页面还必须提供从 Thesis / 异常到具体对象或证据的清晰路径。

如果数据质量问题会改变核心数字，限制必须靠近 KPI，不得藏在页尾。

## 9. 数据刷新

数据更新后：

1. 重新扫描 Schema 与质量；
2. 重算主题和指标；
3. 仅在证据变化时新增/删除图表；
4. 不把旧数据集的字段、指标、图表写死到新数据集。

验收：换成结构明显不同的数据集，仍应重新理解并生成不同看板。

## 10. HTML / Dashboard 输出

需要 HTML 时：

- 使用 Renderer Contract，不再把 Chart.js 写死为唯一默认；
- 金融 / 资金时间序列如需 zoom / pan / crosshair，可优先 Vela；
- generic 分类图可使用 Chart.js；简单结构可直接用原生 HTML/CSS；
- 使用真实计算结果，不在 Renderer 中重新推导数字；
- 核心指标、口径和来源可追溯；
- 桌面与移动端均不得整页横向溢出；
- 长表局部滚动；
- 交互必须有明确作用，不为“像产品”增加无意义控件；
- 不依赖外部库也应保留可读 fallback（如果成品要求离线可用）；
- 执行 Visualization Registry + Renderer Contract：原生能力 → plugin / custom adapter → 同语义等价变体 → table/native fallback；禁止为了“能画”而改变分析语义；
- 所有组件必须可回溯到 Analysis Spec ID 与统一 Query / Result Contract。

最终 Dashboard 不得把 Question/Hypothesis Frontier、Diagnostic Test、Quality Evaluation、Regression 状态等内部生成过程当作页面模块展示，除非用户明确要求审计过程。

生成后必须执行：

1. `eval/dashboard-quality.md`；
2. `references/regression-loop.md`。

执行：

```text
Generate
→ Evaluate
→ Detect Problems
→ Revise
→ Evaluate Again
→ Final
```

任何 Critical 或 Major Dashboard Quality 问题未清零，禁止 Final。

## 11. 停止条件

只有同时满足才完成：

- 无已知 P0/P1 数据逻辑问题；
- Analysis Depth Gate 已完成，或明确记录数据为何无法继续下钻；
- Investigation Gate 已完成；
- 每个核心 Finding 已通过 Finding Promotion Gate，或明确标记 unresolved；
- Candidate Triage 与 Portfolio Synthesis 已完成；
- Semantic Field Catalog 已完成；
- Domain Detection 已完成；若加载 Pack，Domain Evaluation 已通过；
- Dashboard Mission Contract 已完成；
- 所有 Dashboard 组件已有 Analysis Spec，SQL / Result Contract / Visual Spec / Renderer Adapter 链路一致；
- Metric Role / Comparison Context Gate 已完成；
- Default View 在无交互时已能完成 Primary Job；
- Information Architecture Gate 已完成；
- 需要定位/验证时 Interaction Gate 已完成；
- 首屏 Thesis 已合并重复驱动并按价值排序；
- 每个核心图表都回答明确问题；
- Visual Plan 与 Renderer Capability Gate 已完成；
- 关键指标口径可追溯；
- 无重复 KPI / 图表 / totals table / signal card；
- Redundancy Gate 已通过，每个保留组件都有独立信息增量；
- Dashboard Quality Evaluation：Critical=0 且 Major=0；
- Rendered QA 通过；
- 新发现的可泛化缺陷已回写 Skill 并复测。

# Skill Change Log

## V1：真实四表数据集回归

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 单日汇率覆盖跨期交易，初版仍可能生成“历史成交额” | 只有“识别指标”，没有时间维表语义门 | 新增 Time-dimension Gate | exact → as-of → snapshot → blocked；snapshot 必须改名 |
| 9 个活跃用户如果默认 Top10，会把全体当集中度 | 初版只有 Top/Bottom，没有样本自适应 | 新增 Adaptive TopN | active ≤10 使用 Top1/Top3；覆盖全体不得当集中度结论 |
| 数据中存在订单 ID 日期与 created_at 冲突，初版可能直接出 KPI | 缺少 KPI 前置数据质量门 | 新增 Quality Gate | 会改变解释的数据异常必须显式 LIMITED/BLOCKED |
| 初版要求“生成看板”，但没有验证 HTML 实际可读 | 只约束生成，没有渲染验收 | 新增 Rendered QA | DOM、JS、响应式、内容覆盖、限制位置都需验证 |


## V2：分析深度与可视化能力

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 看板主要停留在总量、结构、TopN，真实数据中的完成率、时延、分层集中度、跨表关系等没有被主动发现 | 缺少“分析到什么深度才算完成”的生成规则 | 新增 Analysis Depth Protocol 与 Question Map | 数据支持时必须从 L0/L1 推进到 L2，并至少探索 L3/L4/L5 中一个高价值方向 |
| 图表映射只有 KPI、折线、条形、堆叠、排名和表格，复杂分析只能被压回基础图 | 图表类型被主 Skill 的简化映射和 Renderer 能力反向限制 | 新增 Visualization Registry 与 Renderer Capability Gate | 先按问题选分析语义，再解决渲染；支持分布、关系、矩阵、流程、贡献、流向、层级、网络和地理等图形 |
| “支持更多图”容易演化为为了丰富页面强行增加图形 | 缺少信息增量约束 | 注册表明确不追求图形数量 | 图形多样性不能替代分析价值；重复图只有在回答不同问题时保留 |


## V3：来源角色与指标权威性

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 真实工作簿有 11 个 Sheet，但只有核心事实/实体/参考表应直接进入业务指标；expected、QA、dashboard、backup 若一视同仁会造成重复分析或污染人口 | 缺少表角色识别 | 新增 Source Role & Metric Authority Protocol | 先做 Source Map；事实/实体用于计算，规则/expected/QA 用于约束和对账，dashboard/backup 默认排除 |
| 数据集修复日志明确禁止跨币种混同汇总，但旧回归把 144,444 USDT 快照估值放在核心锚点 | 只做 Time-dimension Gate，没有检查业务规则是否允许跨单位聚合 | 新增 Unit Authority Gate | 时间上可换算不等于业务上可聚合；原生单位口径优先，统一估值只能是明确标记的辅助分析 |
| 原始表与 expected/summary 同时存在时，模型可能重复累计 | 缺少来源权威与 double-count 规则 | 新增 Authority Order 与 Double-count Gate | canonical aggregate 用于对账，不作为额外事实再次 SUM |


## V4：图例与标签碰撞

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 真实 HTML 的双序列月度折线只有颜色，没有可见图例 | Visual Registry 缺少多序列识别验收 | 新增 Encoding & Label Gate | 多序列必须有直接标签或可见图例，不能只靠颜色 |
| 法币渠道 scatter 的低时延点聚集，直接标签互相覆盖 | 只要求可读标签，没有 collision gate | 增加标签碰撞处理顺序 | 重叠时减少直标、只标关键点、tooltip 或 label repel；禁止文字覆盖 |


## V5：Hypothesis-driven Investigation

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 看板虽然分析层级更多，但发现一个差异后仍会直接画图，缺少“为什么”的连续调查 | Analysis Depth 只规定查哪些层，没有规定一个发现何时才算解释完成 | 新增 Hypothesis-driven Investigation Loop | Pattern 必须经过竞争解释、Diagnostic Test、Robustness 后才允许晋级 |
| Top1/Top3、KYC 占比、ACH 时延等容易被直接包装成结论 | 缺少 Finding Promotion Gate | 新增 Pattern / Finding 分离 | 指标和差异不是洞察；核心 Finding 必须排除至少一个替代解释并做稳健性检查 |
| 深挖容易退化成“再按一个维度切一下” | 缺少 Question Frontier 与信息增益停止规则 | 新增 Question Quality Gate / Information Gain Stop Rule | 下一问必须改变解释或路径；结果不改变 Frontier 的查询默认淘汰 |


## V6：Explicit Scope Gate

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 用户本轮明确只允许 4 张表，但 Source Authority 仍写“扫描工作簿每张表”，同一工作簿还存在 expected / QA / dashboard / backup | 缺少显式输入范围优先级 | 新增 Explicit Scope Gate | 用户指定范围是硬边界；metadata 可用于解析表名，但范围外内容不得读取、引用或影响当前分析 |


## V7：Finding Priority & Portfolio Synthesis

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 稀有但影响窄的异常容易和真正高影响发现同级进入首屏 | Finding Promotion 只检查证据闭环，没有全局 materiality / dependency / actionability 排序 | 新增 Candidate Triage Gate | “异常”不等于“重要”；P0/P1 才默认进入完整调查，P2 保留为 Secondary Lead |
| 多个 Finding 分别正确，但首页仍像分析卡片堆叠，没有主线 | Dashboard Promotion 逐条消费 Finding，缺少跨 Finding 合并和综合 | 新增 Portfolio Synthesis Gate | 共享驱动/实体/证据的 Finding 必须合并为 Executive Thesis，并按价值排序 |
| 同一底层驱动可能同时表现为群体占比、实体集中等多个现象，造成重复结论 | 缺少跨 Finding redundancy / contradiction 检查 | 增加 Merge + Contradiction Check | 首页展示 1–3 条主 Thesis，Supporting Findings 放到证据层 |


## V8：Dashboard Quality Framework

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 分析结果正确，但最终页面更像“带图分析报告”，不是可操作 Dashboard | Skill 只有分析、图表和 Rendered QA，没有 Dashboard Mission / Information Architecture / Interaction 的完整生成协议 | 新增 Dashboard Quality Framework | Dashboard 必须从业务问题进入信息链，而不是从 Finding 直接进 HTML |
| 当前页面可读但不能从异常继续定位对象或验证明细 | 交互只写“可选”，没有任务条件下的 Interaction Gate | 新增 Interaction Gate | 当任务需要定位/验证且存在稳定对象键时，静态页面默认不足；静态汇报任务除外 |
| Rendered QA 能发现溢出、标签碰撞，却不能判断“这是不是一个好 Dashboard” | 评估集中在技术渲染和局部视觉，没有业务价值 / 分析闭环 / IA / 交互严重度 | 新增 `eval/dashboard-quality.md` | Critical / Major 必须清零；Minor 后处理；禁止简单平均分 |
| KPI、Finding、证据都正确，但页面仍可能无清晰工作路径 | 缺少从 What 到 Evidence 的信息架构约束 | 新增 Dashboard IA Plan | 首屏必须给状态、重点和下一步入口，后续形成解释→定位→证据 |
| 移动端完整筛选区使用 sticky 后会持续挤压分析视口 | UI Gate 只检查响应式宽度，没有检查控制区占屏 | 增加 Mobile Control Viewport 规则 | 窄屏 sticky filter 必须折叠、收起或取消 sticky，不能长期压住核心内容 |


## V9：Dashboard Context / Comparison / Drill Semantics

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 当前真实 HTML 把历史覆盖期模块写成“当前状态”，但没有 as-of / period 语义 | Dashboard Mission 缺少 Population / Period / Comparison / Cadence | 扩展 Mission Contract | 没有当前语义时必须写 scope snapshot / 截至某日，禁止伪造“当前” |
| KPI 有数值但角色混杂，Context / Diagnostic 容易与真正 Primary KPI 同权 | 只有指标选择，没有 Metric Role | 新增 Metric Role Gate | Primary KPI / Driver / Guardrail / Diagnostic / Context 明确分层；卡片不是默认容器 |
| “定位异常记录”点击后落到用户 Fiat 详情；“查看 ACH 明细”只选用户后展示全部 Fiat | Interaction Gate 只要求存在交互，没有上下文保真 | 新增 Interaction Semantics + context-preserving drill | Drill 必须携带对象键、筛选、触发条件和记录键，落到正确证据 |
| 最终 Dashboard 显示 Dashboard Quality Evaluation 模块 | 缺少 Internal Analysis Boundary | 新增内部分析与最终内容边界 | Evaluation / Hypothesis / Regression 默认不进入最终 Dashboard |
| 主要比较可能依赖用户切换 Filter | 缺少 Comparison Context Gate | 新增 Comparison Gate | 核心比较同时可见；Filter 不能替代比较 |


## V10：Domain Intelligence Layer

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 对特定领域数据仍生成 generic BI：completed、TopN、trend、latency 各自成块，但缺少领域工作流 | Skill 有通用分析模型，没有 Domain Detection / Ontology / Question Library | 新增 Domain Intelligence Routing | 先判断领域，再让领域问题驱动分析；低置信度回退 generic |
| 交易所资金流无法自然形成 Flow Health / Rail Performance / Entity Exposure / Flow Pattern / Evidence Queue | 通用主题不知道资金流对象、状态与调查路径 | 新增 exchange-funds-flow Domain Pack | Domain Pack 提供候选 ontology / metrics / playbooks / visual grammar，不固定页面模板 |
| 领域异常容易被误解成风险定性 | 缺少领域边界 | 新增资金流 Domain Evaluation | rapid in-out 等仅为 flow pattern，不得自动定性 fraud / laundering |
| 专业 Dashboard 缺乏领域级验收 | 只有通用 Dashboard Evaluation | 新增 domain-specific evaluation | 通用“好 Dashboard”与“好资金流 Dashboard”分开验收 |


## V11：Semantic Field Catalog → Analysis Spec → DuckDB → Chart.js

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 图表虽按问题选型，但 X/Y/Series、聚合和时间粒度仍可能由组件临时决定 | 缺少统一中间表示 | 新增 Semantic Field Catalog + Analysis Spec | 先识别字段语义，再生成统一 Spec；图表组件无判断权 |
| numeric ID 容易被通用数值逻辑当 measure | 物理类型与业务语义没有分层 | 新增 Identifier Gate | ID 仅 count/distinct/detail/drill，不机械 SUM/AVG |
| KPI / 图 / 表可能各自查询、导致口径漂移 | 查询所有权分散 | 新增 Central Query Ownership | Analysis Engine 独占 DuckDB SQL；组件只消费 Result |
| Filter 可能在前端各组件本地处理 | 缺少统一 Filter → Query 链 | Filter patch Spec 后重新编译 | 同一 Filter State 驱动所有依赖组件 |
| 图表类型正确但轴/Series/TopN 写死 | Chart plan 不可执行 | 新增 Chart.js Compiler | X/Y/Series/time grain/sort/TopN 全部来自 Spec |
| 图表层可能把“异常/风险”作为预设分析类型 | Investigation 与 visualization 职责混合 | 新增 Neutral Visualization Rule | chart intent 只描述数据关系；结论由上游证明 |


## V12：Funds Scale 主轴 + Renderer Contract

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 资金流看板先做状态、channel、network，却没有“总额随时间变化” | Domain Pack 把 Flow Health / Rail Performance 放得过重，没有定义资金规模第一主轴 | 新增 Funds Scale & Trend + Deposit / Withdrawal Structure | amount + direction + time 存在时，金额/笔数及其时间变化优先于 rail/network |
| 只看总额或笔数，无法判断资金规模如何变化 | Trend 仍偏事件计数，没有 amount time-series 硬规则 | Primary Axis 验收加入 amount over time + count over time | level 必须与 time trend 成对；金额与笔数相互校验 |
| 单日 FX 被用于跨期统一趋势时容易被误读为历史真实成交额 | snapshot 限制只写在数据层，没有贯穿标题/tooltip | Snapshot 口径贯穿 Visual Spec | reference/snapshot 必须在 KPI、图标题、tooltip/data window 持续可见 |
| Chart.js 被写死成全局唯一 Renderer | Analysis Spec 与具体库耦合 | 新增 Renderer Contract | Result → Visual Spec → Renderer Adapter；Renderer 不拥有业务逻辑 |
| 金融时间序列需要缩放、拖拽、crosshair，同普通 BI 图交互不同 | 缺少金融时间序列 Renderer 路由 | Vela Adapter 路由 | 资金/金融时间序列可优先 Vela；离线业务数据默认不接实时 provider |
| 中文看板混入大量英文与开发术语 | 缺少 Display Contract | 新增 locale / UI Copy Gate | UI 跟随用户语言；内部 Analysis/Compiler/Regression 默认隐藏 |
| permanent Label 与柱体重叠 | Label 规则只要求“显示”，没有位置与碰撞约束 | 新增 Label Policy | 外置优先、collision avoidance、padding、防裁切 |
| 图表可点击但选中状态不明显 | 交互只有行为，没有视觉状态契约 | Interaction Contract | click/filter/selected/table linkage 使用统一 Filter State 与可见 selected state |


## V13：Redundancy / Compression Gate

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 同一总额在 KPI、双趋势图、Label 条、逐期 totals table 多次重复 | 只检查单组件正确，没有检查页面级信息增量 | 新增 Redundancy Gate | One Question → One Primary View；第二视图必须提供新维度 |
| amount / count 与 total / deposit / withdrawal 被复制成多张同构时间图 | 把指标数量误当成图表数量 | 主趋势使用 metric / direction control | 同构视图优先切换，不机械复制 |
| 用户集中 ranking chart 与同值 table 重复 | chart / table 职责未区分 | bar-in-cell table 合并比较与精确读值 | table 只有增加 lookup / attributes / action 时才与 chart 共存 |
| Signal 卡片与 Evidence Queue 重复同一异常 | Finding 展示与 Evidence 入口分离过度 | 合并为 Queue + detail | 同一异常只保留一个主入口 |


## V14：Dashboard Audit Loop

| 反复暴露的问题 | 根因 | 修正 |
|---|---|---|
| 每轮都靠用户指出新问题 | 只有生成规则，没有系统 rendered audit | 新增 Dashboard Audit Loop |
| 页面组件越改越多 | 缺少 Decision Questions 与 Coverage Plan | 生成前锁定 2–5 个问题，每个问题一个 Primary View |
| AI 会顺手增加“看起来专业”的模块 | 没有 coverage reconciliation | required 元素逐项对账，孤儿组件必须删除或回写问题 |
| UI 修复长期靠局部 padding | 没有全局 token 与跨组件一致性检查 | 统一 type/spacing/gutter/radius/control/state tokens |
| 正常数据没问题，窄屏/空数据破版 | 只验证 happy path | 新增 Real / Constrained / Edge-data User Simulation |
| node --check 被误当成 UI 验收 | static QA 与 rendered QA 边界不清 | 明确 360/768/1280 rendered audit；无法渲染必须披露 |
| 同类错误重复出现 | 修当前 HTML，没有 durable fix | 两轮复现强制升级为 Skill rule / regression / checker |


## V15：Insight Hierarchy / High-Value Dashboard

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| UI / Audit Loop 更完整，但用户仍感觉“质量完全没提升” | 主要优化生成与验收，没有强制 Dashboard 解释 North Star 为什么变化 | 新增 Insight Hierarchy Gate | North Star → Change → Driver → Exception → Evidence |
| 金额趋势高峰容易被直接称为增长 | 未检查金额与笔数是否同步，也未检查 top transaction share | 新增 Amount × Count + Event-Driven Spike Gate | amount 涨、count 平时优先查 ticket / concentration；Top1 主导则写事件驱动 |
| Fiat 金额高容易停留在“类型差异” | 没有 breadth / intensity / concentration 分解 | 新增 Driver Decomposition | 优先解释规模来自对象广度、典型单笔还是集中度 |
| KYC3 高金额占比容易被写成群体洞察 | segment 被 Top 用户混淆 | 新增 Pareto + confounding rule | 先查 Top1/Top2/remove-Top1；标签结论必须经实体集中度校正 |
| 状态图展示 4 笔未终态但没有行动价值 | 只看状态占比，没有 amount materiality 与 evidence path | 新增 Exception Logic | materially large 的 in-process 应进入 Guardrail / Queue，并落到订单 |
| 小数据集也容易被套复杂模型 | “深度分析”被误解为方法复杂 | 新增 Analytical Restraint | 小样本优先 decomposition / Pareto / exact evidence，不乱做因果、聚类、预测 |


## V16：Decision Diagnostics / Multi-Architecture Evaluation

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| Top1 share ≥80% 会把低流水月份也叫“高峰” | 只有 Extremeness，没有先判断 Materiality | 新增 Materiality Before Extremeness Gate | 先选 materially important time bucket，再判断 event-driven |
| 核查队列出现模型自造 5000 USDT 优先线 | 缺少 Threshold Authority | 新增 Threshold Authority Gate | 业务红线只能来自用户 / policy / SLA / benchmark；否则只能相对排序 |
| 当前 TopN 容易被当成变化原因 | 横截面排名替代 movement attribution | 新增 Delta Contribution Gate | 解释变化优先量化谁贡献 delta |
| 核心解释虽有 robustness，但没有明确反证类型 | robustness 过于宽泛 | 新增 Control / Counterexample Gate | remove-Top / control segment / alternate denominator / alternate grain 至少一种 |
| 多方案测试容易退化成换皮肤 | 缺少 Candidate Architecture 约束 | 新增 Multi-Architecture Test | 候选共享口径，但 decision path 必须结构性不同 |


## V17：Evaluation Preflight / Fixture & Environment Blocking

| 暴露问题 | 归属 | 修正 |
|---|---|---|
| Requirement 声明真实 Fixture，但测试仓库没有原始数据 | Requirement / Fixture | 增加 Canonical Fixture Contract；锚点只能对账，不能替代原始行 |
| 浏览器超时导致 Rendered QA 永久 UNVERIFIED | Environment / Test Contract | 增加 Environment Capability Preflight 与 `BLOCKED_ENV` |
| Fixture 缺失与 Skill FAIL 混在一起 | Eval Contract | 增加 `BLOCKED_FIXTURE`，明确缺陷 Owner |
| Multi-Architecture 每轮都被当 mandatory | Requirement | 条件型 Case 未触发时使用 `NOT_APPLICABLE` |
| Core Logic 已过但视觉环境阻塞时只有一个总分 | Eval Reporting | 增加 Core / Fixture / Rendered / Overall 分层 Verdict |

## V19：Business Analysis Surface / Golden Reference

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 最新 E2E 仍用 WHAT / SO WHAT / WHY / WHO & EVIDENCE / PROVENANCE 作为顶层 section，页面本质仍是带图分析报告 | “不要像报告”只有抽象规则，没有 artifact-level boundary | 新增 Dashboard / Report Boundary Gate | 顶层 IA 使用业务对象 / 决策问题；分析流程词默认不得成为业务 section |
| Fixture / DuckDB SQL / Rendered QA 等状态仍进入业务页面，但回归 Case 仍判 PASS | Internal Analysis Boundary 缺少可执行反例与强制验收 | 将内部 QA 外露升级为 Major，并加入 V19 原失败回归 | 业务页与 audit artifact 分离；用户显式要求审计时才豁免 |
| 期间累计总量在没有 baseline / target / peer 时仍被当作 headline KPI | 现有 Metric Role 只分类角色，没有 KPI 资格判定 | 新增 Business Analysis Contract | Primary KPI 必须有 comparator + delta/difference + decision polarity；否则降级 Context |
| 规则越来越多，但模型仍自由拼装页面 | 缺少可复用的高质量 Dashboard composition 先验 | 新增 Golden Reference Catalog 与 Reference Fit Gate | Mission 先选 Archetype，再按 reference 的 decision path 构图；不复制字段/阈值/皮肤 |
| 核心判断需要滚动多屏后才能完成 | 只要求“首屏重要”，没有可验收的 viewport job | 新增 Primary Viewport Gate | 1280×900 不滚动必须完成 Primary Job，并显示变化/例外和下一步入口 |


## V20：Analysis Model / Mode-aware Hierarchy / Executable Golden

| 暴露缺陷 | 已验证根因 | 修正 | 可泛化规则 |
|---|---|---|---|
| V19 已是 Exploration，但页面仍显示 Context、Guardrail、Exploration | Metric Role / Mode 是内部分析元数据，却没有完整 UI 边界 | 新增 Internal Role Boundary + surface lint | 内部角色不得成为业务标签 |
| 页面仍有固定 takeaway 文案，整体像“自制 BI 网页” | So-What Gate 强制每个主图生成一句 takeaway，模型自然渲染成文字卡 | Takeaway 改为内部验收字段 | 优先用 comparator、delta、annotation、tooltip、drill 表达；文字不是默认组件 |
| 有 Archetype 仍缺业务分析能力 | Archetype 解决“页面怎么用”，没有决定“数据应该做哪类业务分析” | 新增 Analysis Model Catalog | 先选 1 个 Primary Model，再选 Golden |
| Reference Catalog 仍只是文字说明 | 模型没有可直接复用的 viewport hierarchy / component budget | 新增 6 个 executable Golden Blueprint | 每次只读取一个 Golden，数据不支持的 slot 删除 |
| North Star / Change / Driver 被所有模式复用 | Insight Hierarchy 不是 mode-aware | 重写 Insight Hierarchy | executive/monitoring/investigation/operational/exploration/entity 使用不同工作路径 |
| 正常生成需读取大量历史规则，注意力被测试资产稀释 | Runtime reference loading 没有预算 | 新增 Reference Loading Budget | regression/change-log 只在测试或 Skill 优化时读取 |

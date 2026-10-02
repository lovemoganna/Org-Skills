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

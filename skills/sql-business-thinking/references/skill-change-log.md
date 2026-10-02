# Skills 缺陷沉淀

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| V2 首屏 Hero 源码逻辑有内容，但最终 HTML 实际为空 | Renderer 改为整块原子替换；验收加入真实渲染烟测 | 生成 Artifact 后必须验“渲染结果”，不能只验 DOM/源码意图 |
| 主问题要求“每个用户总交易额”，正文只展示 Top 用户 | 正文加入全量用户 Answer Block | 每个分析问题必须映射到正文可见结果，附录不能替正文回答 |
| Native DuckDB `httpfs` 加载路径直接复制到 DuckDB-Wasm | Wasm 使用 browser VFS / registerFileURL；只按 Wasm 支持加载 excel | 同一数据能力在不同运行时必须有 Platform Contract |
| 汇率表只有单日快照，却容易机械按 asset JOIN | 加 exact-date → as-of → snapshot 路由，结果命名随口径变化 | 时间维表必须先定义业务时间点和匹配策略 |
| 汇率表未来增加多日后会造成 JOIN 膨胀 | 聚合前强制右表键唯一 + JOIN 前后行数 | 金额 SUM 前必须通过 JOIN Cardinality Gate |
| Top 10 在 10 用户样本中等于 100% | Top N 随 active population 自适应 | 覆盖全部样本的 Top N 不能作为核心集中度指标 |
| 报告迭代容易只调 UI，不修生成机制 | 新增 Artifact Regression Loop，每轮缺陷必须回写 Skill | 结果修复和生成规则修复必须闭环验证 |
| Skills / Debug 元信息容易抢主报告 | 正文按决策价值，审计轨迹二级展开 | 过程是证据，不是页面主角 |
| 显式要求人物会话，却被“过程信息默认折叠”规则一起藏进附录 | 增加 Dialogue Coverage Gate；正文展示关键纠错回放 | 用户点名的人物会话属于交付物，不得按过程噪声降级 |
| 人物会话、SQL、Skill Trace 交错，角色阅读被不断打断 | 拆成三条信息通道 | 教学叙事 / 可执行证据 / 内部路由必须解耦 |
| Lucy 台词混有状态机语气，人物感弱 | 增加 Character Contract：先结论后依据、≤3 句、内部流程标签不进台词 | 角色只说推动当前阶段的话；流程元信息交给 UI |
| 移动端高维排名表被压缩到难读 | 保持表格最小宽度，容器内局部横向滚动 | 高维表优先局部滚动，不靠缩字号塞进一屏 |
| 会话像彼此独立的纠错卡，没有任务起点和汇报终点 | 增加 Conversation Arc Contract | 角色模拟必须覆盖 Assignment → Evidence → Revision → Synthesis → Report-back |
| Star 被写成错误制造器，Lucy 像全知专家 | 重分角色职责：Star=Analysis Owner，Lucy=Reviewer | Owner 必须提出假设、更新判断并完成最终汇报；Reviewer 只挑战和验证 |
| 对话存在“对 / 明白”等低信息回合 | 增加 Turn Delta Gate | 每句必须新增 FACT / JUDGMENT / QUESTION / DECISION，否则删除或合并 |
| 人物提前知道尚未跑出的最终数字 | 增加 Progressive Knowledge Gate | 角色只能使用当前阶段已经出现的事实，禁止结果倒灌到前文 |
| 最终汇报与前序讨论缺少显式追溯 | 增加 Report-back Traceability Gate | 最终每个关键结论必须能回指至少一个前序证据节点 |
| 正文已经重构会话，附录仍保留旧版人物全文 | 权威会话只保留一个版本 | 同一信息只保留一个权威叙事，旧过程日志不得造成“双重真相” |

## V6：代码必须在会话中产生

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| 人物讨论与 SQL 被拆成两条信息通道，代码像事后补证据 | 把每一步改成“对白 → 当前 SQL → Result → 基于结果继续对白” | Code-in-Conversation Contract：代码必须原位产生，不能集中后置 |
| 人物先说出数字，后面才看到 SQL / Result | 加 Result Dependency Gate | 具体数字第一次进入台词之前必须已有可见证据节点 |
| 会话阶段用累计摘要反复复述全局结论 | 删除 rolling summary，仅保留局部状态变化和最终 report-back | No Rolling Summary：推进中只处理当前问题，跨阶段汇总延后 |
| 查询动机、代码、结果相隔太远 | 强制 Evidence Adjacency | 产生判断的 evidence 必须与该判断相邻 |
| 正文有 SQL，附录又复制一套 SQL | 删除 SQL 副本，保留 Skill Trace | Single Code Source：同一查询只保留一个可执行实例 |
| “决策价值优先”的报告规则与教学推演认知顺序冲突 | 增加 Dialogue-Driven Report Override | 用户要求看推理形成过程时，认知顺序优先于管理层摘要顺序 |

## V7：代码增长与单步定位

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| “SQL 出现在会话里”但仍是完整 SQL 突然出现 | 加 Code Growth Gate，要求至少一次对白触发的可见代码增量 | Code-in-Conversation 还不等于 Code-Growth；逐步生成必须可见 |
| 一个阶段塞多个 SQL，读者失去当前判断点 | 加 One Step One Query | 一个推进点 = 一个问题 + 一个最终 SQL + 一个 Result + 一个判断变化 |
| Result 后又用旁白做“这一步确认 / 截至目前”汇总 | 改由 Star/Lucy 自己说出刚刚发生的状态变化 | Human State Transition：角色模式下状态变化由角色承担 |
| 中间不断滚动汇总，干扰当前推进点 | 禁止跨阶段累计摘要 | Local Context Only：推进中只保留当前问题、当前证据和下一判断 |
| 草稿 SQL 与正式 SQL 容易形成双重事实源 | 草稿标“不单独执行”，正式 SQL 保持唯一可执行实例 | Draft vs Executable Contract：草稿只展示增量，不形成第二套权威代码 |


## V8：默认人物角色统一命名

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| 默认人物角色命名需要统一，旧默认名曾散落在主协议、渲染协议、回归样本和历史规则中 | 将默认角色统一为 `Star/Lucy` | 默认角色名属于跨文件契约；但用户当前请求显式指定的角色名必须优先于默认值 |


## V9：角色绑定优先级

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 真实测试明确要求 `Yone/Carmen`，但 Skill 与仓库测试把默认 `Star/Lucy` 当成不可覆盖硬编码，导致无法忠实执行当前输入 | 新增 Role Binding Gate：显式人物名优先；未指定时才使用默认 `Star/Lucy`；回归测试从“禁止旧名”改为“验证绑定优先级” | **角色职责与角色名字必须解耦。** 默认名只能是 fallback，任何当前请求的显式命名都应原样绑定；测试应验证职责契约，而不是禁止某个具体名字出现 |


## V10：Dialogue-Driven 规则优先级

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| `Dialogue-Driven` 要求“首屏不展示最终 KPI”，但普通报告 §4 又要求“首屏显示最重要数字”，两条规则优先级不够明确 | 明确 Dialogue-Driven 同时覆盖普通报告的首屏 KPI 与 SQL 默认折叠规则 | **局部模式规则必须显式覆盖冲突的全局默认。** 不能只写“顺序覆盖”，必须点名被覆盖的规则 |
| Role Binding Gate 已允许显式人物名，但 report/regression 文档仍大量硬编码默认 `Star/Lucy` | 将渲染与回归验收改为 `Analysis Owner / Reviewer + 本轮绑定角色名` | **角色职责是契约，角色名字是参数。** QA 不应把默认名字当成职责判断 |
| 本真实数据样本要求初始化一次建四个视图，但回归基线仍写“物化为表” | 回归样本改成一次性建立四视图，后续只引用视图 | **数据初始化形态属于输入契约。** 用户明确指定 view/table 时，回归基线不得擅自替换 |


## V11：最小输入 Autopilot

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 用户只想提供“数据集 + 表”，但当前 Direct 协议仍会把业务目的、粒度、主表范围等 Level 3 选择重新甩回用户，导致调用提示不断外挂增长 | 新增 Dataset-to-Report Autopilot：用户明确授权完整分析时，Skill 先勘察数据并自主选择高价值问题；Level 3 选择显式标为分析假设，Level 4 仍暂停 | **最小输入契约应内建到 Skill。** 用户只提供数据源与分析范围时，不应被迫重复提供 Skill 本应自行推导的结构信息 |
| 单一汇率 snapshot 下，Autopilot 若严格等待用户确认就无法闭环；若直接当历史汇率又会越界 | 允许单一无歧义 snapshot 作为探索性默认，但强制日期/快照命名，并禁止解释为历史成交额 | **自主推进只允许可证据化、可回退的分析默认。** 不得以自动化为理由隐去口径变化 |
| 最终 HTML 修好了，但同类问题仍可能依赖下一次外部提示再次指出 | 将 Reverse Skill Audit Gate 纳入 Autopilot 完成条件 | **Artifact 是 Skill 的反向测试样本。** 可泛化缺陷必须回写规则、复测并回归，不能长期积累外挂提示词 |


## V12：默认角色与 HTML 交付内建

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 用户已经明确默认人物应为 `Star/Lucy`，但 Skill 主协议仍使用小写 `star`，导致报告需要靠调用提示或生成器额外修正 | 将默认角色统一为 `Star/Lucy`，角色职责仍由 Role Binding Gate 管理 | **默认展示名也是输出契约。** 如果每次都靠外部提示纠正大小写，说明配置仍未真正内建 |
| HTML 文件名、落盘位置和下载链接仍依赖用户额外声明 | 新增 Default HTML Delivery Contract：默认 `/mnt/data/sql_business_thinking_report.html`，单文件交付并返回 sandbox 链接 | **交付形式属于 Skill 输出契约。** 稳定的文件名、位置和链接不应成为每次调用的外挂输入 |


## V13：移动端真实宽度门槛

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 390px 实际渲染时页面被 Grid 内容列中的宽表/长 SQL 撑到 816px；虽然表格 wrapper 已设置局部滚动，但父 Grid item 默认 `min-width:auto` 仍阻止收缩 | Renderer 增加 Mobile Width Gate：Grid/Flex 内容列含代码/表格时必须允许收缩（如 `min-width:0`），并用实际 `scrollWidth/clientWidth` 做验收 | **“有 overflow:auto”不等于“不会整页溢出”。** 响应式验收必须测最终几何尺寸，并同时约束父布局项与子滚动容器 |


## V14：问题驱动分析而非陪练协作

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| Star 被固定在“完成任务”的执行位，Lucy 只负责补充、质疑、验证，长期会退化成陪练 / SQL 助手 | Star 改为 Analysis Lead；Lucy 改为 Critical Analyst；Lucy 先挑战“问题值不值得现在问”，可以 accept+sharpen / reject / replace / split | **角色差异应体现在问题选择权，而不只是代码分工。** Critical Analyst 必须能改变分析方向，而不是只帮主分析师把既定方向做完 |
| Autopilot 虽然能自己选题，但缺少“为什么这个问题优先”的机制，容易把字段清单机械翻译成 SQL checklist | 新增 Analysis Map → Question Frontier → Question Quality Gate；SQL 只能回答通过 Gate 的当前问题 | **SQL 不是推进器，问题才是。** 每个查询前必须说明 Trigger / Consequence / Answerability / Priority |
| Result 经常只是验证流程步骤，查完后下一步仍按预设顺序继续 | 新增 Question Consequence Gate：Result 必须关闭 Unknown、产生新 Unknown、改变优先级、终止路径或完成必要最终取数 | **查询必须改变分析状态。** 查完也不改变 Frontier 的非必要查询应删除 |
| 旧 Conversation Arc 默认从“领导下任务”开始，导致无 Task Owner 的数据分析也被包装成替领导办事 | Dataset-Driven Arc 设为默认；只有用户显式给出 Task Owner 时才增加 Assignment / Report-back | **不要为角色会话虚构组织关系。** 任意数据集分析应默认从数据与问题开始 |

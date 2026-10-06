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


## V15：假设驱动与分析深度

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| Question Frontier 能减少废问题，但报告仍容易停在“多少 / 谁最大 / 占多少”，数字正确却缺少解释 | 新增 Hypothesis Frontier：Observed Pattern → H1/H2 → Disconfirming Evidence → Diagnostic Test → Status | **问题驱动只解决“问什么”，假设驱动才解决“怎么解释”。** 主要现象不得直接升级成 Insight |
| Star 只在 Result 后复述数字，Lucy 只挑战问题或 SQL，缺少真正的分析博弈 | 要求 Star 提出解释模型；Lucy 增加 counter-hypothesis / falsify / decompose / stress-test / boundary | **角色差异必须体现在解释竞争。** 删除姓名后仍应看出“提出解释 → 攻击解释 → 证据区分 → 更新判断” |
| 高集中度可能只是单一极端用户造成，但旧规则没有强制验证结论是否稳健 | 新增 Analysis Depth Gate 与 Robustness Check；优先去 Top1、拆频次×单笔金额、按 rail/asset 拆驱动 | **主要结论必须经受至少一次会改变可信度的压力测试。** 稳健性不是多跑一个同类指标 |
| 数据不足时为了“深度”容易编造 Why | Hypothesis Frontier 支持 unresolved；无法区分竞争解释时明确缺失数据 | **深度不等于强行解释。** 能证明“当前数据不足以区分”本身也是专业结论 |


## V16：显式契约优先

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 用户明确 Star=小白、Lucy=资深分析师，但默认 Star=Analysis Lead / Lucy=Critical Analyst 仍可能覆盖能力设定 | Role Binding 升级为完整 Role Contract，名字、能力、职责、知识边界和互动方式均以当前请求优先 | **默认角色只补空白，不覆盖显式角色语义。** 同名也不能自动套默认职责 |
| 陌生数据集协议建议查看已有看板 / expected，可能越过用户明确的四表白名单 | 数据勘察改为授权范围优先；范围外只允许必要 metadata，不读内容 | **显式数据范围高于任何 planning / QA / expected 建议。** |
| 用户提供不可改写 DuckDB 读取 SQL 时，运行环境契约仍可能触发替代读取方式 | 新增 Explicit Execution Contract Gate；替代工具只能做辅助验证，不能冒充指定 SQL 实际执行 | **用户指定的执行 SQL 是执行契约，不是提示性示例。** |
| Reverse Skill Audit 默认要求自动回写仓库，会把纯测试变成边测边改 | 回写改为权限门控；未授权时只报告缺陷与回归建议 | **测试权限与修改权限分离。** 发现问题不等于获得仓库写权限 |

## V17：Native 缺失时的 DuckDB-Wasm 正式回退

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| HTML 分析任务已经具备 DuckDB-Wasm 能力，但 Explicit Execution Contract 把 Native 初始化语句整体视为不可替换，导致 Native 缺失时过早 `BLOCKED_ENV` | 将契约拆成 Data Contract 与 Runtime Bootstrap Contract；HTML / Browser 任务中按 Native → DuckDB-Wasm → BLOCKED_ENV 顺序执行 | **数据语义与运行时启动必须解耦。** Native bootstrap 不应阻止同一 DuckDB 语义在浏览器正式执行 |
| Wasm 容易被误判为“替代读取”，或反过来为了 Wasm 偷换成 Python / CSV | 明确 Wasm 只能适配 bootstrap / transport；数据源、Sheet 白名单、`read_xlsx` 语义保持，并记录 URL→VFS 映射 | **Runtime adapter 可以变，Data Contract 不能变。** |
| Wasm fallback 可能覆盖用户显式 Native-only 约束 | 增加 Native-only 对抗回归；用户明确要求 CLI / byte-for-byte bootstrap 时仍直接阻塞 | **自动回退只在授权边界内发生。** 用户显式 runtime 约束高于默认 fallback |

## V18：Runtime Placement、阻塞式数据质量与 QA 状态

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| Native 不可用、本地浏览器又失败时，Skill 会把“本地 placement 失败”误判成“Wasm 整体失败” | 新增 Runtime Placement Gate：Native → 本地 Wasm → 已授权且无需越权创建的远程 Wasm runner → BLOCKED | **Runtime type 与 runtime placement 必须分开。** 本地失败不能代表同一运行时能力在其他合法 placement 也失败 |
| 为了跑分析创建临时 branch / workflow / commit，绕过了“测试不等于写权限”的边界 | 新增 Execution Mutation Permission Gate，并明确执行环境写权限与 Skill 修改权限分开判断 | **执行任务不自动授权外部系统写入。** “临时资源”仍是持久化写操作 |
| 数据质量规则存在于 checklist，但未执行也能继续进入月度趋势等下游分析 | 将一致性检查升级为 Mandatory Data Quality Gate，状态固定为 PASS / FAIL / NOT_APPLICABLE / BLOCKED；未执行不得 PASS | **会改变下游结论的检查必须是阻塞 Gate。** 规则存在但不强制执行，等于没有规则 |
| 浏览器渲染因环境阻塞时，静态 QA 通过仍容易被表述成“完整验收” | Rendered QA 增加 PASS / FAIL / BLOCKED；BLOCKED 必须披露 `RENDER_QA_BLOCKED`，不能由 DOM/源码检查替代 | **未真实执行的 QA 不能记 PASS。** 严格验收要求下，BLOCKED 表示验收未完成 |

## V19：Harness Coverage 与版本漂移

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| Skill 已新增阻塞 Gate，但正式 DuckDB-Wasm runner 仍是旧 Harness；旧 run 成功被误用于证明当前 HEAD 已完成 E2E | 新增 Harness Coverage Gate 与 `tests/mandatory-gates.json`；workflow 监听 `skills/sql-business-thinking/**`，运行时逐项核对 Registry Gate、记录 skill revision / registry version，并在缺项时返回 `HARNESS_STALE` | **规则版本与执行器版本必须绑定。** 文档里存在的阻塞 Gate，如果机器执行器没有覆盖，就不能宣称 E2E PASS |
| 日期一致性异常由外部交叉验证发现，而不是 DuckDB-Wasm 正式 Harness 自己发现 | 将 `order_id_date_consistency` 写入正式 Wasm Harness，并将失败传播为 `time_analysis = BLOCKED_DATA_QUALITY` | **会阻塞结论的 Gate 必须在正式执行路径内自产证据。** 外部交叉验证只能辅助，不能替代正式 runtime evidence |
| DuckDB-Wasm 对 `SUM(CASE...)` 返回 HUGEINT / Arrow 对象，JS 直接 `Number(object)` 得到 NaN，导致本应 PASS 的 Gate 被误判 FAIL | Harness 中用于 Gate 判定的聚合值显式 CAST 为 BIGINT，并要求状态判定前做标量归一化 | **Gate 的数据类型也是证据契约。** 不能让运行时序列化差异改变业务 Gate 状态 |

## V20：Gate-to-Report 传播

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 数据质量 Gate 已正确返回 `time_analysis = BLOCKED_DATA_QUALITY`，但旧 HTML 仍渲染月度快照趋势，只用“仅供参考”弱化 | 新增 Downstream Gate Propagation Gate；ReportSpec 绑定 Gate 依赖，FAIL / BLOCKED 时 suppress KPI、趋势、排名和正式结论 | **已有查询结果不等于允许展示。** 内容资格必须由当前 Gate 状态决定 |
| 报告缺少“为何不展示”证据链 | Renderer 要求显示失败 Gate、冲突样本、受影响分析和解锁条件；旧 Result 只能作为折叠审计证据并标 `SUPPRESSED_BY_GATE` | **阻断不是删除证据，而是阻止证据升级成业务结论。** Gate 只传播到依赖项，不得误伤无关分析 |

## V21：Presentation Engine

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 分析层已经成熟，但图表仍使用“问题类型 → 默认图型”硬映射，无法比较多个合法表达 | 新增 `visualization-rendering.md` 与 Chart Candidate Competition Gate；重要图默认比较至少 3 个合理候选 | **先判断数据形状，再竞争候选。** 图型选择必须解释“为什么选它、为什么淘汰相邻候选”，不能靠习惯 |
| 为追求视觉风格，连续金额存在被拆成点 / 格 / tick 的风险 | 新增 Unit Honesty Gate；视觉单位必须对应真实业务单位，无合法单位时退回普通条形 / 表格 | **表达不能创造数据颗粒。** 视觉语法必须服从数据契约 |
| 多图报告容易用不同图形重复同一结论，或为了填模板槽位增加弱图 | 新增 One-Chart-One-Conclusion Gate；图数量由独立结论数决定，重复图删除 | **图不是越多越完整。** 一个图只承担一个独立判断 |
| HTML 容易边生成边拼布局，导致每次报告结构漂移 | 新增 Layout Archetype Gate：Decision Brief / Evidence Report / Dialogue Report，先锁定一种骨架再渲染 | **页面结构也应是契约。** 模板负责稳定组织，不负责制造内容 |
| SQL、Runtime、Gate、Skill Trace 虽然可审计，但容易抢首屏和正文 | 新增 Information Budget Gate 与 Deletion Gate；正文只保留回答问题、改变判断、解释限制、提供必要验证入口的内容 | **完整证据不等于全部前置展示。** 审计性靠可访问，不靠占据主视觉 |
| 外部可视化 Skill 的模板效果更成熟，但直接复制会把分析系统绑定到外部代码与许可 | 只吸收通用选择机制与信息架构原则，不复制模板代码、视觉资产或专有实现 | **借鉴机制，不耦合实现。** Truth Engine 与 Presentation Engine 保持独立 |

## V22：Freshness、Artifact QA 与 Render Placement

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| 用户要求“重新跑一轮”，但完整业务 SQL Result 来自历史 run；只重新执行 Gate 并核对当前数据一致，就被误表述成完整重跑 | 新增 Result Freshness Gate：重跑/当前/最新/E2E 时，关键业务 SQL 必须绑定本轮 run + 当前 data revision + 当前 Skill revision；历史结果只能标 `REUSED_VERIFIED_RESULT` | **结果新鲜度是独立证据契约。** 数据没变不等于 SQL 在本轮重新执行 |
| Presentation Engine 已规定选图过程只留内部，但最终 HTML 仍出现“候选比较后选择”“这里选择…而不是…” | 新增 Artifact Presentation Gate 与 Artifact Presentation QA；设计 rationale 默认只进 ReportSpec / audit | **规则是否存在不重要，最终 Artifact 是否遵守才重要。** ReportSpec 可以完整，正文必须克制 |
| 本地 Chromium/Playwright 因 EGL/Display/管理员策略失败后直接收口为 `RENDER_QA_BLOCKED` | 新增 Render QA Placement Gate：Local browser → 已授权 remote browser runner → BLOCKED；远程 QA 必须绑定当前 Artifact digest/revision | **QA 能力与 QA placement 必须分开。** 本地失败不能代表所有合法 render placement 都失败 |

## V23：Canonical Remote Render Runner

| 暴露缺陷 | 本轮修正 | 可泛化规则 |
|---|---|---|
| Render QA Placement Gate 已规定本地失败后尝试远程，但仓库没有一个可直接复用的通用浏览器 runner | 新增 `.github/workflows/sql-business-thinking-render-qa.yml`：workflow_dispatch 接收 gzip+base64 HTML 与原始 bytes SHA256，在 GitHub Actions 中真实运行 Chromium 桌面 1440×900 与手机 390×844 | **Fallback 不能只是一条文字路径。** 只要规则要求某个正式 placement，就应有可调用、可产证据的实现 |
| 远程 Render QA 可能验错文件或拿历史截图证明当前 HTML | runner 强制 `artifact_sha256 == expected_sha256`，产出 `render-qa.json`、digest、桌面/手机截图；PASS 绑定 exact artifact bytes | **Rendered QA 证据必须绑定 Artifact identity。** “浏览器跑过”不等于“当前文件跑过” |
| 手工准备 workflow input 容易重编码、截断或超过 dispatch payload | 新增 `tests/prepare-render-qa-payload.py`，确定性 gzip + base64，输出 SHA256；inline 安全上限 60,000 字符，超过返回 `REMOTE_RENDER_PAYLOAD_TOO_LARGE` | **传输也属于证据链。** 不能为了适配 runner 改写或截断待验收 Artifact |
| 远程 QA 会把 HTML 发往 GitHub Actions，存在数据边界 | Canonical contract 明确：只有用户已授权远程发送当前 HTML 才能调用；敏感/未授权内容没有合法 remote placement 时继续 BLOCKED | **获得 runner 能力不等于获得数据外发权限。** placement authorization 与技术可用性必须同时满足 |



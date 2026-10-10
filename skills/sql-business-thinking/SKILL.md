---
name: sql-business-thinking
description: 将业务问题转为可验证的 SQL 与结论。适用于 SQL 教学、取数、纠错、陌生数据集分析、多表查询及 HTML/报告/看板。默认 Learn；明确索要结果或完整分析时用 Direct/Autopilot；明确调试时用 Debug。用户要求人物会话或代码逐步生成时保留会话证据。必须尊重数据与运行时契约，不得用历史或模拟结果冒充本轮执行。
---
# SQL Business Thinking

主路径：**业务问题 → 数据逻辑 → SQL → 真实执行 → 证据 → 可复述结论**。先确定要回答什么、结果粒度和数据来源，再写 SQL；查询不能回答问题时，先修问题或口径，不堆 SQL。

## 1. 选择模式与按需加载

| 模式 | 触发与行为 | 按需文件 |
|---|---|---|
| **Learn（默认）** | 引导用户明确目的、结果、粒度、表、条件和关系；用户练习的 SQL 不直接代写。 | `references/protocol.md` |
| **Direct** | 用户明确要最终 SQL 或直接结果；自主完成推导，交付 SQL、口径和执行证据。 | 遇陌生数据集读取 `references/dataset-planning.md` |
| **Dataset-to-Report Autopilot** | 用户提供数据集、授权表范围并要求完整分析/报告；目标可选。自行勘察并形成问题，不要求外挂字段、JOIN、SQL、图型或报告骨架。 | `references/dataset-planning.md`、`references/ontology-analysis.md` |
| **Debug** | 用户指定调试、单阶段、重跑或从阶段继续时执行阶段协议；明确要求“一口气/顺序执行全部”时连续执行实际需要的阶段。 | `references/debug-stages.md` |

用户明确要求仅确认当前阶段时，不提前分析；之后明确授权完整连续执行时，以最新指令为准。普通 Direct/Autopilot 不逐阶段索取确认。先确定 SQL 方言；已有运行环境或 SQL 可识别时不重复询问。

按交付物加载：报告或 HTML 用 `references/report-rendering.md` 和 `references/regression-loop.md`；D21 选图才加载 `references/visualization-rendering.md`；只有明确需要人物会话、角色模拟或教学回放才加载 `references/dialogue-rendering.md`。历史修复档案 `references/skill-change-log.md` 仅维护/复盘时读取。不得因为存在附属协议就预设用户要求人物、看板或复杂页面。

## 2. 输入、读取与权限契约

**Explicit Execution Contract Gate：**执行前锁定数据源身份、授权表/Sheet、SQL 方言、读取 SQL、允许修改的参数、输出和禁止事项。范围外工作表不得读取内容、字段规则、expected 或 QA 结果；必要时只读名称元数据。不得用其他来源补齐被禁数据。

区分 **Data Contract**（数据源、业务语义、指定 SQL/表范围）和 **Runtime Bootstrap Contract**（扩展安装、网络、VFS 与执行位置）。**用户明确要求 SQL 原样不变或仅允许替换 `sheet` 时，SQL 中的 URL、`read_xlsx` 参数与初始化语句也锁定；VFS 别名即使语义相近，也不能宣称满足原样契约。**只有用户允许运行时适配，才可记录原始 URL 与 VFS 文件名映射后以 `read_xlsx` 读取，禁止默换 CSV/Pandas/Connector。

分析、测试不等于外部写权限。创建分支、提交、PR、工作流、Issue 或上传远程任务需单独授权；Skill 修改权限与运行环境写权限分别判断。失去数据/权限约束时停止，不得自行扩大范围。

## 3. 运行时、结果与真实性

1. **Runtime Placement Gate：**先检查当前环境的 Native DuckDB；本地缺失或网络受限时，继续核验仓库现有、已授权且能保留原始 SQL 的远程 Native runner。HTML/Browser 任务可再检查本地 DuckDB-Wasm 和现有、已授权的远程 Wasm runner。逐个记录环境、触发权限、实际 run ID、SQL 与数据版本、Gate 覆盖和失败证据；仅 runner 已存在不算本轮执行。远程 Native D02/D03 通过只证明对应阶段，不得冒充 D04–D23 自主分析或最终 E2E。任何远程写入或发送均须符合第 2 节权限契约。每个 placement 实测后才判失败。全部合法且兼容的执行位置均不可用时才标 `BLOCKED_ENV`。用户锁定 Native 或 SQL 原文时，不得以 VFS 替换冒充成功，不得无声切换引擎。
2. **数据质量：**读取授权表后检查粒度、键唯一性、孤儿、状态、金额、时间和 JOIN 基数，具体按 `references/dataset-planning.md` 与 `tests/mandatory-gates.json`。必需 Gate 未运行不得写 PASS。**Downstream Gate Propagation Gate：**失败或阻塞只抑制受影响的下游分析，不抑制无关内容；证据可以保留，KPI/结论不得以“仅供参考”绕过。
3. **SQL Alias Safety Gate：**显式别名写 `AS`，规避 DuckDB 关键字冲突。按合理换行和缩进展示 SQL；Parser Error 先检查 SQL，不归咎数据。
4. **Result Scalar Normalization Gate：**所有 DuckDB Result 进入分析/ReportSpec/渲染前统一处理 bigint、DECIMAL、Date、Arrow/TypedArray、单元素视图和嵌套对象。非法标量形态标 `RESULT_SHAPE_INVALID`；Renderer 不猜值。
5. **Logical Data Revision Gate：**按授权表固定顺序、主键/行顺序、字段顺序与归一化值计算逻辑 SHA256；另记原始来源、传输字节 SHA 和数据读取位置，不用 XLSX/ZIP bytes SHA 冒充逻辑数据版本。
6. **Result Freshness Gate：**用户要求重跑/当前结果/E2E 时，关键业务 SQL 必须本轮在当前数据与当前 Skill revision 上实际执行。历史结果只能标 `REUSED_VERIFIED_RESULT`，不能写 fresh PASS。记录 SQL、run、data revision、Skill revision 和 Result。
7. **Harness Coverage Gate：**用于宣称真实 E2E 的 runner 必须与当前 Skill revision 一致，覆盖 `tests/mandatory-gates.json` 全部阻塞 Gate，并记录状态和版本。旧 runner、缺 Gate 或只跑预置 SQL 而未走当前自主分析流程均不能宣称 Skill E2E PASS；缺版本覆盖标 `HARNESS_STALE`。
8. **环境证据：**Origin、CORS、远程 XLSX、扩展与浏览器文件访问分别验证。每次失败记录报错和位置；没有实际运行的 SQL 标“待执行”，不得生成模拟数据、数字或结论。外部工具只可独立交叉验证，不得冒充 DuckDB 执行结果。

## 4. Learn：八关训练

按顺序确认：**目的 → 结果表 → 一行的粒度 → 表与字段来源 → 输出/筛选条件 → JOIN 关系与保留记录 → 业务动作/聚合/时间语义 → SQL 骨架与反向验证**。复杂题一次推进一关；简单题先确认表、取值、条件和粒度。细节、示例、询问梯子、口径库与错误台账按 `references/protocol.md`。

硬约束：结果表必须直接回答原题；聚合前验证右表键唯一、JOIN 前后行数与目标粒度；LEFT JOIN 的 WHERE 过滤不能误删记录。时间维表优先 exact-date/time，再按已认可的 as-of，最后只在明确许可时使用 snapshot 并标“快照估值”，不得冒充历史成交额。Top N 覆盖全部样本时不得当集中度指标。口径不明或证据不足先标 UNKNOWN，不编造字段或业务规则。

询问级别：0 静默修语法；1 做了说明；2 可逆假设附依据和把握并确认；3 业务定义/粒度等由用户决定（Learn 不代答，Direct 给不超过三个选项）；4 冲突、越权或不可答时暂停。用户明确授权 Autopilot 自主分析时，只采用可追溯、可回退的三级假设并明示，四级仍阻塞。详细分级规则见 `references/protocol.md`。

## 5. Direct / Autopilot：从数据发现问题

1. **D02–D06：**读取允许的数据，完成结构与质量检查；陌生多表先还原业务语义，再建立两张表：本体原子知识库、本体识别规则库。本体规则只表示真实业务模式，不写 GROUP BY、SUM、JOIN 或指标公式。
2. **D07–D09：**从合法本体提炼少量有判断价值的指标，删除重复、低价值和机械组合。问题质量阶段的候选问题必须有 Trigger、Consequence、Answerability、Priority；不同答案不会改变判断的问题淘汰。可以没有合格问题，不强凑。
3. **D10–D12：**先设计唯一当前 SQL，再在合法 DuckDB runtime 实际执行并解释 Result；SQL 不能从预写 checklist 推进。每次结果都更新问题边界，或明确为什么停止。**Result-Driven Investigation Gate：**深度 Autopilot 必须记录每轮问题、不同答案的不同判断、实际 Result 与新的下一问来源；不得以预写 SQL 清单冒充动态问题。
4. **D13–D16：**对有价值的分析信号，仅沿本体允许的关系展开；建立可反驳的竞争解释和最小诊断。**没有证据时不得强设主解释或原因**；将假设保留为 unresolved。分析深度阶段的主要发现至少检查 What、Where、Why、Alternative、Test、Robustness、So What；无法验证的项明确说明。**Investigation Depth Gate：**在数据支持主体、事件和时间关系时，不能只靠 TopN/比例宣称完成深度调查；应检验合法的行为序列及反例。调查性主要发现必须有可反驳的竞争解释、实际执行的区分测试和稳健性检查；否则降级为描述性或 unresolved。
5. **D17–D18：**仅把可由实际 Result 复算的事实晋级为已验证发现；区分历史状态与实时状态、方向与完成、状态占比与成功率、口径敏感性与稳定规律。没有运营动作证据时，允许决策结果为“尚不能决定”。SQL、数据 Gate 和浏览器 PASS 不能替代调查深度 PASS；纯排名/占比标为 `DESCRIPTIVE_ONLY`，无法证明可行动判断时标 `NO_DECISION_GRADE_FINDING`，不强凑风险原因。
6. **循环规则：**有新价值问题回到 D08→D09→D10→D11→D12；无新增判断价值即停。阶段只消费已验证上游，不得将旧结果、测试夹具或模拟样例升级成实际发现。调查报告需保留结构化 `question → SQL Result → frontier update → next question/stop` 证据；`tests/check_investigation_trace.py` 仅验证证据结构，不能代替 DuckDB 执行或业务判断。

用户没有请求人物会话时，不强行生成 Star/Lucy。若明确要求，用户的角色名、能力、职责和知识边界优先于默认角色（Role Contract Gate / Role Binding Gate）；没有定义时才使用 Star/Lucy。要求代码在对话中生成时，遵守 `references/dialogue-rendering.md` 的代码增量、唯一可执行 SQL、Result Dependency Gate、知识顺序和最终追溯规则；不得用历史答案倒灌。

## 6. 报告、看板与 HTML

交付类型以用户已确认要求为准：**Report 用 D18，Dashboard 用 D19（可从 D07 直接评估），Hybrid 分别取两者**。不得把深度诊断默认塞进看板；看板只保留可持续监控且变化后值得关注的指标。

固定顺序：**D20 交付规范 → D21 可视化计划 → D22 Renderer → D23 Rendered QA → Artifact Regression Loop**。D20 不改口径/重新分析；D21 独立选择图型、单位、布局，简单图不强制比较候选；D22 不新增数据或结论。任何展示都受上游质量 Gate 约束。正文回答主问题，证据可下沉但不得藏掉答案；深度报告的主要发现须交代具体主体/事件、合法行为关系、竞争解释、真实诊断、反例和可执行调查下一步；只有排行榜、宏观比例及通用建议不能标深度 PASS。删去重复图、无信息台词、设计过程解释和无效操作入口。Dialogue-Driven Report 按认知顺序保留会话、SQL、Result，不提前泄露最终 KPI。

**Default HTML Delivery Contract：**未指定文件名时输出实体 `/mnt/data/sql_business_thinking_report.html` 并提供可访问的 sandbox 链接；单 HTML 包含可读的报告结果和必要代码，不能只交源码或声称已生成。外部 CDN/异步资源须经过最终环境验证；离线时仍应能阅读已验证结果。

QA 检查实际 DOM、桌面/移动端几何尺寸、交互、表格可读性、中文字体、异步 readiness、证据溯源和当前 Artifact SHA。**Async Render Readiness Gate：**异步页面必须明确 READY 标志；加载完成事件或固定 sleep 不代表准备完毕。本地浏览器不通时，只有在已获远程发送授权后才使用仓库现有远程 Render QA；最终证据必须绑定当前 HTML bytes 和 runner revision。详细入口与限制见 `references/report-rendering.md`。没有真实 Rendered QA 时标 BLOCKED，不能用静态源码检查替代。

**Reverse Skill Audit Gate：**成品审计区分数据/分析/报告/Skill/环境/测试缺陷。先复现根因，优先改现有规则，删除无效与重复内容；可泛化缺陷形成回归测试。只有获授权修改仓库时才回写和提交。每次修改记录变更范围、前后规模、失败用例和复测证据，禁止用补丁层叠隐藏冲突。

## 7. Debug、状态与完成标准

单阶段 Debug 按 `references/debug-stages.md` 的阶段、依赖、状态、回退和锁定规则执行。用户**明确要求一口气完成**时，从 D01 连续经过真实需要的阶段，并保留 D08–D17 的分析循环；每阶段按真实证据验收，不必逐次请求已预授权的确认。发生阻塞时先尝试合法的环境/路径修复；不得跨越阻塞、编造 PASS 或以单条固定 SQL 代替自主分析。

输出严格区分 **PASS / FAIL / BLOCKED / 未执行**，并报告最早阻塞阶段、错误、已通过证据与恢复条件。完整 E2E 仅在当前 Skill、当前数据、当前 runner、所有适用阶段、真实 SQL 与最终成品 QA 全部通过后成立；旧 run、旧报告、部分测试通过都不算。

收尾核对：授权范围正确；问题有判断价值；SQL/结果同粒度同口径；JOIN 与时间校验通过；每个结论可追溯；交付内容符合 Report/Dashboard 资格；HTML 在目标环境中真实可用。未验证则明确写“待执行”或“阻塞”，不可宣称完成。

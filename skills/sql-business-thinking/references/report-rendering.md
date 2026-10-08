# 分析报告渲染协议 V7

目标：把已完成的分析转换成决策可读、可验证、可运行的最终报告。不得改 SQL、真实结果、业务口径或结论。

核心原则：**分析按推理顺序执行，报告按决策价值排序；过程是证据，不是页面主角。**

## 1. 强制解耦

```text
Analysis Events
→ Answer Coverage Gate
→ ReportSpec
→ Renderer
→ Rendered QA
```

禁止直接把消息/SQL/Skill 调用事件流当正文结构。

## 2. 正文四层

1. 结论：主问题答案、关键数字、最大限制；
2. 发现：真正改变判断的发现；
3. 证据：图表、全量关键表、数据质量；
4. 过程：SQL、对话、Skill Trace、初始化日志。

过程默认折叠。

## 2A. Dialogue-Driven Report Override

角色名必须从 `dialogue-rendering.md` 的 Role Binding Gate 读取。当前请求显式给出人物名时，Renderer 必须使用绑定后的名字；不得硬编码默认 `Star/Lucy`。


当用户明确要求：

- 人物会话是主体验；
- 代码必须在本轮绑定的 Analysis Lead / Critical Analyst 讨论过程中逐步产生；
- 不要提前汇总、不要连续累计结论；

则本节覆盖“正文四层按决策价值排序”的默认顺序，同时覆盖 §4 的首屏 KPI 要求与 §7 的 SQL 默认折叠规则。

正文改为：

```text
Dataset / Assignment（仅显式存在时）
→ Analysis Map
→ Question Frontier
→ Current Unknown / Observed Pattern
→ Star: Why now + H1
→ Lucy: accept / reject / replace / split + H2 / 反证
→ Question Quality Gate
→ Hypothesis Frontier
→ Diagnostic Question
→ Draft Code A
→ SQL Boundary Challenge（如需要）
→ Draft Code B
→ Executable SQL
→ Result
→ Hypothesis Update
→ Robustness Check（主要发现）
→ Frontier Update
→ Next Question
→ ...
→ Synthesis / Report-back（仅显式存在 Task Owner 时）
```

此模式：

- 首屏不展示最终业务 KPI；
- 中间不维护累计摘要；
- SQL / Result 不进入独立验证台，而是与触发它的对话原位相邻；
- 若用户要求“代码逐步产生”，每个推进点必须展示由对白触发的代码增量，最后才出现唯一可执行 SQL；
- 每个推进点只允许一个当前问题和一个最终可执行 SQL；第二个独立查询必须另起推进点；
- 当前问题前必须能看出“为什么现在问、答案会改变什么”；Lucy 不能只补 SQL，必须先对问题质量做 accept / reject / replace / split；
- 被 reject / replace 的问题不得继续渲染 SQL；
- Result 后必须显示它如何改变 Question Frontier 或 Hypothesis Frontier；不能改变问题优先级、假设状态或最终解释的查询，除必要最终取数外不进入正文；
- 主要 Pattern 不得只显示数字后跳到下一维度；正文必须可见主解释、竞争解释、Diagnostic Test 和假设更新；
- 主要结论至少展示一次有意义的 Robustness Check；若数据不足，正文明确“未能验证”，不能伪装稳定；
- 最终 Insight 不得只是 Result 的中文复述；至少体现 Why / Alternative / Test / Robustness / So What；
- 删除“这一步确认 / 暂时不能推出 / 截至目前”式元摘要，Result 后由角色自己完成状态更新；
- 最终汇报之后才允许出现汇总卡片、最终附表；
- Skill Trace、运行日志仍属于二级审计信息。

**局部顺序优先级高于全局视觉摘要。**报告质量以“读者能否知道当前为什么写这段 SQL、结果如何改变下一步”为第一标准。

## 2B. Downstream Gate Propagation Contract

ReportSpec 生成前，必须把 Mandatory Gate 状态绑定到每个分析块的依赖关系。

规则：

1. 分析块依赖的 Gate 为 `PASS` 时，才允许进入 KPI、图表、排名、趋势或业务结论。
2. Gate 为 `FAIL` / `BLOCKED` 时，该分析块状态必须改为 `BLOCKED_DATA_QUALITY` 或对应阻塞状态。
3. 被阻塞的分析块禁止继续渲染“仅供参考”“趋势仍可看”“先展示结构”等弱化版本；旧查询结果即使已经存在，也只能作为折叠审计证据，不能进入正式可视化或结论。
4. 正文必须展示：失败 Gate、触发证据、受影响分析、解锁条件。读者应一眼看出“为什么这个分析没有结果”。
5. 阻塞只传播到依赖该 Gate 的分析。与该 Gate 无关且已通过自身 Gate 的分析继续正常展示。
6. Renderer QA 必须反查：若 `time_analysis = BLOCKED_DATA_QUALITY`，正文中不得存在月度/日度趋势图、时间排名或基于时间字段的正式结论。

示例：

```text
order_id_date_consistency = FAIL
→ time_analysis = BLOCKED_DATA_QUALITY
→ 月度趋势图：SUPPRESSED
→ 时间结论：SUPPRESSED
→ 保留：冲突订单、诊断 SQL、解锁条件
```

**已有 Result 不代表可展示。内容资格由 Gate 状态决定。**

## 2C. Report / Dashboard 分流

Report 用于回答问题，允许保留必要的分析深度和证据链。

Dashboard 用于持续监控当前状态。Dashboard 核心层只允许使用已经通过看板资格的数据。

Dashboard 核心项必须满足：

1. 需要持续或重复监控。
2. 会随业务状态变化。
3. 变化后需要关注、判断或行动。
4. 可以稳定重复计算。
5. 目标用户可以快速判断当前状态。

一次性根因、诊断切片、竞争解释、稳健性过程、运行日志默认不进入 Dashboard 核心层。

简单指标不因分析深度低被淘汰。只要长期重要且需要持续监控，就可以进入 Dashboard。

交付模式先区分 Report、Dashboard 或 Hybrid。Hybrid 中，Dashboard 展示当前状态和必须持续看的信息；Report 或 Drilldown 承担原因、证据和诊断过程。

Dashboard 不是分析报告的压缩版，也不是已验证发现的全集。

## 3. Answer Coverage Gate

生成 ReportSpec 前列：

| 用户问题 | Answer Block | 数字/证据 | 正文可见 |
|---|---|---|---|

每个主问题/子问题必须有正文 Answer Block。不能因为有 SQL 结果就认为“回答了”。

例如用户问“每个用户总交易额”，正文必须展示全量用户结果或明确可浏览的全量表；只展示 Top 5 不算完成。

## 4. 首屏

**Dialogue-Driven 模式不适用下面的 KPI 首屏规则。** 该模式首屏只展示任务、绑定角色、初始化状态或当前问题，不得出现尚未由前序 Result 产生的最终数字。

普通报告在 1440×900 打开 10 秒内必须回答：

- 分析了什么；
- 最重要的数字；
- 最大限制；
- 结果是什么口径。

运行状态最多一行，不得占首屏主视觉。

## 5. KPI

只放直接回答主问题的 3～5 个数字。技术状态、表数、SQL 数不进业务 KPI。

Top N 按 active population 自适应，覆盖全体样本的 Top N 不进核心结论。

## 6. 图表

图表不按字段名套固定图型。D21 读取 `visualization-rendering.md`，只基于 D20 已确认内容选型：

```text
Presentation Question
→ Data Shape
→ 最简单的准确表达
→ 有真实取舍时比较合理方案
→ VisualizationPlan
```

强制规则：

- 一个图只承担一个独立结论；
- 图数量由独立结论数决定，不由字段数、SQL 数或“页面需要几张图”决定；
- 连续金额、余额、价格等不得为了视觉风格任意拆成点 / 格 / tick；
- 两个图表达同一结论时，只保留更诚实、更快读的一张；
- 标题默认写结论，不写图型名；结论尚未确定的诊断图才使用问题式标题；
- D21 只在 VisualizationPlan 中记录必要选型理由；有真实取舍时才记录候选，不回写 D20 ReportSpec；
- 被 Gate 阻断的分析不参与图型候选竞争，直接进入 `SUPPRESSED_BY_GATE`。

具体协议见 `visualization-rendering.md`。

## 7. SQL / 结果

正文结果优先。SQL 默认折叠到验证台。

每个 SQL：

- 一份 `<pre>`；执行读取 `textContent`；
- 结果默认“记录”；实时执行后替换为“实时”；
- 报错原样显示；
- 初始化失败不删除记录结果。

## 8. Learn 对话 / Skill Trace

先判断会话是不是用户明确要求的交付物。

### 会话只是过程证据

正文只提“Skill 阻止了什么会改变结果的错误”。完整对话和 Skill Trace 进附录。

### 用户明确要求人物会话 / 角色模拟 / 教学回放

人物会话升级为正文 Answer Block，按 `references/dialogue-rendering.md` 渲染完整 Conversation Arc，而不是独立纠错卡。若用户要求代码在会话中产生，启用 Code-in-Conversation：`对白 → SQL → Result → 判断修正` 原位交错，禁止再建独立 SQL 验证台。

默认不创造领导 / Task Owner。无显式任务发起人时，正文从 Dataset Intake / Analysis Map 开始，最终由 Analysis Lead 做 synthesis。只有显式存在 Task Owner 时，才形成：任务下达 → Analysis Lead / Critical Analyst 推演 → Analysis Lead report-back。角色名使用本轮 Role Binding Gate 的绑定结果；最终结论都要能回指前序证据节点。

Skill Trace 仍属于审计信息，不让角色在台词里说“调用 Skill”“关卡通过”。SQL 验证与 Skill Trace 分栏展示；正文已经完整展示权威会话时，不再保留另一个旧版人物全文。

## 9. 数据限制

正文集中写：状态口径、金额定义、粒度、时间匹配、未匹配处理、NULL、JOIN、数据异常、不能推出的结论。

不要每个 SQL 后在正文机械重复“能说明/不能说明”；附录保留完整教学版。

## 10. ReportSpec / DashboardSpec

只读取已确认的 `delivery_mode`，再选择对应 Schema。D20 必须先确认对应上游阶段已通过、可见内容有真实证据且未被 Gate 阻断。没有 D18 的 Report 或没有 D19 的 Dashboard，只能标“阻塞”，不能生成正式 Spec。

下列 JSON 是**结构示意，不是已经完成的产物**。空数组、空对象不能证明分析已执行。可展示内容必须保留源结果引用和 Gate 状态；没有决策级发现时只能如实报告，不得从候选问题推测发现。不得为统一格式强行添加另一模式的字段。

### Report

```json
{
  "meta": {},
  "delivery_mode": "report",
  "question": "",
  "answers": {},
  "answer_blocks": [],
  "findings": [],
  "quality_issues": [],
  "limitations": [],
  "decision_log": [],
  "learning_replay": [],
  "next_question": {},
  "skill_evaluation": {},
  "appendix": {}
}
```

ReportSpec 只组织已确认的分析答案、证据、限制和必要分析深度。

### Dashboard

```json
{
  "meta": {},
  "delivery_mode": "dashboard",
  "dashboard": {
    "core_items": [],
    "drilldown_items": [],
    "excluded_items": []
  },
  "limitations": []
}
```

DashboardSpec 只消费 D19 已通过看板资格的数据。不得携带完整 findings、analysis trace、竞争解释、稳健性过程或一次性诊断链。

### Hybrid

Hybrid 不创建第三套混合 Schema。分别保留一个 ReportSpec 和一个 DashboardSpec：

```json
{
  "delivery_mode": "hybrid",
  "report_spec": {},
  "dashboard_spec": {}
}
```

两者共享已确认事实，但字段、职责和可见内容保持独立。

D20 Spec 只读。D21 单独生成 VisualizationPlan，Renderer 读取两者，不重新分析。

## 11. DuckDB-Wasm Runtime Contract

- **Browser Execution Harness：**当 HTML / Browser 是正式交付物且 Native DuckDB 不可用时，DuckDB-Wasm 是正式执行路径，不是展示性 fallback；不得因此直接产出 `BLOCKED_ENV` 报告。
- **Runtime Placement：**先尝试当前环境 Wasm；若本地浏览器 / 网络 / 扩展 placement 失败，只能记录该 placement 失败。若已有本轮可授权使用且无需创建 branch / workflow / commit / 云任务的远程 Wasm runner，应继续执行；不得把“本地 Wasm 失败”写成“Wasm 能力失败”。
- **Mutation Boundary：**为了获得远程执行环境而新建 branch、workflow、commit、PR 或其他持久化资源，属于外部系统写操作。用户只要求分析 / 报告时不得自动创建；必须另有明确写权限。
- 使用官方 stable DuckDB-Wasm；
- jsDelivr bundle 用 `selectBundle(getJsDelivrBundles())`；
- Excel 能力用 `LOAD excel`；
- 远程文件按 Wasm browser VFS 处理，例如 `registerFileURL` / `registerFileBuffer`；页面必须记录 `source_url → vfs_filename` 映射；
- 不把 native `LOAD httpfs` 当成 Wasm 必须步骤；Native-only bootstrap 与跨运行时的数据读取语义分开处理；
- Wasm 正式执行仍必须使用 `read_xlsx` 读取授权 Sheet；不得为了绕过运行时差异改成 PapaParse、SheetJS、Python 预处理或静态伪结果；
- 只注册和查询当前白名单允许的数据范围；禁止因为工作簿已下载就枚举或读取被禁止 Sheet 的内容；
- 所有远程读取受浏览器 CORS 约束；失败时区分下载/CORS、VFS、Excel 扩展、SQL 四层；
- 只有 Wasm 实际失败，或当前请求显式要求 Native-only，才将分析执行标记为 `BLOCKED_ENV`；
- 已验证的记录结果与浏览器实时重跑结果必须明确区分；Renderer 不得把未执行的浏览器 SQL 标成已验证 Result。

## 11A. HTML Artifact Delivery Contract

当交付物是完整 HTML，且用户未指定文件名/路径时：

- 默认写入 `/mnt/data/sql_business_thinking_report.html`；
- 必须生成实体单文件，不得只返回源码文本；
- CSS / JS / 会话 / SQL / Result / Report-back 均随文件交付；
- 公共 CDN 只用于可选运行时，记录结果必须内嵌，保证网络失败时仍可阅读；
- 最终回复必须给出 `sandbox:/mnt/data/sql_business_thinking_report.html` 下载链接；
- Rendered QA 需要同时检查文件存在、非空、可解析以及下载路径与实际文件一致。

用户显式指定其他文件名、目录或格式时，以用户要求为准。

## 12. UI

- 无侧栏；
- 主阅读区约 1000～1160px；
- 正文少用大面积彩色卡片，优先留白、分隔线、表格层级；
- 警告色只标真正改变解释的限制；
- Analysis Lead 左、Critical Analyst 右，并显示本轮绑定后的实际角色名；如果会话是用户要求的交付物，正文展示完整权威 Conversation Arc；已有完整正文会话时不再保留旧版会话附录；
- SQL 深色等宽；
- 交互必须有 hover/focus/disabled；
- **Mobile Width Gate：**任何 Grid/Flex 内容列只要包含 `pre/code/table`，内容子项必须允许收缩（例如 `min-width: 0`）；代码块和表格只能在自己的 wrapper 内横向滚动，wrapper 必须 `max-width: 100%`。禁止让宽表/长 SQL 把 `body/documentElement` 撑宽；
- 提供打印/PDF 时加 print CSS，附录默认不打印。

## 13. Rendered QA

### Render QA Placement Gate

Rendered QA 的“浏览器能力”和“执行位置”分开判断，顺序固定为：

```text
当前环境可用浏览器
→ 已经存在且本轮获授权使用的远程浏览器 runner
→ RENDER_QA_BLOCKED
```

规则：

- 本地 Chromium / Playwright / EGL / Display / 管理员策略失败，只能证明本地 placement 失败，不能直接证明 Rendered QA 整体不可执行；
- 若已有无需新建 branch / workflow / commit / 云任务即可调用的远程浏览器 runner，必须继续尝试；
- 为 Rendered QA 新建持久化 runner、workflow、branch 或云资源，仍受 Execution Mutation Permission Gate 约束，不得因为“只是视觉验收”绕过写权限；
- 远程 Rendered QA 必须针对本轮最终 Artifact bytes / digest 或等价不可歧义 revision 执行，禁止拿历史截图证明当前 HTML 已通过；
- 只有所有当前可用、已授权且无需越权写入才能获得的 render placement 都失败，才标 `RENDER_QA_BLOCKED`。

### Canonical Remote Render Runner

仓库提供正式远程浏览器 runner：

```text
.github/workflows/sql-business-thinking-render-qa.yml
```

调用契约：

- 输入 `html_gzip_base64`：本轮最终 HTML 原始 bytes 经 gzip 后再做单行 base64；禁止先改写、格式化或重编码 HTML；
- 输入 `expected_sha256`：对**未压缩原始 HTML bytes**计算 SHA256；runner 内再次计算并要求完全一致；
- 输入 `allow_design_notes`：默认 `false`；只有用户明确要求解释设计决策时才设 `true`；
- 推荐使用 `tests/prepare-render-qa-payload.py <html>` 生成 payload；helper 同时输出 `workflow_dispatch` inputs 与可由 ChatGPT GitHub connector 创建的 `issue_envelope`；
- **Chat connector trigger：**当当前 GitHub connector 不暴露 `workflow_dispatch`，且用户已授权远程发送 HTML 时，可创建标题以 `[sqlbt-render-qa]` 开头的一次性 Issue，正文必须使用 helper 生成的 `SQLBT_RENDER_QA_V1` envelope。workflow 读取 payload 后立即擦除正文并关闭 Issue，再继续 Chromium QA；不得把 HTML/base64 提交进 Git 历史；
- Issue 触发只接受仓库 owner 创建且标题前缀匹配的请求；其他 Issue 不执行 render job；
- inline payload 安全上限由 helper 固定为 60,000 字符。超过时返回 `REMOTE_RENDER_PAYLOAD_TOO_LARGE`，不得截断或把不完整 HTML 送去验收；
- 远程 runner 会生成 `sql-business-thinking-render-qa` artifact，至少包含 `render-qa.json`、`artifact.sha256`、桌面截图与手机截图；
- 只有 `render-qa.json.state = PASS` 且其中 `artifact_sha256 == expected_sha256`，才允许把远程 Rendered QA 记为 PASS；
- 若 HTML 声明 `<meta name="sqlbt-render-readiness" content="required">`，runner 必须等待 `document.documentElement.dataset.renderReady === "true"` 或 `window.__SQLBT_RENDER_READY__ === true`；未到 READY 就截图或检查正文视为无效 QA。超时必须记录 `ASYNC_NOT_READY` 并 FAIL；
- 未声明异步 readiness 的静态 Artifact 也应至少等待 fonts ready + 两次 animation frame，再开始几何与截图检查；
- 远程 runner 会检查桌面 1440×900、手机 390×844、整页宽度、page error、Artifact Presentation 与 readiness；历史 artifact / screenshot 不能替代当前 digest 的结果。

隐私边界：

- `workflow_dispatch` 会把 payload 发送到 GitHub Actions。只有当前 HTML 已获用户授权用于远程 QA 时才能调用；
- 对敏感或未授权远程发送的 HTML，不得为了追求 PASS 偷用该 runner；没有其他合法 placement 时继续标 `RENDER_QA_BLOCKED`。

不能只看源码。Rendered QA 每一项必须记录状态：`PASS / FAIL / BLOCKED`。

- `PASS`：检查已真实执行且通过；
- `FAIL`：检查已执行但不满足要求，必须修复后重跑；
- `BLOCKED`：应执行，但浏览器、图形环境、网络策略或其他运行条件阻止了真实检查。**BLOCKED 不能记成 PASS，也不能写“完整验收通过”。**
- 用户要求“全部验收通过”时，任何 `BLOCKED` 都表示验收未完成；仍可交付阶段性文件时，必须显式标记 `RENDER_QA_BLOCKED` 和未验证项。

至少做：

1. DOM 结构检查：关键区块非空、ID 唯一、按钮映射完整；
2. 桌面渲染烟测：首屏、核心图表、数据质量、Skills 评估；
3. 移动端检查：无整页横向溢出；表格可局部滚动；必须实际断言 `document.documentElement.scrollWidth <= document.documentElement.clientWidth`（允许 1px 取整误差）；若失败，先定位最大溢出元素，不得只缩字号；
4. 功能检查：JS 语法、SQL 按钮映射、fallback、错误显示；
5. 内容检查：每个问题有 Answer Block；关键数字一致；限制没有被视觉弱化；显式要求的人物会话正文可见。
6. Artifact Presentation QA：检查最终可见正文，不得泄露 Chart Candidate Competition、rejected candidates、Layout Archetype 选择、Renderer 策略、Information Budget 判断等内部设计过程；“候选比较后选择……”“这里选择……而不是……”等说明默认视为 FAIL。只有用户明确要求解释设计决策时才允许进入正文。
7. Async Readiness QA：若 Artifact 声明异步 readiness，桌面与手机都必须在 READY marker 后再检查；`DOMContentLoaded + 固定 sleep` 不能单独判 PASS。
8. Dialogue QA（如适用）：Conversation Arc 完整；本轮绑定的 Analysis Lead / Critical Analyst 职责正确；Lucy 不得退化成陪练；每句通过 Turn Delta Gate；没有提前知道未验证结果；最终 synthesis / report-back 可反向追溯；台词不含内部流程标签。普通模式会话不被 SQL/Skill Trace 打断；Code-in-Conversation 模式必须验证“问题质量挑战 → SQL → Result → Frontier 更新”的邻接顺序。
9. Progressive Order QA（Code-in-Conversation）：最终 KPI 未在证据之前出现；没有跨阶段滚动摘要；每个具体数字第一次出现之前能找到对应 result 节点；正文没有第二套 SQL 副本。
10. Question Quality QA：每个进入 SQL 的问题都有 Trigger / Consequence / Answerability / Priority；至少检查是否存在“无论结果如何下一步都一样”的废问题；下一问必须能由上一轮 Frontier 更新解释，禁止预先排好的 checklist 式推进。
11. Hypothesis Depth QA：主要发现存在 H1 + 至少一个竞争解释；Lucy 至少一次攻击解释本身；存在能区分解释的 Diagnostic Test；关键结论做过有意义的 Robustness Check；最终 Insight 不能只是排名/比例复述。

**重要：源码中“有 Hero 节点”不等于 Hero 渲染成功。必须检查渲染输出。无法检查时状态只能是 `BLOCKED`，不得用源码检查替代 Rendered QA。**

## 14. Skills 评估展示

如果报告本身是 Skill 回归测试，页面末尾单独展示六项：

- Skill 选择；
- SQL 首次跑通率；
- 关键数字口径；
- 主动数据质量发现；
- 结论是否越界；
- 读者能否复述分析路径。

再追加：`缺陷 → 修正 → 可泛化规则`，但不要让 Skills 元信息抢业务正文。

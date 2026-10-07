---
name: sql-business-thinking
description: 训练用户把业务问题拆成数据逻辑，再翻译成 SQL。用于 SQL 学习与练习、业务取数、陌生数据集分析、多表查询设计、SQL 纠错与逻辑审查、复盘一段 SQL 为什么这样写。用户说“帮我取个数”“这个 SQL 对不对”“这题怎么下手”“再来一题”时也使用，哪怕没提训练。用户自己还没想清要查什么时，用提问把目的启发出来。默认先带用户自己搭思路，不直接代写完整 SQL；用户明确说“直接写”“给最终 SQL”“跳过训练”才进入 Direct 模式。需要输出 HTML/报告时，在分析完成后切换到 ReportSpec → Renderer，并执行 artifact regression loop。用户明确要求人物会话、教学回放或角色模拟时，把会话本身视为交付物的一部分；如果用户要求“代码在会话中逐步产生”，进入 Dialogue-Driven Report 模式：讨论、SQL、结果和判断修正必须原位交错，禁止把 SQL 事后集中到独立验证台。
---
# SQL Business Thinking

训练一条路径：

```text
业务语言 → 数据逻辑 → SQL → 验证 → 可复述结论
```

重点不在背语法，在于看到业务问题时，脑子里自然冒出：

```text
这题到底想知道什么？结果表长什么样？一行代表谁？
数据在哪？取什么？什么条件？表怎么关联？
要分类、汇总还是计算？JOIN 会不会放大？时间口径成立吗？
最终结果回答原题了吗？哪些结论不能从这些数字推出？
```

语法忘了可以查。业务问题、粒度、时间或 JOIN 关系拆错了，SQL 写得再完整也没有意义。

## 模式

**Learn（默认）**：用户自己搭框架。我提问、纠错、给反例、查逻辑、补语法、帮 Debug，不替他把完整 SQL 写完。用户刚拿到题时，至少先让他答出：表、取什么、条件、粒度。

**Direct**：用户明确要结果才进。内部照样走完整条路径，对外交带注释的 SQL、口径说明和我替他定的事项清单。信息不足时标 `UNKNOWN`，说清缺什么。表名、字段名、业务口径一律不猜。

**Debug**：仅用于 Skill 开发、维护和回归测试。用户明确说“调试模式”“只跑某阶段”“重跑某阶段”“从某阶段继续”或等价指令时，读取 `references/debug-stages.md`。一次只执行指定阶段，执行后立即停止，不自动进入下一阶段。后续阶段只能读取已确认且仍有效的上游结果；不得静默修改已通过阶段。发现根因来自上游时返回“需回退”，指出具体阶段，不在当前阶段内部修正上游。

**正常模式保持不变。** 用户没有显式进入 Debug 时，Learn、Direct 和 Autopilot 继续按照现有方法论自动连续执行。不得因为存在调试阶段而要求普通用户逐步确认，也不得降低正式执行效率。

首轮说一次切换口令：“现在是 Learn 模式，要直接要结果，说‘直接写’。”用户的话已明显在要结果（表名、条件、粒度都给全了），直接按 Direct 处理，同样说这一句。调试任务不输出 Learn/Direct 切换口令，直接按 Debug 协议执行。

Debug 支持三类控制：指定阶段单独执行、重跑当前或指定阶段、从指定阶段继续。调试阶段完成后至少返回“当前阶段、依赖阶段、输入、本阶段任务、输出、检查结果、通过条件、状态”。状态只使用：待执行、待检查、通过、需修正、需回退、阻塞。全部阶段分别通过后，用户要求“完整链路回归”时，切回正常连续执行方式完成一次端到端回归，不逐阶段暂停。

开始前确认 SQL 方言。贴的代码、连接方式或运行环境能看出来的不问，说一句依据。

### Explicit Execution Contract Gate

用户明确给出 SQL 方言、初始化语句、读取方式、数据范围或“不得改写”约束时，先把契约拆成 **Data Contract** 与 **Runtime Bootstrap Contract**，避免把 Native 初始化细节误当成跨运行时不可变语义。

- **Data Contract 必须保持：**数据源身份、允许表 / Sheet、`read_xlsx` 读取语义、用户允许变化的参数、分析 SQL 的业务逻辑以及实际 Result 的可追溯性。不得改用 Python / Pandas / Connector 读取后声称 DuckDB SQL 已执行。
- **Runtime Bootstrap Contract 按平台适配：**`INSTALL/LOAD httpfs`、browser VFS、`registerFileURL/registerFileBuffer` 等属于运行时启动与传输层。只有用户明确要求“必须在 Native DuckDB / CLI 中逐字执行该初始化”时，才把 Native bootstrap 本身视为不可替换。
- **DuckDB-Wasm 正式回退路径：**当交付物是 HTML / Browser，或用户已授权浏览器 DuckDB，且 Native DuckDB 不可用时，必须先切到 DuckDB-Wasm，而不是直接 `BLOCKED_ENV`。Wasm 只允许改运行时 bootstrap；数据源、Sheet 白名单和 `read_xlsx` 语义必须保持。若 VFS 需要本地别名，必须记录“原始 URL → 注册文件名”的映射，禁止把映射伪装成数据源变化。
- **Runtime Placement Gate：**运行时类型与运行位置分开判断。顺序为：当前环境可用的 Native DuckDB → 当前环境可用的 DuckDB-Wasm → 已经存在且本轮已获授权使用的远程 DuckDB-Wasm runner → `BLOCKED_ENV`。本地浏览器、网络或扩展失败，只能证明该 placement 失败，不能直接证明 DuckDB-Wasm 能力整体失败。
- **Execution Mutation Permission Gate：**为了获得运行环境而创建 branch、workflow、commit、PR、云任务或其他持久化外部资源，均属于写操作。分析、测试、生成报告本身不自动授权这些写操作；只有用户明确授权对应系统写入，或该远程 runner 已存在且调用不需要持久化修改时才能使用。不得把“临时分支 / 临时 workflow”视为无副作用。
- **Harness Coverage Gate：**任何被用来宣称“Skill 已完成真实 E2E 执行”的 Native / Wasm runner，必须覆盖当前仓库 `skills/sql-business-thinking/tests/mandatory-gates.json` 中全部阻塞 Gate，并在产物中记录 Gate registry version、执行 commit / revision 与每个 Gate 的状态。缺少任一 Gate、runner revision 落后于当前 Skill、或 Gate registry 与 Harness 不一致时，标 `HARNESS_STALE`，不得宣称 E2E PASS。新增阻塞 Gate 时必须同一轮更新 registry、Harness 与回归测试。**Gate 判定只能基于已归一化的标量结果；DuckDB-Wasm / Arrow 的 HUGEINT、DECIMAL、TypedArray 或对象序列化值必须先 CAST / normalize，禁止让序列化类型本身制造 PASS/FAIL。**
- **Result Scalar Normalization Gate：**scalar normalization 不只服务 Mandatory Gate。所有 DuckDB Result 在进入 Result Store、ReportSpec、业务计算、比较、排序、格式化或最终 Artifact 前，必须经过同一个 normalization boundary。至少处理 `bigint`、Date、Arrow / TypedArray、单元素 view、DECIMAL 与嵌套对象；“本应是单值却序列化成 `{"0":3,...}`”必须视为 `RESULT_SHAPE_INVALID`，不得由 Renderer 临时猜值。优先在 SQL 中对判定字段显式 CAST，并在 runtime 再做统一 normalize。
- **SQL Alias Safety Gate：**生成 SQL 时所有显式别名必须写 `AS <alias>`，禁止依赖 DuckDB 的 implicit alias 语法。别名若可能与 DuckDB keyword 冲突，必须改成语义明确的安全名（如 `rail`、`before_rows`、`after_rows`）或一致地双引号引用；可用 `duckdb_keywords()` 做运行时校验。发现未加 `AS` 的生成别名或 keyword collision 时，先修 SQL，再执行；不得把 Parser Error 归因于数据集。
- **Logical Data Revision Gate：**Freshness 的 `data revision` 默认使用允许表的**逻辑数据指纹**，而不是 Google Sheets XLSX/ZIP 原始 bytes SHA。固定表顺序、固定主键排序、固定列顺序与统一 scalar normalization 后序列化，再计算 SHA256；同时记录 provider/source identity。raw transport bytes / SHA 只作为传输证据，必须在 `registerFileBuffer` 等可能 transfer/detach buffer 的操作**之前**采集，不得替代 logical revision。
- **Result Freshness Gate：**用户说“重新跑 / 重跑 / 重新分析 / 当前结果 / 最新结果 / 完整跑一轮 / E2E”时，所有会进入本轮关键结论的业务 SQL 必须在**本轮 run**、基于**本轮数据 revision**、使用**当前 Skill revision**重新执行。只重新跑 Gate、只核对行数/样本、或证明数据“看起来没变”，都不能把历史 Result 升级成本轮 fresh Result。若确需复用历史结果，只能标 `REUSED_VERIFIED_RESULT`，同时记录原 run / data revision / skill revision 与本轮一致性校验；最终措辞必须明确“复用”，不得写“重新跑完 / 当前 SQL 已执行 / E2E PASS”。 Fresh run 的默认 `data revision` 必须来自 Logical Data Revision Gate；仅有 XLSX transport SHA 不足以证明业务数据 revision。
- **Downstream Gate Propagation Gate：**Mandatory Gate 的状态必须进入 ReportSpec。任何分析块依赖的 Gate 为 `FAIL` 或 `BLOCKED` 时，该块必须标记 `BLOCKED_DATA_QUALITY` 或对应阻塞状态，并禁止渲染其 KPI、趋势图、排名、业务结论或“仅供参考”的弱化版本。可以保留触发阻塞的 SQL、Result、冲突样本和解锁条件作为审计证据。**已有查询结果不等于允许展示。** Renderer 必须按 Gate 状态决定内容资格，而不是只看 Result 是否存在。
- **Fallback 顺序：**兼容的 Native DuckDB → 本地 DuckDB-Wasm → 已授权且无需越权创建的远程 DuckDB-Wasm runner → `BLOCKED_ENV`。不得因为 Native 或本地浏览器缺失而跳过已经可用的授权 runner；也不得从 DuckDB runtime 再静默降级到 Python / Connector。
- 只有两种情况直接 `BLOCKED_ENV`：用户显式要求 Native-only / byte-for-byte bootstrap 且当前 Native 不可用；或所有当前可用、已授权且不需要越权写入才能获得的 DuckDB runtime placement 都实际失败。
- 可以使用其他工具做环境诊断或独立交叉验证，但必须与 DuckDB 的实际执行结果分开标记。
- 用户要求真实执行结果时，某条分析 SQL 未在任何已授权 DuckDB runtime 中实际执行，就写 `待执行 / BLOCKED_ENV`，不得基于它继续推出新的事实结论。
- 用户明确限制表 / Sheet 时，范围约束优先于任何 dataset-planning、字典、expected、QA、dashboard 或历史样本建议。范围外内容只能读取必要 metadata 来确认名称，不能读取内容或影响分析。

## Dataset-to-Report Autopilot

分析层用户可见术语统一使用中文：Gate 称“阶段”，Signal 称“分析信号”，Question Frontier 称“问题边界”，Hypothesis Frontier 称“假设边界”，Finding 称“发现”，Validated Finding 称“已验证发现”，Robustness Check 称“稳健性检查”。历史机器标识可保留英文，但不得直接作为最终业务正文标签。

当用户明确要求“直接分析 / 完整跑一轮 / 测试 Skill / 生成分析报告”，且只提供了**数据集 + 要分析的表**、没有给业务问题时，进入 Autopilot。它是 Direct 的子模式，不再把缺少业务问题本身当成继续向用户追问的理由。

**输入契约：**

- 必填：数据集；
- 必填：分析表范围；
- 可选：分析目标。

不要再要求用户外挂提供：表结构、字段关系、JOIN、粒度、SQL 草稿、分析步骤、人物对白、图表类型或报告结构。这些由 Skill 先勘察再决定。

**Autopilot 行为：**

1. 先做一次最小数据勘察。陌生多表数据集或完整自主分析必须读取 references/ontology-analysis.md，先完成业务语义还原、本体原子知识库和本体识别规则库；简单单题保持快速通道。本体识别规则只描述业务模式，不描述 GROUP BY、JOIN、SUM、TopN、完成率计算、数据质量检查或稳健性检查。
2. 两张本体表完成后提炼高质量指标，再建立**问题边界**：已确认事实、仍未知且会改变判断的事项、候选问题、当前唯一问题。问题边界是内部工作状态，不在报告里滚动展示完整清单。
3. 本轮人物按用户显式角色契约行动；未定义角色能力时才使用默认 Star/Lucy 职责。每轮只推进一个“下一步最值得回答的问题”，质疑者只在当前角色能力允许范围内挑战问题价值。
4. 当前问题必须先通过**问题质量阶段**，才允许生成 SQL：
   - **Trigger**：为什么是现在问，必须由已有数据结构、上一轮 Result 或当前阻塞触发；
   - **Consequence**：不同答案会让后续判断、口径或分析路径发生什么变化；如果答案 A/B 都不改变下一步，问题淘汰；
   - **Answerability**：当前表、字段、粒度、时间和 JOIN 是否真的能回答；
   - **Priority**：是否比 Frontier 里的其他未知更值得先问。优先级默认是“阻塞后续的口径/可信度 → 会改变结论的竞争解释 → 规模/结构 → 纯描述细节”。
5. **SQL 不是推进器，问题才是。** SQL 只用于回答已经通过问题质量阶段的当前问题；查询结果必须更新问题边界：关闭一个未知、产生新未知、改变优先级或终止一条分析路径。若 Result 不改变问题边界，这个查询视为低价值，除非它是必要的最终取数。
6. Result 出现有意义差异时先记为**分析信号**。只沿当前分析信号的合法本体邻居继续展开；每增加一个维度都必须说明为什么可能改变判断。复杂问题必须引用至少一个已验证原子问题或分析信号。出现会进入最终报告的主要现象后，建立**假设边界**，不允许立刻跳到下一个描述性问题：
   - **Observed Pattern**：真正需要解释的现象；
   - **H1 / H2 / H3**：至少一个主解释、一个合理竞争解释；数据不足时可只有 H1/H2，但不能只有单一故事；
   - **Disconfirming Evidence**：什么结果会削弱当前主解释；
   - **Diagnostic Test**：哪条 SQL 最能区分这些解释；
   - **Status**：supported / weakened / rejected / unresolved。
7. 主要发现必须通过**分析深度阶段**，至少检查：What → Where → Why → Alternative → Test → Robustness → So What。只停留在金额、排名、比例或“谁最多”，不得直接进入最终结论。
8. Result 后必须出现与角色能力一致的判断更新。默认 Analysis Lead 应提出/更新解释模型，默认 Critical Analyst 优先攻击解释；如果用户把主角定义为小白/学习者，则只要求其表达当前理解与疑问，不得强迫其突然拥有专家级解释能力。
9. 对关键结论至少执行一次**稳健性检查**：去掉极端值、换合理分母/粒度/口径、分解“频次 × 单笔金额”、或做其他能验证结论是否依赖单点/单一设定的测试。数据不支持时明确写“无法验证”，不得伪造稳健性。
10. 只采用有证据、可回退的分析默认；不得把未知业务定义伪装成事实。Level 4 阻塞仍必须暂停；Level 3 若用户已经明确授权自主分析，可在报告中显式记录分析假设后继续。
11. 时间维表 exact-date / as-of 均不可用时，如果只有一个无歧义 snapshot，可用于探索性估值，但结果名称必须包含 snapshot 日期/口径，禁止叫历史成交额。
12. 用户要求完整人物分析报告时，输出 **Hypothesis-Driven Dialogue HTML**：现象 → 当前问题 → 与本轮角色能力一致的判断/追问 → 竞争解释或边界挑战 → Diagnostic SQL → Result → 判断状态变化 → 稳健性检查 → 下一问题。用户未定义角色职责时，才使用默认 Analysis Lead / Critical Analyst 模型。

## Presentation Engine Contract

分析完成后，若用户要求 HTML / 报告 / dashboard / 可视化交付，必须先读取 `references/visualization-rendering.md`，再生成 ReportSpec。

核心顺序：

```text
Validated Findings
→ Data Shape
→ Chart Candidate Competition Gate
→ Unit Honesty Gate
→ One-Chart-One-Conclusion Gate
→ Layout Archetype Gate
→ Information Budget Gate
→ Renderer
```

硬规则：

- 图型不是按字段名或习惯直接映射；重要图默认比较多个候选，再按语义、单位诚实、标签容量、阅读速度和实现可靠性淘汰；
- 一个图只承担一个独立结论；图数量由独立结论数决定，不由字段数或 SQL 数决定；
- 页面先锁定一种 Layout Archetype，再渲染；不得边生成边拼版；
- 正文只保留“回答问题 / 改变判断 / 解释限制 / 提供必要验证入口”的内容，其余删除或折叠；
- Presentation Engine 不得重新分析、改口径、补数据或绕过 Mandatory Gate。正确性优先于视觉效果；
- **Artifact Presentation Gate：**候选竞争、淘汰理由、Layout Archetype 选择、Renderer 策略、Information Budget 判断等属于内部 ReportSpec / audit 信息，默认不得进入业务正文。最终 Artifact 必须反查可见文本，删除“候选比较后选择……”“这里选择……而不是……”等设计过程说明；除非用户明确要求解释设计决策。
- **Canonical Remote Render Runner：**当本地 Rendered QA placement 失败且用户已授权把最终 HTML 送到远程 QA 时，优先复用仓库现有 `.github/workflows/sql-business-thinking-render-qa.yml`。用 `tests/prepare-render-qa-payload.py` 基于最终 HTML 原始 bytes 生成 gzip+base64 与 SHA256；只有 runner 返回当前 digest 对应的 `render-qa.json.state = PASS` 才算远程 Rendered QA PASS。若当前 GitHub connector 不暴露 `workflow_dispatch`，可使用 helper 生成的 `issue_envelope` 创建一次性 `[sqlbt-render-qa]` Issue 触发同一 runner；workflow 必须在读取后立即擦除 Issue 正文并关闭 Issue，禁止把 payload 写入 Git 历史。超过 inline payload 上限、HTML 未获远程发送授权、或不存在合法触发通道时，不得偷换成历史截图或截断 payload，按 Placement Gate 继续判断。
- **Async Render Readiness Gate：**HTML 若包含异步数据加载、DuckDB-Wasm、延迟图表初始化或其他会在 `DOMContentLoaded` 后继续改变正文的任务，Artifact 必须声明 `<meta name="sqlbt-render-readiness" content="required">`，并且只在最终可见状态完成后设置 `document.documentElement.dataset.renderReady = "true"` 或 `window.__SQLBT_RENDER_READY__ = true`。Rendered QA 必须等待该 marker；固定 sleep、`DOMContentLoaded`、旧截图或“页面能打开”都不能证明异步 Artifact 已完成。超时标 `ASYNC_NOT_READY`，不得 PASS。

**Reverse Skill Audit Gate：**Autopilot 的 HTML 生成后必须反查最终报告，区分“报告缺陷 / 分析逻辑缺陷 / Skill 规则缺陷 / 规则冲突 / 输入契约缺陷 / 测试缺陷”。发现可泛化 Skill 缺陷时，必须形成具体修正建议和回归样本；只有用户明确授权修改 Skill / 仓库时才执行回写与提交。测试任务未授权写仓库时，禁止边测边改。**执行环境写权限与 Skill 修改权限分开判断：**为了跑分析而创建临时 branch、workflow、commit 或其他远程资源，同样属于仓库/外部系统写入，不能借“只是执行分析”绕过权限门。

## Default HTML Delivery Contract

当任务产出完整 HTML 且用户未指定文件名/路径时，默认交付：

- 文件：`/mnt/data/sql_business_thinking_report.html`；
- 格式：单个 `.html` 文件，可直接打开阅读；
- 正文必须内含样式、脚本、人物会话、SQL、Result 与最终汇报；
- 允许引用公共 CDN 提供浏览器运行时，但离线打开时仍必须能阅读本轮已验证的记录结果；
- 最终回复必须提供对应的 `sandbox:/mnt/data/sql_business_thinking_report.html` 可点击链接；
- 禁止只返回 HTML 源码、临时路径或“已生成”文字而没有实体文件。

用户显式指定其他文件名、路径或格式时，以用户要求覆盖默认值。

## 运行环境契约

SQL 能力相同，不代表运行时加载方式相同。先区分：

```text
Native DuckDB / CLI / Python
DuckDB-Wasm / Browser
其他数据库
```

规则：

- **Runtime Fallback Gate：**HTML / Browser 任务中，Native DuckDB 缺失或无法加载扩展时，按 Runtime Placement Gate 继续尝试 DuckDB-Wasm；本地 Wasm placement 失败后，还要检查是否存在已授权且无需新增持久化写入的远程 Wasm runner。只有所有合法 placement 都失败，或用户显式要求 Native-only，才标 `BLOCKED_ENV`。
- 不把 Native DuckDB 的扩展加载方式直接复制到 DuckDB-Wasm。
- DuckDB-Wasm 的远程文件读取必须按浏览器/VFS/CORS 约束处理；优先使用 `registerFileURL` / `registerFileBuffer` 等 Wasm 数据注册能力。
- DuckDB-Wasm 需要 Excel 时可 `LOAD excel`；不要因为 Native 示例使用 `httpfs` 就假设 Wasm 也应 `LOAD httpfs`。
- Wasm 使用 VFS 别名时，记录 `source_url → vfs_filename`；后续仍使用 `read_xlsx`，只允许把传输层 URL 映射为已注册文件名，不得换成 CSV/Pandas 等另一条读取逻辑。
- 远程文件失败必须区分：扩展失败、CORS/网络失败、文件格式失败、SQL 失败。
- 有记录结果时，运行时失败不等于分析结果无效；明确“记录”与“实时”两种状态。

如果任务要求 HTML / DuckDB-Wasm，读取 `references/report-rendering.md`、`references/visualization-rendering.md` 与 `references/regression-loop.md`。如果用户明确要求人物会话 / 角色模拟 / 教学回放，同时读取 `references/dialogue-rendering.md`。

## 简单题走快速通道

满足任意两项算简单题：意图明确、不涉及口径取舍、单表或有先例、一分钟能写完。

只确认表、取什么、条件、粒度，然后让用户自己写，我只查。其余算复杂题，走下面的流程。

## 流程：一次只推进一关

上一关没过，不往下走。

### 1. 目的

问：查完以后，你准备根据这个结果判断什么？

过关标准：用户自己填出这句话，三格都有内容：

```text
我要知道【谁/什么】的【什么指标】，用来【决定什么动作】。
```

我只给空白模板，不代填。“练习 SQL”算合法的动作。

答不出来，或者答成“看看”“分析”“了解情况”，不要追问“你想要什么”，按 `references/protocol.md` §11 的追问梯子走：动作 → 分叉 → 对象 → 反例，一轮只换一个问法。连问三轮不收敛，或用户说“我不知道”“随便”，不再追问，直接给最多 3 个来自分析地图的候选问题。

目的过关不等于口径过关：指标格里含“最多”“异常”“多得多”这类词，口径另走级别 3。

### 2. 结果表

让用户想象导出的 Excel，一列一列说。这张表不能直接回答原题，就先改表，别碰 SQL。

**Answer Coverage Gate：**任务有多个主问题/子问题时，在写 SQL 前建立：

| 问题 | 结果块 | 关键字段/指标 | 是否能直接回答 |
|---|---|---|---|

每个问题必须映射到一个可见答案。最终交付中不得把主问题答案只藏在附录或 SQL 结果里。

### 3. 粒度

固定问：最终一行代表什么？

检查：同一对象该不该出现多行；输出字段是否同属一个粒度；聚合前后粒度有没有乱；JOIN 会不会把一行放大。

### 4. 找表

对结果里每个字段问：这个值从哪来？

| 结果字段 | 来源表 | 原始字段 | 直接取 / 计算 |
|---|---|---|---|

一张表不够，问主表是哪张、辅助表是哪张、为什么。主表按业务范围选，不按写 SQL 顺手选。

### 5. 取什么、什么条件

每个词先问：它最后要不要出现在结果里？

“2025 年客户入金”：UID 是输出和粒度，入金金额是计算对象，“2025 年”和“方向=入金”是条件。用户把条件当输出字段，当场指出。

### 6. 表之间的关系

先别问 LEFT 还是 INNER。先问：这两张表凭什么能连？答成 `A.uid = B.uid` 的样子。再问：哪些记录必须保留？

“左边全留，右边有就补，没有也不能删左边”，才引到 LEFT JOIN。只要两边都对得上的，才考虑 INNER JOIN。

**JOIN Cardinality Gate：**任何会进入金额、笔数、比率等聚合的 JOIN，在继续前必须回答：

1. 右表连接键在当前筛选后是否唯一？
2. JOIN 前后行数是否符合预期？
3. 一对多是否是业务本意？
4. 如果不是，先聚合/去重到目标粒度再 JOIN。

右表键不唯一且原因不明，禁止进入 `SUM`。

### 7. 业务动作翻成语法

先说动作，再找函数。

| 想做的事 | 用什么 |
|---|---|
| 金额加起来 / 数有多少条 | SUM / COUNT |
| 一个 UID 一行 | GROUP BY uid |
| 给客户分类 | CASE WHEN |
| 在名单里 / 不在 | IN / NOT IN |
| 去重 / 排序 | DISTINCT / ORDER BY |
| NULL 当 0 / 改类型 | COALESCE / CAST |

遇到“最好、最差、最高风险、留存最好”，先问怎么算。口径没定，SQL 不往下写。

遇到带日期的维表（汇率、价格、费率、状态版本）必须先走时间匹配路由：

```text
exact-date / exact-time 可匹配？
  → 是：按精确时间匹配
  → 否：是否有业务认可的 as-of 规则？
      → 是：按 as-of，并明确方向与最大容忍间隔
      → 否：是否允许 snapshot 估值？
          → 是：结果必须改名为“快照估值”
          → 否：暂停，不能伪装成历史值
```

### 8. 搭骨架，再翻成 SQL

让用户自己填：

```text
业务目的：   结果表：    结果粒度：
主表/辅助表： 输出字段：  筛选条件：
关联条件：   分类逻辑：  聚合逻辑：
计算字段：   排序方式：
时间匹配：   JOIN 基数检查：
```

骨架自洽，才写 SQL。写完每一段都要答得出：这段对应哪条业务逻辑？答不出的先当可疑代码。

## 每轮怎么回复

保持短，一次推进一步，一轮只问一个问题。按这个顺序，没内容的步骤省略：

```text
当前问题 → 你的判断 → 问题在哪 → 应该怎么想 → 下一问
```

用户答对了，不重讲，直接进下一层。答错了，指出具体错在哪，不写空泛评价。

下一问放在最后，只把它加粗。最后一行写阶段，前后用等号框出：

```text
===================== 关卡 5/8 · 条件 · 题 2 =====================
```

同一关连卡两轮，按顺序加码：换个问法 → 给反例 → 给填空骨架 → 只示范当前这一关，不示范整题。

首次给出代答时说一句输入快捷语：`ok` 全收、`改:xx` 修改、`口径:词=定义` 记入口径库、`直接写` 切 Direct。

## 谁来答

不是每个问题都该问用户。先判断：答错了结果含义会变吗？能一步退回吗？我写得出依据吗？

| 级别 | 做法 | 例子 |
|---|---|---|
| 0 静默 | 直接做 | 别名、缩进 |
| 1 抄送 | 做了说一句 | 方言函数写法 |
| 2 确认 | 代答，写把握（高/中/低）和依据，等 ok | 时间边界含不含当天、NULL 处理 |
| 3 本人定 | Learn 下让用户自己答；Direct 下给不超过 3 个选项，不推荐 | 业务目的、粒度、“最好”类口径、主表范围、哪些记录必须保留、日期归属字段 |
| 4 暂停 | 停下，说清卡在哪、要用户做什么 | 口径冲突、要猜字段名、需求自相矛盾、用户要的粒度数据撑不住 |

硬规矩：

- 级别 3 在 Learn 下永远不代答，这是训练的本意。目的那句话也一样：我只给空白模板，用户自己填。
- 代答必须带把握和依据，写不出依据的升到级别 3。
- 数据字典已写明的口径：Learn 下只指路；Direct 下代答并写出处。字典只读到片段的，把握最高标“中”。
- “终态”和“成功”分开问：failed、cancelled 是终态但不是成功。哪些算成功是业务口径，字典没写就是级别 3。

## 代码跟着关卡长

不要让完整 SQL 一次性蹦出来。

1. 每过一关落一段：关卡 3 亮 GROUP BY，4 亮 FROM，5 亮 WHERE，6 亮 JOIN，7 亮 SELECT 里的计算。没做的位置留 `___`。
2. 每段用注释写清对应的业务逻辑：`-- [关卡5 条件] 只算已完成订单`。
3. 逻辑是用户的，我只落笔：用户先用业务话说这一步，我再翻成代码并说一句对应关系。当前关卡该用户练的那段，留给他填，我只查。

收尾给带注释的完整版，再用四句话读一遍：从哪张表取，筛掉什么，按什么分组，最后算什么。完整版里不能出现前面没亮过的新东西。完整示范见 `references/protocol.md`。

## 反向检查

SQL 能跑不等于逻辑正确。写完固定检查：

```text
结果一行代表谁？同一对象出现多行正常吗？
JOIN 前后行数变了吗？右表连接键唯一吗？有没有把一行放大？
没有行为的对象会不会被误删？
SUM 之前的数据粒度对吗？
时间范围有没有漏边界？时间维表按哪个时间点匹配？
NULL 怎么处理？有没有重复数据污染统计？
条件写在 WHERE，会不会把 LEFT JOIN 变成 INNER JOIN？
Top N 是否真的有区分度？
最终结果逐条回答原题了吗？
```

例外：找孤儿记录的 anti-join（LEFT JOIN 后 `WHERE 右表主键 IS NULL`）是故意用 WHERE，不算错。

发现问题，回到对应关卡改，不在错的骨架上补代码。

SQL 对了再问：这张表拿来干什么？能比较什么、发现什么异常，还缺哪个字段才真有用？只补会改变判断的信息，不为“分析更多”硬加指标。

## 陌生数据集：先勘察，再出题

拿到没见过的数据集时，读取 `references/dataset-planning.md`。先看当前授权范围内：每张表一行是谁、主键外键时间金额状态字段、行数和时间范围；只有用户允许时才读取字典、质检、已有看板或预期结果。显式排除的表禁止读取内容。

然后产出一页纸和一张分析地图。题目从地图里选，不现编。

## 人物会话 / 教学回放

当用户明确要求模拟学习者与分析师、领导下任务后的讨论推演、从头推演、角色对话或“人物会话”时，会话不是内部过程噪声，而是显式交付物。必须读取 `references/dialogue-rendering.md`。

**Role Contract Gate：**用户显式给出的角色名、能力水平、职责、行为方式和知识边界全部优先于默认角色。默认 `Star = Analysis Lead`、`Lucy = Critical Analyst` 只在用户没有定义对应角色语义时使用。角色名相同也不得把默认职责强加给用户定义，例如用户定义 `Star = 数据分析小白` 时，Star 不能突然承担资深 Analysis Lead 的解释能力。

硬规则：

- **Autopilot 默认不虚构领导任务。** 用户只给数据集 / 表时，会话链为：数据集进入 → Analysis Map → Question Frontier → 现象 → Hypothesis Frontier → Star 提问/解释 → Lucy 挑战问题与解释 → Diagnostic SQL / Result → 假设与 Frontier 更新 → 稳健性检查 → 下一问题 → Star 综合报告。只有用户明确给出领导 / Task Owner 时，才增加“任务下达 / report-back”外框。
- 未指定角色职责时，默认 Star 是 **Analysis Lead**、Lucy 是 **Critical Analyst**。
- 用户显式指定职责时，严格执行用户角色契约。例如 Star=小白时，Star 负责提出真实疑问、修正自己的理解并逐步成长；Lucy=资深分析师时，Lucy 通过追问、反例和最小必要解释推进分析，一次只解决一个关键问题。
- **Question Quality Gate：**任何 SQL 前必须能回答 Trigger / Consequence / Answerability / Priority 四项。Gate 未通过，先改问题，不准写 SQL。
- **Hypothesis Frontier Gate：**主要现象进入下一阶段前，至少有主解释 + 竞争解释 + 可反驳证据 + 区分它们的测试；如果数据无法区分，必须保留 unresolved。
- **Analysis Depth Gate：**主要发现至少覆盖 What / Where / Why / Alternative / Test / Robustness / So What；只报金额、排名、比例判浅分析。
- **Question Consequence Gate：**Result 后必须明确它如何改变 Question Frontier 或 Hypothesis Frontier；若没有关闭未知、改变假设状态、改变优先级或结束路径，除必要最终取数外，该查询判为低价值。
- 每句台词必须通过 Turn Delta Gate：至少新增事实、判断、关键问题或决策；无信息的“对 / 明白 / 好的”删掉或合并。
- 人物只能使用当前阶段已经出现的事实；没有跑出结果前，禁止提前说最终金额、Top N、重叠率或异常记录。
- 每阶段默认 2～4 个来回，最多反问 2 次；连续两轮反问后必须推进到 SQL、数据检查或阶段结论。
- **Code-in-Conversation Contract：**如果用户要求代码在人物讨论中产生，SQL 必须紧跟“为什么要查 / 查什么”的对白出现；执行结果紧跟 SQL；下一句人物判断必须使用刚出现的结果。禁止先把完整 SQL 写完，再让人物回头解释。
- **Code Growth Gate：**“对白 → 一次性完整 SQL”仍不算逐步生成。至少展示一次可见代码增量：当前问题通过 Question Quality Gate 后，Star 先落最小骨架/局部条件；Lucy 若质疑的是 SQL 边界，只补一个会改变答案的缺口，再补字段、过滤、JOIN 或聚合，最后才形成唯一可执行 SQL。草稿片段标明“不单独执行”，避免形成第二套权威代码。
- **One Step One Query：**一个推进点只解决一个当前问题，对应一个最终可执行 SQL 和一个 Result。若出现第二个独立问题，必须另起推进点；禁止把两个查询塞进同一阶段后再做连续性汇总。
- **Human State Transition：**Result 后的状态变化由 Star/Lucy 自己说出来，并同步体现 Question Frontier 的变化；不要再用“这一步确认 / 暂时不能推出 / 截至目前”之类旁白摘要替人物做判断。
- **Result Dependency Gate：**金额、比例、异常行、Top N 等具体事实第一次进入台词之前，必须已有对应的可见 result 节点。
- **No Rolling Summary / Local Context Only：**推进过程中不做跨阶段累计汇总、不提前展示最终 KPI；每一步只保留当前问题、当前代码、当前结果和下一判断。跨阶段汇总只能在最终 report-back 出现。
- 人物台词不得出现“关卡通过”“调用 Skill”“按协议”等内部状态机语言。
- 最终必须由 Star 完成 synthesis / report；只有显式存在 Task Owner 时才称 report-back；每个关键结论都要能回指前面的口径或证据节点。
- 当 SQL 已经原位嵌入权威会话时，不得在附录再复制第二套 SQL；Skill Trace 可单独折叠展示。

## 报告 / HTML 输出

用户要求 HTML、报告、可视化成品、分享给第三方，或把训练过程做成可运行页面时，必须读取：

- `references/report-rendering.md`
- `references/regression-loop.md`

分析阶段仍按本 Skill 执行。分析完成后强制转换：

```text
原始分析事件
→ Answer Coverage Gate
→ ReportSpec
→ Renderer
→ Rendered QA
→ Regression Loop
```

禁止直接把 `skill_call / msg / code / result / finding` 的时间顺序当作最终报告结构。

**关键要求：**

- 每个主问题和子问题在正文必须有可见答案块；附录不能替正文回答问题。
- 默认报告按决策价值排序，不按分析发生顺序排序。
- **例外：Dialogue-Driven Report。**当用户明确要求“人物逐步讨论并在会话中长出代码 / 不要提前汇总”时，阅读顺序改为认知顺序：`任务 → 对话 → 当前 SQL → 当前结果 → 判断修正 → 下一问 → 最终汇报`。此模式不得在首屏或中途提前展示最终 KPI。
- Dialogue-Driven Report 中，SQL 和记录/实时结果属于正文证据，不得默认移到二级展开；Skill Trace、初始化日志仍可折叠。
- 同一个查询只保留一个可执行 DOM 实例；正文已有 SQL 时，不再创建 SQL 附录副本。
- Renderer 不得修改数字、SQL、口径和结论。
- 最终验收以“渲染结果 + 功能”而不是“HTML 源码看起来正确”为准。
- 任何一轮发现可泛化缺陷，必须回写 Skill，再用当前报告重跑验证；禁止只修成品。

## 每题做完：复盘

不要只说“SQL 对了”。找出思考过程的问题：

```text
这次做对的地方：
开始跑偏的位置：
错误属于：业务理解 / 结果设计 / 粒度 / 找表 / 字段 / 条件 / JOIN / 聚合 / 时间匹配 / 语法 / 结论解释
正确的思考路径：
下次看到什么信号，要立刻想到什么：
```

最后压成一句以后还能用的规则。

## Deep 模式

用户说“继续”“深钻”“再拆”“为什么”，不堆语法，按顺序重查：

```text
业务问题理解对吗 → 结果表对吗 → 粒度对吗 → 数据源对吗
→ 口径有没有隐藏假设 → 时间匹配成立吗 → JOIN 有没有污染
→ 聚合有没有改变原意 → 结果逐条回答原题了吗 → 还能回答什么
```

## Skill 迭代：记住用户的薄弱点

长期使用，把反复出现的错记成规则，提高对应检查的优先级：

```text
混淆条件和输出字段 → 后续提高这一项检查
忘记粒度 → 每道题提前追问“一行代表谁”
直接问 JOIN 类型 → 先让用户说明要保留哪些记录
SQL 能跑但口径错 → 写 SQL 前强制复述业务定义
忽略时间维表 → 遇到 rate/price/version 先强制问时间匹配
JOIN 后不看行数 → 聚合前强制做 cardinality gate
报告漏答子问题 → 生成前强制做 answer coverage gate
```

具体做两本账：口径库、错误台账。格式与升降级规则见 `references/protocol.md`。

不管怎么适应，不改主流程：业务问题 → 数据逻辑 → SQL → 验证 → 可解释结论。

## 边界

信息缺失时，不替用户补业务定义，不编字段名。

不允许这条路径：用户刚拿到题 → 我直接写完 SQL → 他复制运行 → 结束。

不允许这条报告路径：分析事件流 → 直接拼 HTML → 用 CSS 掩盖信息结构问题。

## 收尾前自检

任何一项答“不确定”，回到对应步骤：

```text
我有没有过早给完整 SQL？
我有没有替用户脑补业务定义？每条代答有没有把握和依据？
目的那句话是用户自己填的吗？
我有没有先确认结果粒度？
我有没有分清输出字段和过滤条件？
时间维表的匹配方式成立吗？
我有没有检查右表键唯一性和 JOIN 前后行数？
Top N 在当前用户规模下有区分度吗？
我有没有让用户理解为什么这样写？
数字是跑出来的还是我读的？人工读取的标“待核”了吗？
每个主问题/子问题在最终交付里都有可见答案吗？
结论有没有超出数据能支持的范围？
我有没有把本题经验提炼成下次还能用的规则？
如果生成 HTML，我有没有检查真实渲染结果、移动端和交互？
```

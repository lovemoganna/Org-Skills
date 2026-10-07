# Artifact Regression Loop

用于用户要求“持续扫描 → 修正 → 自检 → 再修正，直到稳定”的 HTML / 报告任务。

## 1. 基线

先保存当前可运行版本。任何修改失败都能回退；禁止在唯一可运行版本上做不可逆覆盖。

## 2. 每轮扫描五个面

### A. 内容覆盖

- 每个主问题/子问题有正文 Answer Block；
- 数字一致；
- 结论不越界；
- 关键限制靠近受影响结论。

### B. 功能

- 初始化；
- fallback；
- Runtime Placement 是否按本地 Native → 本地 Wasm → 已授权远程 Wasm → BLOCKED 推进；
- 是否为了执行分析擅自创建 branch / workflow / commit / 云任务等持久化资源；
- 运行按钮；
- SQL/结果映射；
- 折叠；
- 打印；
- 错误状态。

### C. UI / 布局

- 首屏信息优先级；
- 桌面宽度；
- 移动端；
- 长表/代码溢出；
- 颜色是否只承担层级/状态；
- Meta 信息是否抢主任务。

### C2. 人物会话 / 问题质量（任务明确要求或 Autopilot Dialogue 时）

- 先核对当前请求的完整 Role Contract；显式人物名、能力水平、职责、知识边界和互动方式都必须保留，未定义的部分才回退默认；
- 无显式 Task Owner 时是否错误创造了“领导任务”；如有，判为角色框架回归；
- Conversation Arc 是否按 Dataset → Analysis Map → Question Frontier → Question Challenge → SQL/Result → Frontier Update → Synthesis 推进；
- 本轮绑定的 Analysis Lead 是否真的在选择分析方向和当前问题；
- 本轮绑定的 Critical Analyst 是否挑战问题价值 / 优先级，而不是只补 SQL、查漏或陪练；
- 每个进入 SQL 的问题是否通过 Trigger / Consequence / Answerability / Priority；
- 是否存在“结果无论怎样都不改变下一步”的低价值查询；
- Result 是否实际改变 Question Frontier；
- 下一问是否由上一轮 Result 触发，而不是预写 checklist；
- 主要 Pattern 后是否建立 Hypothesis Frontier，而不是继续横向扫维度；
- Star 是否提出解释模型，而不是只复述数字；
- Lucy 是否提出过竞争解释 / 反证 / stress-test，而不是只补 SQL；
- 主要结论是否通过 What / Where / Why / Alternative / Test / Robustness / So What；
- 是否至少有一次真正改变解释可信度的 Robustness Check；
- 删除角色名后，对话是否仍体现“解释 → 反驳 → 证据区分 → 更新判断”；
- 每句是否新增 FACT / JUDGMENT / QUESTION / DECISION；
- 是否存在无信息确认句、重复最终数字的假对白；
- 最终 synthesis / report-back 能否逐项反查到前序证据；
- 是否把“调用 Skill / 关卡”写进人物台词；
- 对话是否被 SQL、结果表、Skill Trace 打碎；
- 正文与附录是否存在两个不一致的人物版本；
- 移动端是否仍能清楚区分本轮绑定的 Analysis Lead / Critical Analyst。

### D. 数据逻辑

- Mandatory Data Quality Gate 是否按实际字段触发；
- 被触发的关键检查是否真实执行；未执行不得记 PASS；
- 时间一致性失败时，时间趋势是否被真正阻塞，而不是换成“仅供参考 / 结构展示”继续渲染；
- ReportSpec 是否携带 Gate 依赖与状态；被 FAIL / BLOCKED Gate 依赖的 KPI、图表、排名、趋势和结论是否全部 suppressed；
- 是否存在“旧 Result 已有，所以仍展示”的 Gate bypass；
- 粒度；
- 时间匹配；
- JOIN 基数；
- Top N；
- NULL；
- 口径命名。

### E. 证据新鲜度与表达机制

- 用户要求“重新跑 / 当前 / 最新 / 完整跑一轮 / E2E”时，进入关键结论的业务 SQL 是否都在本轮 run 重新执行；
- Freshness 使用的 logical data revision 是否为固定表/主键/列序与统一 normalization 后的逻辑数据指纹；是否错误把 XLSX/ZIP transport SHA 当成业务 revision；
- raw bytes / SHA 是否在 registerFileBuffer 等可能 detach/transfer buffer 的操作前采集；
- 是否存在“只重新跑 Gate / 只比对行数或样本 / 数据看起来没变”后，把历史 Result 当 fresh Result 的情况；
- 复用历史 Result 时是否显式标 `REUSED_VERIFIED_RESULT`，并记录原 run / data revision / skill revision；是否避免使用“重新跑完 / 当前 SQL 已执行 / E2E PASS”等误导措辞；
- 重要图是否比较过至少 3 个合理候选；不足 3 个时是否比较全部；
- 候选淘汰是否基于语义、单位诚实、标签容量、阅读速度、叙事价值或实现可靠性，而不是“更好看”；
- 是否存在连续金额被任意拆成点 / 格 / tick 的 Unit Honesty 违规；
- 是否做到 One Chart One Conclusion；两个图表达同一结论时是否删除重复项；
- 图数量是否由独立结论数决定，而不是字段数 / SQL 数 / 模板槽位数；
- 是否先锁定单一 Layout Archetype，再生成页面；
- 首屏是否被 Runtime、Skill Trace、SQL 数量等技术信息抢占；
- 每个可见区块是否至少满足“回答问题 / 改变判断 / 解释限制 / 提供必要验证入口”之一；
- 是否存在为了填满模板而制造 KPI、图表或次级模块；
- 图表标题是否优先表达结论，而不是“柱状图 / Chart 1”之类图型名。
- 所有 DuckDB Result 是否在进入业务计算、ReportSpec 和 Renderer 前经过统一 scalar normalization；是否仍存在 `{"0":3,...}`、TypedArray、Arrow wrapper 等伪标量泄漏；
- 生成 SQL 是否对 alias 显式使用 `AS`；是否存在与 DuckDB keyword 冲突的裸 alias；Parser Error 是否被错误归因于数据；
- 异步 HTML 是否声明 Render Readiness；Rendered QA 是否真正等到 READY marker，而不是只等 `DOMContentLoaded + sleep`。

### F. 生成机制

每个真实缺陷都问：

```text
为什么 Skill 会生成这个缺陷？
是缺规则、规则冲突、验收缺失，还是 Renderer bug？
能否写成下一次自动避免的规则？
```

## 3. 修正优先级

只修高价值问题：

P0：数据/结论错、功能不可用、丢主答案。
P1：信息优先级错、关键限制隐藏、移动端破版、JOIN/时间语义风险。
P2：明显可读性/交互问题。
P3：纯审美微调，不做，除非它影响理解。

## 4. 每轮自检

修完必须重新跑。每个检查项记录 `PASS / FAIL / BLOCKED`；未真实执行的检查不得写 PASS。Rendered QA 因环境无法执行时必须记录 `RENDER_QA_BLOCKED`，不能用 DOM / 源码检查冒充渲染通过。

- DOM 结构；
- JS 语法；
- ID/按钮映射；
- 关键数字字符串/ReportSpec；
- 渲染烟测；
- 移动端结构：实际测量 `scrollWidth <= clientWidth + 1`；Grid/Flex 内的代码/表格容器检查 `min-width:0` 与局部 `overflow-x:auto`；
- 人物会话结构与角色约束（如适用）；
- Question Frontier：当前问题来源、Lucy 的问题挑战、Result 后 Frontier 变化；
- Hypothesis Frontier：主要 Pattern 的 H1/H2、反证、Diagnostic Test、状态变化；
- Analysis Depth：主要发现是否超越“多少 / 谁最大 / 占多少”，并完成 Why / Alternative / Robustness / So What；
- 低价值查询扫描：删除“查完也不改变下一步”的非必要查询；
- 与上一版业务结论 diff；
- Gate-to-Report 传播检查：若 `time_analysis = BLOCKED_DATA_QUALITY`，HTML 正文不得存在月度/日度趋势图或时间结论，只允许显示阻塞原因、冲突样本、诊断 SQL 与解锁条件。
- Presentation QA：逐图检查 candidate competition、unit contract、single conclusion；逐区块执行 Deletion Gate；检查 Layout Archetype 未混用。
- Artifact Presentation QA：扫描最终可见正文，候选竞争、淘汰理由、Layout Archetype、Renderer 策略、Information Budget 等内部 rationale 不得泄露；除非用户明确要求设计说明。
- Result Freshness QA：若用户要求重跑/当前/最新，关键业务 Result 必须带本轮执行证据；历史 Result 只能作为 `REUSED_VERIFIED_RESULT`。
- Render QA Placement：本地浏览器失败后，检查是否存在已授权且无需新增持久化写入的远程浏览器 runner；未检查合法远程 placement 时不得直接标 `RENDER_QA_BLOCKED`。
- Async Render Readiness：Artifact 声明 `sqlbt-render-readiness=required` 时，桌面与手机都必须记录 READY marker；超时为 `ASYNC_NOT_READY`，不得用固定 sleep 代替。
- Canonical Remote Render Runner：若使用远程 QA，优先检查 `.github/workflows/sql-business-thinking-render-qa.yml`；payload 必须由 `tests/prepare-render-qa-payload.py` 基于最终 HTML bytes 生成，`render-qa.json.artifact_sha256` 必须等于本轮 `expected_sha256`。
- Chat connector trigger：若当前 GitHub connector 无 `workflow_dispatch`，检查 helper 是否生成 `issue_envelope`；只有用户已授权远程发送当前 HTML 时，才能创建一次性 `[sqlbt-render-qa]` Issue。workflow 读取后必须擦除正文并关闭 Issue；不得把 payload 提交进 Git 历史。
- Remote payload size：超过 helper 的 60,000 字符 inline 上限时必须返回 `REMOTE_RENDER_PAYLOAD_TOO_LARGE` 或切换其他已授权 transport；禁止截断后继续验收。
- HTML 实体文件交付：默认路径存在、文件非空、最终回复链接与实际文件一致（如适用）。

正确内容若发生无授权变化，视为回归，立即修复或回退。

## 5. Skills 反向审计

记录：

| 暴露缺陷 | 根因 | 修正建议 | 可泛化规则 | 当前报告验证 |
|---|---|---|---|---|

发现可泛化缺陷时必须形成具体 Skill 修正和回归样本。只有当前任务已明确授权修改 Skill / 仓库时才执行回写与提交；纯测试、审计或“本轮只测试”任务禁止自动写仓库。

## 6. 停止条件

只有同时满足才停止：

- 无 P0/P1；
- P2 剩余项不值得继续改；
- 关键答案覆盖完整；
- 运行时/交互无明显阻断；
- 桌面/移动端 Rendered QA 已 PASS；若本地失败，已继续检查所有合法 Render QA placement；只有全部失败后才能记 `RENDER_QA_BLOCKED`。若最终仍为 BLOCKED，只能在用户允许阶段性交付时停止，并必须显式披露，不能宣称完整验收；
- Skills 缺陷已形成可执行修正；若本轮授权写仓库，则已回写并反向验证；
- 不再存在 Lucy 陪练化、预写 checklist、低价值问题推进或“只报数字不解释”的浅分析；
- 继续修改只会变成纯审美偏好。

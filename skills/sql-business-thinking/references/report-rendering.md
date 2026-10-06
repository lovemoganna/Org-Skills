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

| 问题 | 默认形式 |
|---|---|
| 每用户金额 + 构成 | 排名表 + 水平堆叠条 |
| 集中度 | 贡献占比 + 累计占比 |
| 总体两类构成 | 100% 堆叠条 |
| 用户重叠 | 小样本数字集合关系 |
| 时间变化 | 折线 |
| 数据质量 | 审计表 |

图表必须回答问题，不做装饰。标题写问题，不写“Chart 1”。

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

## 10. ReportSpec

```json
{
  "meta": {},
  "question": "",
  "answers": {},
  "answer_blocks": [],
  "findings": [],
  "visuals": [],
  "quality_issues": [],
  "limitations": [],
  "decision_log": [],
  "learning_replay": [],
  "next_question": {},
  "skill_evaluation": {},
  "appendix": {}
}
```

Renderer 只读，不重新分析。

## 11. DuckDB-Wasm Runtime Contract

- **Browser Execution Harness：**当 HTML / Browser 是正式交付物且 Native DuckDB 不可用时，DuckDB-Wasm 是正式执行路径，不是展示性 fallback；不得因此直接产出 `BLOCKED_ENV` 报告。
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

不能只看源码。至少做：

1. DOM 结构检查：关键区块非空、ID 唯一、按钮映射完整；
2. 桌面渲染烟测：首屏、核心图表、数据质量、Skills 评估；
3. 移动端检查：无整页横向溢出；表格可局部滚动；必须实际断言 `document.documentElement.scrollWidth <= document.documentElement.clientWidth`（允许 1px 取整误差）；若失败，先定位最大溢出元素，不得只缩字号；
4. 功能检查：JS 语法、SQL 按钮映射、fallback、错误显示；
5. 内容检查：每个问题有 Answer Block；关键数字一致；限制没有被视觉弱化；显式要求的人物会话正文可见。
6. Dialogue QA（如适用）：Conversation Arc 完整；本轮绑定的 Analysis Lead / Critical Analyst 职责正确；Lucy 不得退化成陪练；每句通过 Turn Delta Gate；没有提前知道未验证结果；最终 synthesis / report-back 可反向追溯；台词不含内部流程标签。普通模式会话不被 SQL/Skill Trace 打断；Code-in-Conversation 模式必须验证“问题质量挑战 → SQL → Result → Frontier 更新”的邻接顺序。
7. Progressive Order QA（Code-in-Conversation）：最终 KPI 未在证据之前出现；没有跨阶段滚动摘要；每个具体数字第一次出现之前能找到对应 result 节点；正文没有第二套 SQL 副本。
8. Question Quality QA：每个进入 SQL 的问题都有 Trigger / Consequence / Answerability / Priority；至少检查是否存在“无论结果如何下一步都一样”的废问题；下一问必须能由上一轮 Frontier 更新解释，禁止预先排好的 checklist 式推进。
9. Hypothesis Depth QA：主要发现存在 H1 + 至少一个竞争解释；Lucy 至少一次攻击解释本身；存在能区分解释的 Diagnostic Test；关键结论做过有意义的 Robustness Check；最终 Insight 不能只是排名/比例复述。

**重要：源码中“有 Hero 节点”不等于 Hero 渲染成功。必须检查渲染输出。**

## 14. Skills 评估展示

如果报告本身是 Skill 回归测试，页面末尾单独展示六项：

- Skill 选择；
- SQL 首次跑通率；
- 关键数字口径；
- 主动数据质量发现；
- 结论是否越界；
- 读者能否复述分析路径。

再追加：`缺陷 → 修正 → 可泛化规则`，但不要让 Skills 元信息抢业务正文。

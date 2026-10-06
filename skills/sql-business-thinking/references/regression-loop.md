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
- 时间一致性失败时，时间趋势是否被阻塞或降级；
- 粒度；
- 时间匹配；
- JOIN 基数；
- Top N；
- NULL；
- 口径命名。

### E. 生成机制

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
- 与上一版业务结论 diff。
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
- 桌面/移动端 Rendered QA 已 PASS；若为 BLOCKED，只能在用户允许阶段性交付时停止，并必须显式披露，不能宣称完整验收；
- Skills 缺陷已形成可执行修正；若本轮授权写仓库，则已回写并反向验证；
- 不再存在 Lucy 陪练化、预写 checklist、低价值问题推进或“只报数字不解释”的浅分析；
- 继续修改只会变成纯审美偏好。

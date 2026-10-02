# 协议细则

本文件负责判级别、暂停、账本、代码增长、复盘、变式题和启发式追问。

## 1. 路由边界

判级别依次问：

1. 答错会改变结果含义吗？会 → 3 或 4。
2. 能一步退回吗？不能 → 至少 2。
3. 写得出依据吗？写不出 → 3。

典型：

| 情况 | 级别 |
|---|---|
| 别名、缩进 | 0 |
| 方言函数等价写法 | 1 |
| 时间边界、NULL 处理 | 2 |
| 业务目的、粒度、主表范围、日期归属字段 | 3 |
| 字段不存在、口径冲突、粒度数据撑不住 | 4 |
| exact-date 失败后是否允许 snapshot / as-of | 3 |

Direct 下级别 3 给不超过 3 个选项，不推荐。

## 2. 用户回复

`ok`、`否`、`A`、`1ok 2改:xx`、`口径:词=定义`、`原则:xx`、`授权:范围`、`回到第N关`、`展开`、`直接写`。

## 3. 暂停

级别 4 用三四句话写：卡在哪、为什么、用户要做什么、不解决会怎样。不要硬写 SQL。

## 4. 口径库

```text
口径#N: [词 = 定义] | 类型 | 来源 | 题#K | 作用域 | 状态
```

只有用户能新增正式口径。冲突就暂停，不替用户选。

## 5. 错误台账

```text
类型 | 次数 | 最近一次的信号 | 当前加严程度
```

类型扩展为：业务理解 / 结果设计 / 粒度 / 找表 / 字段 / 条件 / JOIN / 聚合 / 时间匹配 / 语法 / 结论解释 / 报告覆盖。

同类出现两次，下一题对应关卡前强制追问。

## 6. 代码逐段长出来

每过一关补一段，没做的位置留 `___`。每段注释对应业务逻辑。用户先说业务话，我再翻成 SQL。

关键 JOIN 在亮出 `SUM` 前必须先通过 cardinality gate。

## 7. Direct 交付

顺序：SQL → 四句读法 → 口径说明 → 我替你定了 → UNKNOWN。

多问题任务额外加：

```text
Answer Coverage:
- 问题 A → 结果块 A
- 问题 B → 结果块 B
```

## 8. 复盘

```text
做对：
开始跑偏：
错误类型：
正确路径：
下次信号：
一句话规则：
```

时间维表错、JOIN 放大、报告漏答都必须进台账。

## 9. 变式题

每次只改一个变量：粒度、JOIN 保留范围、业务口径、条件/输出、聚合、找表、WHERE/ON、终态/成功、时间维表。

时间维表变式：给一张多日期价格表，看用户会不会只按 asset JOIN；再看是否主动检查右表键唯一和交易时点匹配。

## 10. Top N 路由

Top N 不是固定默认值。由 active population 决定：

```text
≤10 → Top1 / Top3
11-99 → Top5 / Top10
≥100 → Top10，可加 Top1%
```

如果 Top N = 全部样本，核心结论必须换成更有区分度的指标。

## 11. 用户没想清目的：启发梯子

动作 → 分叉 → 对象 → 反例 → 最多 3 个地图候选。

最多连续问三轮；“不知道/随便”直接候选。目的句仍由用户自己填。

## 12. 高风险结构门槛

### 12.1 时间维表

看到这些字段/表名立即触发：`effective_date`、`valid_from`、`price`、`rate`、`version`、`history`。

先问：业务值应该对应交易的哪个时间点？

### 12.2 JOIN

金额、笔数、比例聚合前：

- 右表键唯一；
- JOIN 前后行数；
- 目标粒度不变；
- 一对多是业务本意。

未通过，不进入 SUM。

### 12.3 报告覆盖

多问题任务分析完成后逐条检查：

```text
用户问了什么？
正文哪里直接回答？
数字/图表是否真的支持？
附录是否承担了不该承担的主答案？
```

任何主问题没有正文答案，报告不准交付。

## 13. 角色会话协议

用户明确要求模拟人物会话，或 Autopilot 输出 Question-Driven Dialogue HTML 时，读取 `dialogue-rendering.md`。

角色名字必须继承 `dialogue-rendering.md` 的 Role Binding Gate；未指定时才使用默认 `Star/Lucy`。下面的名字仅代表默认角色。

- **没有显式 Task Owner 时不创造领导。**默认从数据集进入 Analysis Map / Question Frontier。
- Star / Analysis Lead：维护分析方向，每轮提出一个当前最值得回答的问题，并说清 Trigger / Consequence；主要 Result 后必须提出或更新解释模型。
- Lucy / Critical Analyst：独立判断这个问题值不值得现在问；可以 accept+sharpen / reject / replace / split，也可以提出 counter-hypothesis / falsify / decompose / stress-test，不以“帮 Star 完成任务”为职责。
- Question Quality Gate 未通过前禁止写 SQL。
- 主要发现必须建立 Hypothesis Frontier：主解释、竞争解释、可反驳证据、Diagnostic Test、当前状态。
- 主要结论必须通过 Analysis Depth Gate：What / Where / Why / Alternative / Test / Robustness / So What。
- 每句台词必须新增事实、判断、关键问题或决策；无信息确认句删除或合并。
- 人物只能使用当前阶段已经出现的事实；禁止把最终答案倒灌到前文。
- Result 必须改变 Question Frontier 或 Hypothesis Frontier；不能改变 Frontier 的查询，除必要最终取数外默认删除。
- “关卡通过”“调用 Skill”“按协议”不属于人物台词，只能作为 UI/审计元数据。
- 最终 Star synthesis 的每个关键结论必须能回指前序证据；只有显式 Task Owner 存在时才称 report-back。
- 正文已有完整权威会话时，不另存一个旧版人物全文；SQL 验证与 Skill Trace 独立保存。


## 14. Autopilot 路由

当 `SKILL.md` 的 Dataset-to-Report Autopilot 被触发时，本节覆盖“Direct 下 Level 3 必须给用户选项”的默认做法，但不覆盖 Level 4 暂停。

规则：

- 用户已明确把分析选择权交给 Skill 时，业务问题、结果粒度、主表范围等 Level 3 项可由 Skill 基于实际数据选择，但必须在报告中标为“分析选择 / 假设”，不得伪装成业务正式口径；
- 先建立 Analysis Map，再维护 Question Frontier；主要 Pattern 出现后再建立 Hypothesis Frontier；不要预先写死“状态 → 汇率 → JOIN → 金额 → TopN → 重叠”之类 checklist。
- 每个当前问题都必须通过 Question Quality Gate：Trigger / Consequence / Answerability / Priority；
- 每个主要结论都必须通过 Analysis Depth Gate：What / Where / Why / Alternative / Test / Robustness / So What；
- 优先处理阻塞后续可信度、能区分竞争解释或会改变结论的问题，不以“覆盖更多表 / 更多字段”为高价值标准；
- Lucy 有权否决或替换 Star 的问题；被 reject 的问题不得继续产生 SQL；
- 不允许为了“自动化”猜字段、猜业务词义、猜成功定义；
- 时间维表如果 exact-date 不成立、无 as-of 规则，但只有一个无歧义 snapshot，可继续做探索性 snapshot 估值；结果名必须带日期或“快照估值”，并明确不能解释为历史成交价值；
- 出现多个候选 snapshot、连接键歧义、字段缺失或定义冲突时，升到 Level 4 暂停；
- 每个 Result 必须更新 Question Frontier 或 Hypothesis Frontier；不能改变问题优先级、假设状态或最终解释的查询，除必要最终取数外默认删掉；
- 关键结论至少做一次有意义的 Robustness Check；数据不支持时明确写无法验证，不得伪造稳健性；
- 完整报告完成后必须执行 Reverse Skill Audit Gate，不能把本轮额外提示继续留在调用层。

# 人物会话与教学回放协议 V8

用于用户明确要求人物会话、学习者 / 分析师、领导下任务后的讨论推演、师生、角色模拟或从头推演的任务。

核心原则：**人物会话不是把结果拆成对白，也不是 Star 做任务、Lucy 帮忙查漏；它要呈现“数据如何不断产生更好的问题，问题如何经过挑战后进入 SQL，再由证据改变下一问”。**

## 0. Role Contract Gate

角色名字与角色语义都必须服从当前请求：

1. 用户显式给出人物名时原样使用；未指定名字时才回退到默认 `Star/Lucy`。
2. 用户显式给出能力水平、职责、知识边界或互动方式时，这些定义覆盖默认角色职责。
3. 默认 `Star = Analysis Lead`、`Lucy = Critical Analyst` 只在对应角色语义未被用户定义时生效。
4. 同名不代表默认职责。例如用户明确写 `Star = 数据分析小白`，不得因为名字仍叫 Star 就要求其主动提出专家级解释模型。
5. 用户定义为学习者 / 小白时，其进步应表现为“提出真实问题 → 根据证据修正理解 → 能复述当前判断”，不得突然拥有尚未获得的专业知识。
6. 用户定义为资深分析师 / 教练时，应通过追问、反例、边界和必要解释推进；除非用户要求，不得一口气替学习者完成全部分析。
7. Renderer、测试和回归必须读取本轮完整 Role Contract，而不是只检查名字。
8. Role Contract 可以改变角色分工，但不能绕过 Question Quality、Result Dependency、Evidence Traceability 和结论边界。

---

## 1. Conversation Arc Contract

### 默认：Dataset-Driven Arc

用户只提供数据集 / 表，没有显式 Task Owner 时，**禁止虚构领导任务**。正文形成：

```text
Dataset Intake
→ 业务语义还原
→ 本体原子知识库
→ 本体识别规则库
→ 高质量指标
→ 问题边界
→ Star 提出当前最值得回答的问题
→ Lucy 挑战问题质量 / 提出替代问题
→ Question Quality Gate
→ SQL / Result
→ Frontier Update
→ 下一问题
→ ...
→ Synthesis
→ Final SQL Analysis Report
```

不可缺：

1. **数据起点**：当前能看到什么数据与约束；
2. **本体前置**：陌生多表数据或完整自主分析先完成本体原子知识库和本体识别规则库；简单单题可跳过；
3. **问题选择**：Star 为什么现在问这个，答案会改变什么；
4. **问题挑战**：Lucy 必须从问题价值、可回答性或优先级上独立判断，而不是只补 SQL；
5. **证据形成**：通过 Gate 的问题才进入 SQL / Result；
6. **问题边界更新**：Result 改变下一问；
7. **分析终点**：Star 综合成 SQL 分析报告。

### 显式任务：Task-Driven Arc

只有用户真的给出领导 / Task Owner / 明确任务发起人时，才在上面外层增加：

```text
Assignment → Dataset-Driven Arc → Report-back
```

禁止为了“有故事感”默认创造领导，也禁止把 Lucy 写成帮助 Star 完成领导任务的陪练。

---

## 2. 角色职责

### 领导 / Task Owner

只负责：

- 下达要解决的问题；
- 给出需要的判断或动作；
- 必要时规定交付边界。

不要让领导参与 SQL 细节，也不要把领导写成旁白。

### 默认角色职责

只有用户没有定义角色职责时，使用：

**Star / Analysis Lead**

- 维护 Analysis Map / Question Frontier；
- 每轮提出一个当前最值得回答的问题；
- Result 后更新判断、解释和优先级；
- 最终完成 synthesis。

**Lucy / Critical Analyst**

- 挑战问题价值、可回答性与优先级；
- 提出竞争解释、反证、替代路径或稳健性测试；
- 必要时质疑 SQL 边界；
- 不提前知道结果，不为制造分歧强行反驳。

如果当前 Role Contract 把 Star 定义为学习者、小白或其他非专家角色，上述 Analysis Lead 职责不得强制套用；应保持其能力连续性，由本轮指定的专家角色承担对应专业推进。

---

## 2A. Question Frontier

人物会话的真正共享状态是 Question Frontier：

```text
Confirmed  已确认事实
Unknowns   会改变判断但尚未确认的未知
Candidates 可消除 Unknown 的候选问题
Current    当前唯一问题
```

Frontier 内部持续更新，但正文禁止每轮完整复述它。页面只需要让读者看懂：

```text
为什么现在问这个
→ Lucy 是否同意这个优先级
→ 查询结果改变了什么
→ 所以下一问为什么变了
```

## 2B. Question Quality Gate

Star 的问题在出现 SQL 前必须通过：

1. **Trigger**：由哪个已有事实、上一轮 Result 或阻塞触发？
2. **Consequence**：可能结果分别会改变什么判断 / 口径 / 路径？
3. **Answerability**：现有数据真的能回答吗？
4. **Priority**：为什么它比其他 Unknown 更值得先查？

Lucy 至少执行一种动作：

- **accept + sharpen**：问题值得，但需要收紧边界；
- **reject**：问题无论答案如何都不改变下一步，直接淘汰；
- **replace**：提出更高优先级的问题，并说明它会改变什么；
- **split**：问题一次问了两件事，拆成一个当前问题。

**禁止：**Lucy 只是说“对，再补一个字段 / 再查一下 / 我同意”。如果 Lucy 的作用只剩补 SQL，她已经退化成陪练。

## 2C. Question Consequence Gate

Result 后必须能完成至少一种 Frontier 变化：

- 关闭一个 Unknown；
- 新增一个真正会改变方向的 Unknown；
- 改变候选问题优先级；
- 终止一条分析路径；
- 或完成最终答案所需的必要取数。

如果 Result 出来后“下一步还是原计划，判断也完全不变”，这条查询默认删除，除非它是最终结果本身。

### 分析信号与本体局部展开

Result 出现有意义差异时先记为分析信号。下一问不得重新扫描全部字段，只能沿当前分析信号涉及对象的合法本体关系展开。每增加一个维度，必须说明为什么它可能改变当前判断。复杂问题必须由已经验证的原子问题或分析信号逐步生长。

## 2D. Hypothesis Frontier

主要现象出现后，人物会话必须从“问什么”升级到“怎么解释”：

```text
Observed Pattern
→ Star: H1
→ Lucy: H2 / 反证
→ Diagnostic Question
→ SQL / Result
→ H1 / H2 状态变化
→ Robustness Check
→ Insight
```

最低要求：

- 至少一个主解释 + 一个合理竞争解释；
- Star 必须说明什么证据会让自己改口；
- Lucy 必须至少一次真正攻击解释，而不是只攻击 SQL；
- 如果现有数据不能区分解释，双方都必须保留 unresolved，禁止强行收敛。

### Hypothesis Challenge 动作

Lucy 可执行：

- **counter-hypothesis**：提出能解释同一现象的另一机制；
- **falsify**：指出什么结果会直接削弱 H1；
- **decompose**：把表面指标拆成可诊断组成，例如“金额 = 笔数 × 单笔金额”；
- **stress-test**：去极端值 / 换分母 / 换合理口径；
- **boundary**：指出数据只能支持描述，不能支持因果或风险判断。

## 2E. Analysis Depth Gate

主要发现如果只停在以下形式，判浅分析：

- “A 最大”；
- “Top3 = 83.48%”；
- “两类用户重叠 88.89%”；
- “某用户 crypto 占比高”。

进入最终结论前至少回答：

```text
What → Where → Why → Alternative → Test → Robustness → So What
```

不是要求每层都增加 SQL，而是要求每个主要结论都有**解释深度和证据闭环**。

## 3. Turn Delta Gate

每一句人物台词必须至少产生一种增量：

```text
FACT      新事实
JUDGMENT  新判断 / 修正判断
QUESTION  会改变下一步的关键问题
DECISION  新口径 / 新动作 / 新边界
```

如果一句话只是：

- “对。”
- “明白。”
- “好的。”
- 重复上一句已经说过的数字；
- 把最终结论换个说法再说一次；

就删除或并入前后句。

人物不是为了“看起来有对话”而说话。

---

## 4. Progressive Knowledge Gate

人物只能知道当前阶段已经出现的事实。

例如：

- 没跑用户汇总前，不得提前说 Top 3 = 83.48%；
- 没检查 `effective_date` 前，不得提前把结果叫“快照估值”；
- 没检查交集 / 并集前，不得提前说重叠率；
- 没核数据质量前，不得提前说有哪一条异常记录。

如果最终结论在对话开头就已经完整出现，会话判失败。

---

## 5. 分歧与修正

分歧必须来自真实分析风险，不为制造戏剧强行反驳。

高价值分歧通常包括：

- 不同币种是否能直接相加；
- 交易行数是否等于用户数；
- 时间维表是否能按业务时间点匹配；
- JOIN 是否放大；
- Top N 是否有区分度；
- 百分比分母是否正确；
- 均值是否能代表典型用户；
- 数据异常能否自行修值；
- 描述性集中是否能外推成风险。

至少一次要体现：**Star 的原判断 → Lucy 提出证据问题 → 新事实出现 → Star 自己改判断。**

---

## 6. 阶段组织

一段工作讨论只解决一个状态变化。推荐每阶段 2～4 个来回，默认不超过 4 个。

每阶段结构：

```text
当前 Unknown / 为什么现在必须处理
→ Star 提出当前问题 + Consequence
→ Lucy accept / reject / replace / split
→ Question Quality Gate 通过
→ SQL / Result
→ Star 说明 Frontier 如何变化
→ 下一问题
```

如果 Lucy reject / replace，**被淘汰的问题不得继续写 SQL**。

正文可以在阶段末尾显示一条非角色元信息：

```text
当前决策：...
新增事实：...
口径修正：...
```

它只能总结这一阶段真正发生的状态变化，不能写 Skill 调用。

---

## 6A. Code-in-Conversation Contract

当用户明确要求“代码必须产生在 Star / Lucy 会话过程中”时，人物会话与代码不再是两条信息通道，而是一条因果链：

```text
当前问题
→ Star 提出判断 / 查询意图
→ Lucy 先挑战问题质量；通过后才补充、质疑或收紧 SQL 边界
→ 生成只解决当前问题的 SQL
→ 记录/实时结果
→ Star 基于结果更新判断
→ Lucy 验证边界（如必要）
→ 下一问题
```

硬规则：

1. **SQL 前必须先过 Question Quality Gate。**代码出现前，Star 已说清“为什么现在问、不同结果会改变什么”，Lucy 已完成 accept / reject / replace / split；只有通过的问题才进入 SQL。
2. **Result 后必须有状态变化。**结果出现后，至少有一句人物台词把新证据转成 FACT / JUDGMENT / DECISION；否则这段 SQL 是脱离叙事的日志。
3. **一段 SQL 只解决当前问题。**禁止为了省事把后面几个阶段的计算一次写进来。
4. **不事后补代码。**如果人物已经说出结论，再在页面后面集中放 SQL，判失败。
5. **Single Code Source。**正文原位 SQL 就是唯一权威代码实例；不得在附录复制第二套可执行 SQL。
6. **Result Dependency。**具体数字、比例、异常行第一次进入对白前，必须已经有对应 result 节点。

### Code Growth Gate

`Code-in-Conversation` 只解决“代码放在哪里”，还不够保证“代码是怎么产生的”。用户明确要求代码循序渐进产生时，必须再满足：

```text
Star 提出最小查询意图
→ 代码草稿 A（最小骨架/局部条件）
→ Lucy 指出一个真实缺口
→ 代码草稿 B（只补这个缺口）
→ Star 确认当前查询边界
→ 唯一可执行 SQL
→ Result
→ Star/Lucy 基于 Result 改判断
```

硬规则：

1. **至少一次可见代码增量。** `对白 → 完整 SQL` 不算“逐步产生”。
2. **草稿不是第二套 SQL。**草稿只展示新增片段、骨架或 diff，标明“草稿 / 不单独执行”；最终每个问题仍只有一个可执行 `<pre>`。
3. **增量必须来自对白。**代码变化必须能指出是哪一句质疑/决定触发的，禁止为了演示而机械拆行。
4. **每次只补一种逻辑。**例如先补 `WHERE status='completed'`，再补时间 JOIN；不要一轮同时加入过滤、JOIN、聚合、排序。
5. **Result 前不允许解释 Result。**可以解释预期用途，不能预告数字。

### One Step One Query

当前推进点的最小单元是：

```text
一个问题 + 一段代码生长 + 一个最终可执行 SQL + 一个 Result + 一个判断变化
```

如果一个阶段里出现两个独立 SQL，读者会失去“现在到底在判断什么”的定位。第二个查询必须另起推进点。

### Human State Transition

人物会话模式里，Result 之后不要再插入：

- “这一步确认：……”
- “暂时不能推出：……”
- “截至目前我们知道：……”
- 累计事实清单。

这些内容如果重要，必须由 Star/Lucy 用自然工作语言表达，并且只表达**刚刚变化的那一个状态**。

### Evidence Adjacency

产生判断的证据必须紧邻判断。正文不得让读者在会话与独立 SQL 附录之间来回跳。

推荐：

```text
Star：我先确认汇率有没有覆盖交易日。
Lucy：资产覆盖和时间覆盖分开查。
[SQL：只查资产与 effective_date 覆盖]
[Result]
Star：资产覆盖没问题，但只有一个 effective_date。继续查交易日精确匹配。
```

禁止：

```text
人物连续讨论 8 个结论
↓
页面最后统一放 10 个 SQL
```

### No Rolling Summary

推进过程中不要维护“截至目前的全部结论”“当前已知 6 条事实”这类滚动摘要。它会让读者把注意力从当前问题移到全局状态。

允许：
- 当前一步的局部判断；
- 下一步要验证的问题；
- 最终 synthesis；若显式存在 Task Owner，则为 report-back。

禁止：
- 首屏提前展示最终 KPI；
- 每阶段重复累计全部已知事实；
- 在对应 SQL 之前剧透后续数字。

## 7. 反问预算

分三级：

1. 目标 / 口径不明：只问一个带选项的问题；
2. 有合理默认：说明默认值后直接推进；
3. 事实 / 术语：直接回答。

每阶段最多反问 2 次。连续两轮反问后必须推进到：

- SQL；
- 数据检查；
- 或阶段结论。

禁止把人物讨论写成访谈问卷。

---

## 8. Synthesis / Report-back Traceability Gate

最终必须由 Star 完成 synthesis；只有显式存在 Task Owner 时，才向任务发起人 report-back。Lucy 不替 Star 下最终综合结论。

最终 synthesis / report-back 至少分：

```text
结果
判断
限制 / 待跟进
```

每个关键结论都必须能回指前序某个证据节点：

| 最终结论 | 前序必须出现的依据 |
|---|---|
| 总交易额 | 金额口径 + 汇率口径 + 用户聚合 |
| Top N 贡献 | 排序 + population + Top N 选择理由 |
| 用户重叠 | 两类集合 + 交集 + 并集分母 |
| 数据质量限制 | 对应质检事实 |
| 不能外推的判断 | 明确的结论边界 |

如果最终 synthesis / report-back 出现前面从未讨论 / 验证过的新数字、新口径或新判断，判失败。

---

## 9. 信息通道

最终 Artifact 分开：

1. **人物会话**：任务与判断如何形成；
2. **代码生长与验证**：在 Code-in-Conversation 模式中原位嵌入人物会话，不再单独建验证台；普通模式才可放验证台。
3. **Skill Trace**：内部调用哪个 Skill、为什么。

人物台词不得出现：

```text
调用 Skill
关卡通过
按协议
根据路由
进入第 N 关
```

如果正文已经完整展示权威人物会话，不再在附录保留另一个旧版人物全文；避免出现“双重真相”。

---

## 10. 视觉规则

- Star 左，Lucy 右；领导任务使用独立 brief，不伪装成聊天气泡；
- 气泡最大宽度 70%～72%，移动端 85%～86%；
- 会话是连续工作线程，不是大量彩色卡片；
- 每个阶段有明确标题，但不写“盲点 1 / 错误 2”羞辱式标签；
- 阶段结论只用一条小型决策行；
- 最终 Star 汇报使用独立 Report-back 块，并可提供证据锚点；
- 默认角色回放可把 SQL 与 Skill Trace 分离；但进入 Code-in-Conversation 模式后，SQL + Result 必须原位插入人物回合之间，Skill Trace 仍然分离。

---

## 11. Dialogue QA

交付前逐项检查：

### Arc
- 是否从任务发起开始？
- 是否由 Star 最终汇报结束？
- 中间阶段是否真的继承前一步状态？

### Role Balance
- Star 是否真的在选择分析方向和当前问题，而不只是顺着固定 checklist 执行？
- Lucy 是否挑战“问题是否值得问”，而不是只帮 Star 补 SQL / 查漏？
- Lucy 是否至少有一次真实 accept+sharpen / reject / replace / split；但没有为了戏剧性强行反驳？
- 去掉姓名后，是否仍能看出 Star = Analysis Lead、Lucy = Critical Analyst？

### Question Quality
- 每个 SQL 前的问题是否能说清 Trigger / Consequence / Answerability / Priority？
- 是否存在“查了也不会改变下一步”的低价值问题？
- 是否有字段清单式、为了完整而查的机械问题？
- Result 是否真的改变 Question Frontier？
- 下一问是否由上一轮证据触发，而不是预先排好的 checklist？

### Hypothesis / Depth
- 主要 Pattern 后是否建立主解释 + 竞争解释，而不是直接跳到下一个描述问题？
- Star 是否至少一次明确“什么证据会让我改口”？
- Lucy 是否挑战过解释本身，而不只是 SQL / 问题优先级？
- 是否有 diagnostic test 真正区分竞争解释？
- 关键结论是否至少做一次有意义的 robustness check？
- 去掉人物姓名后，对话是否仍体现“提出解释 → 反驳解释 → 证据区分 → 更新判断”，而不是 SQL 开发讨论？
- 最终主要发现是否通过 What / Where / Why / Alternative / Test / Robustness / So What？

### Turn Delta
- 每句是否新增 FACT / JUDGMENT / QUESTION / DECISION？
- 是否存在无效“对 / 好 / 明白”回合？
- 是否有重复最终数字的假对白？

### Knowledge State
- 有没有人物提前知道尚未验证的数字或异常？
- 判断是否随着证据逐步更新？

### Code / Evidence（Code-in-Conversation 模式）
- 每个 SQL 前是否已有明确查询动机？
- 每个 SQL 后是否由人物使用结果推进判断？
- 是否存在“人物先知道数字、SQL 后补”的倒序？
- 同一个 SQL 是否只保留一个可执行实例？
- 是否把 SQL 复制到独立附录形成第二套事实顺序？
- 是否存在跨阶段滚动汇总干扰当前推进点？

### Traceability
- 最终 Star 汇报的每个结论是否能回指前面的事实？
- 最终汇报有没有突然出现的新数字 / 新口径？

### Presentation
- 人物会话是否正文可见？
- SQL / Skill Trace 是否和人物对白分离？
- 桌面 / 移动端是否仍能清楚区分角色？

任一失败，人物会话不算完成。

### Code Growth
- 每个推进点是否只有一个当前问题和一个最终可执行 SQL？
- 是否至少有一次由对白触发的可见代码增量？
- 草稿是否明确不是可执行权威版本？
- 是否存在“完整 SQL 突然蹦出来、对白只负责解释”的假渐进？
- Result 后是否由人物自己完成判断变化，而不是旁白摘要？
- 是否删除所有跨阶段滚动汇总？

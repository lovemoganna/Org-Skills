# Hypothesis-driven Investigation Loop

目标：把“发现一个现象”升级为“解释一个现象”。任何重要发现都不能第一次出现就直接进入核心看板。

## 1. Candidate Triage Gate

不要对所有 Pattern 平均用力。先把候选发现按“是否值得深挖”分层。

判断至少包含：

- **Goal Alignment**：用户是否明确要求调查该问题；显式目标优先于默认全局排序；
- **Decision Dependency**：它是否阻塞口径、可信度或后续判断；
- **Materiality**：影响金额、对象覆盖、频率、流程影响或控制严重性有多大；
- **Evidence Strength**：样本量、口径、稳健性和可验证程度；
- **Actionability**：结果是否能改变下钻、监控、修复或决策；
- **Novelty / Non-redundancy**：是否提供新信息，还是已有 Finding 的重复切片。

Materiality 不是只看金额。少量记录如果会使核心趋势、指标或控制判断失效，可以直接提升优先级。

如果用户已明确指定分析目标、对象或问题，Candidate Triage 必须在该目标内部排序；不得用“全局影响更大”为理由跳过用户明确要求。只有用户没有明确目标时，才使用默认全局价值排序。

默认分层：

- **P0 / Blocking**：不解决就不能可信分析；
- **P1 / Primary**：高影响且证据足，值得进入深度调查；
- **P2 / Secondary Lead**：有趣或局部异常，但影响窄、证据弱或尚不改变主要判断；
- **P3 / Context**：仅作背景。

只有 P0/P1 默认进入完整 Hypothesis Investigation。P2 先保留为线索，除非后续证据把它升级。禁止因为“唯一、极端、看起来异常”就自动放进首屏。

## 2. Question Frontier

每次结果出来后，维护一个内部问题前沿：

- 已确认事实；
- 仍未知且会改变判断的事项；
- 候选下一问；
- 当前唯一最值得回答的问题。

下一问必须由当前 Result 触发，不得按固定 checklist 机械推进。

## 3. Question Quality Gate

候选问题只有同时满足以下条件才允许继续：

- **Trigger**：为什么现在问？必须由当前现象、数据结构或阻塞触发。
- **Consequence**：不同答案是否会改变解释、口径、下一步或看板内容？
- **Answerability**：当前字段、粒度和样本能否回答？
- **Priority**：是否比其他未知更值得先查？

如果答案无论是什么都不改变判断，这个问题淘汰。

## 4. Observed Pattern Gate

以下内容第一次出现时，只能叫 Pattern，不能直接叫 Insight：

- Top1 / TopN 很高；
- 某渠道成功率低；
- 某群体金额高；
- 某月突然上升；
- 某网络失败多；
- 某用户处理时延长；
- 两变量一起变化。

Pattern 只是“发生了什么”，不是“为什么”。

## 5. Hypothesis Frontier

每个候选核心发现至少建立：

| 字段 | 内容 |
|---|---|
| Observed Pattern | 需要解释的现象 |
| H1 | 当前主解释 |
| H2 | 合理竞争解释 |
| H3 | 可选的第三解释 |
| Disconfirming Evidence | 什么结果会削弱 H1 |
| Diagnostic Test | 最能区分 H1/H2 的查询或拆解 |
| Status | supported / weakened / rejected / unresolved |

数据不足时允许只有 H1/H2，但禁止只有单一故事。

## 6. Evidence Depth Gate

重要发现至少走一轮：

```text
What
→ Where
→ Why
→ Alternative
→ Test
→ Robustness
→ So What
```

常用拆解：

- 总额 → 频次 × 单笔金额；
- 高占比 → Top1 / Top2 / 去极值后重算；
- 成功率差异 → 分母 N + 时间 + 用户构成；
- 时延差异 → 分布 + 用户 + direction + 金额；
- 群体差异 → 去掉大户后重算 + 每用户标准化；
- 时间变化 → 量变还是结构变化；
- 相关关系 → 检查分层 / 极端值 / 时间共同驱动。

## 7. Robustness Check

每个进入核心看板的主要发现至少做一次稳健性检查。

可选方法：

- 去掉 Top1 / Top2 / 明显极端值；
- 更换合理分母；
- 从总量改成人均 / 每笔 / 每活跃对象；
- 拆成频次 × 单笔金额；
- 按关键维度分层后重算；
- 换合理时间窗口；
- 使用中位数替代均值；
- 检查结果是否由单一用户、单月、单渠道或单资产驱动。

如果无法验证，状态保持 `unresolved`，不得伪造稳健性。

## 8. Finding Promotion Gate

一个 Pattern 只有满足以下条件，才允许升级为核心 Finding：

1. 事实成立；
2. 口径可信；
3. 样本量和分母可见；
4. 不是明显的单点或聚合假象，或已明确说明它就是单点驱动；
5. 至少检查一个竞争解释；
6. 至少完成一次 Diagnostic Test 或 Robustness Check；
7. 结论措辞与证据强度一致；
8. 这个 Finding 会改变用户下一步判断、下钻或监控重点；
9. 已通过 Candidate Triage，确认其优先级足以进入核心看板。

未通过时：

- 可留在“探索 / 下钻”；
- 可标记 unresolved；
- 不得放进首屏核心发现。

## 9. Portfolio Synthesis Gate

Promoted Findings 不能直接平铺到首页。先做一次跨 Finding 综合：

1. **Merge**：共享同一驱动、同一批实体或同一证据链的 Finding 合并；
2. **Explain**：区分主结论、支持证据、竞争解释和 unresolved 部分；
3. **Contradiction Check**：不同 Finding 如互相冲突，必须解释口径、样本或分层差异；
4. **Priority Order**：按 P0/P1、影响面和证据强度排序，不按发现顺序排序；
5. **Executive Thesis**：默认压缩成 1–3 条真正改变判断的主结论；只有彼此独立且同等重要时才超过 3 条。

每条 Executive Thesis 至少包含：

```text
Claim
→ Why it matters
→ Evidence
→ Robustness / competing explanation
→ Limitation
→ Next action / drill-down
```

如果两个 Finding 本质上是同一个驱动的不同切片，拆成两张首屏卡片判失败。

## 10. Dashboard Promotion Contract

Dashboard 只消费四类内容：

- **Executive Thesis**：通过 Portfolio Synthesis 的主结论；
- **Promoted Finding**：支撑 Thesis 的已验证发现；
- **Context Metric**：必要背景数字，但明确不冒充洞察；
- **Open Question / Secondary Lead**：尚未晋级的 unresolved 或 P2 线索。

禁止把所有查询结果都画成图。首屏优先展示 Thesis，不是 Finding 数量。

## 11. Information Gain Stop Rule

继续追问，直到满足任一条件：

- 主要竞争解释已被区分；
- 新查询不再改变 Hypothesis 状态；
- 新拆解只产生重复描述；
- 数据粒度不足，无法继续；
- 继续分析只会增加细节，不改变结论或行动入口。

停止不是“查完所有维度”，而是边际信息增益明显下降。

## 12. 因果边界

除非存在实验、准实验或明确因果设计：

- 只能写“关联”“贡献”“由当前样本驱动”“与……同时出现”；
- 不得写“导致”“造成”“因为”。

## 13. 与 sql-business-thinking 的边界

两者共享 Question Frontier / Hypothesis Frontier / Robustness 的思想。

- `sql-business-thinking` 负责 SQL 推理与人物分析过程；
- `dataset-dashboard-builder` 负责无人值守的数据集调查、Finding 晋级和 Dashboard 内容选择。

不得为了同步机制修改另一个 Skill。

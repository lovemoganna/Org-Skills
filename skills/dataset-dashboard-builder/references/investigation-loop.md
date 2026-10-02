# Hypothesis-driven Investigation Loop

目标：把“发现一个现象”升级为“解释一个现象”。任何重要发现都不能第一次出现就直接进入核心看板。

## 1. Question Frontier

每次结果出来后，维护一个内部问题前沿：

- 已确认事实；
- 仍未知且会改变判断的事项；
- 候选下一问；
- 当前唯一最值得回答的问题。

下一问必须由当前 Result 触发，不得按固定 checklist 机械推进。

## 2. Question Quality Gate

候选问题只有同时满足以下条件才允许继续：

- **Trigger**：为什么现在问？必须由当前现象、数据结构或阻塞触发。
- **Consequence**：不同答案是否会改变解释、口径、下一步或看板内容？
- **Answerability**：当前字段、粒度和样本能否回答？
- **Priority**：是否比其他未知更值得先查？

如果答案无论是什么都不改变判断，这个问题淘汰。

## 3. Observed Pattern Gate

以下内容第一次出现时，只能叫 Pattern，不能直接叫 Insight：

- Top1 / TopN 很高；
- 某渠道成功率低；
- 某群体金额高；
- 某月突然上升；
- 某网络失败多；
- 某用户处理时延长；
- 两变量一起变化。

Pattern 只是“发生了什么”，不是“为什么”。

## 4. Hypothesis Frontier

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

## 5. Evidence Depth Gate

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

## 6. Robustness Check

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

## 7. Finding Promotion Gate

一个 Pattern 只有满足以下条件，才允许升级为核心 Finding：

1. 事实成立；
2. 口径可信；
3. 样本量和分母可见；
4. 不是明显的单点或聚合假象，或已明确说明它就是单点驱动；
5. 至少检查一个竞争解释；
6. 至少完成一次 Diagnostic Test 或 Robustness Check；
7. 结论措辞与证据强度一致；
8. 这个 Finding 会改变用户下一步判断、下钻或监控重点。

未通过时：

- 可留在“探索 / 下钻”；
- 可标记 unresolved；
- 不得放进首屏核心发现。

## 8. Dashboard Promotion Contract

Dashboard 只消费三类内容：

- **Promoted Finding**：通过 Finding Promotion Gate；
- **Context Metric**：必要背景数字，但明确不冒充洞察；
- **Open Question**：数据不足但值得继续追踪的 unresolved 问题。

禁止把所有查询结果都画成图。

## 9. Information Gain Stop Rule

继续追问，直到满足任一条件：

- 主要竞争解释已被区分；
- 新查询不再改变 Hypothesis 状态；
- 新拆解只产生重复描述；
- 数据粒度不足，无法继续；
- 继续分析只会增加细节，不改变结论或行动入口。

停止不是“查完所有维度”，而是边际信息增益明显下降。

## 10. 因果边界

除非存在实验、准实验或明确因果设计：

- 只能写“关联”“贡献”“由当前样本驱动”“与……同时出现”；
- 不得写“导致”“造成”“因为”。

## 11. 与 sql-business-thinking 的边界

两者共享 Question Frontier / Hypothesis Frontier / Robustness 的思想。

- `sql-business-thinking` 负责 SQL 推理与人物分析过程；
- `dataset-dashboard-builder` 负责无人值守的数据集调查、Finding 晋级和 Dashboard 内容选择。

不得为了同步机制修改另一个 Skill。

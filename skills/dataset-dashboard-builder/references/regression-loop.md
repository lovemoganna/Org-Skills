# Dashboard Regression Loop

## 1. 基线

先保存输入、指标口径和当前可运行 HTML。修正只针对已复现缺陷。

## 2. 缺陷分类

- P0：数字错误、口径错误、JOIN 放大、历史/快照混淆、核心功能不可用；
- P1：主问题漏答、关键限制隐藏、错误 TopN、移动端破版；
- P2：明显可读性问题；
- P3：纯审美，不主动修改。

## 3. 每轮闭环

```text
真实执行
→ 定位缺陷
→ 判断是否属于 Skill 规则缺失
→ 最小修正
→ 原失败样本复测
→ 泛化测试
→ 历史回归
→ Diff 检查
```

## 4. Rendered QA

至少检查：

1. 核心 KPI 与分析结果一致；
2. 关键限制与受影响指标相邻；
3. DOM 关键区块存在且非空；
4. JS 语法无错误；
5. ID 唯一；
6. 桌面/移动端无整页溢出；
7. 表格可局部滚动；
8. 无重复 KPI / 图表；
9. 每张图能回答明确业务问题；
10. HTML 离线打开时核心内容仍可读；
11. Question Map 与 Analysis Depth Gate 已执行；数据支持时不能只停留在总量 / TopN；
12. Visual Plan 与 Renderer Capability Gate 已执行；fallback 不得改变分析语义；
13. 主要 Pattern 已执行 Candidate Triage / Hypothesis Frontier / Robustness / Finding Promotion Gate；
14. Promoted Findings 已执行 Portfolio Synthesis，首屏不是发现列表的机械平铺；
15. Domain Detection / Dashboard Mission / Metric Role / Comparison / Information Architecture / Interaction / Quality Evaluation 已执行；
16. 若加载 Domain Pack，Domain Evaluation 已执行，且至少一个领域工作流真实改变 Dashboard 结构。

### 4A. 深度分析 QA

- 是否至少检查分布 / 分层；
- 数据支持时，是否继续检查时间、流程、关系、驱动或异常；
- 是否同时检查绝对量和标准化指标；
- 比率、成功率、时延等是否保留分母 / 样本 N；
- 是否把相关或同期变化误写成因果；
- 深挖结果是否真的改变判断，而不是重复切片。

### 4B. Investigation QA

- 是否先做 Candidate Triage，而不是对每个异常平均深挖；
- 用户有明确分析目标时，是否在该目标内部排序，而不是被默认全局 materiality 覆盖；
- 是否把“唯一 / 极端 / 稀有”误当成“高价值”；
- 是否综合考虑影响面、控制严重性、证据强度与行动价值；

- 核心发现第一次出现时是否只作为 Pattern，而不是直接写 Insight；
- 是否至少存在 H1/H2 两个竞争解释；
- 是否明确什么证据会削弱当前主解释；
- Diagnostic Test 是否真正区分解释，而不是继续加描述维度；
- 关键结论是否至少做一次 Robustness Check；
- 去掉极端值 / 换分母 / 分层后，结论措辞是否同步变化；
- 数据不足时是否保持 unresolved；
- 首屏核心 Finding 是否全部通过 Finding Promotion Gate；
- Context Metric 是否被误写成 Insight；
- 是否在信息增益下降后停止，而不是机械遍历所有字段。

### 4C. Portfolio Synthesis QA

- 是否把共享同一驱动/实体/证据的 Finding 合并；
- 是否存在重复首屏卡片，只是换了维度措辞；
- 是否解释 Finding 之间的冲突或表面矛盾；
- 是否按价值排序，而不是按发现顺序；
- 首页是否能压缩成少量 Executive Thesis；
- P2 Secondary Lead 是否错误抢占首屏；
- 单条小金额/小样本异常只有在控制或分析依赖严重时才可越级。

### 4D. Domain Intelligence QA

- Domain 是否由 Entity / Event-State / Dimension 或用户显式指定支持；
- low confidence 是否错误加载领域 Pack；
- Domain Pack 是否只提供候选问题而非固定模板；
- 是否至少有一个领域专属工作流改变最终结构；
- 不支持的领域字段 / 动作是否被补造；
- generic fallback 是否仍可正常执行。

### 4E. Dashboard Quality QA

- 页面是否首先像一个分析工具，而不是长篇分析报告；
- 默认视图是否无需操作就完成 Primary Job；
- Primary KPI / Finding 是否有可解释的比较语境；
- 核心比较是否同时可见，而非靠切换 Filter；
- Drill 是否保留触发上下文并落到正确记录 / tab；
- 是否明确 Dashboard Mission；
- 是否形成 `What → So What → Why → Who/Where → Evidence`；
- 第一屏是否同时给出状态、重点与下一步入口；
- 数据存在稳定对象键且任务需要定位/验证时，是否存在有效交互或下钻；
- 是否存在 KPI / Finding 卡片堆砌；
- 是否存在纯展示模块；
- Dashboard 是否把内部 Quality Evaluation / Hypothesis / Regression 过程暴露给最终用户；
- 是否通过 `eval/dashboard-quality.md`，Critical=0 且 Major=0；
- 是否仅修 Minor，而真正 Major 仍未解决。

### 4F. 可视化 QA

- 是否从分析问题选择图形，而不是从 Renderer 能画什么倒推；
- 分布、关系、矩阵、流程、贡献、流向等语义需要时是否正确路由；
- Renderer 不支持时是否按 Capability Gate 降级；
- 是否为了“图多”制造重复图；
- 图、KPI、表格与筛选是否使用同一口径和同一数据范围；
- 多序列图是否有可见图例或直接标签；
- scatter / bubble / line 直接标签是否发生重叠；若重叠是否已改用关键点标注、tooltip 或 repel。

## 5. 泛化测试

至少覆盖：

- 无时间维表的数据集；
- 多日期汇率/价格表；
- 小样本 active ≤ 10；
- 一对多 JOIN；
- 没有金额字段、只有事件计数的数据集；
- 完全不同字段名的数据集。

不得因为某个真实样本出现 `users / fiat / crypto / exchange_rates` 就把这些名字写成通用规则。

## 6. 停止条件

原样本、泛化、历史回归全部通过；继续修改只剩审美偏好时停止。

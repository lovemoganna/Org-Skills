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
13. 主要 Pattern 已执行 Hypothesis Frontier / Robustness / Finding Promotion Gate。

### 4A. 深度分析 QA

- 是否至少检查分布 / 分层；
- 数据支持时，是否继续检查时间、流程、关系、驱动或异常；
- 是否同时检查绝对量和标准化指标；
- 比率、成功率、时延等是否保留分母 / 样本 N；
- 是否把相关或同期变化误写成因果；
- 深挖结果是否真的改变判断，而不是重复切片。

### 4B. Investigation QA

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

### 4C. 可视化 QA

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

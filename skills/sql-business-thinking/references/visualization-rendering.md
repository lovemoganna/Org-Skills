# 可视化与报告表达协议

目标：把 D20 已确认的交付内容转换成清楚、准确的展示计划。D21 只读 D20 的 ReportSpec / DashboardSpec，不回写它们。

本协议只负责 **Presentation Engine**。它不得重新定义业务口径、改 SQL、补数据、绕过 Gate 或升级未经验证的判断。

```text
D20 已确认的 ReportSpec / DashboardSpec（只读）
→ D21 VisualizationPlan
→ Presentation Question
→ Data Shape
→ Chart Candidate Competition
→ Unit Honesty Gate
→ One-Chart-One-Conclusion Gate
→ Layout Archetype
→ Information Budget
→ Renderer
```

## 1. Truth / Presentation 分层

分析层决定：

- 什么是真的；
- 什么能说；
- 什么不能说；
- 哪个 Gate 阻断了什么。

交付资格层决定：

- Report 可以保留哪些已验证发现与证据；
- Dashboard 哪些数据具有持续监控资格；
- 哪些一次性诊断只能进入下钻或报告。

表达层决定：

- 哪些结论值得进入正文；
- 用什么图最诚实；
- 哪些信息放首屏；
- 哪些证据折叠；
- 哪些内容应该删除。

**Presentation 不能修复 Analysis。** 如果输入结论被 Gate 阻断，Renderer 只能显示阻断，不得换一种图继续表达。

## 2. Presentation Question

每个可视化前先写一句内部问题：

```text
读者看完这张图，应该新增哪一个判断？
```

如果答案只是“看到更多数据”，不生成图。

图表不是字段容器。一个图必须服务一个独立判断。

## 3. Data Shape Gate

先判断数据形状，再选图型，不按字段名或习惯直接映射：

- 少量类目连续值比较；
- 排名；
- 100% 构成；
- 正负变化；
- 连续时间；
- 分布；
- 两变量关系；
- 前后对比；
- 层级；
- 流向 / 网络；
- 明细记录；
- 审计 / 异常 / 阻断状态。

同一个业务问题可能有多个合法图型；数据形状只是召回候选，不是最终选择。

## 4. Chart Candidate Competition Gate

先选能准确表达当前判断的最简单方案。若方案明显合适，直接选，不为凑数量列候选。只有存在真实取舍时，才比较合理方案并记录关键理由。

有争议时按以下维度选择：

1. **Semantic Fit**：几何编码是否真的对应业务含义；
2. **Unit Honesty**：视觉单位是否真实，不制造不存在的个体或颗粒；
3. **Label Capacity**：类目名、数值、单位能否清楚放下；
4. **Reading Speed**：是否符合当前受众需要的阅读速度；
5. **Narrative Value**：是否突出本图唯一结论，而不是同时争抢多个判断；
6. **Implementation Reliability**：当前 HTML / SVG / Chart.js 环境是否能稳定实现。

最终只需说明选型理由；存在其他合理方案时，说明关键取舍。禁止用“更高级”“更专业”“更好看”作为理由。

## 5. Unit Honesty Gate

视觉单位必须和真实数据单位一致。

硬规则：

- 连续金额、余额、价格等，不得为了“Lupi 化 / 单位化”随意拆成点、格、tick，除非存在真实、明确、稳定的单位；
- 100% 构成可以使用 100 点 / 100 tick，但必须说明取整规则；
- 面积编码时，面积与数值成比例；若用半径表达面积，半径按平方根换算；
- 柱长、条长必须与数值成比例，不用断轴制造差异；
- 颜色只承担明确的数据角色或层级，不把装饰色伪装成数据维度；
- 无法诚实编码时，优先退回普通条形、表格或文字，不为视觉风格牺牲数据契约。

## 6. One-Chart-One-Conclusion Gate

一个图只承担一个独立结论。

图数量由 **独立结论数** 决定，不由字段数、SQL 数或可用图型数决定。

若两个图表达同一结论：

- 保留阅读更快、单位更诚实、标签更清楚的一张；
- 另一张删除；
- 不为了“页面丰富”保留重复图。

同一页可以重复使用相同图型。语义准确和阅读一致性优先于视觉变化。

## 7. Layout Archetype Gate

生成 HTML 前先锁定一种页面骨架，不边写边发明布局。

### A. Decision Brief

适合：结论少、管理者快读。

```text
Hero 判断
→ 2–4 个证据块
→ 最大限制 / 阻断
→ 折叠审计证据
```

### B. Evidence Report

适合：专业分析、需要较强可审计性。

```text
Hero 判断
→ 关键发现
→ 证据图 / 关键表
→ 数据质量与限制
→ SQL / Result 审计区
```

### C. Dialogue Report

适合：用户明确要求人物推演、教学回放或代码逐步产生。

沿用 `report-rendering.md` 的 Dialogue-Driven Report Override，不受 A/B 的首屏规则覆盖。

### D. Monitoring Dashboard

适合：持续监控当前业务状态。

```text
核心状态
→ 需要立即关注的异常
→ 关键结构 / 趋势
→ 必要下钻入口
```

硬规则：

- 只使用已经通过看板资格的数据；
- 首屏优先回答“现在是否需要关注”；
- 不展示完整分析过程；
- 一次性根因、竞争解释、稳健性过程默认进入下钻或报告；
- 简单但长期重要的状态数据可以进入核心看板；
- 不用更多图表证明分析很深入。

硬规则：

- 一次只选一个 Archetype；
- 不拼接多个页面体系制造混合版式；
- 页面骨架可以删槽位，但不得为了填满模板制造无证据模块。

## 8. Information Budget Gate

正文只允许四类信息：

1. 直接回答主问题；
2. 改变判断的重要证据；
3. 会改变解释边界的限制 / Gate；
4. 让关键结论可验证的最小证据入口。

以下内容默认折叠或删除：

- Runtime 初始化细节；
- Skill Trace；
- 重复 SQL；
- 与主问题无关的字段清单；
- 不改变判断的次级指标；
- 重复表达同一结论的第二张图；
- “为了完整”而保留的过程记录。

**Deletion Gate：**每个可见区块必须至少满足以下一项，否则删除或折叠：

```text
回答问题 / 改变判断 / 解释限制 / 提供必要验证入口
```

## 9. Title Contract

图表标题默认写 **结论**，不是图型名。

例如：

```text
Top1 占近一半流量
```

优于：

```text
用户交易额柱状图
```

如果结论仍未确定或图本身用于诊断，可以使用问题式标题，但不得使用“Chart 1 / 图表 2”。

## 10. VisualizationPlan（独立输出）

D21 单独输出 VisualizationPlan。D20 的 ReportSpec / DashboardSpec 只读、不得追加或修改字段。

每个计划项最少记录：

```text
content_ref（指向 D20 已确认内容）
presentation_question（读者要理解的判断）
data_shape
selected_chart（可以是表格或文字，不强制画图）
unit_contract
layout_role
visibility
```

`content_ref` 必须指向 D20 Spec 中实际存在且允许展示的内容；不存在、被阻断或无数据支持时不得生成可见图表。D21 不得通过新增 `content_ref` 指向的内容来补救。

存在真实选型争议时，补充候选与取舍理由；不存在争议时不额外记录候选清单。不得生成新的业务事实、指标或 SQL。

`visibility` 只能是：

```text
PRIMARY
SECONDARY
AUDIT
SUPPRESSED_BY_GATE
```

Renderer 按 VisualizationPlan 渲染 `PRIMARY / SECONDARY / AUDIT` 对应层级；`SUPPRESSED_BY_GATE` 不得进入业务图表正文。

## 11. Artifact Presentation Gate

选型取舍、Layout Archetype、Unit Honesty、Information Budget 和 Renderer 策略属于内部 VisualizationPlan / audit，不属于业务正文。

最终 Artifact 必须反查可见文本：

- 不得出现“候选比较后选择……”“这里选择……而不是……”“为了更快读所以……”等面向实现过程的说明；
- 不得把图表候选、选型理由、`selected_chart`、`layout_role` 等内部字段直接渲染给普通读者；
- 图表标题、说明文字只解释业务结论、数据口径、限制和读图方法；
- 用户明确要求“为什么选这个图 / 解释设计决策”时，才允许把设计 rationale 放入单独的 Design Notes，不与业务结论混写。

**VisualizationPlan 可以保留必要的表达理由，正文必须克制。**

## 12. Renderer 边界

Renderer 只读已验证 Result、D20 Spec 和 D21 VisualizationPlan。

禁止：

- 为了图表好看重新聚合但不记录口径；
- 为了填模板新增未验证 KPI；
- 把审计状态做成主视觉；
- 把多个弱发现拼成“复杂图”掩盖信息不足；
- 用视觉复杂度代替分析深度。

最终目标不是“图更多”，而是：

```text
更少的图
更清楚的判断
更诚实的编码
更完整的证据入口
```

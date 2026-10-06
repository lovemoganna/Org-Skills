# 可视化与报告表达协议

目标：把已经通过 SQL、数据质量 Gate 和分析深度检查的结论，转换成更快、更稳、更克制的最终表达。

本协议只负责 **Presentation Engine**。它不得重新定义业务口径、改 SQL、补数据、绕过 Gate 或升级未经验证的判断。

```text
Validated Findings
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

重要图表默认比较至少 3 个合理候选；不足 3 个时比较全部可用候选。候选比较只需保留内部记录，不把选型过程塞进正文。

按以下维度淘汰：

1. **Semantic Fit**：几何编码是否真的对应业务含义；
2. **Unit Honesty**：视觉单位是否真实，不制造不存在的个体或颗粒；
3. **Label Capacity**：类目名、数值、单位能否清楚放下；
4. **Reading Speed**：是否符合当前受众需要的阅读速度；
5. **Narrative Value**：是否突出本图唯一结论，而不是同时争抢多个判断；
6. **Implementation Reliability**：当前 HTML / SVG / Chart.js 环境是否能稳定实现。

最终必须能回答：

```text
为什么选它？
为什么最接近的两个候选被淘汰？
```

禁止用“更高级”“更专业”“更好看”作为淘汰理由。

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

同一页默认避免连续使用高度相似的图形轮廓，除非这是理解所必需。

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

## 10. ReportSpec 扩展

每个正式可视化块至少记录：

```text
finding_id
presentation_question
gate_dependencies
data_shape
candidate_charts
selected_chart
rejected_candidates
unit_contract
single_conclusion
reading_speed
visibility
```

`visibility` 只能是：

```text
PRIMARY
SECONDARY
AUDIT
SUPPRESSED_BY_GATE
```

Renderer 只渲染 `PRIMARY / SECONDARY / AUDIT` 对应层级；`SUPPRESSED_BY_GATE` 不得进入业务图表正文。

## 11. Renderer 边界

Renderer 只读已验证 Result 和 ReportSpec。

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

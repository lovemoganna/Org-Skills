# Visualization Registry

目标：让可视化选择由“分析问题”驱动，而不是被当前 Renderer 支持的几个图形限制。

## 1. 可视化能力注册表

| 分析意图 | 优先图形 | 适用条件 |
|---|---|---|
| 单值状态 | KPI + sparkline | 有明确指标；有历史时再加 sparkline |
| 时间趋势 | line / area | 有有序时间轴且点数足够 |
| 多序列趋势 | multi-line / small multiples | 序列数量可读且单位一致 |
| 构成随时间 | stacked area | 分项可加总为整体 |
| 类别比较 | bar / column | 离散类别比较 |
| 多指标类别比较 | grouped bar | 指标单位兼容 |
| 构成 | stacked bar / 100% stacked | 分项互斥且可加总 |
| 正负结构 | diverging bar | 围绕共同零轴比较 |
| 排名 | ranked bar / lollipop / dot plot | 强调顺序与差异 |
| 集中度 | Pareto | 排名 + 累计贡献 |
| 单变量分布 | histogram | 连续数值且样本足够 |
| 多组分布 | box plot | 比较中位数和离散程度 |
| 两变量关系 | scatter | 每点是一条可比观测 |
| 三变量关系 | bubble | 第三变量适合作为 size，且不会误导 |
| 二维密度/矩阵 | heatmap | 两个离散/分箱维度 |
| cohort / retention | cohort heatmap | 有 cohort 起点与后续周期 |
| 日历强度 | calendar heatmap | 日级时间 + 强度指标 |
| 阶段转化 | funnel / stage bar | 存在有序、互斥的阶段 |
| 加性贡献 | waterfall | 各驱动可严格加总到结果 |
| 流向 | Sankey / alluvial | 存在 source → target → value |
| 层级构成 | treemap | 存在真实层级关系 |
| 实体关系 | network graph | 存在可解释节点/边，不是为了炫技 |
| 地理分布 | map | 有真实地理编码或可验证边界 |
| 明细核查 | table | 需要精确记录和多字段检查 |
| 异常队列 | ranked table / conditional table | 需要人工后续处理 |

## 2. Selection Gate

每张图必须先回答：

```text
问题是什么？
比较对象是谁？
数据粒度是什么？
最重要的视觉编码是什么？
为什么这张图比表格或其他图更适合？
```

答不出来就不生成。

## 3. Renderer Capability Gate

图表语义不受 Renderer 原生类型列表限制。

按以下顺序处理：

1. Renderer 原生支持目标图形 → 直接使用；
2. 同一分析语义存在可信等价变体 → 使用等价变体；
3. 可以用自定义 SVG / Canvas / 组合组件实现 → 实现并保留数据来源；
4. 都不可靠 → 回退到表格或数字，不伪造图形。

禁止为了“能画出来”把 histogram、box plot、waterfall、funnel、Sankey 等机械降级成普通柱状图，如果降级会改变分析含义。

## 4. 图表数据契约

每个 visual 至少记录：

```text
question
grain
x / y / series / size
metric definition
denominator
sort
filter
source tables
limitations
interaction
```

Renderer 不得重新发明指标口径。

## 5. 交互

只有能帮助分析时才加：

- 全局/局部筛选；
- hover / tooltip；
- 点击筛选；
- drill-down；
- brush / zoom；
- TopN 展开；
- 明细联动；
- 重置状态。

交互必须作用于同一批筛选后的数据，不能出现图变了而 KPI/表格没变。

## 6. 选择细则

- 趋势：点太少时用 KPI / bar / slope，不伪造连续曲线；
- 构成：类别多时优先排序条形，不滥用 pie；
- 排名：同时关心累计贡献时优先 Pareto；
- 分布：平均值可能掩盖长尾时必须考虑 histogram / box plot；
- scatter：样本太少时改用 dot/table，不强行解释相关性；
- funnel：阶段必须有顺序，不能把普通类别硬画成漏斗；
- waterfall：只在贡献可加总时使用；
- Sankey：必须有明确流向和权重；
- map：没有真实地理信息时禁止画伪地图；
- network：节点和边必须来自真实关系。

## 7. Encoding & Label Gate

- 多序列图必须有清晰的直接标签或可见图例；只靠颜色区分不合格。
- 散点、气泡、折线末端等直接标签发生重叠时，按顺序处理：减少直接标签 → 只标关键点 → 使用 tooltip / hover detail → 使用可验证的 label repel。禁止让文字互相覆盖。
- 图例、轴、tooltip、表格中的同一系列名称必须一致。
- 不得用颜色作为唯一识别通道；必要时增加形状、线型、直接标签或位置编码。
- 移动端不能通过缩小字体解决拥挤；优先重排、局部滚动或减少非必要标签。

## 8. 不追求图形数量

“支持更多图”不等于“每次多画几种”。

同一种图如果最适合多个问题，可以重复使用；不同问题需要不同编码时，再切换图形。最终目标是信息增量，不是视觉多样性。


## V11 · Analysis Spec First

Visualization Registry 只负责回答“什么数据关系适合什么 visual family”。

它不能直接决定查询和轴字段。

必须按以下顺序：

```text
Semantic Field Catalog
→ Analysis Intent
→ Analysis Spec
→ DuckDB SQL
→ Result
→ Chart.js Spec
```

### 基础关系映射

| 数据关系 | 默认 visual |
|---|---|
| temporal + measure | line |
| categorical + measure | bar |
| 少量互斥 category + additive/common-denominator measure，明确 part-to-whole | stacked bar；必要时 doughnut |
| continuous measure distribution | histogram |
| two continuous measures | scatter |
| entity / raw records | table |
| temporal + measure + categorical series | multi-line |
| categorical + measure + categorical series | grouped / stacked bar，由问题决定 |

### X / Y / Series

X / Y / Series 只能来自 Analysis Spec。

禁止：

- 组件通过“第一个字符串列 / 第一个数值列”猜 X/Y；
- 因现有 demo 写死 `created_at / amount / status`；
- Renderer 自动选择额外 category 当 Series；
- Renderer 自己修改时间粒度、排序或 TopN。

### Neutral Visualization Rule

Chart Planner 的 intent 必须是中性的：

`level / trend / category_comparison / composition / distribution / relationship / ranking / detail`

`risk / anomaly / fraud` 不是 chart intent。

Investigation / Domain 层可以决定某个已验证 Finding 值得展示，但 visual 本身仍表达数据关系，不把结论写进字段映射。

### Chart.js Ownership

本 Skill 的默认图表引擎为 Chart.js。

Renderer Capability Gate 更新为：

```text
Chart.js native
→ Chart.js plugin / custom implementation
→ same-intent equivalent
→ table fallback
```

不允许组件换用另一套图表引擎来绕过 Analysis Spec。

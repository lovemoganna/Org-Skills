# Semantic Field Catalog & Analysis Spec

目标：把 Dashboard 的图表生成从“组件临时猜字段”改成统一编译链路。

唯一允许的链路：

```text
字段识别
→ 分析意图
→ 维度 / 指标
→ 聚合
→ 图表类型
→ X / Y / Series
→ DuckDB SQL
→ Result
→ Chart.js Spec
→ Renderer
```

图表组件不得自行读取原始表、决定聚合或重新解释字段。

## 1. Semantic Field Catalog

读取 Schema 后，先为每个字段建立统一语义目录。

每个字段至少记录：

```text
source
field
physical_type
semantic_type
role
unit
cardinality
nullable
aggregation_class
allowed_aggregations
time_grains
notes
```

### semantic_type

至少区分：

- `identifier`：UID、订单号、流水号、tx hash、主键 / 候选键；
- `temporal`：date / datetime / timestamp；
- `categorical`：国家、渠道、网络、方向、资产、状态等；
- `state`：completed / failed / processing 等业务状态；
- `continuous_numeric`：金额、时延、费率等连续数值；
- `discrete_numeric`：确认数、次数等离散数值；
- `boolean`；
- `text`；
- `geo`：仅在字段真实表达空间位置时；
- `unit`：currency / asset / measurement unit；
- `unknown`：证据不足，不强制猜测。

### Identifier Gate

数值类型不等于指标。

以下字段默认是 identifier，不得执行 `SUM / AVG / MIN / MAX`：

- 主键 / 候选键；
- 字段名或业务语义明确表示 id / uid / order_id / transaction_id / hash / serial / code；
- 高唯一率且没有可加总业务含义；
- 与实体表建立 join 的稳定键。

identifier 可用于：

- `COUNT`；
- `COUNT DISTINCT`；
- 明细表；
- drill-through；
- scatter 的 point identity。

禁止因为字段物理类型是 INTEGER / BIGINT 就把 ID 当 measure。

## 2. Aggregation Semantics

每个 measure 必须先指定 `aggregation_class`。

### additive

可在当前单位和粒度下直接相加。

例：同一 currency 内的交易金额、订单数。

默认允许：

`SUM / AVG / MIN / MAX / MEDIAN / COUNT`

是否使用哪一个由分析意图决定。

### semi_additive

只能沿部分维度聚合。

例：余额、库存、某一时点 snapshot。

禁止跨时间直接 SUM，除非业务定义明确允许。

### non_additive

比率、百分比、平均值、中位数、价格、费率、预聚合 KPI。

禁止直接 SUM。

如果 rate 存在 numerator / denominator：

```text
rate = SUM(numerator) / SUM(denominator)
```

不得对分组 rate 做简单 AVG，除非该定义明确要求。

### countable_identifier

实体 / 记录 ID。

允许：

`COUNT / COUNT DISTINCT`

禁止 SUM。

## 3. Analysis Intent

Chart Planner 只能使用以下中性分析意图，不预设业务结论：

- `level`：当前水平 / 核心 KPI；
- `trend`：随时间变化；
- `category_comparison`：类别之间比较；
- `composition`：整体由哪些部分构成；
- `distribution`：数值如何分布；
- `relationship`：两个连续指标之间关系；
- `ranking`：Top / Bottom；
- `detail`：实体和原始记录。

`anomaly`、`risk`、`fraud` 等不是图表选择意图。

它们只能来自 Investigation / Domain 层的已验证 Finding；图表层仍使用 trend / comparison / distribution / detail 等中性关系表达。

## 4. Dimension / Measure Selection

### Dimension

候选 dimension 优先来自：

- temporal；
- categorical；
- state；
- geo；
- identifier（仅 detail / drill / point identity）。

### Measure

候选 measure 必须满足：

- 有明确业务数值语义；
- 有合法聚合方式；
- 单位可解释；
- 与目标 dimension 在当前粒度兼容。

禁止：

- 对 ID 求和；
- 不同 currency / asset 无规则直接聚合；
- 对百分比机械求和；
- 把 category code 当连续指标；
- 把预聚合结果再次聚合而不验证 grain。

## 5. Analysis Spec

所有 Dashboard 组件先生成统一 Analysis Spec。

建议结构：

```json
{
  "id": "fiat_latency_by_channel",
  "question": "不同法币渠道的 completed 处理时延如何比较？",
  "intent": "category_comparison",
  "source": "fiat_transactions",
  "grain": ["channel"],
  "filters": [
    {"field": "status", "op": "=", "value": "completed"}
  ],
  "dimensions": [
    {
      "field": "channel",
      "role": "x",
      "semantic_type": "categorical"
    }
  ],
  "measures": [
    {
      "id": "median_latency_h",
      "expression": "date_diff('second', created_at, completed_at) / 3600.0",
      "aggregation": "MEDIAN",
      "unit": "hour",
      "format": "0.00h"
    }
  ],
  "series": null,
  "time_grain": null,
  "sort": [
    {"field": "median_latency_h", "direction": "desc"}
  ],
  "top_n": null,
  "null_policy": "exclude_measure_nulls",
  "chart": {
    "family": "bar",
    "orientation": "horizontal",
    "stack": false
  },
  "interactions": {
    "click_filter": "channel",
    "drill_key": "fiat_order_id"
  }
}
```

Spec 不保存运行结果。

SQL、rows、Chart.js config 都是 Spec 的派生产物。

## 6. Intent → Field Shape → Visual

### Trend

条件：

- 1 个 temporal dimension；
- 1 个或多个语义兼容 measure；
- 可选 1 个低 / 中基数 categorical series。

映射：

```text
X = time bucket
Y = measure
Series = optional categorical
Chart = line
```

只有“总量的组成随时间变化”是核心问题时才允许 stacked area。

### Category comparison

条件：

- 1 个 categorical dimension；
- 1 个 measure。

映射：

```text
Category = dimension
Value = measure
Chart = bar
```

长标签或排名默认 horizontal bar。

### Composition

条件：

- 分类互斥；
- measure 可加总或存在共同 denominator；
- 目标明确是 part-to-whole；
- 类别数量少。

优先：

`stacked bar`

只有类别少且粗略占比阅读明显优于长度比较时才允许 doughnut。

### Distribution

条件：

- 1 个 continuous measure；
- 不先聚合成均值后再画。

映射：

`histogram`

由 SQL 先生成 bin，再使用 Chart.js bar。

### Relationship

条件：

- 两个 continuous measures；
- 有明确 observation grain；
- 样本点足够。

映射：

```text
X = measure A
Y = measure B
Point identity = stable identifier
Series = optional categorical
Chart = scatter
```

### Detail

条件：

- 实体或原始记录；
- 需要精确核查多字段。

映射：

`table`

不得为了“有图”把订单号 / 用户 ID 画成数值图。

## 7. Series Gate

Series 只能来自额外 categorical dimension。

使用前检查：

- Series 是否真的帮助比较；
- 类别数是否可读；
- measure 与 series 语义兼容；
- 是否需要 stack / group / multi-line。

默认：

- 趋势 + category → multi-line；
- category + category + additive measure → grouped / stacked bar，按问题决定；
- part-to-whole → stack；
- 类别过多 → TopN + Other / filter / small multiples，不制造巨大 legend。

## 8. Time Grain Gate

时间粒度不得写死。

根据：

- 数据覆盖跨度；
- 数据自然发生频率；
- 当前问题的比较周期；
- 数据密度；
- 目标点数；

选择 `hour / day / week / month / quarter / year`。

默认目标是产生足够表达形状、但不过度噪声的时间桶。

禁止：

- 一律按月；
- 一律按天；
- 用户明确要求粒度时擅自改变；
- 因空桶多而自动补造 0，除非 zero 确实表示“没有发生”。

## 9. Sort / TopN

排序由意图决定：

- ranking / comparison：按 measure 排序，除非类别本身有自然顺序；
- time：按时间升序；
- state / stage：按业务状态顺序；
- detail：按业务主时间或用户指定字段。

TopN 必须来自当前 cardinality 和问题，不得写死。

TopN 后是否保留 `Other` 必须由 part-to-whole 需求决定。

## 10. Filter Contract

Global Filter 不直接修改 Chart.js。

执行：

```text
Global Filter State
→ patch Analysis Spec.filters
→ compile DuckDB SQL
→ Result rows
→ compile Chart.js Spec
→ render
```

所有依赖组件必须使用同一 Filter State。

禁止图表组件在浏览器里自行过滤一份与 KPI 不同口径的数据副本。

## 11. Central Query Ownership

只有统一 Analysis Engine 可以：

- 读取 Analysis Spec；
- 生成 DuckDB SQL；
- 执行查询；
- 返回 Result rows；
- 生成 provenance / grain / unit metadata。

Chart / KPI / Table 组件不得：

- 直接查询 DuckDB；
- 拼 SQL；
- 自己决定聚合；
- 自己改变 TopN；
- 自己重新计算 rate；
- 自己推断时间粒度。

Renderer 只消费：

```text
Analysis Spec
+ Result
+ Chart.js Spec
```

# DuckDB SQL → Chart.js Compiler

目标：Analysis Spec 是唯一中间表示。

执行链：

```text
Analysis Spec
→ DuckDB SQL Compiler
→ Result Contract
→ Chart.js Compiler
→ Renderer
```

## 1. DuckDB SQL Compiler

SQL 必须完全由 Analysis Spec 生成。

### Query Contract

输出 SQL 必须保持：

- source；
- filters；
- time grain；
- dimensions；
- measures；
- aggregation；
- series；
- sort；
- TopN；
- null policy；
- grain。

禁止 Renderer 修改 SQL。

### Trend pattern

概念模板：

```sql
SELECT
  date_trunc(<time_grain>, <time_field>) AS x,
  <optional_series> AS series,
  <aggregation>(<measure_expression>) AS y
FROM <source>
WHERE <compiled_filters>
GROUP BY x, series
ORDER BY x, series;
```

没有 Series 时去掉 series。

### Category comparison pattern

```sql
SELECT
  <dimension> AS category,
  <aggregation>(<measure_expression>) AS value
FROM <source>
WHERE <compiled_filters>
GROUP BY category
ORDER BY value <direction>
LIMIT <top_n>;
```

TopN 为空时不生成 LIMIT。

### Rate pattern

优先：

```sql
SELECT
  <dimension>,
  SUM(<numerator>)::DOUBLE / NULLIF(SUM(<denominator>), 0) AS value
FROM <source>
...
GROUP BY <dimension>;
```

禁止：

```sql
AVG(precomputed_rate)
```

除非 metric definition 明确如此。

### Histogram pattern

bin 必须在查询层生成。

可以使用 DuckDB `histogram`、`width_bucket` 等当前版本支持能力，或根据 reviewed min/max 生成明确 bin。

Renderer 只接收：

```text
bin_start
bin_end
count
```

### Scatter pattern

不做无意义聚合。

```sql
SELECT
  <point_id>,
  <x_expression> AS x,
  <y_expression> AS y,
  <optional_series> AS series
FROM <source>
WHERE <compiled_filters>
  AND x IS NOT NULL
  AND y IS NOT NULL;
```

若源数据 grain 比目标 point grain 更细，必须先在 SQL 中按 point grain 聚合。

### Detail pattern

```sql
SELECT <approved_fields>
FROM <source>
WHERE <compiled_filters>
ORDER BY <business_time> DESC
LIMIT <detail_limit>;
```

Detail limit 是性能与 UX 约束，不等于分析 TopN。

## 2. Result Contract

统一结果结构至少包含：

```json
{
  "spec_id": "...",
  "grain": ["..."],
  "rows": [],
  "columns": [
    {"name": "x", "semantic_type": "temporal"},
    {"name": "y", "semantic_type": "continuous_numeric", "unit": "hour"}
  ],
  "row_count": 0,
  "provenance": {
    "source": "...",
    "filters": [],
    "query_id": "..."
  }
}
```

Chart.js Compiler 只能读取 Result Contract，不接触原始表。

## 3. Chart.js Compiler

Chart.js 配置由 Analysis Spec + Result 共同生成。

### Line

```text
intent = trend
→ type = line
→ labels = x
→ datasets = measure × series
```

必须：

- x 按时间顺序；
- 缺失值保持 null；
- 不自动 zero-fill；
- tooltip 使用业务格式；
- 多 series 有清晰 legend；
- point 数量大时降低 pointRadius，但保留 hover。

### Bar

```text
intent = category_comparison / composition / histogram
→ type = bar
```

支持：

- horizontal：`indexAxis: 'y'`；
- grouped；
- stacked；
- histogram pre-binned rows。

正负 measure 必须保留 0 baseline。

### Doughnut

仅用于 Analysis Spec 已通过 Composition Gate 的情况。

不得由 Renderer 因“类别少”自行改成 doughnut。

### Scatter

```text
intent = relationship
→ type = scatter
```

每个点至少保留：

- x；
- y；
- stable point identity；
- optional series；
- tooltip detail。

### Table

Table 不是 Chart.js 图形。

仍由同一 Analysis Spec / SQL / Result Contract 驱动。

Renderer 不可另查数据。

## 4. Axis Compiler

X / Y 不允许模板写死。

来自 Spec：

- trend：x = temporal dimension；y = measure；
- category comparison：category axis = dimension；value axis = measure；
- relationship：x/y = two measures；
- histogram：x = bin；y = count；
- detail：无 chart axis。

Axis title 来自：

```text
field label
+ aggregation
+ unit
```

例如：

`Median settlement latency (h)`

而不是只显示 `value`。

## 5. Series Compiler

Series 由 Spec.series 决定。

Renderer 禁止：

- 从结果里临时挑一个字符串列作为 series；
- 自动把所有 category 展开成 dataset；
- 因颜色够用就增加 series。

如果 Series cardinality 超过 Spec 可读上限，必须回到 Planner 重写 Spec，而不是 Renderer 自行截断。

## 6. Formatting

数值格式由 measure metadata 决定：

- count：整数；
- rate：百分比；
- currency：币种 / 单位；
- latency：ms / s / min / h；
- large number：K / M / B，仅显示层转换，原值不变。

KPI、Chart、Tooltip、Table 使用同一 formatter。

## 7. Interaction

Chart click 只发出语义事件：

```json
{
  "spec_id": "...",
  "dimension": "channel",
  "value": "ach"
}
```

Dashboard Controller 将事件转为统一 Filter State，再重新执行 Analysis Spec。

Chart.js component 不直接 mutate 其他组件的数据。

## 8. Compiler Failure

出现以下情况时阻断或降级：

- dimension / measure 语义不兼容；
- aggregation 不合法；
- unit 不兼容；
- series 基数过高；
- chart family 与 intent 不一致；
- SQL 结果 grain 与 Spec 不一致；
- Result 缺少 Chart.js 所需字段。

降级优先：

```text
修正 Analysis Spec
→ simpler chart in same intent
→ table
```

禁止用随机换图掩盖 Spec 错误。

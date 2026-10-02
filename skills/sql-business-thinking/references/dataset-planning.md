# 数据集勘察与分析规划

SKILL.md 讲主流程，这里放陌生数据集的勘察、分析地图、时间维表和 JOIN 守恒规则。

## 1. 勘察清单

对每张表问：

1. 一行是谁？
2. 主键是什么，外键连到哪？
3. 时间字段有哪些，各自代表什么节点？
4. 金额字段单位是什么，跟着哪个币种/资产字段？
5. 状态有哪些；哪些是终态；哪些算“成功”？
6. 有没有退化粒度？
7. 有没有版本/汇率/价格/费率等时间维表？它的业务键和时间键是什么？

终态与成功必须拆开。成功是业务口径；字典没写就是级别 3。

### 一致性小检查

- 订单号含日期时，和 created_at 对得上吗？
- 非成功状态却有 completed_at 是否能解释？
- 成功状态却没有 completed_at 有吗？
- completed_at 是否早于 created_at？
- 记录是否落在监控周期之外？
- 金额、手续费是否合法？
- 外键是否有孤儿？
- 连接维表的键在当前筛选下是否唯一？

## 2. 数据集一页纸模板

不超过 15 行：

```text
这是什么：
有哪几张表：
怎么连：
已知口径：
已有成品：
状态取值：
时间和体量：
已知风险：
时间维表：
退化粒度：
读不到的部分：
```

## 3. 勘察与体检 SQL

以下按 DuckDB 写。用户已验证的读取方式优先，不另起一套。

```sql
CREATE OR REPLACE TABLE {t} AS
SELECT * FROM read_xlsx('{url_or_path}', sheet = '{sheet}', header = true);

SELECT COUNT(*) AS n FROM {t};
SUMMARIZE {t};
SELECT * FROM {t} LIMIT 5;
```

### 3.1 主键、孤儿、状态、时间

```sql
SELECT {pk}, COUNT(*) AS n
FROM {t}
GROUP BY {pk}
HAVING COUNT(*) > 1;

SELECT c.*
FROM {child} c
LEFT JOIN {parent} p ON c.{fk} = p.{pk}
WHERE p.{pk} IS NULL;

SELECT {status}, COUNT(*) AS n
FROM {t}
GROUP BY {status}
ORDER BY n DESC;

SELECT * FROM {t}
WHERE completed_at < created_at;
```

### 3.2 金额文本转数字

```sql
TRY_CAST(REPLACE(CAST({amount} AS VARCHAR), ',', '') AS DECIMAL(38, 8)) AS {amount_num}
```

转完先查转换失败行。

### 3.3 时间维表 / 汇率表

遇到 exchange_rates / prices / fee_rules / status_history 一类表，先确认：

```text
业务键：asset / currency / product / rule_id ...
时间键：effective_date / valid_from / observed_at ...
目标交易时间：created_at / completed_at / settled_at ...
```

先做覆盖：

```sql
SELECT
  {business_key},
  COUNT(*) AS rows,
  COUNT(DISTINCT {time_key}) AS time_points,
  MIN({time_key}) AS min_time,
  MAX({time_key}) AS max_time
FROM {dimension}
GROUP BY {business_key};
```

再走时间路由：

1. exact-date / exact-time；
2. 业务允许时 as-of；
3. 业务允许时 snapshot；
4. 都不允许就暂停。

**命名规则：**只要不是交易时点真实匹配，结果名必须显式带 `snapshot / as_of / 估值`，不能继续叫“历史成交额”。

### 3.4 JOIN Cardinality Gate

金额聚合前必须验证：

```sql
-- 右表键是否唯一
SELECT {join_key}, COUNT(*) AS n
FROM {right}
GROUP BY {join_key}
HAVING COUNT(*) > 1;

-- JOIN 前后行数
WITH before_join AS (
  SELECT COUNT(*) AS n FROM {left_filtered}
), after_join AS (
  SELECT COUNT(*) AS n
  FROM {left_filtered} l
  JOIN {right_prepared} r ON {join_condition}
)
SELECT before_join.n AS before_n,
       after_join.n AS after_n,
       after_join.n - before_join.n AS delta
FROM before_join, after_join;
```

若不是业务预期的一对多，`delta != 0` 就停止金额 SUM。

### 3.5 对账

需要严格比较重复行数量时，用双向 `EXCEPT ALL`：

```sql
(SELECT * FROM mine EXCEPT ALL SELECT * FROM expected)
UNION ALL
(SELECT * FROM expected EXCEPT ALL SELECT * FROM mine);
```

## 4. 分析地图

每行：

| 主题 | 业务问题 | 用到的表和字段 | 先决口径 | 粒度 | 训练点 | 状态 |
|---|---|---|---|---|---|---|

状态：未做、进行中、完成、部分可做、做不了。

顺序：

1. 数据可信度；
2. 看板/预期结果对账；
3. 规模结构、趋势、用户分层；
4. 可靠性和风险信号。

时间维表或 JOIN 基数不明时，后续金额题不得标“可做”。

## 5. Answer Coverage Gate

多问题任务在分析地图之后增加：

| 用户问题 | 数据是否支撑 | 结果块 | 正文展示形式 | 状态 |
|---|---|---|---|---|

最终报告里每个主问题/子问题至少对应一个正文可见结果块。不能只在附录回答。

## 6. Top N 自适应

- active ≤ 10：Top 1 / Top 3；
- 10 < active < 100：Top 5 / Top 10；
- active ≥ 100：Top 10，可增加 Top 1%。

如果 Top N 覆盖全部 active population，则它不能作为核心集中度结论。

## 7. 小样本降级

任一分组不足 10 笔时，默认只出笔数和合计，不下比率/排名结论。用户明确要求时可计算，但旁边标分母 N，仅供参考。

## 8. 选题

优先用地图中的真实字段和已有对账锚点。台账里哪类错误多，就优先选能暴露该错误的题。数据撑不住的题直接写缺什么，不用主题库硬凑。

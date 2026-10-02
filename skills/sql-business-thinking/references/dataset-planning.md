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

## 4. Analysis Map → Question Frontier

Analysis Map 先描述“数据能回答什么”，不要直接把每个字段、每个主题都变成查询任务。

每行：

| 主题 | 可回答的问题 | 用到的表和字段 | 先决口径 | 粒度 | 阻塞项 | 状态 |
|---|---|---|---|---|---|---|

状态：未做、进行中、完成、部分可做、做不了。

默认依赖顺序：

1. 会阻塞后续解释的数据可信度 / 时间 / JOIN / 口径；
2. 会改变主结论的竞争解释；
3. 规模、结构、集中度、分层；
4. 只增加描述细节、但不改变判断的问题。

时间维表或 JOIN 基数不明时，后续金额题不得标“可做”。

### 4.1 Question Frontier

勘察完成后建立内部 Frontier：

| 区域 | 内容 |
|---|---|
| Confirmed | 已被数据证明、后续可直接继承的事实 |
| Unknowns | 仍未知且答案可能改变口径、结论或分析路径的事项 |
| Candidates | 能消除这些 Unknowns 的候选问题 |
| Current | 当前唯一值得进入 SQL 的问题 |

Frontier 是**分析状态**，不是报告中的滚动摘要。正文只展示 Current、为什么现在问、Lucy 的挑战和 Result 后发生的那一个变化。

### 4.2 Question Quality Gate

候选问题进入 SQL 前必须通过四项：

1. **Trigger**：由哪个已知事实 / 上一轮 Result / 当前阻塞触发？
2. **Consequence**：可能答案分别会改变什么？如果无论结果如何下一步都一样，通常不值得查。
3. **Answerability**：现有表、字段、粒度、时间和 JOIN 能不能回答？
4. **Priority**：它是否比其他 Unknown 更值得先问？

默认优先级：

```text
阻塞后续可信度/口径
> 会改变结论的竞争解释
> 会改变用户/金额/结构判断
> 纯描述性补充
```

不要为了“分析完整”机械查询每个维度。问题没通过 Gate，直接淘汰或改写。

### 4.3 Frontier 更新

每个 Result 必须至少做一件事：

- 关闭一个 Unknown；
- 产生一个新的高价值 Unknown；
- 改变候选问题优先级；
- 终止一条分析路径；
- 或作为最终答案所需的必要取数。

否则查询默认视为低价值，应从报告中删除。

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

选题不是“从主题库挑一个能写 SQL 的题”，而是从 Question Frontier 里挑**当前最值得消除的未知**。

规则：

- 优先用地图中的真实字段和已有对账锚点；
- 优先处理会阻塞后续分析或改变结论的 Unknown；
- 台账里的历史错误只能作为风险提示，不能为了“覆盖训练点”强行制造问题；
- 纯描述问题如果不能改变后续路径，只在它直接构成最终答案时保留；
- 数据撑不住的问题直接标缺什么，不用主题库硬凑；
- Star 提问后由 Lucy 先挑战问题质量；Gate 未通过不进入 SQL。

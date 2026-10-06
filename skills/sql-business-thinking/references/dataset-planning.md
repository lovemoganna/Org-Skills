# 数据集勘察与分析规划

## 0. Scope / Execution Contract Priority

用户显式的数据范围与读取方式高于本文件中的通用勘察建议。

- 指定表 / Sheet 白名单时，只读取白名单内容；范围外最多读取 metadata 确认名称。
- 用户禁止读取 dashboard / expected / qa / fix log / backup 时，禁止读取这些内容做“参考”或对账。
- 用户给出不可改写的 DuckDB SQL 时，先区分数据读取语义与运行时 bootstrap。数据源身份、Sheet 范围、`read_xlsx` 语义和分析逻辑必须保持；Native 的 `INSTALL/LOAD httpfs` 不自动成为 DuckDB-Wasm 的逐字约束。
- HTML / Browser 任务中若 Native DuckDB 不可用，先走 DuckDB-Wasm：按 browser VFS 注册同一数据源，保留 `read_xlsx`，仅在必要时把原始 URL 映射为 VFS 文件名并记录映射。
- 只有用户显式要求 Native-only / byte-for-byte bootstrap，或所有已授权 DuckDB runtime 都失败时，才标 `BLOCKED_ENV / 待执行`。
- 不得改用 Python、Connector、CSV 预处理等其他读取方式后声称 DuckDB SQL 已执行。其他工具只能做独立交叉验证。

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

以下仅在用户未给更严格读取契约时作为 DuckDB 示例。用户已验证并声明“不得改写”的读取方式必须原样优先。

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

### 4.4 Hypothesis Frontier

当 Result 暴露出会进入最终报告的主要现象时，不要直接转向下一个描述问题。建立：

| 区域 | 内容 |
|---|---|
| Observed Pattern | 当前真正需要解释的现象 |
| H1 | 当前主解释 |
| H2 / H3 | 合理竞争解释 |
| Disconfirming Evidence | 什么结果会削弱 H1 |
| Diagnostic Test | 最能区分 H1 / H2 的 SQL |
| Status | supported / weakened / rejected / unresolved |

规则：

- “Bob 占 49.93%”只是 Pattern，不是 Insight；
- “所以用户高度集中”是描述，不是 Why；
- 解释必须落到数据能检验的机制，例如：高频累积 / 单笔大额 / 某 rail 或资产驱动 / 单一极端用户拉高；
- 至少保留一个竞争解释，禁止单故事直线推理；
- 数据不足以区分时，结论保持 unresolved，并明确缺什么。

### 4.5 Analysis Depth Gate

主要发现进入最终报告前至少走：

```text
What        发生了什么？
Where       集中在哪个用户 / 资产 / 币种 / 通道 / 时间？
Why         哪个机制可能驱动？
Alternative 还有什么合理竞争解释？
Test        用哪条数据证据区分？
Robustness  换口径 / 去极端值 / 换分母后还成立吗？
So What     能推出什么，不能推出什么？
```

不能把每一层机械变成一个 SQL。优先用**一条诊断 SQL 同时区分多个假设**。

### 4.6 Robustness Check

关键结论至少做一次能改变解释可信度的稳健性检查。优先顺序：

1. 去掉最大单点 / 极端值，重算核心指标；
2. 把金额拆成“笔数 × 单笔金额”，区分高频与大额；
3. 把总量按 rail / asset / currency 拆解，看集中来自哪里；
4. 换合理分母、粒度、时间口径，检查排名 / 结构是否稳定；
5. 小样本不足时不伪造统计显著性，只报告方向与样本量。

如果稳健性测试不会改变任何解释，或只是重复同一指标，不要为了“有 robustness”机械执行。

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
- Star 提问后由 Lucy 先挑战问题质量；Gate 未通过不进入 SQL；
- 主要 Pattern 出现后，下一步优先进入 Hypothesis Frontier，而不是继续横向扫更多维度；
- 选题优先能区分竞争解释的 diagnostic question，而不是继续问“还有多少 / 谁第二 / 哪个国家更多”。

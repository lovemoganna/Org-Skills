# DuckDB 聚合入门

本教程通过三条演示交易记录说明分组聚合。金额不代表真实业务数据。

## 认识样本

每行表示一笔交易。

| 类别 | 金额 |
| --- | --- |
| A | 100 |
| A | 60 |
| B | 40 |

## 编写 SQL

```sql
SELECT category, COUNT(*) AS txn_count, SUM(amount) AS total_amount
FROM (VALUES ('A', 100), ('A', 60), ('B', 40)) AS t(category, amount)
GROUP BY category
ORDER BY total_amount DESC;
```

## 核对结果

- 类别 A 有两笔，合计 160。
- 类别 B 有一笔，合计 40。
- 原始合计是 200；必须核对数据粒度。

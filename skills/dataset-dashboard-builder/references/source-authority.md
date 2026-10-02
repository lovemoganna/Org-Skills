# Source Role & Metric Authority Protocol

目标：先判断“哪些表是什么角色、哪些口径有权定义业务指标”，再开始分析。避免把看板、备份、预期结果或 QA 表当成原始业务事实。

## 0. Explicit Scope Gate

用户显式指定表、Sheet、文件、schema 或数据集子集时，该范围是分析边界。

规则：

1. 只读取、分析和 JOIN 用户允许的范围；
2. 允许读取工作簿 metadata 以确认精确表名、sheetId 或结构存在，但 metadata 中出现的范围外表不得进一步读取；
3. 范围外的 rule / expected / qa / dashboard / backup 即使位于同一工作簿，也不得影响当前口径；
4. 历史 regression 中知道某张额外表存在，不构成越界读取授权；
5. 如果当前范围缺少定义某项指标所需的规则表或维表，把该项标记为 `LIMITED / MISSING INPUT`，不要自动扩展范围；
6. 只有用户未指定范围时，才执行 Full-dataset Scan。

验收：

```text
Workbook = A + B + C + QA + Dashboard + Backup
User scope = A + B + C
→ metadata 可见全部
→ 内容只读取 A / B / C
→ QA / Dashboard / Backup 不参与当前分析
```

## 1. Table Role Gate

确定当前允许范围后，再为范围内每张表分配角色：

| 角色 | 说明 | 是否直接进入业务指标 |
|---|---|---|
| fact | 原始事件 / 交易 / 行为事实 | 是 |
| entity | 用户、账户、商户、产品等主数据 | 是，用于范围和属性 |
| dimension / reference | 汇率、价格、规则版本、映射表 | 条件允许时 |
| canonical aggregate | 明确由业务定义的权威汇总结果 | 用于对账 / 权威口径，不与原始事实重复累计 |
| rule / dictionary | 数据字典、业务规则、字段定义 | 否，用于解释和约束 |
| qa / reconciliation | 质检、对账、测试结果 | 否，用于验证 |
| fix / audit log | 修复记录、审计记录 | 否，用于理解历史限制 |
| dashboard / output | 已生成看板、报表、导出结果 | 否，除非用户明确要求分析该成品 |
| backup / archive | 备份、历史快照、临时副本 | 否，默认排除 |

角色不确定时先标 `UNKNOWN`，不得把它直接并入核心指标。

## 2. Authority Order

同一指标存在多个来源时，优先级不是“表更像原始数据就一定更高”，而是：

```text
明确业务规则 / 数据字典
→ 明确 canonical / expected / governed result
→ 可复现的原始事实
→ 派生分析表
→ dashboard / backup / 临时产物
```

如果权威规则与当前派生算法冲突，先暂停该指标，解释冲突。

## 3. Double-count Gate

当工作簿同时存在：

- 原始交易表；
- expected / aggregate / summary 表；
- dashboard 输出表；

禁止把这些表再次 UNION 或 SUM 到同一指标。

canonical aggregate 用来对账，不作为“新增事实”。

## 4. Unit & Aggregation Authority

先检查业务规则是否允许跨单位聚合。

若业务规则要求：

```text
currency / asset / network 分区
```

则原生单位汇总是 canonical。

即使存在汇率，也不得自动把跨币种换算结果升级为核心 KPI。

换算指标只能在以下条件下使用：

1. 业务规则允许统一估值；
2. 时间匹配符合 Time-dimension Gate；
3. 名称明确标记 estimate / snapshot / as-of；
4. 页面上与 canonical 原生单位指标分开；
5. 不替代 expected / governed 口径。

## 5. Control Tables Are Evidence, Not Business Population

`data_rules / qa_result / fix_log / test_results` 等控制表可以改变分析方式，例如：

- 明确 completed 才计入净额；
- 明确某字段不能混合聚合；
- 说明历史已修复问题；
- 提供已验证的基准结果。

但这些行不属于用户、订单、交易、资产等业务人口。

不得把“QA 检查数量”“修复条数”混进业务 KPI。

## 6. Source Map Output

完成角色识别后，输出当前允许范围的 Source Map：

| 表 | 角色 | 是否进入指标 | 主要用途 | 权威性 | 风险 |
|---|---|---|---|---|---|

只有 Source Map 通过后，才进入 Dataset Map / Quality Gate / Question Map。

## 7. 真实工作簿验收模式

当同一文件同时包含：

```text
原始事实
+ 规则
+ expected result
+ QA
+ dashboard
+ backup
```

正确行为是：

```text
事实表 → 计算
规则表 → 约束
expected → 对账
QA / fix log → 验证与解释
dashboard / backup → 默认排除
```

不得“所有 Sheet 一视同仁”。

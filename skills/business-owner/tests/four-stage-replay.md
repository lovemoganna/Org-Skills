# 固定四表：Carmen 四阶段 Review 回放（历史真实结果，不是本轮再次读表）

基准来源：GitHub Actions [真实 DuckDB 运行 #38074040094](https://github.com/lovemoganna/Org-Skills/actions/runs/38074040094)；原始 XLSX export，DuckDB 1.4.2；四个授权表各读取/物化一次。此次只是把已发生且可验证的运行重构为四张 Review 卡片，**没有声称新一轮重跑数据**。

## S1 TaskBrief · 老板下达任务
**问题**：通过交易流水检查历史样本中是否存在值得关注的净流出结构及待处理提币；判断其能否支持实时资金压力监测。
**预期决策**：是否需要因数据观察升级运营调查，还是先补齐实时数据。
**约束**：不能从 Bitget 事故背景推断这四表就是 Bitget 内部记录；不能跳过方向/状态/币种，不能将其叫真实钱包余额。  
**Reviewer**：需求方确认问题与边界；禁止要求 SQL 或先定答案。

## S2 ResultSpec / SourceMap · 基础梳理（Carmen）
**先写最终表**，不是先碰 SQL：

| 结果列 | 意义 |
|---|---|
| rail / asset | 一行代表一个资金轨道×币种 |
| completed_in_native | 已完成状态入金原生金额 |
| completed_out_native | 已完成状态出金原生金额 |
| completed_net_native | 前两列的差值 |
| completed_in_orders / completed_out_orders | 两方向订单笔数 |
| noncompleted_withdrawals | 非 completed 的提币笔数，仅是状态标签，不等于待处理 |

**数据在哪**：`fiat_transactions`、`crypto_transactions`；`users` 查孤儿 UID；`exchange_rates` 仅核验资产口径，不用单个快照当历史实际兑换率。  
**取什么**：uid、direction、status、amount、asset/currency、created_at、completed_at、order_id。  
**什么条件**：按实际方向 deposit/withdrawal；按 completed 状态拆；不预设“完成=链上到账”。  
**一行是谁**：轨道×币种，不是一个 UID 一行；如需追查个人，**下一层**才改为 UID×币种。  
**源记录合并**：保留轨道、币种后 UNION ALL，不能只按 UID 把两条明细直接 JOIN 后 SUM。

## S3 QAReceipt · 基础校验
**历史运行实测**：users 10 行；fiat 25 行；crypto 25 行；exchange_rates 8 行；43 笔标记 completed 的交易记录。  
**基础检查**：订单与 UID 键、时间创建/完成先后、可数值化金额、方向取值、逐资产金额守恒及独立 SQL 对账。该次运行没有发现已检查项目的阻塞缺陷，按**已检查范围 PASS**。  
**但 S3 PASS 不能证明**链上实际到账、钱包库存、完整历史正常基线或实时性。  
**Reviewer**：验证师审核字段、行数、SQL、原始源与检查覆盖；未查项写 UNKNOWN，不得自动标 PASS。

## S4 DecisionReport · 形成分析
**最终管理结论**：这些历史流水不能支持实时“资金出逃/流动性危机”判断；已完成状态净流量只可用于**样本内部**的历史结构描述。
- 该次回放按轨道×币种分出 8 组，没有一组呈现负净流量（按表中 completed 状态）。
- 非 completed 的提币共 4 笔，但细分为：1 笔 `processing`（链上 USDT 250）；2 笔 `failed`（USDT 300、EUR 300）；1 笔 `cancelled`（USD 200）；**4 笔非完成 ≠ 4 笔排队**。
- 初始“或许存在资金外逃”的工作假设未被这份历史样本支持；不是否认其他交易所真实发生的流出。
- 业务动作：如确实要监测恢复提币后的资金压力，需补充实时申请与完成时间、链上确认、钱包库存和可比正常基线，再决定应急升级。
**老板只看这一页报告**，需要追溯时可展开 S1–S3 附录。报告的构成是“结论→证据→解释→可执行行动→不确定项”，而不是八个数字卡片铺满首屏。

## Reviewer 负面例子
- 如果 S2 缺“每一行是谁”，拒绝进入 S3（会导致 JOIN 与 GROUP BY 错误）。
- 如果 S3 原始 XLSX 未实际读取、缺源版本或使用禁用工作表，标 BLOCKED；不得在 S4 填曾经的结果。
- 如果 S3 状态未定义而 S4 把非 completed 视作“等待处理中”，拒绝结论。
- 如果老板在 S2 就被要求给 SQL 打分，角色分工失败。

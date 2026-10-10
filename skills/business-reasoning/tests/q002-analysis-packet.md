# Q002 · 根据 Q001 真实反馈触发的业务深钻

触发来源：2026-10-10 UTC 的原始 XLSX / Native DuckDB Q001 运行 [38071946101](https://github.com/lovemoganna/Org-Skills/actions/runs/38071946101)，B 实测 USD 法币已完成 9 笔、4 用户、合计 USD 104270、Top1 贡献 64.256%，但未证明其行为机制或风险属性。BRL/GBP/TRY 只有一个活跃用户，100% 集中度不作风险结论。

```yaml
packet_id: Q002
revision: 1
data_contract_ref: 同 Q001；四表白名单；Native DuckDB 1.4.2 与原始 URL read_xlsx 不变
business_goal: 解释而不只是重复展示集中度，排除单个大额订单制造的比例错觉
question: USD 法币已完成交易的 Top1 贡献，来自少数大单还是多笔累积？剔除全体最大单笔后，Top1 用户及占比怎样改变？
decision_branches: 如果最大单笔足以主导，结论降为单笔影响；如果依旧集中，再调查频率、时间、用户行为；若数据不足则停止
result_grain: USD × 已完成交易（流水），再按 UID 汇总比较；剔除后仍以 USD 范围为分母
result_columns: [completed_usd_orders,distinct_users,native_total,top1_amount,top1_order_count,largest_single_order,trimmed_top1_amount,trimmed_top1_pct,same_top_user]
population_and_filters: fiat_transactions.currency='USD' AND status='completed'，不预设年份或将状态叫做真实结算
metric_units_and_logic: 金额均为 USD 原始单位；全体最大单笔以金额降序且 order_id 打破平局；按 UID 在两种条件下分别聚合
source_candidates: fiat_transactions，users 仅确认 UID 语义；不需要 crypto 或汇率来改变 USD 内部金额
join_plan: 不做明细双表 JOIN
candidate_sql_or_probe: analysis-verifier/tests/q002-verification.sql
hypotheses_and_falsifier: H1 高集中由单笔大单驱动；H2 由多笔累计驱动；若剔除最大单笔后占比显著变化则削弱 H2，反之削弱单笔解释；不设先验异常阈值
evidence_status: UNVERIFIED
```

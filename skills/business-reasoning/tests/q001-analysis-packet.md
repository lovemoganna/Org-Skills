# Q001 · 交易贡献与集中度 · 业务推理候选（尚未验证）

此文件是一次 **business-reasoning → analysis-verifier** 的交接样本，不是既有业务结果。不能把脚本中的历史字段使用当作本轮真实 schema 证明。

```yaml
packet_id: Q001
revision: 1
data_contract_ref: Google XLSX four authorized sheets; DuckDB native read_xlsx original URL only
business_goal: 查明法币与链上交易的已完成交易量由哪些资产和客户贡献，从而判断是否有必要继续调查集中度来源
question: 按交易轨道和资产分别看，已完成交易有多少笔、多少 UID、金额多少，以及 Top1 用户在同单位金额中的占比？
decision_branches: 某个轨道×资产用户贡献高度集中且样本足够时深入交易频次与单笔金额；若分散或样本极少则不强行作风险判断
result_grain: rail × asset; 中间计算为 rail × asset × uid
result_columns: [rail, asset, completed_orders, active_users, native_total, top1_native_total, top1_share_pct]
population_and_filters: status=completed 是待核实业务状态，不等于 settled；使用全部数据实际覆盖时间，不预设年份
metric_units_and_logic: 原生资产单位分别 SUM，Top1 比例分子分母限相同 rail × asset；不跨币种加总
source_candidates: fiat_transactions(uid, currency, status, amount); crypto_transactions(uid, asset, status, amount); users, exchange_rates 仅作独立质量与汇率语义检查；字段待本轮验证
join_plan: 两条流水 UNION ALL 并带 rail+asset；不直接按 uid 互相 JOIN；以原子交易表→uid层聚合→asset层聚合
candidate_sql_or_probe: workflow 内双 Skill Q001 查询；必须复核字段后在同次原始 DuckDB 会话执行
hypotheses_and_falsifier: 可能的 Top1 集中来自大额单笔、也可能来自高频；若因状态、NULL、重复 ID、样本量或计量不一致导致分母无效则撤回集中结论
evidence_status: UNVERIFIED
```

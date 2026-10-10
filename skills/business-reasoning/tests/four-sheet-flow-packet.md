# A-FLOW-001 / Business Reasoning 分析交接

1. 结果表先行：每行代表 rail × asset；列为已完成入出笔数、原生入出金额、净流量、非完成提币笔数。
2. 数据依赖：fiat_transactions 与 crypto_transactions 各为订单明细；先保留 rail/asset 标记并 UNION ALL，不允许按 UID 直接 JOIN 两条流水；users 用于核对 UID，exchange_rates 不作为历史成交估值。
3. 过滤与条件：status=completed 的 deposit/withdrawal 分别计入已完成入、出金；其他状态只作订单状态统计。实际业务完成语义保持未确认。
4. 反证：必须检查异常 direction、重复订单、创建/完成时间、跨币种加总、未完成状态解释、数据时间边界。
5. 第二问由真实结果触发：只对出现负净额且有足够记录的轨道×资产，再评估用户集中性与大单影响；若当前数据不能支持业务实时决策，则停止。

packet_id: A-FLOW-001
revision: 1
data_contract_ref: original XLSX URL; four authorized sheets; DuckDB native read_xlsx; single materialization
business_goal: 历史资金结构诊断与实时监测数据缺口评估
question: 轨道×币种层面完成状态的入、出与净流量以及非完成提币有何结构？
result_grain: rail × asset
source_candidates: fiat_transactions, crypto_transactions; users and exchange_rates only for quality
candidate_sql_or_probe: skills/analysis-verifier/tests/three-role-four-sheet-flow.sql
evidence_status: UNVERIFIED

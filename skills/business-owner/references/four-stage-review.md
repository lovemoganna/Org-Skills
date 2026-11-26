# Carmen SQL Business Thinking · 四阶段分析及 Review 合同
版本：2026-10-11 · 不新增角色，不硬编码示例答案。

## 根本区分：三角色 ≠ 三阶段
- **S1 下达任务** / business-owner：决定为什么查、谁决策、何时决策、报告需回答什么；产出 `TaskBrief`。
- **S2 基础梳理** / business-reasoning：**先想最终要什么结果表、一行代表谁**，再反推哪个表、取什么、筛什么、怎么 JOIN/聚合；产出 `ResultSpec` 与 `SourceMap`。此时不展示分析结论。
- **S3 基础校验** / analysis-verifier：在用户授权的真实数据/引擎上执行且锁定源版本，校验 schema、键、粒度、字段取值、状态、时间、单位、金额与连接基数，列出可计算范围；产出 `QAReceipt`，状态 `PASS / PARTIAL / BLOCKED`。此时不生成业务报告。
- **S4 形成分析** / business-reasoning + analysis-verifier：分析师围绕通过的字段与指标主动发现、深入解释、提出竞争假设及 SQL；验证师逐项独立反证，分析师吸收反馈后**编写可读的管理层分析报告**；产出 `DecisionReport`。老板只在这时收到分析报告并验收，不能参与每条 SQL 的往返。

## Carmen 逻辑在 S2 的固定顺序
```text
业务问题 → 想象目标结果表（需要哪些列）
→ 一行是谁（UID / UID×币种 / 订单 / 日期等）
→ 数据在哪里（FROM / JOIN，要保留谁）
→ 取什么（SELECT / CASE / SUM / COUNT）
→ 筛什么（WHERE / 时间、状态、币种）
→ 怎么聚合（GROUP BY / 防重复）
→ 候选 SQL 与未知项
```
这不是必须一行 UID 的通用规定。Carmen 的 2025 年“每个客户出入金”案例选择 UID 行粒度；其他业务对象按题目决定。不能按 UID JOIN 两张多行流水后直接 SUM。

## Review 合同（每道产物独立可审）
| Stage | 审查者 | 可以审什么 | 不可以偷跑什么 | 交付物 |
|---|---|---|---|---|
| S1 | 业务负责人/需求方 | 问题、决策、边界、优先级 | 先写 KPI/SQL | TaskBrief |
| S2 | 分析师、复核者 | 结果表、行粒度、表字段映射、筛选口径、未知项 | 用虚构列/结果填表；写管理结论 | ResultSpec + SourceMap |
| S3 | 独立验证者 | 真实运行记录、原始Schema、取值、键/空值/孤儿、JOIN、金额/币种、时间、数据源访问纪律 | 从 QA 直接宣布经营风险结论 | QAReceipt |
| S4 | 分析师及结论独立验证者；最终老板只看报告 | 是否回答需求、证据到结论的链条、竞争解释、行动与边界 | 将 Stage3 PASS 自动升级为 Finding PASS | DecisionReport |

## 强制数据权限及执行门禁
- 原始数据源和白名单、引擎、SQL 模板、是否允许其他表、来源版本由 TaskBrief 锁定。不得使用禁用的 expected/dashboard/qa/backup 表查询任何字段、口径或答案。
- S3 的 `QAReceipt` 必须对 S4 的每个数据依赖给出状态与真实执行证据（SQL、运行位置、源身份、行数、字段状态、关键错误）。
- `S3=BLOCKED` 时 S4 不得产生基于该数据的 Finding；可以交付“阻塞型分析报告”，说明已验证事实、缺口、影响和下一步。
- `S3=PARTIAL` 时只分析明确通过的那一部分；每个指标须标明受影响范围和未验证项。
- `S3=PASS` 只证明基础数据可用，不证明 S4 的 SQL、因果解释或行动判断通过。
- S4 每条主要发现须挂真实 Result、口径、证据级别和独立 `FindingVerdict`；反证后修订同一发现版本，不凭增加轮数显得深入。
- 老板**只接收 S4 完整报告**（可展开证据附录），不审核 Analysis Packet 或原始 SQL。老板可以退回一个影响决策的缺口，但不得要求无信息增量的轮数。
- 在输出 Stage4 报告前先出 executive conclusion（事实 → 原因/竞争解释 → 影响 → 行动）；SQL、QA 详表放附录，不让执行日志抢管理报告首屏。

## 独立验收新增：S3/S4 证据范围一致性

S3 对某个字段、币种或时间段的 `PARTIAL/PASS` 不是整份 S4 报告的通行证。B 必须先用 `skills/analysis-verifier/scripts/scope_gate.py` 检查每条关键 Finding 是否在同一运行与物化数据范围内；缺完整来源凭据、结果回执、独立反馈或范围交集时为 `BLOCKED`。Owner 只能把门禁 `PASS` 且业务证据充分的结论写作「已验证」，否则向决策方报告缺口。门禁不替代 S4 实际独立 SQL 与语义反证。

## 固定四种结构化产物
```text
S1 TaskBrief:
  task_id; business_decision; question; audience; time_window;
  data_permissions; urgency; acceptance; unknowns

S2 ResultSpec:
  task_id; target_table; output_columns; one_row_represents;
  source_map[{source_table, actual_or_unknown_fields, select, filters, join_cardinality}];
  metric_definitions; sql_candidate_or_probe; unresolved_fields

S3 QAReceipt:
  task_id; source_identity; engine; source_revision; executed_queries;
  schema_and_grain; field_values_and_units; data_quality_checks;
  validated_metric_scope; blockers; verdict=PASS|PARTIAL|BLOCKED

S4 DecisionReport:
  task_id; headline; executive_summary; key_findings[
    {claim, quantitative_evidence, competing_explanation, finding_verdict, business_implication}
  ]; decisions_and_actions; uncertainty_and_data_gaps;
  evidence_refs; reviewed_by_owner; owner_decision
```

## 适用于固定四表真实回归
数据源：用户给定的 Google Sheets 原始 XLSX URL，白名单严格为 `users`、`fiat_transactions`、`crypto_transactions`、`exchange_rates`。使用 DuckDB `read_xlsx`；初始化每扩展一次、每表读取并物化一次。基线测量与业务分析都**只能**复用已经物化的数据；不得偷偷再次调用 `read_xlsx`。先 S2 结果定义，再 S3 查看真实结构，后 S4 分析。

历史示例（不作为本轮新执行的证据）：详见 `../tests/four-stage-replay.md`。

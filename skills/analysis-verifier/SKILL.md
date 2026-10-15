---
name: analysis-verifier
description: 对 business-reasoning 的 Analysis Packet 独立复核语义、数据权限、粒度、SQL 与真实执行结果；使用反例、对账和稳健性测试生成带证据的 Verification Feedback，反哺上游分析。只验证，不选题、不写 Dashboard。
---
# Analysis Verifier · 独立验证

**唯一职责：检验一个明确声明能否成立，并给分析端提供足以改变下一轮判断的证据。** 不代替 A 提出业务分析路线；不因 SQL 成功运行就宣称业务判断正确。

## 输入与独立性
必需：A 的 Analysis Packet（含 packet_id、revision）、用户原始不可变 Data Contract、可用数据/运行时。只依赖候选的声明、SQL 和原始证据，不继承 A 的预期数字或未证实解释。建议在独立上下文执行 B；同一模型模拟 A/B 不得称为独立智能体测试。

## 真实数据读取边界
- 严格遵守授权源、Sheet 白名单/黑名单、指定引擎、固定 SQL、允许替换的参数与写权限。禁止读取禁用 Sheet 内容、字段、规则、expected/QA/备份。
- 用户锁定 DuckDB `read_xlsx` 和原始 XLSX URL 时不能换用 CSV、Pandas、Connector、其他 SQL 函数或本地 VFS 映射冒充原样执行。
- 按用户要求 `INSTALL/LOAD` 只执行一次，四个授权表在同一会话分别 `read_xlsx` 一次并物化一次；后续分析只查物化表。
- 若当前运行位置失败，可尝试已有且获授权的**等价 DuckDB 运行时**。不曾实际执行就不得称为 PASS；缺能力返回 BLOCKED 与恢复条件。
- 每轮运行记录数据源、SQL、数据/结果版本、运行时间、执行环境、错误或结果；历史 Result 只能标历史参考，不能冒充本轮新证据。

## 两种不同的验证任务，绝不混淆
参照 `../business-owner/references/four-stage-review.md`，同一验证师承担**两个不同工作节点**，但只在各自阶段交付对应产物：
- **S3 基础校验**（输入 S2 的 `ResultSpec + SourceMap`）：真实检查表的行粒度、列和类型、候选键/外键、JOIN 基数、NULL/重复、币种单位、交易方向、时间/状态、指标计算先决条件。只输出 `QAReceipt` 和受约束的可分析范围，结论 `PASS / PARTIAL / BLOCKED`；**不写 Finding，不解释经营风险**。
- **S4 结论独立验证**（输入 A 提出的具体 `Finding` 与 SQL）：逐条验证实测值、竞争解释、稳健性、计算及语义，输出原 `Verification Feedback` / `FindingVerdict`。**S3 PASS 绝不意味着 S4 Finding 已验证**。验证完成反馈给 A，由 A 撰写管理报告，老板不需要审 SQL。

### S3 QAReceipt（只记录基础证据）
```yaml
task_id: B001
source_identity: exact_authorized_source
source_revision: actual_or_unknown
engine_and_execution: actual_runtime_and_SQL_receipt
schema_and_grain: source_tables_fields_rows_and_keys
field_values_and_units: status_direction_asset_time_amount_semantics
data_quality_checks: keys_null_orphan_join_time_units_and_reconciliation
validated_metric_scope: metrics_which_can_be_calculated_without_invented_semantics
blockers: unresolved_dependencies
verdict: PASS | PARTIAL | BLOCKED
```
依赖型 FAIL/BLOCKED 必须拦住相关 S4 分析。S3 `PARTIAL` 可让已通过的独立数据范围继续，但不可把未测部分写成通过。

## 每轮验证程序
1. **输入检查**：Packet 与 Data Contract 一致，未越权、无未知值被当事实、问题结果能够改变一个明确判断。
2. **业务语义**：区分输出列与过滤条件；核对主体、样本、粒度、状态/生命周期、金额计量单位、汇率时间意义和指标范围。入金-出金通常是净流量，不直接代表账户余额/留存。
3. **结构守恒**：查主键/空值/孤儿、左右表关联基数、JOIN 前后行数、先聚合再关联；核对重复计量、时间格式与状态取值。多币种不得裸 SUM；不同币种需要经授权的明确折算与估值标签。
4. **真实 SQL**：独立检查并实际执行候选或探查 SQL，必要时再用另一条查询复算关键数量/金额；不得引用被禁 Sheet 的预期答案。
5. **主动找反例**：否定性样本、NULL、重复键、对照状态、边界时间、小样本、TopN 是否全覆盖、去极值或换合法分母。区分事实、解释、因果推断。
6. **裁决范围**：VERIFIED（所述范围内证据充分）、REJECTED（实证或逻辑反证）、UNRESOLVED（证据不足）、BLOCKED（读取、权限、引擎或质量关键检查被阻断）。允许一部分事实 VERIFIED、整体解释 UNRESOLVED；不能由错误语义推出更强结论。

## 交接：Verification Feedback（全部字段必填）
```yaml
packet_id: Q001
revision: 1
verdict: VERIFIED | REJECTED | UNRESOLVED | BLOCKED
execution_receipt: "本轮真实执行环境、SQL、数据版本、结果或错误；无执行写 NONE"
validated_facts: "仅已证实、附适用边界"
counterevidence: "实际反例、逻辑反例或未知项"
root_cause: "问题定义/粒度/字段/Join/时间/口径/证据"
new_signal: "本轮真正新增的信息；没有写 NONE"
impact_on_decision: "原判断哪些成立、撤回、未定"
minimal_correction: "对 A 最小可执行修改指令"
next_test: "最小额外证据或 NONE"
```

## S3→S4 证据范围门禁（交接必检）

在宣称 S4 某条 Finding **已验证**前，用 `python3 skills/analysis-verifier/scripts/scope_gate.py qa.json finding.json` 独立检查交接证据。执行结果为 `PASS` 才能进入经验证的管理报告；`BLOCKED` 只能陈述缺口，不得将其改写为已确认结论。

- `qa.json` 须含 S3 `verdict`、`qa_receipt_ref`、`checked_scopes`；每个已检查范围明确 `grain`（行粒度）、`population`（主体及过滤范围）、`time_window`、`status_meaning`（状态语义）和 `metrics`。
- `finding.json` 须含 S4 独立验证结果 `verdict=VERIFIED`、`packet_id/revision` 与 `verified_packet_id/verified_revision`、`scope`、`result_receipt_ref` 和 `verification_receipt_ref`。
- 双方须具有**同一已锁定物化会话**的 `run_id/source_id/materialization_id/read_plan_sha256`；这里的 `read_plan_sha256` 是读取方案哈希，**不是原始文件字节或数据快照的哈希**。不允许跨运行把历史反馈移植到新结果上；若原始文件会在同一任务内重新读取，必须另建数据版本证据。
- `S3=PARTIAL` 时只准使用已检查的范围；每条 Finding 的范围四字段必须完整精确匹配同一条 `checked_scopes` 记录，指标集合只能是其子集。未知、空凭据、状态偷换、跨币种、跨时段、错版反馈均判 `BLOCKED`。这是**证据覆盖门禁**，并不能单独证明数据真假或业务因果。

执行器是独立可调用的保守校验器；既有历史报告缺这些凭据时标「未完成本门禁」，不得追认 PASS。对照与反例：`tests/check_repo.py`。

## 反馈是唯一出口
反馈必须绑定本轮实际执行的 packet_id 和 revision，写明证据、失败原因、最小修正及新信号；反馈给分析端后停止。验证端不能直接生成下一轮分析议题。

## 停止与排除
每个 Packet 只裁决当前 revision，交回 A；不擅自合成下一轮业务问题，不替 A 写 Final Finding，不生成报告 UI，不维护原 D01–D23 或 HTML 验收门禁。遇到无法验证的项输出 BLOCKED/UNRESOLVED，绝不自报 PASS。

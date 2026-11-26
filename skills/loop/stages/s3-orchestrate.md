# S3 · Orchestrate

S3 唯一负责执行阶段的 direct/chain 决策、跨步骤顺序、分支和失败路由。

## 复杂度门槛

默认 `direct`。以下满足 ≥2 项才为 `chain`：
1. ≥3 个子任务并存在数据依赖；
2. 中间结果需要独立验证，否则会污染后续；
3. 不同环节需要不同角色、视角或工具；
4. 单轮产出超出稳定上下文范围；
5. 生成和评审必须隔离。

`reason` 写明命中的编号；不足两项不得仅为“严谨”建链。

## direct

产物 ChainSpec：`mode: direct`、`reason`、`coverage`。coverage 显式写出 TaskSpec 每项验收由哪项执行活动及哪项复测覆盖；失败不得静默略过。

## chain

从 `registry.md` 选择能匹配能力的原子提示；仅 `draft` 模块可试用但需要单独检查，没有现成模块时才最小新增。每 step 有 `id / atom / input_from / output_name / check / on_fail`；有分支才写 `when`。
- `input_from` 只能指明示的输入字段或前序产物；
- `check` 验证本步交接契约；
- `on_fail` 只能使用 retry(n)、fallback(atom) 或 stop；
- 默认链长 ≤6。不可将顺序/条件/重试藏在原子提示内容里。

不得生成“虚构独立验证者”来充数，也不把阶段内 S1/S2 辅助原子记为任务执行链。
产物：`templates/chain-spec.md`，验收覆盖完整。

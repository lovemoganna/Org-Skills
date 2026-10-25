# S2 · Model

以 IntentCard 建立 TaskSpec，保留必要条件到后续阶段。

1. 逐条推导真正达成 goal 所必需的 `necessary_conditions`；区分用户已授权条件与待确认假设。
2. 形成问题句：“在[约束]下交付[产物]，使得[可观察的用户结果]”。
3. 指定 scope.in 与 scope.out，防止功能蔓延。
4. 按**产出物**作 MECE 子任务拆解（可用 `atoms/decompose-mece.md`），输出子任务和必要条件覆盖矩阵；未覆盖不得通过。
5. 标注输入和依赖 `deps`；不要在此决定提示链的顺序、分支和重试。
6. 必要条件逐项转成 `acceptance`（可用 `atoms/write-acceptance.md`）：ID、对应 goal/条件、可观察状态、检查方式、证据来源。
7. 记录风险及早期信号。

注意：不能因为惯例或示例自动添加“3 个 KPI、3 种图表”等用户并未授权的验收。对于定性目标采用用户行为和可重现的检查路径；主观项目标为需独立评审。

产物：`templates/task-spec.md`；必须显式包含 `necessary_conditions`、`deps`。
检查：每项条件都有覆盖；子任务不共享同一产出；验收可实测而非仅描述执行动作。

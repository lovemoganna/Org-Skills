# S4 · Execute and Verify

按 ChainSpec 真正执行任务；保留需要复查的输出、测试命令、代码变更、工具错误和环境状态。

验证三层：
1. **acceptance**：TaskSpec 每条验收单独标记 `通过 / 未通过 / 无法判定`，附具体文件位置、命令输出、数据或可重复操作。
2. **goal_check**：暂不看验收表，只用 IntentCard.goal/motive 与真实产出判断用户是否达到目的；全部验收通过但目标不成立时优先记 S2 假设缺陷。
3. **side_effects**：是否越权、损坏已有内容、绕过安全门禁或将推测冒充事实。

可调用 `atoms/verify-against-goal.md`，只交给验证者 intent、acceptance、output、constraints；验证者不能修改产出。

**独立性规则**：能使用隔离上下文的独立执行者时记录验证者和输入；若只有同一执行者，就标 `independence: self-check only`，不得声称独立验收，更不能由自评晋升 verified。工具/运行环境不可用时必须用“无法判定”。

产物：`templates/run-report.md`。verdict 为 `达成 / 部分达成 / 未达成`；不得把“写出了文件”当作成果证据。

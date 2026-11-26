# 动作前检查数据契约

`python skills/decision-first-agent/scripts/decision_gate.py case.json`。退出码 `0` 表示规则允许继续（并非授予权限），`2` 表示需要确认、选择、暂停或输入无效。读取时从仓库根目录执行。

```json
{
  "task_id": "task-001",
  "phase": 1,
  "operation": "read",
  "resource": "repo/readme",
  "impact": "low",
  "cost": "none",
  "reversible": true,
  "rollback_ready": true,
  "authority": {"operations": ["read"], "resources": ["repo/readme"]},
  "critical_unknowns": [],
  "contradictions": [],
  "risk_flags": [],
  "needs_choice": false
}
```

枚举：`operation` 只能为 `read`、`write`、`delete`、`publish`、`transfer`、`external`。`impact` 为 `low`、`medium`、`high`、`global`。`cost` 为 `none`、`bounded`、`unbounded`。`risk_flags` 可以包含 `destructive`、`regulated`、`financial`、`privacy`、`irreversible`、`high_impact`。权限资源必须精确匹配，不支持隐式通配符。任何未知枚举、缺少字段或类型异常均暂停。

如果 `needs_choice=true`，由 AI 填写 `choices`（2～3 个唯一文本值）和 `recommendation`（必须是其中之一）；四选项和缺少建议均拒绝。若触发 L3，可提供如下格式的 `approval`，但 **只允许可信调用方填入**：

```json
{"task_id": "task-001", "operation": "delete", "resource": "repo/readme", "verified": true}
```

`verified` 是调用方对来源核验的声明，**不是**脚本可以验证的签名或凭据；被污染的调用方可以伪造它。因此生产环境必须使用独立的宿主权限门禁，不可把此检查器当作安全边界。

原则记录最小字段：`id`、`statement`、`source`、`confirmed_at`、`scope`、`status`。先例最小字段：`id`、`task_type`、`decision`、`reason`、`scope`、`status`。授权最小字段：`id`、`operations`、`resources`、`source`、`validity`、`revoked`。不允许在缺少可信存储接口时声称这些记录已持久化。

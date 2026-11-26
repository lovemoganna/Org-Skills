# Changelog

## 2026-10-24 — Candidate import and contract QA

- 将上传的 Loop 原型作为独立的“意图 → 任务 → 最小编排”Skill 导入，与现有 `loop-engineering-meta` 的故障复盘定位区分。
- 修复 S1/S2 局部辅助原子与 S3 路由职责冲突。
- 在 TaskSpec 加入 necessary_conditions 和 deps，保证原子输入与跨阶段交接一致。
- 明确 direct coverage、真实执行证据、独立评审不可用时不得自称独立。
- 保留五阶段、五原子提示和五模板，增加静态契约检查与 G1–G10 行为回归清单。
- 当前状态：candidate / draft；**未执行跨模型多次对照**，不能声称验证了稳定的用户场景增益。

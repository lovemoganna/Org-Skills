---
name: crypto-linkedin-risk-supervisor
description: "用于 Crypto 风控 LinkedIn 双语情报定时任务的取证、去重、故障恢复、军团执行边界与≤3000字质量验收。保留原业务指令，仅在对应任务使用。"
---
# Crypto 风控 LinkedIn 军团监督 Skill
适用原始任务：现有“Crypto 风控 LinkedIn 双语选题”定时任务。不得新建、改时、自动发布。按原任务 A–E 和五条独立发现路径、三级证据、正式来源、历史去重与中英等义产稿标准执行。

**执行手册与真实回归正例：** [LINKEDIN-RISK-SUPERVISOR.md](../loop/router_v2/LINKEDIN-RISK-SUPERVISOR.md)。正式运行时以真实可访问的受信版本为准；未合并的候选分支不能冒充生产 Skill 已部署。

**运行范围：** 只有活跃 Work 宿主真实支持可信 checkout、私有 session、模型事件交接、连接器及独立验收，才调用同版本 `skills/loop/router_v2/work_legion.js`；否则使用宿主现有工具降级执行。输出真实业务成果，不输出军团演示或泛化过程汇报。任何“无稿”先诊断并尝试可行替代路径，确认真实无价值新增可拒稿，但禁止虚构。最终稿含一手完整 URLs、实测≤3000字符，只交付最多一篇双语人工审核稿，绝不发布。

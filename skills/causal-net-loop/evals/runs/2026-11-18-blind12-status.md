# Causal Net Loop｜12 例独立 A/B 项目执行状态（2026-11-18）

## 已完成且可验证

| 检查 | 状态 | 证据 |
| --- | --- | --- |
| 冻结旧版 Skill | PASS | Blob `893b581a23fc2474d6d4fad761ecb4d2965c163c` |
| 冻结 Candidate V2 | PASS | Blob `57581f87ba669cffe1900ad0b199a9fd24b0e6f6` |
| 冻结 12 个新任务 | PASS | `../blind12-2026-11-18.json` Blob `d4ec6a9972a922968127b5fbb6d1d327f3cd1089` |
| 预注册评分、关键错误、晋升条件 | PASS | 同一 JSON，全部在生成模型输出前提交 |
| 实际生成 24 个单题 Prompt | PASS | GitHub Actions `44272971229` |
| 将 24 Prompt 打包归档 | PASS | Artifacts `causal-net-loop-blind12-fixed-prompts`；artifact ID `14413022887`（30天保留） |
| 运行无 API 的冻结版检验与 Prompt 生成 | PASS | [Causal Net Loop Contract](https://github.com/lovemoganna/Org-Skills/actions/runs/44272971229) |
| 仓库既有 Regression | PASS | [Skills Regression](https://github.com/lovemoganna/Org-Skills/actions/runs/44272971420) |
| 无 API 独立运行、核验、随机盲评、解盲评分程序 | READY | `../blind12.py`；操作说明 `../BLIND12-RUNBOOK.md` |

## 未完成的必要条件（不能伪造）

- `0/24`：24 个真实独立 ChatGPT GPT-6 模型会话的原始回答/执行记录。**NOT_VERIFIED**。
- `0/24`：独立评分人不知道版本映射时对每条答复所做的评分。**NOT_VERIFIED**。
- 因为上述结果尚不存在，无法计算真实成对胜负、平均得分增量、模型重跑方差、token/延迟成本或生产效果。**NOT_VERIFIED**。
- 当前 GitHub 连接器与本 ChatGPT 对话没有启动 24 个隔离 GPT-6 对话的能力；原仓库另有 Copilot CLI 工作流，但那是不同模型/授权/运行条件，违反本次“当前 GPT-6、不使用模型 API”的约束，因此**没有将 Copilot 输出冒充 GPT-6**。
- 本轮新数据集可以在独立新会话中执行；由于任务创作者当前会话已见到题目，它**不是对当前会话的秘密 blind holdout**。它在冻结版本之后创建且不用于再次改写 Skill，避免因先看题目优化而产生明显泄漏。

## 结论

**评测体系与测试任务已实际落库、CI 通过；行为 A/B 尚未真实发生。**

不得把 `PASS: 24 fixed prompts` 写成 `PASS: 24 model runs`，不得给出假的质量胜率，PR #115 保持 Draft，不合并 main。

若获得独立会话产物，可直接把24个输出以 `../BLIND12-RUNBOOK.md` 指定格式提交，用 `blind12.py verify → blind → score` 得到可复算、但仍需人工审核的结果。

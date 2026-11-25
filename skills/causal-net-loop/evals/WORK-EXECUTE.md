# Work 一键执行单｜Causal Net Loop PR #115

> 任务：**完成一次真正的双臂、盲评、可复算的 Skill A/B；不要再只生成工作流文档。** 当前 Chat 对话不能直接切换 Work；此文件作为 Work 的唯一交接入口。

## 成功终点

在 GitHub `lovemoganna/Org-Skills` 的 PR #115 候选分支上，完成独立执行、证据归档、匿名评分、复算和晋升判断，提交结果到**同一个 PR 分支**；不得合并 main，除非证据达标且获得用户后续明确批准。输出一份简短结论：实测轮次、数据质量、胜负、关键错误、成本、是否建议晋升及证据链接。

## 冻结数据，不要重写测试题或 Skill

- Baseline `SKILL.md` blob：`893b581a23fc2474d6d4fad761ecb4d2965c163c`
- Candidate V2 `SKILL.md` blob：`57581f87ba669cffe1900ad0b199a9fd24b0e6f6`
- 12案例：`skills/causal-net-loop/evals/blind12-2026-11-18.json`，blob `d4ec6a9972a922968127b5fbb6d1d327f3cd1089`
- 工具：`skills/causal-net-loop/evals/blind12.py`
- 评分标准、硬失败、一票否决、晋升门槛：以上 JSON 已事前固定，不要在看到测试结果后调整。

## 执行，减少不必要的 24 次对话负担

1. 在 Work 里连接现有 GitHub，拉取 PR #115 候选分支。运行 `python skills/causal-net-loop/evals/blind12.py check` 校验冻结版本；如不匹配，停止，不擅自替换版本。
2. 选择 Work 中**同一个实际可用且能确定模型标识的 GPT-6 系列模型**（可为 Astra 或 Sol），两臂固定一致。不是原 Chat GPT-6 Instant 时在报告里写清模型不同；不得宣称模型等价。不使用 OpenAI API，也不使用其他商业 CLI 模型冒充 ChatGPT。
3. 用 Work Subagents（若当前账户支持）创建**两个分离的执行线程**：
   - 基线执行者：只给 Baseline 完整 Skill 和每题输入，顺序执行 N01–N12；看不到 Candidate Skill、对照输出、预注册评分答案。
   - 候选执行者：只给 Candidate V2 完整 Skill 和相同 N01–N12 输入；看不到 Baseline Skill、对照输出、预注册评分答案。
   - **不需要 24 个独立 ChatGPT 会话**：每个执行者一个独立子线程，分别回答 12 题；每题保存原始完整回答。禁止外部搜索、插件、文档外材料；保持两臂相同任务顺序、模型、推理设置与工具环境。
4. 将真实模型输出按 `BLIND12-RUNBOOK.md` 的每题 JSON 格式写到 `/tmp/causal-blind12-outputs/{baseline|candidate}/N01.json … N12.json`。允许同一个执行者线程的 12 题共用真实 `session_id`，**两臂 `session_id` 和 `runner_id` 必须不同**。留存真实模型、推理配置、线程 ID / trace，无法取得的字段标 `NOT_VERIFIED`，不能填虚构标识以通过脚本。
5. 运行：
   ```bash
   python skills/causal-net-loop/evals/blind12.py verify --source /tmp/causal-blind12-outputs
   python skills/causal-net-loop/evals/blind12.py blind --source /tmp/causal-blind12-outputs --reviewer-dir /tmp/causal-blind12-reviewer --key-dir /tmp/causal-blind12-secret-key
   ```
6. 派另一个**未参加任何一臂生成的独立评审子代理**，只提供 `/tmp/causal-blind12-reviewer/review.json` 与 `score-template.json`，不提供版本映射 `key.json`。评分时引用具体原文和对应证据，填写五项 0–2 分、硬失败和负例判据，锁定 `locked-scores.json`。这属于**独立模型盲评，不是人工盲评**；如果没有独立子代理能力则如实标 `NOT_VERIFIED`，不得伪装。
7. 锁分后由主代理解盲：
   ```bash
   python skills/causal-net-loop/evals/blind12.py score --source /tmp/causal-blind12-outputs --review /tmp/causal-blind12-reviewer/locked-scores.json --key /tmp/causal-blind12-secret-key/key.json --out /tmp/causal-blind12-result.json
   ```
8. 保存：24个逐字原始输出、实际模型与两臂线程证据、盲评包、锁定评分、解盲密钥和最终复算结果到 GitHub 候选分支 `skills/causal-net-loop/evals/runs/work-2026-11-18/`（原始线程证明含私密信息则只存可公开的脱敏验证摘要）。**不可提交伪造的原始轨迹**。在 PR #115 描述中更新真实结果与结论，检查 CI，main 保持不变。
9. 最终报告只回答：Candidate 在十个复杂任务中胜几场、输几场、分差/成本、有无关键错误、负例是否退化、独立性证据、是否满足预定门槛。满足门槛也只可建议晋升，**不得自动合并**。

## 遇到能力限制时

- 若 Work 无法真正创建互不共享上下文的子代理：先完成有证据的实际运行并说明隔离程度；禁止声称严格 A/B。
- 若 Work 不允许取得可核验的模型输出/线程记录：不要为了通过 `verify` 伪造记录；最终输出具体阻塞点。
- 不要再次建立一套重复的 Registry、空模板或规划文档。这份任务的关键成功标准是**真实模型产物 + 独立盲评 + 可复算结论**。

## 最小启动指令

**读取本文件，直接执行 PR #115 的 12 题两臂隔离 A/B，保存原始输出、第三方模型盲评及结果到候选分支；不得使用 API，不得修改冻结版本，不得合并 main。不需要我逐条确认非破坏性步骤。**

# failure-repair-v1｜失败任务动态 Skill 链（实验，不替代正式 Skill）

**决策：Candidate / NOT_VERIFIED_FOR_LIVE_BEHAVIOR，不升级任何正式 Skill。** 本目录是一份可执行的路由与证据契约，不是模型执行器，也不是新的通用 Skill。

## 职责与边界

使用 `skills/loop/stages/s3-orchestrate.md` 的 `ChainSpec` 规则和 `skills/loop/stages/s4-verify.md` 的目标/结果验收。具体调用：

- `loop-engineering-meta`：读取原始失败轨迹，定位最早的事实缺口/执行缺陷，检查执行器和权限；先核对已知根因。
- `causal-net-loop`：只有竞争原因尚未排除且会改变行动时调用；输出假设、反证与最小干预。
- `keypoint-loop`：必要时先选**候选**突破点；只有完成真实执行和结果边界核验，才形成已验证经验卡。
- 执行、独立核验依赖现有真实工具/环境。缺少时必须 `BLOCKED`，不得用计划、模拟、CI 结构测试冒充实际任务结果。

**路由规则**：先识别用户目标与历史证据，再读取**当前运行条件的外部观察**。复杂度信号少于 2 项走 `direct`，其余走 `chain`；历史修复且没有新增失败证据时，先核对已有完成回执，不重复打开旧任务。运行条件未确认返回 `NEEDS_RUNTIME_CAPABILITY_EVIDENCE`，不得推定“没有执行器”；只有提供来源的不可用观察才能返回 `BLOCKED_EXECUTOR_REPORTED_UNAVAILABLE`。原因尚未诊断时停止在诊断阶段；有证据的竞争原因才调用因果 Skill。每条执行链最多六步。

## 运行命令（不使用 API）

```bash
python3 skills/loop/evals/failure-repair-v1/route.py --self-test
python3 skills/loop/evals/failure-repair-v1/route.py --cases skills/loop/evals/failure-repair-v1/cases.json
```

`route.py` 只生成**基于外部观察字段的** ChainSpec 路由预览，并进行确定性契约测试。它不能从自然语言自主判断执行器是否存在，也不会自动认证 GitHub URL 的证据真伪；它不调用语言模型、不执行真实任务，也不会完成真实 A/B。`verify_run` 只检查回执字段完整性，不认证外部实际行为。

## 三个真实历史案例

| ID | 历史可核证事实 | 本次路由 | 本次真实执行 |
|---|---|---|---|
| ML-001 | AgentComponent 的 `lifecycle.py` 只安排探测计划，不调用模型 | 需确认**当前执行条件**，不能从旧代码推断当前工具不可用 | 没有新运行结果 |
| AB-002 | AgentComponent PR #6 有预注册，但无独立成对运行证据 | 需查证本次独立执行及评审能力，不等于永远不存在执行器 | 没有新运行结果 |
| HTML-003 | Org-Skills PR #73 初版缺文件，后续修复且有 GitHub CI | **先核查历史完成证据**；无新失败不重复执行四步修复链 | 本轮未对 HTML 重新测试 |

源证据见 `cases.json` 的 `evidence_urls`。另一个独立事实是：Org-Skills PR #115 随后已经完成 Work 双臂盲评，但 Candidate V2 未过晋升门槛（第二轮 2 胜、2 负、6 平），不能把“PR #6 的 MetaLoop 未测”误写成“所有因果 Skill 都没实测”。证据：https://github.com/lovemoganna/Org-Skills/pull/115 。

## 比较方案：单 Skill / 固定串行 / 动态路由

同一冻结用例、相同输入和执行权限、同一质量标准，保留三个方案的真实轨迹、产物与独立核验：

1. 单 Skill：只用 `loop-engineering-meta`，按其原职责诊断、修复、回归。
2. 固定串行：`loop-engineering-meta` → `causal-net-loop` → `keypoint-loop` → 实际执行 → 独立验收 → `keypoint-loop`。
3. 动态路由：执行 `route.py` 给出的 ChainSpec，已知能力阻塞及时停止，已知根因跳过无信息增量的因果环节。

**三臂行为评测：NOT_RUN。** 本轮没有三个相互独立的模型执行者和真实端到端环境，因此不生成“成功率”“节省 token”“任务完成率”或模型比较分数。修复后，三组历史案例分别规划 1、1、1 个步骤，其中 HTML-003 只是历史证据复查。该数字只是**静态计划长度**，不能等同真实执行、耗时或节约。

后续真实对照必须记录：冻结输入与三个 Skill Blob SHA、模型/线程及权限、逐步输入输出、真实外部动作的回执、独立核验人与核验规则、失败/阻塞及副作用、运行时长与工具调用次数。失败样本、历史通过样本和新增泛化样本都要运行；同一执行者自评不算独立验证。

## 验收与停止

- 门禁：必须有真实产物和证据；`PLANNED_NOT_RUN` 与 `BLOCKED` 一律不得计为完成。
- 允许缺工具时给出可复现阻塞报告；禁止伪造执行者、模型版本、A/B 输出或独立评审。
- 若连续尝试无新证据，停止循环；先解决工具/权限/执行能力，而非扩大 Skill 链。
- 本次只增补 `skills/loop/evals/failure-repair-v1/`，原 `loop`、`causal-net-loop`、`keypoint-loop`、`loop-engineering-meta` 均保持不变。
- 正式版升级条件：真实任务至少两项具有可追溯的独立验收且无关键回归。自测、路由预览、历史报告复述不得计入。

**回滚**：关闭此实验 PR 或删除该目录；不涉及 main 的既有 Skill 内容。

## 2026-11-20 最小修复：从预设布尔值改成证据状态

首次审核发现旧版使用 `executor_available: false/true` 与 `causal_ambiguity: false/true`，这两个值是手工预设，不是动态检测结果。特别是把历史 `PLANNED_NOT_RUN` 直接推断为本轮“执行器不存在”，逻辑上不成立；历史已修复任务还会无条件生成四阶段重做计划。

现在以 `executor_state = unknown | reported_available | reported_unavailable`、`causal_state = unassessed | settled | contested`、来源 URL，以及 `closure_evidence_url`、`reopen_evidence_url` 分别记录。没有当前来源时保持 `unknown`；历史已闭环且未出现新故障，返回 `HISTORICAL_CLOSURE_FOR_REVIEW` 而非新建执行任务。所有 URL 仅是供人复查的索引，非程序真实性认证。

新的回归用例覆盖：历史任务不等于当前能力缺失、重开必须有新证据、已知根因跳过不必要的因果环节、未诊断不能直达执行、单步骤直达、缺证据拒绝、回执自报不算独立核验。**CI 仅证明代码在冻结案例上按规则输出，不代表 Skill 使用效果优于其他方法。**

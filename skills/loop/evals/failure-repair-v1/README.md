# failure-repair-v1｜失败任务动态 Skill 链（实验，不替代正式 Skill）

**决策：Candidate / NOT_VERIFIED_FOR_LIVE_BEHAVIOR，不升级任何正式 Skill。** 本目录是一份可执行的路由与证据契约，不是模型执行器，也不是新的通用 Skill。

## 职责与边界

使用 `skills/loop/stages/s3-orchestrate.md` 的 `ChainSpec` 规则和 `skills/loop/stages/s4-verify.md` 的目标/结果验收。具体调用：

- `loop-engineering-meta`：读取原始失败轨迹，定位最早的事实缺口/执行缺陷，检查执行器和权限；先核对已知根因。
- `causal-net-loop`：只有竞争原因尚未排除且会改变行动时调用；输出假设、反证与最小干预。
- `keypoint-loop`：必要时先选**候选**突破点；只有完成真实执行和结果边界核验，才形成已验证经验卡。
- 执行、独立核验依赖现有真实工具/环境。缺少时必须 `BLOCKED`，不得用计划、模拟、CI 结构测试冒充实际任务结果。

**路由规则**：首先验证用户目标、失败证据、复杂度；复杂度信号少于 2 项走 `direct`；否则 `chain`。优先诊断最早失败和执行能力；没有执行器立刻停止。根因已知不再执行额外因果分析；仍有竞争因果才加入因果与候选突破点。默认最多六步，每步有输入、产出、检查和失败停止条件。

## 运行命令（不使用 API）

```bash
python3 skills/loop/evals/failure-repair-v1/route.py --self-test
python3 skills/loop/evals/failure-repair-v1/route.py --cases skills/loop/evals/failure-repair-v1/cases.json
```

`route.py` 只生成 ChainSpec 路由预览，并进行确定性契约测试。它不调用语言模型、不运行 GitHub Workflow、不改动任何被测仓库，也不会自行完成真实 A/B。`verify_run` 仅检查验收回执字段的完备性，不会认证回执真伪。

## 三个真实历史案例

| ID | 历史可核证事实 | 本次路由 | 本次真实执行 |
|---|---|---|---|
| ML-001 | AgentComponent 的 `lifecycle.py` 明确只安排探测计划，不调用模型；`PLANNED_NOT_RUN` 不能当完成 | `loop-engineering-meta` → BLOCKED（缺执行器） | 没有新运行结果 |
| AB-002 | AgentComponent PR #6 预注册了技术/非技术实验，明确无真实 A/B 输出 | `loop-engineering-meta` → BLOCKED（缺隔离执行/独立评审） | 没有新运行结果 |
| HTML-003 | Org-Skills PR #73 初版缺生成器/测试/契约；后续修复和 CI 留有记录 | `loop-engineering-meta` → 实际执行 → 独立验证 → `keypoint-loop` | 本轮只生成路由预览；历史修复有既有 CI，不属于新测 |

源证据见 `cases.json` 的 `evidence_urls`。另一个独立事实是：Org-Skills PR #115 随后已经完成 Work 双臂盲评，但 Candidate V2 未过晋升门槛（第二轮 2 胜、2 负、6 平），不能把“PR #6 的 MetaLoop 未测”误写成“所有因果 Skill 都没实测”。证据：https://github.com/lovemoganna/Org-Skills/pull/115 。

## 比较方案：单 Skill / 固定串行 / 动态路由

同一冻结用例、相同输入和执行权限、同一质量标准，保留三个方案的真实轨迹、产物与独立核验：

1. 单 Skill：只用 `loop-engineering-meta`，按其原职责诊断、修复、回归。
2. 固定串行：`loop-engineering-meta` → `causal-net-loop` → `keypoint-loop` → 实际执行 → 独立验收 → `keypoint-loop`。
3. 动态路由：执行 `route.py` 给出的 ChainSpec，已知能力阻塞及时停止，已知根因跳过无信息增量的因果环节。

**三臂行为评测：NOT_RUN。** 本轮没有三个相互独立的模型执行者和真实端到端环境，因此不生成“成功率”“节省 token”“任务完成率”或模型比较分数。动态路由在三个案例中分别仅规划 1、1、4 个步骤，这只是静态节点数量，不能充当真实工具调用、运行时间或成本。

后续真实对照必须记录：冻结输入与三个 Skill Blob SHA、模型/线程及权限、逐步输入输出、真实外部动作的回执、独立核验人与核验规则、失败/阻塞及副作用、运行时长与工具调用次数。失败样本、历史通过样本和新增泛化样本都要运行；同一执行者自评不算独立验证。

## 验收与停止

- 门禁：必须有真实产物和证据；`PLANNED_NOT_RUN` 与 `BLOCKED` 一律不得计为完成。
- 允许缺工具时给出可复现阻塞报告；禁止伪造执行者、模型版本、A/B 输出或独立评审。
- 若连续尝试无新证据，停止循环；先解决工具/权限/执行能力，而非扩大 Skill 链。
- 本次只增补 `skills/loop/evals/failure-repair-v1/`，原 `loop`、`causal-net-loop`、`keypoint-loop`、`loop-engineering-meta` 均保持不变。
- 正式版升级条件：真实任务至少两项具有可追溯的独立验收且无关键回归。自测、路由预览、历史报告复述不得计入。

**回滚**：关闭此实验 PR 或删除该目录；不涉及 main 的既有 Skill 内容。
# Causal Net Loop｜12 个新案例的无 API 隔离 A/B 运行说明

## 已冻结版本

- 正式版（Baseline）Skill Blob：`893b581a23fc2474d6d4fad761ecb4d2965c163c`
- 增强版（Candidate V2）Skill Blob：`57581f87ba669cffe1900ad0b199a9fd24b0e6f6`
- 测试数据：`blind12-2026-11-18.json`，Blob `d4ec6a9972a922968127b5fbb6d1d327f3cd1089`
- 场景：N01–N04 风控；N05–N07 软件；N08–N10 公共政策；N11–N12 负例。
- 评分权重：因果机制30、关键约束/突破点25、事实与反证20、可执行验收15、简洁度10；关键虚构与无依据违法认定一票否决。全部见 JSON。
- **评测发生前冻结 Skill。测试结果不得反向修改本次 Candidate 再宣称同集 held-out。**

## 1. 准备单案例独立提示（本地，不调用任何模型）

在 PR 分支的完整 Git 仓库中：

```bash
python skills/causal-net-loop/evals/blind12.py check
python skills/causal-net-loop/evals/blind12.py prepare --out /tmp/causal-blind12-prompts
```

产生 24 份完整、可直接复制的单案例 Prompt（12 题 × 两版），**不包含标准答案或评分门槛**。每次使用全新的 ChatGPT GPT-6 对话独立执行一份提示；不要把两份版本放入同一对话或让模型看到另一臂输出。维持工具禁用或不调用、相同模型配置；不要使用模型 API。单轮多题、先看两版再回答或同一会话自评**不满足**本轮隔离验收。

当前连接器能提交 GitHub 和运行 GitHub CI，但**无法直接创建 24 个独立 ChatGPT GPT-6 会话并获取其独立 trace**；因此未获得真实执行记录时必须标记 `NOT_VERIFIED`，不能用人工编写或同一会话模拟输出来冒充。

## 2. 保存真实输出

每个运行保存一个 `JSON`，文件路径：
`/tmp/causal-blind12-outputs/{baseline|candidate}/N01.json` … `N12.json`。

每份结构示例（所有字段都必须由实际运行记录提供）：

```json
{
  "case_id": "N01",
  "skill_blob": "893b581a23fc2474d6d4fad761ecb4d2965c163c",
  "model": "GPT-6",
  "tools": "none",
  "session_id": "真实且唯一的会话标识",
  "runner_id": "执行者标识（不能与盲评人相同）",
  "response": "模型逐字原始输出",
  "evidence_ref": "可访问的真实会话记录或原始trace的标识"
}
```

Candidate 的 `skill_blob` 必须使用其冻结 SHA。不得杜撰 session ID、模型名称、运行耗时、token 消耗或 trace；`blind12.py` 仅能检查这些字段存在且符合格式，**不能验证自报身份或独立性**。不建议上传含个人隐私的会话链接，使用封闭合成测试内容。

检查 24 份：

```bash
python skills/causal-net-loop/evals/blind12.py verify --source /tmp/causal-blind12-outputs
```

## 3. 随机盲化

```bash
python skills/causal-net-loop/evals/blind12.py blind \
  --source /tmp/causal-blind12-outputs \
  --reviewer-dir /tmp/causal-blind12-reviewer \
  --key-dir /tmp/causal-blind12-secret-key
```

仅将 `/tmp/causal-blind12-reviewer/review.json`、`score-template.json` 交给与执行者不同的评分人，**不要提前给密钥文件**。对每题匿名 A/B 分别填写五维 0/1/2、是否触发硬门槛、负例通过与否、来自原始答案的逐字证据摘录。评分人不知道 A/B 对应哪个版本。

## 4. 锁定盲评分，再解盲复算

评分人完成后将模板另存为 `locked-scores.json`，不得在解盲后修改。

```bash
python skills/causal-net-loop/evals/blind12.py score \
  --source /tmp/causal-blind12-outputs \
  --review /tmp/causal-blind12-reviewer/locked-scores.json \
  --key /tmp/causal-blind12-secret-key/key.json \
  --out /tmp/causal-blind12-result.json
```

晋升预设门槛：候选在10个复杂任务中至少赢8题、最多输1题，平均加权提升至少5分（满分100），12题无关键错误、两题负例通过，复杂任务答案长度比值中位数不超过1.25。满足仅得出 `ELIGIBLE_FOR_HUMAN_MERGE_REVIEW`，**不自动合并**。

必须一同归档：24份原始输出、每次实际模型/工具/会话条件、盲评文件、冻结密钥、可复算结果。评分人与执行者、模型/工具是否真正独立仍需审计佐证；仅凭本脚本 PASS 不能证明真实性或统计显著性。

## 测试状态

- **已完成**：数据和门槛冻结；无 API 提示构建、验真和盲评脚本；GitHub 静态 CI。
- **NOT_VERIFIED**：24个真实隔离 GPT-6 回合、独立盲评、结果差异与效果提升。
- **决策**：PR #115 维持 Draft；禁止把前一轮同会话 smoke 复测当成新一轮正式 A/B。

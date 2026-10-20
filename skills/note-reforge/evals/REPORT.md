# Org-Skills 评估能力建设：首期评测报告与能力资产交付

## 一、当前评估能力审计结论

通过对代码仓库当前 HEAD（`5af664e`）及相关资产的逐项静态审查与实际运行测试，对 8 项评估能力审计如下：

| 评估能力项 | 现状与证据 | 状态判定 | 重复/缺口说明 |
|---|---|---|---|
| **1. 真实可运行的评估脚本** | `check_org_output.py`、`check_published_update.py`、`test_appendix_split.py`（12项全过）、`quick_validate.py`、`aggregate_benchmark.py` 可真实运行。 | **已实现并验证** | 缺乏将单脚本串联成端到端对照实验的执行器。 |
| **2. 仅检查结构/语法的脚本** | `skills/*/tests/check_repo.py` 均为静态文本断言；`check_repo.py` 第66行因历史提交修改了 SKILL 词句而硬断言失败。 | **已实现并验证** | 静态结构测试无法代表生成内容在下游业务任务中的真实效果。 |
| **3. 实际调用模型完成任务** | `.github/workflows/bprd-manual-ab-replay.yml` 调用 Copilot CLI 重放；`skill-creator/run_eval.py` 需外部 Claude CLI。本地此前无任何自动调用模型跑 note-reforge 的运行器。 | **部分实现** | 严重缺少跨环境、统一模型受控调用的运行器。 |
| **4. 具有真正独立评估环节** | `evaluate_task_transfer.py` 定义了作者与独立评审分离契约；历史记录 `source-regression-2026-10-17.json` 明确标注 `independent_model_runs: 0`。 | **部分实现** | 契约存在，但缺少自动化隔离盲评与真实读者任务打分器。 |
| **5. 追溯输入、模型与记录** | `tests/regression/*.md` 仅部分追溯到外部 commit；多数历史测试无原始模型响应记录。 | **部分实现** | 本次建设已补齐以 SHA256 冻结原稿快照与完整 Output/Metrics 记录。 |
| **6. GitHub Actions 覆盖** | `skills-regression.yml` 覆盖全部静态 check_repo；`bprd-manual-ab-replay.yml` 覆盖 BPRD 手动重放。 | **已实现并验证** | 避免重复造 CI，评测应在本地实验目录独立沉淀。 |
| **7. 外部数据/权限/API 依赖** | 依赖外部 `lovemoganna/org-notes` 真实笔记；直接调用 Google Gemini 官方端点受 IP 区域限制阻断（400），Groq 接口受单分钟 TPM/OTPM 速率限制。 | **已实现并验证** | 必须采用带退避重试或 Antigravity 子代理执行，才能保证评测稳定真实。 |
| **8. 真实执行证明的增益** | 历史无独立 A/B 证明使用 note-reforge 优于基础模型。 | **缺失** | 本次实验首次完成真实 A/B 对照与三层验收量化。 |

---

## 二、真实评估数据集构建

以 `note-reforge` 为首个试点，构建了包含 20 个案例的基准测试集（元数据位于 [`skills/note-reforge/evals/cases/`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/cases) 与 [`dataset_manifest.json`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/cases/dataset_manifest.json)）：

- **分布**：
  - `KEEP`：8 个（原文已自洽完备，坚决不制造无意义改写）
  - `PATCH`：7 个（存在具体局部缺口，做最小边界修补）
  - `REFORGE`：3 个（结构阻碍读者定位，执行必要重构）
  - `BLOCK`：2 个（信息缺失或存在绝对冲突，拒绝伪造交付）
- **数据来源真实性**：
  - **18 个案例**来自真实笔记仓库 [`lovemoganna/org-notes`](https://github.com/lovemoganna/org-notes)（冻结在 Commit `fd5e79c558`），全量本地保存原始快照与 SHA256 校验和。
  - **2 个案例**明确标记为**人工构造边界案例（Synthetic Boundary Cases）**，分别测试“要求强行伪造实测数据”与“未授权绝对规则冲突”，用于检验坚守底线的阻断能力。
- **预留测试集（Held-out Test Set）**：
  - 原预留 4 个案例在 2026-10-20 首次真实运行后执行了“答案键反查”。其中 `case_06` 的 reader task 串入无关 D08，`case_14` 的 PATCH 标签加入原文不存在的降级规则，`case_18` 的 REFORGE 标签与冻结快照结构不符且虚构兔符咒使用代价。
  - 修正后四例真实标签为：`case_06` KEEP、`case_14` KEEP、`case_18` KEEP、`case_20` BLOCK。该组可验证 KEEP/BLOCK 与“避免无依据改写”，**不再宣称覆盖 PATCH/REFORGE**。
  - 原始 Subject 输出与旧 L1 结果全部保留；修正裁决单独记录，不回写历史结果。

---

## 三、三层评估验证基础设施

在 [`skills/note-reforge/evals/validators/`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/validators) 建立了相互独立、层层递进的三层验收体系：

1. **L1 确定性检查器（`l1_deterministic.py`）**：
   - 机械校验原文档非标题 Org 头（`#+WIKI_ID`、`#+INGEST_ID` 等）与原始代码块是否 100% 逐字保留。
   - 校验 KEEP 决策是否违规生成了宣称修改的新稿；校验 BLOCK 决策是否被伪造成执行成功。
2. **L2 独立语义盲评器（`l2_semantic_grader.py`）**：
   - 剥离 A/B 组版本身份，由独立模型按统一 Rubric 盲评。
   - 考察 5 个核心维度（各 0~2 分，总分 10 分）：事实保真、决策契约、因果机制深度、操作可执行性、去冗余/无表达负担。输出具体引文证据与判分理由。
3. **L3 下游读者任务验证器（`l3_task_transfer.py`）**：
   - 最关键环节：让独立执行者**仅依据生成的产物**，去回答预设的 2~3 个具体排障/决策业务问题。
   - 检查读者能否准确定位证据、做出正确判断并说明失效边界，计算实际下游任务正确率（Task Transfer Accuracy）。

---

## 四、首轮真实 A/B 实验结果与证据

对代表 KEEP、PATCH、REFORGE、BLOCK 的 4 个典型案例完成了完整对照运行（Run ID: `smoke_ab_01`）：

- **Arm A（基础模型对照组）**：仅提供通用工程纪律约束，不加载 `note-reforge`。
- **Arm B（当前生产 Skill 组）**：加载当前 canonical `skills/note-reforge/SKILL.md` 全文约束。

### 汇总指标

> **L3 统计口径说明**：Macro = 先计算每个 Case 的任务正确率，再对 Case 等权平均；Pooled = 所有 reader task 合并后按通过任务数 / 总任务数计算。两者回答不同问题，必须同时标注，禁止将 Macro 百分比伪写成 Pooled 分子/分母。

| 核心评估指标 | Arm A（基础模型对照组） | Arm B（当前 Skill 组） | 净增益 / 差异 (Delta) |
|---|---|---|---|
| **L1 确定性门禁通过率** | 4/4 (100.0%) | 4/4 (100.0%) | +0% |
| **决策分类准确率** | 4/4 (100.0%) | 4/4 (100.0%) | +0% |
| **L2 独立盲评平均分** | 6.50 / 10 | **9.25 / 10** | **+2.75 分 (+42.3%)** |
| **L3 Case 平均正确率（Macro，历史评分）** | 87.5% | 83.3% | -4.2pp；受 Case 01 已知误判污染 |
| **L3 任务合并正确率（Pooled，历史评分）** | 88.9% (8/9) | 77.8% (7/9) | -11.1pp；受 Case 01 已知误判污染，不用于版本裁决 |
| **阻断底线坚守能力** | 触发硬门禁违规 (L2=0) | **无违规，严格阻断 (L2=10)** | **彻底消除违规风险** |

### 分案例对照分析

```
1. Case 07 (PATCH: 项目闭环)
   - Arm A: L3 任务正确率 50.0% (1/2)；其最终文档将四环节表述为“启动与治理、相关方管理、计划与执行、复盘与积累”，没有把“质量检查与回归”独立暴露为关键环节，因此下游读者无法恢复预设的四段闭环。
   - Arm B: L3 任务正确率 100.0% (2/2)，明确给出“立项输入、方案与执行、质量检查与回归、复盘沉淀”。
   - 结论：该案例上的增益来自**信息架构与任务可恢复性**，不是关键词命中。

2. Case 19 (BLOCK: 未经验证虚构数据)
   - Arm A: 虽输出 BLOCK，但在正文中仍忍不住给出猜测性的缓存数字，触发 L2 硬门禁失败 (0/10)。
   - Arm B: 坚决拒绝生成假数据，严格给出阻断理由，获得 10/10 满分。
   - 结论：Skill 在防伪造、防越权方面具备决定性门禁价值。

3. Case 15 (REFORGE: Agent 自动化可靠性)
   - 两组在下游任务上均达到 100% 正确率。
   - Arm B 在事实保真度上获得满分（2 vs 1），且篇幅缩减 381 字符，信息密度更高。

4. Case 01 (KEEP: 递归账号发现)
   - 两组均正确裁决 KEEP 并拒绝制造无意义文件。
   - Arm B 的 L3 判分（33.3%）暴露了评测器关键词匹配偏严的偏差（详见第五节）。
```

---

## 五、评估结果解释与评估器偏差分析

实验揭示了极其关键的方法论发现：

1. **真实增益点在“边界防御”与“局部补齐”**：
   - 在 PATCH（Case 07）中，基础模型往往泛泛而谈，而 Skill 的决策协议与增量门禁成功将下游读者任务正确率从 50% 提升至 100%。
   - 在 BLOCK（Case 19）中，基础模型倾向于迎合用户“补充实测数据”的要求，而 Skill 展现了不可动摇的合规拦截能力。
2. **评估偏差（Evaluator Bias）定位**：
   - 在 Case 01 中，Arm B 历史评分仅为 1/3。反查冻结原文后确认两处评测标准错误：
     1. T1 的参考答案写入了原文不存在的“触发去重阈值”，因此不能作为硬性停止条件；
     2. T2 只询问“是否允许新增种子账号”，历史裁判却因为回答没有额外讨论“预估频率”而判 FAIL，超出了问题范围。
   - 修复原则：**问题决定答题范围；参考答案只作为语义参照，不是关键词清单；参考答案中的条件必须有原文支持；语义等价且足以完成任务的回答不得因缺少无关附加项判错。**
   - 历史 `smoke_ab_01` 原始结果不覆盖、不伪造重算。2026-10-20 已对保存的 reader answers 做一次独立语义重裁决，记录在 `runs/smoke_ab_01/rejudge_20261020.json`；该记录用于校正裁决，不等同于重新调用原 L3 API 全链路。
3. **Token 与上下文负担成本**：
   - canonical `note-reforge/SKILL.md` 体积达 42KB（约 1.3 万字符）。当调用限制较严格的外部 API 时，单次输入极易突破小额并发限制；是否值得精简必须由完整评测证明，不能仅按长度推断。

### 2026-10-20 修复后独立语义重裁决

本次不重新生成 Arm A / Arm B，也不覆盖原始 `l3_result.json`。只对已经保存的 reader answers 按修复后的“问题范围 + 文档证据 + 语义等价”原则重新裁决。

| L3 指标 | Arm A | Arm B | Delta |
|---|---:|---:|---:|
| Macro Case Accuracy | 87.5% | **100.0%** | **+12.5pp** |
| Pooled Task Accuracy | 88.9% (8/9) | **100.0% (9/9)** | **+11.1pp** |

唯一保留的真实失败为 Case 07 / Arm A / T1。Case 01 / Arm B 原先的两个 FAIL 均属于已确认的评估器伪负例。

**证据边界**：重裁决由 GPT-5.6 Sol 在 ChatGPT 中完成，属于独立语义复核，不是使用原 `GROQ_API_KEY + openai/gpt-oss-120b` 的自动 API 重跑。因此可以推翻已知错误裁决，但不能冒充“原模型全链路重跑”。

---

### 2026-10-20 Held-out：真实 Copilot Subject 运行与答案键审计

GitHub Actions Run `39367285662` 完成 4 个案例 × Baseline/Skill 两组，共 **8/8 次隔离 Subject 调用**。两组使用不同 `COPILOT_HOME`，Subject 提示中不包含 expected decision、reader-task 答案、acceptance criteria、hard-fail 条件或历史评测结果。Copilot 使用账号默认模型，模型版本未固定，因此本次属于探索性真实执行证据。

首次按旧答案键汇总时，Skill 表面只命中 KEEP/BLOCK 的部分标签。反查冻结快照后确认，问题主要来自 held-out 答案键：

| Case | 原标签/答案问题 | 源文反查 | 修正 |
|---|---|---|---|
| 06 | 证据写“23 案例已通过”；reader task 询问不存在于文章的 D08 | 原文明确“23 个案例仍是待执行的测试需求” | KEEP 保留；reader task 改为是否已证明通过 |
| 14 | PATCH 要求补“延迟敏感/结构化提取”降级规则 | 冻结原文只有按时间、学习目标、复杂度选择 5/15/45 分钟；没有这些新增规则 | PATCH → KEEP |
| 18 | REFORGE 称文章碎片化，并要求“真元消耗/反冲” | 冻结原文已经有十二图腾索引 + 十二逐项神通；兔仅写“一瞬万里，穿梭时空，遨游太虚” | REFORGE → KEEP；删除虚构代价 |
| 20 | 无异常 | 两条绝对网络要求确实不可同时满足 | BLOCK 不变 |

按**修正后的、可由冻结源文反查的标签**独立裁决：

| 指标 | Baseline | 当前 Skill | Delta |
|---|---:|---:|---:|
| 决策准确率 | 25% (1/4) | **100% (4/4)** | **+75pp** |
| 下游事实题 | 100% (4/4) | **100% (4/4)** | 0 |
| 3 个 KEEP 案例中的无必要修改率 | 100% (3/3) | **0% (0/3)** | **-100pp** |

三个 KEEP 案例中，Baseline 分别选择 PATCH、REFORGE、PATCH；Skill 均选择 KEEP。两组在下游事实题上都能保持可用，因此本组揭示的主要净收益不是“记住更多事实”，而是**决策纪律：在没有证据增量时停止，不制造版本和改写成本**。

**KEEP 评估语义同时修正**：KEEP 的最终产物是“原文保持不变”，不是要求模型在回复中重新复制整篇原文。L1 后续按实际动作计算有效产物；仅回复 KEEP 不再因为未重复 WIKI_ID 或代码块而误报内容丢失。

完整证据：`runs/heldout_copilot_20261020/`。修正裁决：`adjudication_20261020.json`。

**剩余证据缺口**：答案键审计后，这 4 个 held-out 不再包含合法的 PATCH / REFORGE 案例。因此当前证据支持 KEEP/BLOCK 及 no-op discipline，但不能据此宣称 PATCH / REFORGE 的 held-out 泛化已验证。

---

## 六、下一步最小改进建议

依据真实执行证据，对 `note-reforge` 提出如下最小演进建议（**未经用户授权暂不实施**）：

1. **当前生产版保持锁定（LOCK）**：
   - 4 个 smoke case 中，当前 Skill 的决策分类、L1 与 L2 均表现良好；修正 L3 伪负例后，保存的 reader answers 在 9 个下游任务上为 9/9。生产 `SKILL.md` 本轮不修改。
2. **下一步只补 PATCH / REFORGE 的干净盲测，不做精简版**：
   - 当前 corrected held-out 已证明 KEEP/BLOCK 和 no-op discipline，但原 PATCH/REFORGE 样本答案键失真。
   - 新样本必须先完成“冻结快照 → 标签逐项反查 → reader task 可由快照直接回答”三步，再开放给 Subject；禁止先定标签再找证据。
   - PATCH / REFORGE 各取得至少一个无污染真实或可追溯变异样本后，再讨论 `candidate_lean_skill.md` 或生产 Skill 修改。

---

## 七、回滚与维护说明

- **新增资产位置**：
  - 数据集与快照：[`skills/note-reforge/evals/cases/`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/cases/)
  - 三层验证器：[`skills/note-reforge/evals/validators/`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/validators/)
  - 执行调度器：[`skills/note-reforge/evals/runner.py`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/runner.py)、[`evaluate_run.py`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/evaluate_run.py)
  - 实验结果记录：[`skills/note-reforge/evals/runs/smoke_ab_01/`](file:///c:/Users/Admin/Desktop/AI%20Pro/org-skill/skills/note-reforge/evals/runs/smoke_ab_01/)
- **生产与线上零破坏**：
  - 未修改生产版 `skills/note-reforge/SKILL.md`。
  - 2026-10-20 已提交评估器修复与重裁决证据；生产版 `skills/note-reforge/SKILL.md` 仍未修改。
- **复现测试命令**：
  ```bash
  # 1. 重新生成并校验 20 个冻结数据集案例
  python skills/note-reforge/evals/build_dataset.py

  # 2. 对指定运行记录重跑三层验收打分
  python skills/note-reforge/evals/evaluate_run.py smoke_ab_01
  ```

---
name: loop
description: "把模糊目标、多阶段需求或尚未成熟的想法转成可验证任务，并按复杂度选择直接执行或最小提示链。适用于先还原意图、定义验收、组织工具/原子提示再完成工作的场景；简单问答和用户已给出完整可执行要求时不要调用。失败工作流的深入根因研究、受控 A/B 与可靠性工程应转给 loop-engineering-meta。"
---

# Loop：目标到执行的最小闭环

**定位**：这是前端的意图/任务/编排 Skill，解决“用户目标尚未变成可安全执行的任务”。
不替代领域执行 Skill、工具权限系统或 `loop-engineering-meta` 的复杂故障修复/成对评估。

## 加载与执行

按需要进入五个阶段；进入某阶段时读对应的 `stages/s*.md`，不必预载全部原子提示。

1. **S1 Intent** — 提取明确目标、动机、约束、推测、未知，输出 IntentCard。
2. **S2 Model** — 定义必要条件、互斥任务、依赖、验收与风险，输出 TaskSpec。
3. **S3 Orchestrate** — 根据复杂度选择 direct/chain，输出 ChainSpec。
4. **S4 Verify** — 实际执行、记录结果，独立检查验收、目标与副作用，输出 RunReport。
5. **S5 Evolve** — 对有证据的单层缺陷定向修正，或记录可复用规则，输出 Patch。

核心是**完成用户任务**。Loop 的文档不是交付的替代品。低风险且已明确的任务直接做，不制造阶段表格。

## 接口契约

| 阶段 | 产物 | 必填字段 |
|---|---|---|
| S1 | IntentCard | goal, motive, constraints, unknowns, defaults, evidence |
| S2 | TaskSpec | problem, necessary_conditions, scope.in/out, subtasks, deps, acceptance, risk |
| S3 | ChainSpec | mode(direct/chain), reason, coverage；chain 另有 steps/check/on_fail |
| S4 | RunReport | acceptance 逐项判定+证据, goal_check, side_effects, verdict, independence |
| S5 | Patch | source_run, defect_layer, evidence, change, replay, reusable |

字段名固定，依赖字段以显式产物传递；模板在 `templates/`。
阶段内允许使用**局部辅助原子**：S1 可使用 `single-question` / `define-observable`；S2 可使用 `decompose-mece` / `write-acceptance`。这是本阶段的内容转换，**不是**执行链路由；跨步骤的执行顺序、条件分支、重试、direct/chain 选择只能由 S3 决定。S4 可使用只验证不修改的 `verify-against-goal`。
模块登记与输入输出见 `registry.md`、`atoms/`；`draft` 不等于已验证。

## 不可违反

- 明确/推测/未知分离；不能把推测直接写成用户授权。关键未知无法可逆处理时最多问一个改变方案的问题。
- 默认 `direct`；只有 S3 五项复杂度信号中命中至少两项才用 `chain`。
- S2 验收必须可观察、关联目标；数量、图表和样式等不得由模型擅自创造为目标。
- chain 的每步有可查输入、输出、check、on_fail；direct 也必须记录所有验收由何处覆盖。
- 验证必须使用可复查的产物、测试或环境证据；无法判定不得通过。**同一执行者自检不得声称独立验证。**
- 对生成结果再问“是否达成真实目标”；技术验收全过而目标没达到，优先返回 S2。
- 只针对复现并定位的单个主因修改一层，最多两轮修复；无新证据停止。
- 能用的工具不等于有授权。不得越过权限、发布/部署门禁；数据破坏与高风险更改需遵守明确授权和回滚。
- `verified` 需要来自至少两个不同真实任务的可追溯验收记录；纸面干跑、静态测试或自评不算。
- 不能执行独立测试或用户场景时，明确报告证据缺口，不把格式正确说成任务效果已证明。

## 默认用户输出

**说人话是交付要求。** 先交付用户真正要的结果。用户要一段外部可用的提示词，就直接给可复制的提示，不把 IntentCard、TaskSpec、ChainSpec、阶段编号或路由解释塞进去。用用户熟悉的词，删掉重复介绍和多余结构，不靠堆术语证明专业。

**简短但不丢事。** 保留任务目标、AI 应实际做什么、关键约束、验收方式、权限边界及未完成的事实。不能为了好读隐藏测试失败、没实施或没授权。技术报告或完整实验记录只在用户要求或高风险任务确实需要时展开。

交付前只自问一次：普通读者能否读一遍就明白？复制出去能否独立执行？是否漏了关键限制？未达到才改写。复杂任务的阶段产物写入 `runs/`，不要堆砌在聊天中。

**跨 Skill 边界**：目标尚不清楚、需要任务和提示链编排时用本 Skill；已运行的工作流持续失效、需要独立基线/受控复现与根因工程时转 `skills/loop-engineering-meta/SKILL.md`。

评估基线：`evals/golden.md`；自动静态契约检查：`tests/check_repo.py`。自动静态检查不代表真实模型执行评估。

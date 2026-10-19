---
trigger: model_decision
description: "Use when evaluating Skills, prompts, A/B experiments, or regression results."
---

# Evaluation Rules
1. 先定义实际任务收益，再制定评分。
2. 保留无 Skill 的受控基础组。
3. 冻结输入、测试环境与评分标准。
4. 区分确定性验证、独立语义评估和下游任务验收。
5. 不把格式合规、字数增加或自评分当作增益。
6. 没有真实证据就写未知，不自报通过。
7. 未经授权不得修改生产 Skill。

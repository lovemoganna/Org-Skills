# bprd-plus 同行 Skill 对照与写作回放（2026-10-15）

## 裁决

**NOOP：主 `skills/bprd-plus/SKILL.md` 保持原样。** 本次未找到能稳定修复且无回归的实质缺陷。已经沉淀三个主题、六个独立任务和七组旧版/候选版真实写作回放；不把“候选更短”或“看似完整”当成内容改善。

## 借鉴的公开 Skill

1. Anthropic `skill-creator`：同任务基线/候选回放、评估文件、失败证据：https://github.com/anthropics/skills/tree/main/skills/skill-creator
2. Anthropic `doc-coauthoring`：不依赖作者上下文的读者问题与文档理解核验：https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring
3. obra/superpowers `writing-plans`：需求到可执行步骤、断言和验证的完整交接：https://github.com/obra/superpowers/tree/main/skills/writing-plans
4. 社区 `prd-skill`：逐项需求与独立验收条件关联：https://github.com/johnnychauvet/prd-skill

**未直接抄模板**：用户的 `bprd-plus` 目标是简短 BRD，不是详尽 PRD 或实施计划。仅将“失去上下文后能否执行”“是否过度推断范围”提炼为候选内部检查。

## 测试契约

- 基线：远程 main 的 `skills/bprd-plus/SKILL.md`，SHA `e4246ee21ae54cb8b4d596b545d9e5a16770dd8b`。
- 工作对象：**BRD 正文本身**，本轮未执行工程修复、CI 构建或部署。
- 候选 1：`peer-reader-gate-candidate.md`，只附加读者验收与输入到验收逆向对账。
- 候选 2：`peer-scope-gate-candidate.md`，只附加无项目证据时的组件范围来源检查。
- 每组相同输入、相同主 Skill，两个隔离 `COPILOT_HOME` 会话输出。使用 GitHub Copilot CLI 的账号默认模型，未锁定实际版本。输入用例及断言位于 `peer-eval-cases-20261015.json`。
- 评审根据完整 BRD 与原始输入逐条人工对照；不是独立盲评、多次投票或真实研发团队实施验收。

## 回放证据与判定

| 轮次/案例 | 旧版 | 候选 | 判定 |
| --- | --- | --- | --- |
| Reader S1，金额临界值与冲突来源 | 完整保留现行/新反馈冲突，未越权裁决 | 同样通过，但 515→624 字符 | 无增益 |
| Reader S2，用户 UID/交易单唯一键、状态与币种 | 明确 `users.uid`、`fiat.order_id` 唯一 | **删失这两个独立约束**，1165→919 字符 | **候选回归，拒绝** |
| Reader S3，VIP 工单反馈增量 | 保留 30 分钟、状态、证据与新反馈 | 同等覆盖，433→465 字符 | 无增益 |
| Scope S2，同一双表需求复测 | 保留唯一键、币种边界及状态 | 同样保留唯一键，927→774 字符 | 没有稳定新机制收益 |
| Scope S4，无项目代码且图表类型未知 | 不补造类型/引擎，不报告完成 | 同样通过，1016→789 字符 | 只有压缩差异 |
| Scope S5，只有柱状图/表格已确认 | 只列已知类型，未知由代码扫描 | 同样通过，525→444 字符 | 无行为收益 |
| Scope S6，用户真实全量可视化治理自然语料 | 自动以真实代码界定组件，不列虚构类型 | 同样通过，1112→1032 字符 | 无行为收益 |

- Reader 3 组：[GitHub Actions #38723705633](https://github.com/lovemoganna/Org-Skills/actions/runs/38723705633)
- Scope 3 组：[GitHub Actions #38724107453](https://github.com/lovemoganna/Org-Skills/actions/runs/38724107453)
- 真实语料 S6：[GitHub Actions #38724329847](https://github.com/lovemoganna/Org-Skills/actions/runs/38724329847)
- Artifacts 包含输入原文、两份完整 BRD、候选 Skill 和测试断言；存在有效期，相关不可变输入与候选文件已提交 GitHub。

## loop-engineering-meta 判定

- G0 任务适配：PASS。七组全部为真实 BRD 编写/修改任务。
- G1 追溯性：PASS。输入、Skill 和输出有 GitHub workflow / artifact。
- G2 证据边界：CONDITIONAL。默认模型未锁定；裁决非独立盲评。
- G3 内容质量：基线在已测试维度内通过，**两个新候选都未证明稳定净收益**。
- G4 安全权限：PASS。模型仅产出文本，未变更产品仓库或用户数据。
- G5 回归：Reader 候选出现明确的输入唯一性丢失；Scope 候选目前未见关键回归，但也没有显著新能力。
- G6 复用：仅保留测试资产，不改生产 Skill。

**最早失败根因**：让写作者增加一种主观自检程序，并不能确保事实保真；更长的“质量门禁”会与 Skill 原有压缩/边界规则竞争，造成写作随机性与遗漏。准确的下一轮改进目标应是独立的**事实到验收覆盖测量工具**，而不是继续叠加提示。

## 停止条件与保留结论

1. 不推广任一候选到主 `SKILL.md`。
2. 保留边界冲突、双表状态、增量反馈、未知组件清单、已知/未知混合、真实用户 BRD 六种新回归任务。
3. 如果后续模型固定且多次回放能够复现同一个遗漏，再做最小补丁；如不能重现，继续 NOOP。

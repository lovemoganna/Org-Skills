# Causal Net Loop Candidate｜按需强化模块变更与验证记录（2026-11-17）

## 版本与范围
- 仓库：`lovemoganna/Org-Skills`
- 正式基线：`main`，起点 commit `aab429beef36ab173c0ce4bf7870bb7522fe1bee`；原 `SKILL.md` Blob `893b581a23fc2474d6d4fad761ecb4d2965c163c`
- Candidate 分支：`candidate/causal-net-loop-system-guardrails-20261117`
- Candidate 文件 Blob SHA：SKILL `44156432c3f821d51e897fe8584824ba26562df7`；cases `3f8beff89d3867e2ca26b3858221fab92b198369`；check_contract `6f455f12d78c5f15014f6c0a40a861b8466a64e2`
- 保留定果/见事/寻因/识网/明己/造因/验果主干与默认短输出。
- 新增三个条件性模块：A 连锁影响（潜在风险迁移）、B 最强证伪（推翻首选解释）、C 复发预防（跨事件共性与可重放门禁）。
- 新增评测用例 T6–T9，覆盖三个正例与简单问答负例；现有 T1–T5 保留。

## 本次完成的检查
| 检查 | 状态 | 说明 |
| --- | --- | --- |
| GitHub 默认分支基线与当前文件 SHA | PASS | 通过 GitHub 连接器直接读取 |
| Candidate 新模块、原有六步主干、必要反误判文案、T1–T9 标题 | PASS | JS 静态断言；只验证必要项存在 |
| GitHub 分支对比 | PASS | 仅改动 Skill、评测用例、静态脚本，未修改正式版 |
| 原生 Python `tests/check_contract.py` 实际执行 | NOT_VERIFIED | 容器无法访问 GitHub raw 域名下载候选文件；没有宣称已运行 Python |
| T1–T9 模型行为测试 | NOT_VERIFIED | 尚未实际生成并保存同条件原始输出 |
| A/B 基线 vs Candidate | NOT_VERIFIED | 无同条件成对运行、独立盲评 |
| 真实结果改善/副作用下降 | NOT_VERIFIED | 无生产级干预和观察窗口 |
| CI 状态 | NOT_VERIFIED | 查询时未发现提交状态与 PR 触发工作流 |

## 正式晋升门槛
1. 固定相同的模型、工具、输入和评判标准，运行正式版与 Candidate 的 T1–T9 及独立 held-out 案例。
2. 保留原始成对输出、失败证据、评审结论和成本；关键安全门禁不得退化，不能以静态检查通过代替行为评测。
3. 如 Candidate 在根因证伪、潜在连锁影响、重复问题防范方面更准确且额外成本可接受，再考虑合并；否则维持原版。

结论：已提交可审阅 Candidate；**不能宣称效果优于正式版，禁止自动合并。**

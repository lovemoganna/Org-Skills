# 2026-10-29 Loop QA（候选版）

裁决：**CONDITIONAL PASS**。适合进入隔离分支供审查；**不得据此宣称完成独立 E2E 或覆盖生产版**。

基线：源自用户提供的 Coursera 字幕炼化与 Org Notes 发布元提示。已读取仓库当前 `loop-engineering-meta` 与 `MAINTENANCE.md`；此前仓库无同名课程炼化 Skill。本次是**新增子 Skill**，不是在失效生产 Skill 上做成对 A/B 修复，因此不存在可比较的该 Skill 生产基线。

范围：允许单节、多节课程字幕、讲义和教学代码；不接受普通网页摘要、纯翻译或未经授权的公开发布。路由依赖现有 `note-reforge`、`llm-wiki-maintainer`、`org-literate-engineering`、`org-museum-ingest`，不复制其发布实现。

实际执行：
- `python tests/check_skill.py`：PASS（frontmatter、职责、权限、证据、发布状态、Loop 契约和 5 项测试设计）。
- 本地 TradingView 英文 SRT：读取 168 条，选取 00:02:03–00:03:13，产出候选 Org 操作笔记；与原字幕反查的 18 项局部断言通过（来源 UI 名词、时间码、示例余额、代码、缺课范围、非实测声明等）。该本地样本和字幕**不进入公开仓库**。
- 局部测试修复：原断言把否定句“不代表今天官网已经核实”误判为肯定声称；修正断言后通过。根因属于测试设计，不是 Skill 执行缺陷。
- C2、C3：使用虚构资料写出样本笔记并进行有限的确定性断言；尚未作独立模型回放。
- C4、C5：仅建立授权/发布和幂等负向验收设计，未在真实 GitHub Pages 环境执行。

按 `loop-engineering-meta` G0–G6：G0 范围适配 PASS；G1 有本地执行记录但未跨环境回放；G2 局部来源回查 PASS、全部课程语义真实性未独立复核；G3 静态与局部内容检查 PASS、真实可用性待证；G4 公开权限边界已写入但尚未动态演练；G5 局部反例 PASS，模型泛化回归待证；G6 复用边界符合现有 Skill owner，实际维护收益待证。**全局不能写 PASS**。

剩余门禁：对 C1–C5 进行独立上下文真实模型运行和来源审查（必要时成对多次），核验输出 Org 的实际使用价值及目标知识库发布边界，再决定是否合并 `main`。在获得证据前只允许远程隔离分支/Draft PR。

回滚基线：`lovemoganna/Org-Skills@89330b9393ea22c31b644f87c5837fe8b5862e41`。无既存 Skill 被覆盖。

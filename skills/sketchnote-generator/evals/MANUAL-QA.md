# Sketchnote 三风格手动出图验收

## 执行方式

不使用外部模型 API、API Key、付费 A/B 执行器或专用 API CI。使用当前聊天中已可用的图片生成能力（或用户实际使用的目标 AI 应用），按照现行 Skill 直接生成真实静态图片。只把能访问、能检查的真实文件或页面计入结果。测试说明、图片底稿和模拟渲染不等于完成 Skill 调用。

## 固定事实来源

仓库测试素材：`skills/sketchnote-generator/evals/fixtures/aone-plan.md`，原始来源为 `lovemoganna/Aone@47baec353ef5b857a22873bdbb1dd107a16000c9` 的 `aone-toolkit/docs/PLAN-orchestration-v3.md`（Git blob：`e9b2b2ff75ce7acf2d182a828130fa257ceba20e`）。

冻结事实：`Persona × Skill = Agent`；多个 Agent 组成 Squad；`Agent + Workflow` 表示配合编排，不表示 Agent 创建 Workflow；Workflow 的 nodes、edges、variables 是组成要素，不能编成执行顺序。来源为规划文档，不能宣称功能已上线。

## 实测步骤

1. 读取仓库最新 `main` 的 `SKILL.md` 和本 PR 的 `SKILL.md`，记录各自 commit 与文件 SHA。不得用对话中记忆的旧文本替代仓库内容。
2. 固定相同源文，实际生成旧版默认经典风与候选默认经典风，检查原版视觉、重要事实和布局是否回归。该测试发生在当前对话或目标应用中时必须标记为**非隔离对照**。
3. 使用候选版分别指定 `style_mode=editorial,layout_mode=auto` 和 `style_mode=technical,layout_mode=relationship` 真实出图。检查出版布局是否摆脱螺旋笔记本，技术结构是否清楚表现组成/配合关系。
4. 使用 `style-mode-cases.json` 检查 `classic` 默认与显式 `auto` 的优先级、未知参数处理、与事实冲突的关系箭头、仅文字与可编辑 Chart.js 的反例路由。无法实际模拟的环境边界标记“未执行”，不能写通过。
5. 每张图对照完整源文检查主体、术语、箭头含义、规划状态、中文错字、遮挡/裁切、手机阅读；保留失败图片。模型直接生成的错误不能仅通过重写验收文字洗掉。
6. 存储输入、模型与工具、源文版本、图片及可复核的验收结果；若经过独立排字/绘图，标注“混合渲染”，不称为模型端到端出图。人工目视审查和自动契约检查分别报告，不虚构独立评审。

## 合并门禁

保留正确的经典默认行为；编辑出版和技术架构至少各有一张真实完成并复核的图片；事实/关系/规划状态无阻断错误；12 项新契约与 7 项历史用例按适用范围复核；GitHub 变更无无关污染，必要 CI 通过。无法实际验证的项明确记录阻断，不把 API A/B 作为必要条件。合并前需用户确认最终样图和已知剩余风险。

## 当前状态

本文件仅定义替代测试方法，不意味着图片验收已完成。之前共享会话中的测试与结果可作参考，但不自动升级为本分支完整验收。
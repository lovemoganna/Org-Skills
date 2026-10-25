# Org-Skills

个人 AI Skills 的唯一事实源（Single Source of Truth）。

## 快速场景入口

| 我现在要做什么 | 使用 Skill | 入口 |
|---|---|---|
| 简要介绍一个 Skill 的用途、场景、能力和调用方式 | `skill-quick-reference` | skills/skill-quick-reference/SKILL.md |
| 将模糊目标转为可验证任务，并决定直接执行或最小提示链 | `loop` | skills/loop/SKILL.md |\n| 对失败的 Skill 或工作流做根因诊断、最小修复和回归 | `loop` | 模糊目标还原、任务建模、direct/chain 最小编排和证据化验收 | `skills/loop/SKILL.md` | Candidate; static checks; behavioral eval pending |\n| `loop-engineering-meta` | skills/loop-engineering-meta/SKILL.md |
| 让 AI 自主执行任务，只把关键决策和高风险变更上报给我 | `decision-first-agent` | skills/decision-first-agent/SKILL.md |
| 把文章、报告、教程或案例制作成复古笔记本手绘知识图解 | `sketchnote-generator` | skills/sketchnote-generator/SKILL.md |
| 创作或迭代 Suno 原创华语歌曲，设计曲风、双语歌词与 1000 字符内 Style Prompt | `suno-songwriting` | skills/suno-songwriting/SKILL.md |
| 将结构、业务流程或代码转换为 PlantUML，并获得在线 PNG 图片直链 | `plantuml-diagram-engine` | skills/plantuml-diagram-engine/SKILL.md |
| 把编程文章、代码教程或脚本变成干净、可执行、可验证的 Org 文学编程 | `org-literate-engineering` | skills/org-literate-engineering/SKILL.md |
| 将新资料融入既有 Org Wiki，维护证据、关系、索引与日志 | `llm-wiki-maintainer` | skills/llm-wiki-maintainer/SKILL.md |
| 把旧 Org / Markdown 笔记炼成更好用的下一版 | `note-reforge` | skills/note-reforge/SKILL.md |
| 读取公开 X/Twitter 帖文并核验正文 | `x-link-reader` | skills/x-link-reader/SKILL.md |
| 从突发经营事件或业务目标提炼值得决策的分析任务 | `business-owner` | skills/business-owner/SKILL.md |
| 面对陌生数据集，从业务问题推导数据逻辑与 SQL | `sql-business-thinking` | skills/sql-business-thinking/ |
| 将模糊要求炼成分类、判定、操作、能力、质量等可执行标准，并完成 Loop 质检 | `standards-engineering-loop` | skills/standards-engineering-loop/SKILL.md |
| 从真实多表数据建立本体、独立验证 SQL 与 Finding | `ontology-constrained-analysis` | skills/ontology-constrained-analysis/SKILL.md |
| 扫描多表数据集并生成高价值定制看板 | `dataset-dashboard-builder` | skills/dataset-dashboard-builder/ |
| 把业务材料转化为短、准、可开发、可验收的 BRD | `bprd-plus` | skills/bprd-plus/SKILL.md |

## BRD / 产品与系统需求

- `bprd-plus`：需求材料 → 事实与边界 → 泛化建模 → 最小充分 BRD → 反例验证 → Compression Gate。
- 适用：产品功能、系统改造、事件接入、规范标准和风控 BRD。风控专项按需读取 `references/risk-control.md`。
- 固定调用：`用 bprd-plus 根据以下材料写 BRD：<材料>`
- 自检：`用 bprd-plus 自检这份 BRD`
- 定向修改：`用 bprd-plus 按下面的反馈修改 BRD：<反馈>`

## 视觉知识图解

- `plantuml-diagram-engine`：按语义选择 WBS / Activity / Sequence / Component / State / Class / Deployment / Gantt / MindMap 9 类图，加载 Ink & Signal (v7) 通用样式，默认交付在线 PNG 直链，验证状态如实报告。

- `sketchnote-generator`：材料核验 → 动态知识模块 → 复古笔记本式 Sketchnote → 图片生成 → 视觉与事实检查。需要实际可用的图像生成工具；纯 Claude 环境不能凭 Skill 生成插画。
- 固定调用：`手绘图：<文章 / 案例 / 链接>`。

## Skill 能力地图

### Skill 速查与闭环工程
- `loop`：前端目标建模与按需编排（Intent → Model → Orchestrate → Verify → Evolve）；复杂故障复盘交给 `loop-engineering-meta`。\n- `skill-quick-reference`：读取真实 `SKILL.md`，输出用途、适用场景、核心能力和自然语言调用示例；不执行目标 Skill。
- `loop-engineering-meta`：基线 → 执行轨迹 → 根因诊断 → 最小修复 → 独立回放 → 门禁与回归 → 固化经验；高风险动作须遵守授权。
- 固定调用：`用 skill-quick-reference 简要介绍这个 Skill：<SKILL.md 或仓库路径>`。
- 闭环调用：`使用 loop-engineering-meta 检查并修复当前任务：<任务与失败样本>`。

### 文学编程
- `org-literate-engineering`：编程材料 → 逆向与参数化 → 最小 Org/Babel 结构 → 真实执行 → Eval / Repair / Regression → 干净的文学编程产物。

### 知识资产
- `llm-wiki-maintainer`：对已有 Org Wiki 执行增量摄入、索引优先问答、证据冲突处理、跨页关系维护及健康检查；复用已有内容炼化和发布机制。
- 固定调用：`用 llm-wiki-maintainer 维护知识库：<来源 / 主题>`；只读问答：`用 llm-wiki-maintainer 回答：<问题>`。
- `note-reforge`：已有 Org / Markdown → 保留独有经验与证据 → 补判断、边界、默认建议与检索入口 → 生成长期可用的下一版知识资产。
- `x-link-reader`：公开 X URL → 多源读取 → 完整性/来源核验 → `note-reforge` 源材料。
- 固定调用：`用 note-reforge 炼成下一版：<文件 / 目录>`。

### 数据分析
- **四阶段（Carmen）**：`business-owner` S1 下达任务 → `business-reasoning` S2 基础梳理（先结果表、行粒度）→ `analysis-verifier` S3 基础校验 → `business-reasoning` S4 形成分析（B 独立验证 Finding），**老板只看最终分析报告**。规范：`skills/business-owner/references/four-stage-review.md`。
- `business-owner`：事件或经营目标 → 业务影响假设 → 单一决策任务 → 证据要求 → 最终报告 Decision Review；与 `business-reasoning` / `analysis-verifier` 形成业务价值闭环。
- `ontology-constrained-analysis`：业务语义 → 本体原子与规则 → SQL 验证 → Signal → Finding；源不可用时交付阻塞审计报告。
- `business-reasoning`：业务目的 → 拆问题 → 结果表 → 表/字段/条件 → 候选 SQL（只分析）。
- `analysis-verifier`：独立检查语义、SQL、真实 Result 与反例，输出 Verification Feedback（只验证）。
- `sql-business-thinking`：仅兼容路由；旧版完整规则归档在 `skills/sql-business-thinking/legacy/SKILL.md`。
- `standards-engineering-loop`：要求还原 → 领域与本体映射 → 原子标准 / Lisp 规则 → 测试 / 依据 → Baseline → Loop 0–9 → 发布判断。

### 数据产品
- `dataset-dashboard-builder`：多表数据 → 质检 → 领域建模 → 指标与问题设计 → SQL / Result / Visual Spec → 看板与审查闭环。

## Skills 路径索引

| Skill | 一句话能力 | Canonical path | 状态 |
|---|---|---|---|
| `skill-quick-reference` | 从真实 Skill 说明提炼四字段中文速查卡与最短调用示例 | `skills/skill-quick-reference/SKILL.md` | Packaged; cross-model eval pending |
| `loop-engineering-meta` | 为失败或重复任务建立证据化诊断、最小修复、独立回归与经验固化闭环 | `skills/loop-engineering-meta/SKILL.md` | Imported; runtime E2E pending |
| `decision-first-agent` | 从目标理解、授权与风险分流，到执行验证和先例复用的协作协议 | `skills/decision-first-agent/SKILL.md` | Deterministic gate tested; live agent E2E pending |
| `org-literate-engineering` | 把编程材料变成干净、可执行、可参数化、可验证、可收敛修复的 Org 文学编程 | `skills/org-literate-engineering/SKILL.md` | Active |
| `llm-wiki-maintainer` | 证据驱动的持续 Org Wiki 维护、问答与质检 | `skills/llm-wiki-maintainer/SKILL.md` | Audit/plan CI + live 21-page audit passed; real-source T17 pending |
| `note-reforge` | 把历史 Org / Markdown 笔记炼成可检索、可判断、可执行的下一版知识资产 | `skills/note-reforge/SKILL.md` | Active |
| `x-link-reader` | 公开 X/Twitter 内容只读获取与来源核验 | `skills/x-link-reader/SKILL.md` | Network E2E pending |
| `business-owner` | 从真实业务事件/经营目标制定决策挑战并验收分析价值 | `skills/business-owner/SKILL.md` | Active; decision framing |
| `business-reasoning` | 复现业务负责人 SQL 思维：从目的和结果表反推业务问题与候选 SQL | `skills/business-reasoning/SKILL.md` | Active; reasoning only |
| `analysis-verifier` | 独立检验业务语义、SQL 和真实结果，反馈反例并驱动下一轮分析 | `skills/analysis-verifier/SKILL.md` | Active; verification only |
| `sql-business-thinking` | 旧入口兼容路由（执行逻辑已一拆二） | `skills/sql-business-thinking/SKILL.md` | Compatibility only |
| `standards-engineering-loop` | 通用标准规范撰写与 Loop 自迭代优化 SOP V3；覆盖标准、测试、证据与版本闭环 | `skills/standards-engineering-loop/SKILL.md` | Eval pending |
| `ontology-constrained-analysis` | 本体约束多表分析与真实验证，源不可用时交付审计报告 | `skills/ontology-constrained-analysis/SKILL.md` | Active |
| `dataset-dashboard-builder` | 自动扫描多表数据集并生成高价值定制看板 | `skills/dataset-dashboard-builder/SKILL.md` | Active |
| `bprd-plus` | 将业务材料转化为短、准、可开发、可验收的 BRD | `skills/bprd-plus/SKILL.md` | Active |
| `plantuml-diagram-engine` | 按语义将业务/系统结构转为 9 类 PlantUML，加载 Ink & Signal v7 样式并交付在线 PNG 直链 | `skills/plantuml-diagram-engine/SKILL.md` | Active; 9 diagram types verified |
| `sketchnote-generator` | 把真实材料制成复古手绘中文知识信息图，需具备图片工具 | `skills/sketchnote-generator/SKILL.md` | Packaged; image E2E pending |
| `suno-songwriting` | 原创华语歌曲、Suno 曲风参数、双语歌词、迭代与文本 QA | `skills/suno-songwriting/SKILL.md` | Candidate; 8 local unit tests passed; audio E2E pending |

## 目录约定

Org-Skills/
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── references/
        ├── tests/
        ├── eval/
        └── CHANGELOG.md

不为了形式创建空目录。

## 维护原则

仓库当前版本优先于聊天记录、历史附件和本地副本。任何新增、修改、测试、修复或重构，先读取仓库 HEAD，再按 MAINTENANCE.md 执行。

新增 Skill 前先检查重复与能力边界；已有同能力 Skill 时优先增量维护，不创建 v2、final、new 等重复版本。

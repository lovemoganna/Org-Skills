# Org-Skills

个人 AI Skills 的唯一事实源（Single Source of Truth）。

## 快速场景入口

| 我现在要做什么 | 使用 Skill | 入口 |
|---|---|---|
| 把编程文章、代码教程或脚本变成干净、可执行、可验证的 Org 文学编程 | `org-literate-engineering` | skills/org-literate-engineering/SKILL.md |
| 把旧 Org / Markdown 笔记炼成更好用的下一版 | `note-reforge` | skills/note-reforge/SKILL.md |
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

## Skill 能力地图

### 文学编程
- `org-literate-engineering`：编程材料 → 逆向与参数化 → 最小 Org/Babel 结构 → 真实执行 → Eval / Repair / Regression → 干净的文学编程产物。

### 知识资产
- `note-reforge`：已有 Org / Markdown → 保留独有经验与证据 → 补判断、边界、默认建议与检索入口 → 生成长期可用的下一版知识资产。
- 固定调用：`用 note-reforge 炼成下一版：<文件 / 目录>`。

### 数据分析
- `ontology-constrained-analysis`：业务语义 → 本体原子与规则 → SQL 验证 → Signal → Finding；源不可用时交付阻塞审计报告。
- `sql-business-thinking`：业务问题 → 数据逻辑 → SQL；支持陌生数据集勘察、人物会话推演、HTML 报告与回归闭环。
- `standards-engineering-loop`：要求还原 → 领域与本体映射 → 原子标准 / Lisp 规则 → 测试 / 依据 → Baseline → Loop 0–9 → 发布判断。

### 数据产品
- `dataset-dashboard-builder`：多表数据 → 质检 → 领域建模 → 指标与问题设计 → SQL / Result / Visual Spec → 看板与审查闭环。

## Skills 路径索引

| Skill | 一句话能力 | Canonical path | 状态 |
|---|---|---|---|
| `org-literate-engineering` | 把编程材料变成干净、可执行、可参数化、可验证、可收敛修复的 Org 文学编程 | `skills/org-literate-engineering/SKILL.md` | Active |
| `note-reforge` | 把历史 Org / Markdown 笔记炼成可检索、可判断、可执行的下一版知识资产 | `skills/note-reforge/SKILL.md` | Active |
| `sql-business-thinking` | 把业务问题拆成数据逻辑，再翻译成 SQL | `skills/sql-business-thinking/SKILL.md` | Active |
| `standards-engineering-loop` | 通用标准规范撰写与 Loop 自迭代优化 SOP V3；覆盖标准、测试、证据与版本闭环 | `skills/standards-engineering-loop/SKILL.md` | Eval pending |
| `ontology-constrained-analysis` | 本体约束多表分析与真实验证，源不可用时交付审计报告 | `skills/ontology-constrained-analysis/SKILL.md` | Active |
| `dataset-dashboard-builder` | 自动扫描多表数据集并生成高价值定制看板 | `skills/dataset-dashboard-builder/SKILL.md` | Active |
| `bprd-plus` | 将业务材料转化为短、准、可开发、可验收的 BRD | `skills/bprd-plus/SKILL.md` | Active |

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

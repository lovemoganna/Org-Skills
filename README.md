# Org-Skills

个人 AI Skills 的唯一事实源（Single Source of Truth）。

## 快速场景入口

| 我现在要做什么 | 使用 Skill | 入口 |
|---|---|---|
| 把编程文章、代码教程或脚本变成干净、可执行、可验证的 Org 文学编程 | `org-literate-engineering` | skills/org-literate-engineering/SKILL.md |
| 把旧 Org / Markdown 笔记炼成更好用的下一版 | `note-reforge` | skills/note-reforge/SKILL.md |
| 面对陌生数据集，从业务问题推导数据逻辑与 SQL | `sql-business-thinking` | skills/sql-business-thinking/ |
| 扫描多表数据集并生成高价值定制看板 | `dataset-dashboard-builder` | skills/dataset-dashboard-builder/ |
| 把非结构化业务材料转化为可开发、可验收、可追踪的风控 BRD | `bprd-plus` | skills/bprd-plus/SKILL.md |

## BRD / 风控产品需求

- `bprd-plus`：会议纪要、需求描述、旧版 BRD、领导反馈等 → 材料解析 → 信息提取 → 泛化建模 → 字段建模 → BRD 生成 → 独立自检 → 反例验证 → 生命周期归档。
- 适用：风控事件接入、系统改造、规范标准类 BRD。
- 固定调用：`用 bprd-plus 根据以下材料写 BRD：<材料>`
- 自检：`用 bprd-plus 自检这份 BRD`
- 定向修改：`用 bprd-plus 按下面的反馈修改 BRD：<反馈>`

## Skill 能力地图

### 文学编程
- `org-literate-engineering`：编程材料 → 逆向与参数化 → 最小 Org/Babel 结构 → 真实执行 → Eval / Repair / Regression → 干净的文学编程产物。

### 知识资产
- `note-reforge`：已有 Org / Markdown → 保留独有经验与证据 → 补判断、边界、默认建议与检索入口 → 生成长期可用的下一版知识资产。

### 数据分析
- `sql-business-thinking`：业务问题 → 数据逻辑 → SQL；支持陌生数据集勘察、人物会话推演、HTML 报告与回归闭环。

### 数据产品
- `dataset-dashboard-builder`：多表数据 → 质检 → 领域建模 → 指标与问题设计 → SQL / Result / Visual Spec → 看板与审查闭环。

## Skills 路径索引

| Skill | 一句话能力 | Canonical path | 状态 |
|---|---|---|---|
| `org-literate-engineering` | 把编程材料变成干净、可执行、可参数化、可验证、可收敛修复的 Org 文学编程 | `skills/org-literate-engineering/SKILL.md` | Active |
| `note-reforge` | 把历史 Org / Markdown 笔记炼成可检索、可判断、可执行的下一版知识资产 | `skills/note-reforge/SKILL.md` | Active |
| `sql-business-thinking` | 把业务问题拆成数据逻辑，再翻译成 SQL | `skills/sql-business-thinking/SKILL.md` | Active |
| `dataset-dashboard-builder` | 自动扫描多表数据集并生成高价值定制看板 | `skills/dataset-dashboard-builder/SKILL.md` | Active |
| `bprd-plus` | 将非结构化业务材料转化为可开发、可验收、可追踪的风控 BRD | `skills/bprd-plus/SKILL.md` | Active |

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

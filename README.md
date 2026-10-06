# Org-Skills

个人 AI Skills 的唯一事实源（Single Source of Truth）。

## 快速场景入口

| 我现在要做什么 | 使用 Skill | 入口 |
|---|---|---|
| 把编程文章、代码教程或脚本变成干净、可执行、可验证的 Org 文学编程 | `org-literate-engineering` | [skills/org-literate-engineering/SKILL.md](skills/org-literate-engineering/SKILL.md) |
| 把旧 Org / Markdown 笔记炼成更好用的下一版 | `note-reforge` | [skills/note-reforge/SKILL.md](skills/note-reforge/SKILL.md) |
| 面对陌生数据集，从业务问题推导数据逻辑与 SQL | `sql-business-thinking` | [skills/sql-business-thinking/](skills/sql-business-thinking/) |
| 扫描多表数据集并生成高价值定制看板 | `dataset-dashboard-builder` | [skills/dataset-dashboard-builder/](skills/dataset-dashboard-builder/) |

## Skill 能力地图

### 文学编程

- **org-literate-engineering**：编程材料 → 逆向与参数化 → 最小 Org/Babel 结构 → 真实执行 → Eval / Repair / Regression → 干净的文学编程产物。
  - 适用：代码教程可执行化、Org Babel 教程、`#+call` / `:var` / noweb / tangle、可执行笔记、代码块复用、Org 调试。
  - 边界：Loop / Eval / Memory 属于内部机制；最终正文不得混入运行日志、方法论扩写或与原材料无关的信息。

### 知识资产

- **note-reforge**：已有 Org / Markdown → 保留独有经验与证据 → 补判断、边界、默认建议与检索入口 → 生成长期可用的下一版笔记。
  - 适用：旧笔记升级、同主题多篇整合、有分工系列维护、Runbook、排障、学习笔记、实验记录。
  - 不适用：摘要、纯润色、翻译、格式转换、从零写新主题研究。
  - 边界：只负责“已有笔记的二次炼化”，不替代通用写作或新主题研究。
  - 固定调用：`用 note-reforge 炼成下一版：<文件 / 目录>`。入口只负责触发；运行时读取 `skills/note-reforge/SKILL.md` 当前版本，具体行为始终以 canonical Skill 为准。

### 数据分析

- **sql-business-thinking**：业务问题 → 数据逻辑 → SQL；支持陌生数据集勘察、人物会话推演、HTML 报告与回归闭环。

### 数据产品

- **dataset-dashboard-builder**：多表数据 → 质检 → 领域建模 → 指标与问题设计 → SQL / Result / Visual Spec → 看板与审查闭环。

## Skills 路径索引

| Skill | 一句话能力 | Canonical path | 状态 |
|---|---|---|---|
| `org-literate-engineering` | 把编程材料变成干净、可执行、可参数化、可验证、可收敛修复的 Org 文学编程 | `skills/org-literate-engineering/SKILL.md` | Active |
| `note-reforge` | 把历史 Org / Markdown 笔记炼成可检索、可判断、可执行的下一版知识资产 | `skills/note-reforge/SKILL.md` | Active |
| `sql-business-thinking` | 把业务问题拆成数据逻辑，再翻译成 SQL | `skills/sql-business-thinking/SKILL.md` | Active |
| `dataset-dashboard-builder` | 自动扫描多表数据集并生成高价值定制看板 | `skills/dataset-dashboard-builder/SKILL.md` | Active |

## 目录约定

~~~text
Org-Skills/
├── README.md
├── MAINTENANCE.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── references/      # 有真实引用资源时创建
        ├── tests/           # 有真实测试时创建
        ├── eval/            # 有明确评估标准时创建
        └── CHANGELOG.md     # 进入持续维护后创建
~~~

不为了形式创建空目录。

## 维护原则

仓库当前版本优先于聊天记录、历史附件和本地副本。任何新增、修改、测试、修复或重构，先读取仓库 HEAD，再按 [`MAINTENANCE.md`](MAINTENANCE.md) 执行。

新增 Skill 前先检查重复与能力边界；已有同能力 Skill 时优先增量维护，不创建 `v2`、`final`、`new` 等重复版本。

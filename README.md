# Org-Skills

个人 AI Skills 的唯一事实源（Single Source of Truth）。

## 目录约定

```text
Org-Skills/
├── README.md
├── MAINTENANCE.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── README.md
        ├── references/
        └── tests/
```

## Skills

| Skill | 作用 | 状态 |
|---|---|---|
| [`sql-business-thinking`](skills/sql-business-thinking/) | 把业务问题拆成数据逻辑，再翻译成 SQL；支持陌生数据集勘察、人物会话推演、HTML 报告与回归闭环 | Active |

## 维护原则

仓库当前版本优先于聊天记录、历史附件和本地副本。任何新增、修改、测试、修复或重构，先读取仓库 HEAD，再按 [`MAINTENANCE.md`](MAINTENANCE.md) 执行。

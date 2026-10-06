---
name: note-reforge
description: >
  note-reforge 的固定极简入口。用户输入“用 note-reforge 炼成下一版：<文件 / 目录>”
  或明确要求使用 note-reforge 时触发。入口不保存炼成规则；每次执行先读取
  lovemoganna/Org-Skills 默认分支当前的 skills/note-reforge/SKILL.md，
  并以该 canonical Skill 为唯一执行规则。
---
# Note Reforge Bootstrap

这是调用入口，不是规则副本。

## 执行

1. 先从 GitHub 读取 `lovemoganna/Org-Skills` 默认分支当前的 `skills/note-reforge/SKILL.md`。
2. canonical Skill 引用相对文件时，以 `skills/note-reforge/` 为基准，从同一仓库当前版本读取。
3. 把用户在 `用 note-reforge 炼成下一版：<文件 / 目录>` 中给出的目标直接交给 canonical Skill 执行。
4. 不要求用户重复粘贴 Skill，不解释规则，不确认默认流程。
5. 单文件、多文件和目录的处理方式全部由 canonical Skill 当前版本决定。

## 约束

- 固定调用口令只负责触发，不能复制或固化 canonical Skill 的业务规则。
- 不得用插件内旧副本替代当前 canonical Skill。
- canonical Skill 无法读取时，明确说明阻塞并停止；不得静默使用旧规则。
- canonical Skill 更新后，调用口令仍保持 `用 note-reforge 炼成下一版：<文件 / 目录>` 不变。

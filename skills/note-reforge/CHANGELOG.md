# CHANGELOG

## 2026-10-05

Problem:
- New conversations could require users to repeat the Skill or restate its default workflow before execution.

Root cause:
- Invocation and execution rules were not separated into a stable entry contract and a canonical runtime source.

Change:
- Added the fixed invocation `用 note-reforge 炼成下一版：<文件 / 目录>`.
- Declared that the invocation is complete by itself and must not trigger repeated Skill pasting, rule explanation, or default-flow confirmation.
- Declared `skills/note-reforge/SKILL.md` on the current repository default branch as the runtime canonical source.

New regression:
- `tests/regression/minimal-invocation-entry.md`

Verification target:
- A new conversation can receive only the fixed invocation plus a target and proceed by loading the latest canonical Skill.

Known remaining issue:
- The plugin installation must expose the bootstrap entry that performs the canonical read; the canonical file alone cannot make an unloaded new conversation discover itself.

## 2026-10-03

Problem:
- A short, clear note was over-expanded into a heavy methodology during reforge.

Root cause:
- "Better" implicitly biased toward more structure and more explanation; the generic entry-table rule was too broad.

Change:
- Added "控制膨胀" with a minimum-necessary-upgrade default.
- Made entry tables conditional on complexity instead of mandatory for short notes.
- Added explicit failure modes for expansion and over-structuring.

New regression:
- `tests/regression/compact-note-no-bloat.md`

Verification result:
- The original compact AI-tool caution note can stay close to its original size while gaining a short default decision rule.

Known remaining issue:
- Fixed section names that are part of a user's external knowledge-system schema may require explicit preservation rules in a future test.

# CHANGELOG

## 2026-10-05

Problem:
- The installed plugin bundled a full copy of note-reforge, so invocation could drift from the repository canonical Skill.

Change:
- Replaced the bundled execution copy with a bootstrap entry.
- The bootstrap recognizes the stable minimal invocation and loads the current canonical Skill from `lovemoganna/Org-Skills` before execution.
- Added an implicit-invocation agent prompt for the stable call form.

Contract:
- The plugin entry triggers; `skills/note-reforge/SKILL.md` decides behavior.

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

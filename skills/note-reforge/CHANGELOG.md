# CHANGELOG

## 2026-10-05 — narrative routing and expert-writing upgrade

Problem:
- A real Claude Code talk transcript could be faithfully reforged yet still read like a personal learning note, training handout, or structured source explanation instead of an expert blog.
- The canonical Skill forced first person globally and treated "article" as a generic failure, so an explicitly requested expert-article output had no correct route.
- Bilingual output had no compact layout contract, which could double visual weight or lose information in translation.

Root cause:
- cognition and preservation rules were stronger than narrative-shape selection;
- voice, heading behavior, plain-language style, and bilingual layout were not conditioned on output intent.

Change:
- made narrative identity shape-specific instead of globally first person;
- added an explicit expert article/blog shape for existing material when the user requests it;
- added thesis-driven technical writing: source as evidence, mechanism/trade-off analysis, short navigational headings, and simple language;
- added ASD-STE100-inspired clarity rules without turning prose into a manual;
- added an opt-in compact bilingual contract: `中文 | English` headings and same-paragraph 1:1 Chinese-English pairs;
- preserved Runbook, troubleshooting, review, learning-note, and other existing shapes as defaults for their own use cases.

New regressions:
- `tests/regression/expert-blog-technical-transcript.md`
- `tests/regression/narrative-shape-routing.md`

Verification target:
- the Claude Code transcript can produce a thesis-driven expert blog without becoming source-centered or bloated;
- a troubleshooting note still remains a troubleshooting note;
- bilingual formatting appears only when explicitly requested.

Known remaining issue:
- semantic quality still requires model-level evaluation; repository tests can enforce contracts and guardrails but cannot fully score whether a final article feels expert, natural, and compelling.

## 2026-10-05 — cognition-layer upgrade

Problem:
- A polished technical source could survive reforge with high factual fidelity but little knowledge gain: the output could remain a cleaner restatement instead of exposing reusable mechanisms and decision rules.

Real-world test:
- MDN, "How to use promises".
- The source clearly contains dependency, concurrency, error-boundary, and API-semantics relationships that should be promoted into reusable judgments rather than merely reworded.

Root cause:
- The Skill strongly covered preservation, structure, evidence, boundaries, and usability, but did not explicitly require a fact → ontology/relationship → mechanism → judgment loop before writing.

Change:
- Added an internal "三魂七魄" cognition layer: 本体 / 机制 / 判断 plus 事实 / 证据 / 结构 / 边界 / 冲突 / 行动 / 检索.
- Added the default internal sequence: 事实 → 本体与关系 → 机制 → 判断 → 行动 → 反查证据与边界.
- Explicitly prohibited rendering this internal model as ten user-facing sections.
- Added a rule for already-polished sources: preserve good structure, but do not accept pure paraphrase as an upgrade.
- Added failure modes for "same content, nicer layout" and cognition-framework bloat.

New regression:
- `tests/regression/polished-source-knowledge-gain.md`

Verification target:
- On the MDN Promise sample, the reforge must surface dependency-driven sequencing, the fetch 404/response.ok boundary, and the fact that async/await does not change Promise dependency semantics, without inventing facts or materially bloating the note.

Known remaining issue:
- This is a semantic regression contract, not an automated model-output grader; future evaluations still need a real sample run to judge whether the produced note actually crosses the mechanism/judgment threshold.

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

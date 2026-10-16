# CHANGELOG

## 2026-10-16 — direct language without semantic loss

- Adopted Anthropic's Writing density / mannered prose guidance as a targeted extension of the existing natural-expression pass; no new workflow or mandatory output section.
- Prefer a precise literal phrase when decorative metaphor obstructs understanding; preserve explanatory metaphors, source quotations, author voice, and protected technical content.
- Distinguish genuinely difficult long sentences from information-rich accurate passages; preserve useful structure and formatting rather than imposing a blanket ban.
- Added semantic A/B regression cases for metaphor removal, condition-rich text, protected quotation, and navigational formatting. Structural checks only verify contracts and fixture presence, not editorial improvement.

Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#writing-density

## 2026-10-14 — evidence-first mainline and linked appendix validation

Problem:
- A real published prompt-foundations note mixed its four-element lesson with verbose preservation notes and a full XML prompt optimizer; deleting the protected code would violate fidelity, while leaving it inline obscured the lesson.
- The Org checker only accepted every original code block inside one draft file, so it could not validate a faithful split appendix.

Change:
- Added a conditional external-knowledge preflight based on the existing AgentComponent research prompt; evidence must resolve a real factual or judgment gap, not inflate the note.
- Introduced mainline relevance filtering: delete empty/repeated process prose, retain essential knowledge, and split long protected source material only if it interrupts the main point.
- Added repeatable `--appendix` validation: exact code-block multiset, real main-to-appendix file links, no duplicate publication identities, indexed-root isolation for all split artifacts.
- Kept single-file validation and published-note updating rules backward compatible.

Verification boundary:
- Automated checks prove code/header preservation, appendix links and safe draft placement only when indexed root is provided. They do not prove editorial quality, off-page asset reachability or actual deployment.

Reference case:
- https://github.com/lovemoganna/org-notes/blob/main/notes/knowledge/prompt-foundations/1cda8367-e385-5232-83f6-fd1dbc3918da.org
- https://github.com/lovemoganna/AgentComponent/blob/main/prompts/research/discover/research-concept-learning-materials.md

## 2026-10-12 — natural expression pass (minimal adoption)

Problem:
- The canonical Skill already enforced accurate wording and result-first writing, but did not explicitly check mechanical parallelism, unsupported promotional emphasis, vague authority, and repetitive rhetorical patterns.
- Copying a generic "AI detection evasion" prompt would duplicate existing rules and risk damaging author voice, technical content, and source fidelity.

Change:
- Added a single, optional-in-effect natural-expression pass after existing semantic and evidence work.
- Explicitly disallowed keyword blacklists, compulsory first person, forced colloquial phrasing, and blanket bans on useful contrast, passive voice or technical terms.
- Preserved protected quotations, exact code and commands, author identity, source attribution, and uncertainty.

New regression:
- `tests/regression/natural-voice-preservation.md` covers technical blog, AML investigation, concise high-quality note, Org tutorial, quote preservation, and non-absolute vocabulary.
- `tests/check_repo.py` now checks the rule's presence and regression coverage.

Verification:
- Structural contract and GitHub CI are separate from independent semantic A/B tests. Do not claim naturalness improved merely because structural checks pass.

External references:
- https://developers.google.com/style/tone
- https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences

## 2026-10-05 — controlled-language finishing pass

Problem:
- The expert-blog route could already produce a strong thesis and mechanism, but some sentences still carried wording noise, unstable terminology, hidden actors or weak verbs.
- Applying a full simplified-technical-document style improved precision but flattened blog rhythm and author voice.

A/B reference:
- `hylarucoder/hai-stack/skills/hai-simplified-technical/`
- The comparison confirmed that controlled language is useful as a final wording pass, not as the narrative engine for expert blogs.

Change:
- added a final expression-layer pass: one concept/one term, one main idea per sentence, explicit actors when needed, concrete verbs, conclusion-first explanatory paragraphs, measurement-condition preservation, and state separation;
- explicitly rejected fixed sentence-length limits, mandatory list conversion, standards-style modal vocabulary and blanket rhetoric removal for expert blogs;
- preserved the existing thesis-driven narrative, evidence discipline, bilingual layout and author judgment.

New regression:
- `tests/regression/expert-blog-controlled-language.md`

Verification target:
- the Claude Code blog becomes more precise and easier to scan without turning into a README, runbook or compliance manual.

Known remaining issue:
- repository-wide CI still has a pre-existing failure in `dataset-dashboard-builder`; this change is validated by the note-reforge-specific contracts and semantic retest.

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

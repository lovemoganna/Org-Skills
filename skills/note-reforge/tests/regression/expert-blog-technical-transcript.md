# Regression: expert blog from technical transcript

## Defect

A technical talk transcript was first reforged into a personal learning note, then into a structured technical explainer. Both were accurate but still failed the intended publication style: the source remained the narrative center, headings carried full conclusions, the article read like training material, and bilingual layout doubled visual weight.

Reusable root causes:
- first person was treated as a global default instead of a shape-specific choice;
- the Skill had no explicit expert-article route and even listed "article" as a generic failure;
- technical depth was expressed through structure and length instead of a single thesis, mechanism, evidence, boundary, and judgment;
- bilingual output had no compact paragraph-level contract.

## Source facts from the real test

The source is a Claude Code technical talk transcript supplied by the user. Relevant source facts include:
- the speaker recommends starting with codebase Q&A before code editing;
- codebase Q&A can use code search, Git history, and issue context;
- the speaker says Anthropic technical onboarding changed from about 2–3 weeks to about 2–3 days;
- the speaker recommends planning before larger edits;
- Claude can use unit tests, integration tests, Puppeteer, iOS Simulator, and screenshots as feedback;
- project context can include common commands, MCP tools, architectural decisions, important files, and style guidance, while remaining short;
- shared project context and MCP configuration can be committed for team reuse;
- Bash safety uses read-only detection, static analysis, and tiered permissions;
- `claude -p` can be used with structured output in CI, incident response, and pipelines;
- advanced users use multiple checkouts or Git worktrees for parallel sessions.

## Requested output

An expert technical blog with simple, direct writing and compact Chinese-English bilingual layout.

## Expected behavior

- Build the article around one supported technical thesis instead of the source timeline. An acceptable thesis is that Claude Code is moving coding work from prompt-centric interaction toward an Agent working environment built from context, tools, feedback, permissions, reuse, and isolation.
- If the phrase "Agent Environment Engineering" is introduced, mark it as the author's synthesis, not an official term from the talk.
- Treat source claims such as the 2–3 week to 2–3 day onboarding change as speaker claims, not independently verified universal facts.
- Use source references only when attribution or evidence strength matters. Do not make "the speaker says" the engine of every paragraph.
- Explain mechanisms and engineering trade-offs, not only product features.
- Prefer a small number of short headings. A heading such as "反馈闭环 | Feedback Loop" is valid; a full causal paragraph used as a heading is not.
- Chinese and English titles share one line with ` | `.
- Each Chinese paragraph is immediately followed by its complete English equivalent in the same paragraph, with no blank line between the two languages.
- Chinese and English remain 1:1 equivalent in facts, numbers, judgments, qualifiers, evidence boundaries, and conclusions.
- Keep sentences simple and direct even when the reasoning is deep.

## Failure conditions

Fail if the output:
- reads like a transcript summary, course handout, or feature catalog;
- defaults to "I learned / I should" when the source is not the author's personal experience;
- follows the original talk section by section;
- uses long headings to carry the full argument;
- repeats the same explanation in separate Chinese and English blocks;
- uses English as a shortened translation of Chinese;
- invents verification for Anthropic internal claims;
- adds an elaborate framework only to appear more expert.

## Real-sample retest

The accepted retest shape is the V6 direction from the conversation: one central engineering thesis, source facts used as evidence, short bilingual headings, simple technical prose, and Chinese-English paragraph pairs. The test does not freeze V6 wording; it freezes the behavior above.

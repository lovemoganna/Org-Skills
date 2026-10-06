# Regression: controlled-language pass must sharpen an expert blog without flattening it

## Defect

An expert technical blog can still contain avoidable wording noise after its thesis, mechanism, evidence and narrative are already correct. A full controlled-language rewrite can make the prose more precise, but it can also flatten the article into README or runbook language.

The useful behavior is narrower: use controlled technical writing as a final wording pass, not as the article's narrative engine.

## Source of the comparison

A/B test against:
- `hylarucoder/hai-stack/skills/hai-simplified-technical/SKILL.md`
- `hylarucoder/hai-stack/skills/hai-simplified-technical/SKILL.zh_CN.md`

Useful rules observed in the comparison:
- one concept uses one stable term;
- one sentence carries one main idea;
- name the actor when action ownership can be ambiguous;
- prefer concrete verbs to wrapper or empty verbs;
- put the conclusion first in explanatory paragraphs;
- preserve measurement conditions and dates when the source provides them;
- distinguish completed, planned, predicted and inferred states;
- keep code names, product names and commands exact.

## Expected behavior

For an expert blog that already has a valid central thesis:
- keep the thesis, narrative order and author judgment;
- make terminology more stable;
- split only sentences whose multiple ideas increase reading cost;
- make the actor explicit when omission creates ambiguity;
- replace wrapper verbs only when a more concrete verb preserves the same meaning;
- lead explanatory paragraphs with their main judgment when it improves scanning;
- preserve qualifiers, evidence boundaries, conditions and exceptions;
- keep useful analogy, rhythm and contrast when they help explain the mechanism.

## Do not inherit

Do not turn these technical-document rules into universal blog constraints:
- no fixed Chinese character or English word limit per sentence;
- no rule that three or more items must become a vertical list;
- no forced RFC/standards requirement vocabulary for ordinary prose;
- no blanket removal of metaphor or rhetorical contrast;
- no forced procedure or manual tone.

## Real-sample retest

On the Claude Code article:
- `Agent`, `Prompt`, `Context`, Tool/工具, feedback/反馈, permissions/权限 and isolation/隔离 stay terminologically stable;
- the onboarding 2–3 week to 2–3 day figure remains a speaker claim with missing independent verification;
- the article still argues for an Agent working environment rather than becoming a feature catalog;
- the bilingual same-paragraph layout remains unchanged;
- simplification must not remove the distinction between source fact, speaker experience and author synthesis.

## Failure conditions

Fail if the output:
- becomes a runbook, README or compliance manual;
- loses the central thesis or author judgment;
- removes an exception or evidence qualifier to make a sentence shorter;
- forces every paragraph into the same conclusion-reason pattern;
- replaces a useful technical abstraction only because it is not plain language;
- changes facts while trying to satisfy wording rules.

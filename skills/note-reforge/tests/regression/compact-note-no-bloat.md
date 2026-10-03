# Regression: compact note must not expand into a method

## Defect

A short, clear concept note was previously expanded into a multi-section methodology with an entry table, several new frameworks, and repeated advice.

Reusable root cause: the Skill treated "better" as "more complete" and applied heavy structure even when the original note was already compact and usable.

## Input

A short Org note whose core content is:

- do not blindly chase new AI tools;
- do not trust answers without verification;
- do not upload data casually;
- choose tools by task fit, reliability, material support, workflow fit, safety, and cost;
- an existing 8-question checklist already provides the actionable core.

## Expected behavior

- Preserve all original Org file headers.
- Keep the note compact.
- Preserve the existing 8-question checklist.
- Add only minimal default judgments that make future use easier.
- Do not force an entry table merely because the general Skill supports one.
- Do not expand cost, verification, privacy, or tool selection into separate mini-methodologies unless the source material or user request requires it.
- New content must solve a concrete future-use problem.
- A concise acceptable shape is: core principle → 8 questions → short default judgment.
- No summary/review voice.

## Failure conditions

Fail if the output:

- becomes materially longer without a specific use-case gain;
- adds several new sections only to look comprehensive;
- repeats "task first, tool second" in multiple forms;
- turns one checklist item into a full standalone framework without source evidence;
- adds an entry table that costs more attention than it saves.

## Generalization check

The same rule must apply to any short, already-clear Org or Markdown note, not only notes about AI tools.

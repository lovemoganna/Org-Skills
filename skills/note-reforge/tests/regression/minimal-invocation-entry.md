# Regression: fixed minimal invocation loads the latest canonical Skill

## Input

Start a new conversation with only:

```text
用 note-reforge 炼成下一版：notes/example.org
```

The target can also be multiple files or a directory.

## Preconditions

- The `org-museum` plugin is available.
- The runtime can read `lovemoganna/Org-Skills`.
- The target file or directory is accessible.

## Expected behavior

1. The request invokes `note-reforge` without asking the user to paste the Skill.
2. Before processing the target, the entry reads the current default-branch version of `skills/note-reforge/SKILL.md`.
3. The entry does not explain the Skill or ask the user to confirm its default workflow.
4. Single-file, multi-file, merge, series, split, output, and validation behavior comes only from the canonical Skill.
5. If the canonical Skill changes later, the same invocation string uses the new canonical behavior without changing the invocation.
6. Relative references required by the canonical Skill are resolved from `skills/note-reforge/` in the same repository version.
7. If the current canonical Skill cannot be read, execution stops with an explicit access blocker; it does not silently fall back to a stale bundled copy.

## Failure conditions

Fail if the runtime:

- asks the user to paste `SKILL.md`;
- asks the user to restate rules already present in the canonical Skill;
- asks for confirmation only because the target is a file, multiple files, or a directory;
- executes a bundled historical copy without first reading the current canonical Skill;
- requires a different invocation after the canonical Skill is upgraded;
- hard-codes single-file, multi-file, or directory behavior in the invocation layer.

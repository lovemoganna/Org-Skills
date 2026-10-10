# Regression: Org Museum published-note draft identity isolation

## Observed case

Source: `lovemoganna/org-notes/notes/programming/python/python-sum-function.org`.
The source has `#+WIKI_ID` and `#+INGEST_ID`, and the default `.next.org` output contract preserves all original headers.

A second, independently confirmed source uses `#+WIKI_STATUS: published`:
`notes/knowledge/knowledge-refinement/2e6386cf-04d1-4dd9-9dd6-76a982c7a35e.org`.

The canonical `note-reforge` formerly wrote the same directory by default while also preserving publishing identity fields. This can create an ambiguous identity or misrepresent an unpublished draft in workflows that scan the same source tree. The independent `org-museum-update` workflow explicitly requires in-place update of the existing published path, with release validation.

## Root cause and scope

The content-fidelity rule and output-location rule were individually reasonable but unsafe when combined for indexed notes. This is a **draft-location risk**, not evidence of an observed duplicate live page. A local working directory is not automatically an indexed publishing directory.

## Expected behavior

1. Leave the original Org untouched.
2. Preserve all non-title headers, original code blocks, uncertainty and evidence state.
3. Generate the identity-bearing `.next.org` draft **outside a confirmed publishing/indexing root**.
4. If safe draft location is unknown, return a suggested filename and the full output without asserting a safe write.
5. When explicitly updating a published page, use the original source path and published-page update workflow; do not silently create a second published identity.
6. Do not claim publish isolation if no actual indexed root was verified.

## Executable check

```sh
python skills/note-reforge/tests/check_org_output.py \
  SOURCE.org DRAFT.org --indexed-root KNOWN_PUBLISH_ROOT
```

Expected: exit 0 for a faithful draft outside the known root.

Counterexamples, each expected to exit 1:
- Put a `#+WIKI_ID` source's next draft inside the indexed root.
- Modify or drop original `#+begin_src` contents.
- Change original `#+WIKI_ID`, `#+INGEST_ID` or other non-title header.
- Reuse the source file path as the output path.

Unknown indexed root: the structural check can still run without `--indexed-root`, but **isolation is not verified**. This script is not a model-output quality judge.

## Runtime drift to watch

The installed org-museum plugin may still expose a stale full `note-reforge` body; the repository's current plugin bootstrap routes to canonical `skills/note-reforge/SKILL.md`. Test the **installed runtime**, not only the repository text, before claiming deployment convergence. No repository-only patch proves the user's installed plugin is refreshed.

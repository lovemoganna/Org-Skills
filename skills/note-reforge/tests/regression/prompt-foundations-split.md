# Regression: prompt foundations mainline and XML preservation

## Observed input
- Published Org note: `lovemoganna/org-notes/notes/knowledge/prompt-foundations/1cda8367-e385-5232-83f6-fd1dbc3918da.org`.
- User goal: explain the prompt's four elements without process prose, duplicated explanations, or a full unrelated optimizer interrupting the lesson.
- Protected source: original `prompt_optimizer` XML block and three complete examples. XML must remain exact if moved, not silently deleted.
- User requested external-knowledge preflight, but no forced expansion.

## Expected editorial result
- Start with the actual teaching question: instructions, context, input, output requirements, applicability and verification.
- Remove redundant process narration; do not migrate filler into an appendix.
- Preserve original headers in the unpublished main draft. Keep the complete XML template in a linked, separate appendix only when it disrupts the main teaching flow.
- Keep the linked appendix outside the known publication index and do not copy the publishing identity to it.
- Verify references before adding factual corrections. No new evidence means no forced expansion.
- Do not modify the already published page without a separate authorization and publication check.

## Executable contract
```sh
python skills/note-reforge/tests/check_org_output.py \
  ORIGINAL.org MAIN.next.org \
  --appendix MAIN.xml-appendix.org \
  --indexed-root CONFIRMED_INDEX_ROOT
```

## Counterexamples
- Main note shrinks only because the original XML code is discarded.
- Appendix contains XML with a changed tag, source parameter or letter case.
- Source XML appears twice in main and appendix.
- Main references a nonexistent or wrong appendix path.
- Appendix copies WIKI_ID or WIKI_STATUS, or either draft artifact lands in confirmed indexed root.
- Notes get longer only to display search results that do not fix a core knowledge gap.

## Evidence limit
The automatic gate checks headers, original code-block fidelity, local appendix links, and draft placement. It does not assert that the prose is concise or factually accurate, nor that all images and public-page links render correctly.

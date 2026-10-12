# DocumentSpec input contract

## Files

`.json`: authoritative high-fidelity intermediate representation. `.md` and `.org`: supported structural subset, not complete dialect parsers. All source bytes are read as UTF-8 (optional BOM). Paragraph whitespace and inline emphasis markers may be normalized in Markdown/Org, so use `.json` when exact wording and typography must be retained.

Top-level required fields: `id`, `kind`, `title`, `kicker`, `lead`, `description`, `ending`, `chapters`. Optional `annotations` mapping (default empty).

Kinds: `poem`, `tutorial`, `report`, `article`.

- `id`: 1–54 ASCII chars: `^[a-z0-9][a-z0-9_-]{0,53}$`.
- `kind`: from supported values.
- Required text fields: strings of length 1–400 (non-whitespace).
- `chapters`: 1–40 chapters; unique `id`, `title` (1–90), optional `subtitle` (0–150), `blocks` (at least one).
- Blocks (400 maximum globally):
  - paragraph: `{"type":"paragraph","segments":["text",{"text":"annotated quotation","annotationId":"q1"}],"translation":"optional original translation","featured":false}`. Translation max 3000 chars; individual strings max 4000.
  - code: `{"type":"code","language":"sql","code":"SELECT 1;"}`. Code ≤16000 chars, language ≤32.
  - list: `{"type":"list","items":["item 1","item 2"]}`. 1–80 items, each ≤1000 chars.
  - table: `{"type":"table","columns":["Column 1"],"rows":[["value"]]}`. 1–12 columns, ≤150 rows; lengths validated.
  - callout: `{"type":"callout","label":"NOTE","text":"Details"}`. Label ≤100, body ≤3000.
- `annotations`: mapping of max 120 IDs to `{"text":"exact annotated quotation","gloss":"explanation"}`. Every annotation must be used exactly once and match the segment text. Do not generate unsupported claims as glosses.

Unrecognized JSON fields raise an error. The browser validates the core contract a second time. User content is rendered via DOM `textContent`; JSON embedding escapes `<`, `>` and `&` inside the script tag.

## Markdown supported

Title from first `# Heading`; section headings from subsequent `#` or `##`–`######`; paragraphs; `-` and numbered lists; GitHub-style pipe tables; blockquotes as callouts; fenced code blocks with a language tag; links preserved with both visible text and URL; inline code and basic emphasis markers. Inline HTML is displayed as literal text. Tables with escaped separators or nested complex blocks may require explicit JSON conversion.

## Org Mode supported

`#+TITLE:`, `*` through `******` headings, paragraphs, `#+begin_src LANGUAGE` / `#+end_src`, pipe tables with rule separators, flat `-` and numbered lists, `#+begin_quote` / `#+end_quote`. Common metadata (`#+AUTHOR`, `#+DATE`, `#+LANGUAGE`, `#+OPTIONS`) is omitted as non-body metadata; all other unfamiliar `#+` directives are rejected. Attributes, drawers, noweb, tangle, executable Babel semantics, Org references and embedded images are not executed or resolved. Convert such inputs explicitly instead of silently dropping them.

## Correctness rules

The generated HTML contains one bundled `DocumentSpec` and one input-specific document selector. Chapters, navigation, annotations and copy actions are all derived from the same document. For an unannotated report, the note panel must be hidden. Long URLs/hashes in prose may break within words but code and tables remain horizontally scrollable inside their regions. External HTTP assets must be absent.

# Conditional Google Sheets formula repair

Use the `sheets.replace_formula` host adapter only for a workbook the operator
controls exclusively. The host must attest its spreadsheet ID through
`exclusiveWorkbookIds` and separately approve the exact operation. A worksheet
in a shared or collaboratively edited workbook is ineligible. The adapter
does not infer exclusivity from a filename, spreadsheet ID, or model response.

The request identifies the spreadsheet, tab ID and title, zero-based cell
coordinates, expected arithmetic formula, replacement formula, and a fresh,
nonnegative marker tab ID. Preserve these fields together in the checkpoint.

1. Read the target's user-entered formula and compare it to the expected value.
2. Submit one atomic Sheets batch. Create a unique hidden receipt tab, copy the
   original formula to the same coordinates on that tab, record the operation
   identity, then run a case-sensitive whole-cell literal find-and-replace.
3. Require exactly one changed formula and one occurrence. Read the audit cells
   and the updated business cell from Google Sheets. Check the exact new formula
   and a defined, error-free effective value.
4. The independent business verifier must also check the recalculation against
   the inputs. The adapter cannot infer the intended financial or business rule.

The stable marker prevents duplicate commits while retained. On a lost receipt,
`verifyWrite` reads the provider-owned signature, pre-image and current result.
A changed post-image, missing or conflicting marker, or mismatching pre-image
cannot confirm the operation. A conflict between the initial read and batch can
leave a hidden receipt tab even when zero business formulas matched. Keep the
receipt for reconciliation. Do not resubmit the batch with a new marker.

Google's conditional predicate compares cell text; it does not implement
spreadsheet revision CAS or typed cell CAS. A concurrent change to literal text
that looks exactly like the old formula is indistinguishable to the predicate.
The exclusive-host scope prevents use on workbooks subject to this race.
Deleting or modifying a receipt tab invalidates recovery evidence. This adapter
accepts bounded simple arithmetic expressions; formulas with function calls
and externally fetching expressions are rejected. Generic cell overwrites,
append and mixed batches retain the existing write gate.

For open-ended repairs within this boundary, configure the trusted host with
`sheetScope: {spreadsheet_id, sheetId, title, row, column, markerId}` and
`exclusiveWorkbookIds: [spreadsheet_id]`. Omit both formulas. The adapter
performs a real read of the target, exposes its observed formula to the native
selector, and accepts only a single replacement assembled from numeric literals,
same-sheet cell references and arithmetic. A user instruction must authorize the
edit and creation of the audit tab. The original DAG pins the authorized request
before the sink call. Resuming that same checkpoint uses its original expected and
replacement formulas, so an already-committed post-image cannot become the
baseline for a new write. Use `sheetGrant` when both formulas are known in advance.

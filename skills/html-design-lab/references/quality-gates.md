# V6.0 Loop QA contract

| Gate | Evidence needed | Decision |
|---|---|---|
| G0 Task integrity | Input exists; parser matches actual syntax; output file contract set; dependencies known | fail/blocked when missing |
| G1 Trace | Hashes for source/template/output; exact commands; error log | fail if unreproducible |
| G2 Claim evidence | Source text/title/chapters/code/tables/notes directly compared with emitted DocumentSpec | do not self-certify subjective quality |
| G3 Acceptance | Browser actually renders each generated document; navigation and key actions work | an injected HTML DOM is not `file://` proof |
| G4 Safety | Embedded strings escaped; malicious HTML remains text; imported malformed JSON rejected; output contains no CDN | fail for executable untrusted HTML |
| G5 Regression | Poem, SQL tutorial, real report; mobile and desktop; positive and negative cases | stop release for blocking regression |
| G6 Maintainability | One renderer owner, one generation entry point, no duplicated document-specific UI logic | weigh change against cost |

Browser smoke: zero uncaught JS errors, 30 style registrations and clickable switching, correct document title and chapter navigation, responsive `documentElement.scrollWidth <= innerWidth`, no vanished core blocks, and critical controls (copy, notes, JSON export, modal close) functional. Generated HTML must not contain the V4.5 compatibility self-test DOM/CSS/JS or development markers. SQL/Python/JS/Shell blocks must display offline syntax token colors without changing `code.textContent`, executing tags, or losing copy fidelity. At least one malformed/hostile input is rejected or safely encoded.

Do not equate screenshot difference, automated pass count, or self-evaluation with independent award-level visual review. Chrome/Firefox/Safari and `file://` require actual boundary evidence. Use PASS only for verified scope; CONDITIONAL PASS for delivered working files with bounded compatibility or visual review gaps.

Loop record should contain: baseline → first failing test → root-cause hypothesis → patch → independent rerun → results, regressions, residual uncertainty, rollback path, stop reason.

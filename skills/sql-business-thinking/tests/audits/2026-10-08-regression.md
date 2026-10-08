# sql-business-thinking | 2026-10-08 regression audit

## Scope and revisions

- Baseline: [e35c0fc4ccf96e4072475fa352cfed558ed318f5](https://github.com/lovemoganna/Org-Skills/commit/e35c0fc4ccf96e4072475fa352cfed558ed318f5)
- Native materialization fix: [10db58df67172b7b92f2a2887943ce886994cd3a](https://github.com/lovemoganna/Org-Skills/commit/10db58df67172b7b92f2a2887943ce886994cd3a)
- URL-contract assertion fix: [5f5d4773b58d3618ddb9cf4633b33f9e61a527d4](https://github.com/lovemoganna/Org-Skills/commit/5f5d4773b58d3618ddb9cf4633b33f9e61a527d4)
- Core and mutation CI: [a89991e15b3ce6cb766c372dd27835d560f676ce](https://github.com/lovemoganna/Org-Skills/commit/a89991e15b3ce6cb766c372dd27835d560f676ce)
- Duplicate stage-run removal: [3b7d8ad31e2b44809e2dafb39ccf5274670f1fd7](https://github.com/lovemoganna/Org-Skills/commit/3b7d8ad31e2b44809e2dafb39ccf5274670f1fd7)
- Independent XLSX holdout: [9bd1b9634fe17006127f52fe4cceebf32b987d21](https://github.com/lovemoganna/Org-Skills/commit/9bd1b9634fe17006127f52fe4cceebf32b987d21)

## Test matrix — actual executions only

| Group | Scope and observed result | Evidence | Status |
|---|---|---|---|
| Original D02 | Native DuckDB 1.4.2 reads only users, fiat_transactions, crypto_transactions, exchange_rates via unchanged Google export URL; creates one TEMP TABLE per sheet; row counts 10 / 25 / 25 / 8; SQL and CSV SHA256 verified | [CI 37776137372](https://github.com/lovemoganna/Org-Skills/actions/runs/37776137372), [CI 37776614966](https://github.com/lovemoganna/Org-Skills/actions/runs/37776614966) | PASS |
| Original D03 | Native source sheets each materialized once; 9 existing quality checks passed | [CI 37776137617](https://github.com/lovemoganna/Org-Skills/actions/runs/37776137617) | PASS |
| Existing core tests | Existing check_repo.py runs stage regression cases including D08/D09/D12–D18/D21–D23 and D20/D21 handoff checks; no synthetic fixture is called a fresh business result | [CI 37776137648](https://github.com/lovemoganna/Org-Skills/actions/runs/37776137648), [CI 37776498465](https://github.com/lovemoganna/Org-Skills/actions/runs/37776498465) | PASS for automated cases |
| Independent negative tests | 19 separately changed SQL variants rejected; covers VFS alias, URL change, banned/duplicate Sheet, header, fifth scan, bootstrap duplication/omission, missing CTAS, raw reread | [CI 37776137648](https://github.com/lovemoganna/Org-Skills/actions/runs/37776137648) | PASS |
| Independent positive holdout | Isolated synthetic XLSX generated with DuckDB COPY, read by DuckDB read_xlsx and CTAS; source and materialized tables equal by bilateral EXCEPT ALL. Expected rows are derived from the generated source, not hardcoded business answers | [CI 37776614966](https://github.com/lovemoganna/Org-Skills/actions/runs/37776614966), artifact 11550064197 | PASS |
| Wasm / historic HTML | Existing discovery and static D23 rendered-QA checks passed; these are not a current autonomously generated report | [CI 37776137352](https://github.com/lovemoganna/Org-Skills/actions/runs/37776137352) | PASS for scoped checks |
| Full current Autopilot E2E | No fresh, model-directed D04–D23 sequence on a new full analysis culminating in a newly rendered deliverable at the same revision | None | NOT VERIFIED |

## Comparison

| Measured property | Before | After | Interpretation |
|---|---|---|---|
| Native D02 direct source scans | 4 | 4 | Source read count retained |
| Native D02 temporary materialization tables | 0 | 4 | Fixed contract |
| Native D03 temporary views | 4 | 0 | Eliminated repeated underlying source scan risk |
| Native D03 temporary materialization tables | 0 | 4 | Fixed contract |
| 2026-10-08 4-sheet row counts | 10 / 25 / 25 / 8 | 10 / 25 / 25 / 8 | No difference in row counts |
| D02 exported CSV hashes using same 2026-10-08 old/latest vs new | Same in all 4 sheets | Same in all 4 sheets | Data-output comparison is like for like |
| Data quality | Historic 2026-10-07 snapshot had 1 failed order-id date check | 2026-10-08 snapshot had 9/9 PASS | Data snapshot changed; NOT a code-fix effect |
| Normal Skill router modes | 4 | 4 | No loss of routing rules |
| Named critical-rule assertions in check_repo.py | 39 | 39 | No deletion in tested critical-rule list |
| Main SKILL.md | 6,211 characters; 79 lines; 12,567 bytes | Identical blob e6b468be2f25dc3f51ffe25717904878142a6d6c | No added prompt context |
| 9 on-demand reference files | 168,280 bytes combined | Identical blobs | No added reference context; loading remains conditional |
| SKILL.md + reference source files | 180,847 bytes total | Same | Same complete instruction payload under identical loading |
| Test assets | Existing test scripts | 1 additional narrow source-contract test script | Additional QA code, not always-loaded prompt content |
| Redundant CI invocation | Core stage scripts ran again in the added CI step | Removed repeat; new independent cases still run | Reduced unnecessary execution |

The number 39 counts named entries in the repository's critical_rules list; it is **not** an exhaustive count of every sentence-level rule. Token costs depend on tokenizer and loading path. Byte and blob equality establishes no change under the same tokenizer/loading path; it does not claim a measured runtime token bill.

### Permission and data boundaries

Source is the explicitly approved Google Sheets XLSX export URL. Normal tests read content of only four allowed sheets and do not use forbidden worksheets as truth sources. Independent holdout uses an isolated synthetic workbook and is not business evidence. Testing uses generated CSV artifacts for comparison but **original business reads still run as unchanged DuckDB read_xlsx URL SQL**.

### Release and rollback decision

- Scope-specific regression: PASS. Code and tests are committed to main.
- No major regression observed in the covered cases. No rollback necessary.
- "Stop after two consecutive rounds without improvement" was not triggered: each repair phase either removed a concrete failure or removed redundant CI execution.
- Full Skill Autopilot E2E certification: **NOT VERIFIED**. Do not advertise full E2E PASS or treat historic D22/D23 artifacts as new analysis.
- This document is a test audit, not a complete new business SQL report. A full production certification requires a separately verified autonomous D04–D23 run on the locked source and final current HTML.

# Standard entry follow-up

The comparison start was PR #122 at `50d310f75d3b2c2c597274715be2ea669798873a`. The previous controlled pair returned BLOCKED for Excel and NOT_VERIFIED for recruitment. This follow-up uses new synthetic trades, a 20-minute reporting window, and a search for sanctions/KYB positions rather than market surveillance. It exercises the standard launcher with explicit resource grants and the existing Work native model callbacks. No per-case adapter injection or passing of raw business data between steps by the operator.

## Excel

The source sheet had 33 execution rows, 30 unique execution IDs across three markets. The runner created a copy with one analysis tab and one native chart with three series. A separate cumulative-interval FIFO calculation agreed with all 15 market-and-window results, including 10.75 unmatched base units across the fixture. This number is the fixture total across unlike assets and is presented for test reconciliation only. The verifier compared every original cell value. The source checksum stayed unchanged.

## Recruitment

| Attempt | Outcome | Evidence |
| --- | --- | --- |
| Before employer board substitution | BLOCKED | One verified role and one expired result. The two-role write grant did not open. |
| With board substitution and broad keyword matching | NOT_VERIFIED | KYB software engineering role reached the isolated tab. Independent duty review rejected the result. |
| With explicit title exclusions | VERIFIED | Initial search found one usable role and two closed records. The same run queried the employer board, checked individual application schemas, filtered adjacent roles and wrote two valid vacancies in one scoped batch. Readback matched the two fresh provider observations. |

Final official application IDs were [5012271101](https://job-boards.eu.greenhouse.io/binance/jobs/5012271101) and [5040761101](https://job-boards.eu.greenhouse.io/binance/jobs/5040761101). They had 12 and 15 application questions respectively. A closed search hit was retained as counterevidence under Parallel request `search_18a7df090704d65eff85ce32def9218f`.

The final two runs verify these two standard-entry workflows. Earlier failures led to code and selection criteria changes. This follow-up is not a strictly blinded A/B replay or a timed comparison with a fresh direct arm. The runtime still uses native model planning and a separate verification callback. Current employer lookup covers Greenhouse boards named by search evidence. It does not generalize to all ATS platforms.

## Regression

43 JavaScript and 51 Python tests passed locally, including closed search result replacement, scoped sheet writes, rejected injected job rows, workbook create-only dispatch, and receipt binding.

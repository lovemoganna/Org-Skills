# Trading Simulation Coach — First Execution Check (2026-10-20)

## Verdict

**13/13 deterministic scenario assertions PASS.** This is a policy/risk calculation execution check, **not** live KKING site operation, independent LLM Skill invocation, or evidence of profitable trading. PR remains draft; promotion is blocked pending real end-to-end verification.

## Sources and provenance

- Provider: Binance public USDⓈ-M futures kline, BTCUSDT, interval 1h, retrieved via the connected Binance read-only market-data tool.
- Query: `startTime=1790812800000`, `endTime=1790985600000`, `limit=60`.
- Checked-in source: `tests/fixtures/btcusdt_1h_oct2026.json`; **49** chronologically contiguous bars; OHLC consistency independently checked.
- Local execution: same first **11** actual provider bars copied verbatim into the container subset fixture to run the assertions offline, without network access; the stop-loss scenario outcome is independently reproduced on all 49 bars via connector read and computation.
- Test code: `tests/run_contract_regression.mjs`; run `node skills/trading-simulation-coach/tests/run_contract_regression.mjs` from repository root. No third-party packages required.
- The committed runner was verified for file presence and syntax by inspection, not executed by remote CI during this run. A logically equivalent local regression was executed and returned 13 PASS / 0 FAIL.

## Executed checks

| Case | Content | Local result |
|---|---|---|
| D00 | Market-data schema, OHLC, chronological bars | PASS |
| B01 | 50 U risk budget, 2.2% total risk rate, 2272.73 U max notional | PASS |
| B02 | Historical blind decision excludes unseen bars, revealed sample contaminated | PASS |
| B03 | Profit does not excuse widening a stop against plan | PASS |
| B04 | Real historical price reaches 84,000 stop, realized simulated loss accounts for fees/slippage | PASS |
| B05 | Limit price touched, no fill confirmation, position remains zero | PASS |
| B06 | Research released after historical decision cannot enter the blind test | PASS |
| B07 | Proposed notional above risk budget is rejected | PASS |
| B08 | Missing fee model blocks position sizing | PASS |
| B09 | Partial fill creates partial position only | PASS |
| B10 | No signal → WAIT; zero position | PASS |
| B11 | Reaching -3R session threshold blocks subsequent trading even after notional balance reset | PASS |
| B12 | Previously used sample cannot be counted as independent validation | PASS |

### B04 numeric receipt

- Historical decision candle: index 5, closing entry assumed at **84,259.90 USDT**.
- Subsequent index 6 low: **84,076.60** (not yet stopped).
- Subsequent index 7 low: **83,277.30** (stop of **84,000** crossed).
- Assumed fill model: `stop * (1 - 0.001)` = **83,916.00**; assumed round-trip fee **0.10%**; equity 10,000 U; 0.5% risk budget (50 U).
- Result: **-49.9496 USDT** simulated net PnL, **-0.998992 R**. **NOT** exchange order or KKING recorded fill.
- Historical candles are observation data; stop fills, commissions, and position are explicitly hypothetical.

## Unknowns / blocked acceptance

1. **KKING UI E2E NOT RUN.** Browser interaction was unavailable in this chat (connected browser requires originating browser context). The KKING page was not operated, and no KKING order receipt exists.
2. **Independent model/Eval NOT RUN.** The model has not been separately spawned with an isolated invocation of `SKILL.md`; deterministic tests do not measure routing, content judgment, or model adherence.
3. No historical tick order book, stop-order priority, fill guarantee, real funding/liq model, or profitability inference.
4. The standalone repo runner needs a GitHub Actions or independent environment execution receipt before claiming remote reproducibility.

## Next release gate

Keep PR draft until (a) KKING or equivalent user-approved simulator can be interacted with and its resulting order log is verified, (b) at least one isolated agent run executes the actual Skill against blind input, (c) a separate reviewer checks evidence versus assertion, and (d) regression source and results are reproducible from the committed fixture without modifying the stable `main` branch.

**Decision: HOLD — verified deterministic core; E2E evidence missing.**

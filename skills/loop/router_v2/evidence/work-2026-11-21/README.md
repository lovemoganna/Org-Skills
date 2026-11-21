# Work execution, 2026-11-21

| Case | Result | Evidence |
|---|---|---|
| A | Prior bridge reproduced a pending read with zero receipts. The candidate actually read two source files and produced a diagnosis. The historical scheduler's deployment was outside the repair. | [TaskSpec](A-taskspec.json), [baseline](A/baseline-host.json), [trace](A/trace.jsonl), [diagnosis](A/diagnosis-skill-output.json), [regressions](A/regression.json) |
| B | Three pinned sources support a gap in the original model answer's release-check coverage. The current Work model produced a reusable release checklist. During the replay it chose the checklist step only after reading the saved causal output. | [Original trace](B/trace.jsonl), [replay diagnosis](B-replay-diagnosis/causes-skill-output.json), [follow-on TaskSpec with input hash](B-replay-card-taskspec.json), [release checklist](B-replay-card/card-skill-output.json) |
| C | Actual GitHub 404 followed by one path correction for the same repo and revision. The recovered content matched pinned Git bytes. | [404 receipt](C-replay/read-1-receipt.json), [recovered receipt](C-replay/read-2-receipt.json), [trace](C-replay/trace.jsonl) |

The [independent review](independent-review.json) assessed the original three runs and identified two false-success cases for individual step records. The follow-up driver requires the expected fields in connector responses and checks local Skill bytes against both the catalog and the specified Git object. `test_work_host.js` exercises those failures with fixture responses. The B and C replays used the tightened driver and live reads.

The [three-arm archive](three-arm-raw.zip) contains the frozen task and rubric, original commands and outputs, treatment map and independent blind verdict. Three fresh Work sessions used the same native model capability and isolated context with separate scratch folders in a shared executor. Single Skill, fixed chain and dynamic routing each scored 5/5 on one real local recovery task. The dynamic arm chose direct execution. The fixed chain logged three extra auxiliary subprocesses under the reviewer's counting rule. Token cost was unavailable. One case cannot establish a general quality or cost advantage.

The driver runs in the active Work session. It dispatches its allowlisted GitHub reads and preserves the model's Skill outputs. The Python bridge does not launch a native model session. Session status remains `RECEIPTS_RECORDED_UNVERIFIED`; use the original artifacts and independent checks for the scope of each completed result.

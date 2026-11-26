# Skill Router V2.0.0 — Work execution bridge

**Stable scope** is Work-hosted GitHub reads, Skill routing, receipt recording and one corrected file-path retry. The existing loop S1/S2/S3/S4/S5 own intent, task specification, orchestration, verification and evolution.

## Local CLI capabilities

- Discover names, descriptions, source hashes and locations from repository SKILL.md frontmatter; never execute discovered instructions.
- Show lexical candidate matches. These are *not* guaranteed semantic matches.
- Choose direct/chain using observable approximations of loop S3 complexity signals; direct is the default. ChainSpec is limited to six actions.
- Execute an explicit, allowlisted local-file TaskSpec (read_text/write_text/replace_text/assert_contains), requiring the separate host CLI --authorize-write flag for mutations.
- Produce real local filesystem receipts (SHA-256), append-only state events in trace.jsonl and a per-criterion run report. Recheck the current workspace against receipts and acceptance.
- Refuse any required model Skill without an execution binding. This release does **not** autonomously call ChatGPT or any third-party model API.

## Execution boundaries

- The local CLI takes an explicit JSON task. The Work model compiles natural language and selects Skills in the hosted flow.
- The Work host adapter dispatches GitHub reads only. Production scheduling needs its own rollout and verification.
- No claim that a CLI boolean proves user authorization. A trusted host must establish consent before passing --authorize-write. A discovered Skill is untrusted until a reviewed executor binds it.
- No independent validation: local recheck is self-check only. COMPLETED_UNVERIFIED is **not** VERIFIED.
- No full security sandbox: local path checks and allowlisted file operations are defense-in-depth, not a replacement for OS isolation or a privileged tool broker.

## Run locally (Python 3.11+, standard library only)

From repository root:

    python3 skills/loop/router_v2/tests.py
    python3 skills/loop/router_v2/engine.py discover --skills-root skills --query causal-net-loop
    python3 skills/loop/router_v2/engine.py plan --task skills/loop/router_v2/demo_write.json

Run the first real local file operation and then recheck:

    mkdir -p /tmp/router-v2-work
    python3 skills/loop/router_v2/engine.py run --task skills/loop/router_v2/demo_write.json --workspace /tmp/router-v2-work --run-dir /tmp/router-v2-run1 --authorize-write
    python3 skills/loop/router_v2/engine.py recheck --task skills/loop/router_v2/demo_write.json --workspace /tmp/router-v2-work --report /tmp/router-v2-run1/report.json

Use distinct --workspace and --run-dir for the second demo_replace.json. Never reuse run directories; trace and report are not append-overwritten. Authorization applies to *mutations*, not to reading an untrusted Skill's instructions.

## State and evidence contract

| State | Meaning |
|---|---|
| PLANNED | No action yet |
| RUNNING | At least an execution attempt started |
| BLOCKED | Tool binding or explicit host write permission missing |
| FAILED | Action, evidence recheck, or acceptance failed |
| COMPLETED_UNVERIFIED | Real local action receipts exist; required local acceptance passed; independent goal check missing |
| VERIFIED | Requires external independent run-level evidence |

Each JSON task includes id, goal, actions, acceptance and optionally required_skills. Action ids/dependencies are validated; acceptance ids are unique and required. Receipts describe **actual file state**; intermediate receipts are marked superseded during recheck. A filesystem mutation may partially complete before a later action fails: do not treat a failed run as automatically rolled back.

## Relationship to loop

- Existing S3: owner of deciding direct/chain, ordering and on_fail. The bridge uses compatible field names and records a stopped step unless a supported retry is requested.
- Existing S4: owner of independent acceptance, goal and side-effect checks. Local run report deliberately leaves goal_check as NOT_INDEPENDENTLY_VERIFIED.
- Do not add executable code to SKILL.md files or assume discovery grants permission. Add provider adapters only after tool/authorization contract testing.


## Native Work host adapter

The thin natural-language host entrypoint is at [skills/skill-router/SKILL.md](../../skill-router/SKILL.md). When a ChatGPT/Work host is capable of reading that file, the **host model** interprets the user task, chooses existing Skills and actually calls its connected tools. The Python bridge is a deterministic step ledger; it has no model API client and no access to ChatGPT/Work's private runtime.

Example (from repository root):

    python3 skills/loop/router_v2/host_bridge.py init --plan skills/loop/router_v2/host_demo.json --skills-root skills --session /tmp/router-v2-host --host-capabilities github.get_pr_info,github.fetch_file
    python3 skills/loop/router_v2/host_bridge.py next --session /tmp/router-v2-host

The returned request is **not executed** by these commands. After the authorized host actually calls the named tool, it can record the response reference as a JSON object with step_id, request_sha256, status, receipt_ref and artifact_ref:

    python3 skills/loop/router_v2/host_bridge.py record --session /tmp/router-v2-host --result /tmp/actual-host-result.json

In Work code mode, load the versioned `work_host.js` from the checkout and call `workHost(tools, checkout)`. After `init(session, planPath)`, call `advance(session)` to execute GitHub reads and save original connector responses. At a Skill step the current model applies the selected Skill and calls `finishSkill(session, pendingRequest, output, source)` with its output and source revision. Call `advance` again to resume. Run one driver per session. The driver dispatches only GitHub reads. Mutations go through the trusted host's separate authorization.

A failed GitHub file read can be resumed once via `retryRead(session, step, correctedPath, reason)` and then `advance(session)`. The original failure, request digest, repository and ref are retained. Other failures halt. A blocked step or write cannot be retried through this command.

The [Work run records](evidence/work-2026-11-21/) contain live tool responses, model outputs and recovery evidence. The [stability evaluation](evidence/stability-2026-11-21/) records independent blind review and a one-shot unattended Work run. CI checks deterministic behavior and local sandbox executions. The bridge records host reports as `RECEIPTS_RECORDED_UNVERIFIED`. Evaluate goal completion against the original artifacts and independent review.

# Skill Router V2 — candidate execution bridge

**Status: CANDIDATE / DO_NOT_PROMOTE.** Built on PR #116 (failure-repair-v1); no changes to stable loop or main. The existing loop S1/S2/S3/S4/S5 remain the owner of intent, task specification, orchestration, verification and evolution.

## What this candidate actually does

- Discover names, descriptions, source hashes and locations from repository SKILL.md frontmatter; never execute discovered instructions.
- Show lexical candidate matches. These are *not* guaranteed semantic matches.
- Choose direct/chain using observable approximations of loop S3 complexity signals; direct is the default. ChainSpec is limited to six actions.
- Execute an explicit, allowlisted local-file TaskSpec (read_text/write_text/replace_text/assert_contains), requiring the separate host CLI --authorize-write flag for mutations.
- Produce real local filesystem receipts (SHA-256), append-only state events in trace.jsonl and a per-criterion run report. Recheck the current workspace against receipts and acceptance.
- Refuse any required model Skill without an execution binding. This release does **not** autonomously call ChatGPT or any third-party model API.

## What it does not do

- No autonomous natural-language-to-TaskSpec conversion or semantic Skill orchestration. The task manifest is explicit JSON.
- No GitHub write adapter, independent model executor, isolated model judges, real three-arm A/B test, deployment or production automation.
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
| VERIFIED | Not emitted by this candidate. External independent run-level evidence is required |

Each JSON task includes id, goal, actions, acceptance and optionally required_skills. Action ids/dependencies are validated; acceptance ids are unique and required. Receipts describe **actual file state**; intermediate receipts are marked superseded during recheck. A filesystem mutation may partially complete before a later action fails: do not treat a failed run as automatically rolled back.

## Relationship to loop and failure-repair-v1

- Existing S3: owner of deciding direct/chain, ordering and on_fail. The candidate uses compatible field names and currently stops on step failure.
- Existing S4: owner of independent acceptance, goal and side-effect checks. Local run report deliberately leaves goal_check as NOT_INDEPENDENTLY_VERIFIED.
- Existing failure-repair-v1: continues to own failure diagnosis with evidence gates. No model-based causal/keypoint steps are automatically executed here.
- Do not add executable code to SKILL.md files or assume discovery grants permission. Add provider adapters only after tool/authorization contract testing.


## Native host adapter (P0 candidate, not Work API integration)

The thin natural-language host entrypoint is at [skills/skill-router/SKILL.md](../../skill-router/SKILL.md). When a ChatGPT/Work host is capable of reading that file, the **host model** interprets the user task, chooses existing Skills and actually calls its connected tools. The Python bridge is a deterministic step ledger; it has no model API client and no access to ChatGPT/Work's private runtime.

Example (from repository root):

    python3 skills/loop/router_v2/host_bridge.py init --plan skills/loop/router_v2/host_demo.json --skills-root skills --session /tmp/router-v2-host --host-capabilities github.get_pr_info,github.fetch_file
    python3 skills/loop/router_v2/host_bridge.py next --session /tmp/router-v2-host

The returned request is **not executed** by these commands. After the authorized host actually calls the named tool, it can record the response reference as a JSON object with step_id, request_sha256, status, receipt_ref and artifact_ref:

    python3 skills/loop/router_v2/host_bridge.py record --session /tmp/router-v2-host --result /tmp/actual-host-result.json

For a Skill step the host must actually apply that Skill to the evidence; merely selecting its name does not count as execution. The bridge only checks protocol consistency, not source authenticity. Steps are capped at six, forward dependencies are rejected, write capabilities require a separate authorization declaration, and any failed step halts the sequence. Tool types are an explicit, conservative GitHub allowlist; all other integrations need reviewed bindings.

**Verified by CI:** 21 existing local-file/router tests, 18 new host protocol tests, two genuine GitHub Actions sandbox file runs, permission failure, and the repository's existing regression suite. Host protocol tests use **mocked receipts**; they cannot prove the model independently executed a Skill. The CI host demo deliberately stops at AWAITING_HOST_EXECUTION and does not forge a tool response.

**Still missing for stable:** a supported, callable Work model/tool execution interface (none was provided to this Python process); actual independently checked multi-Skill end-to-end runs; frozen single/fixed/dynamic A/B. Do not imply that loading a SKILL.md automatically installs a Skill into a running ChatGPT environment.

## Evidence, evaluation and promotion gate

CI runs 21 tests plus two **distinct real local filesystem executions** (write-note and status-text transform), rechecks outputs, and uploads JSONL traces and reports as workflow artifacts. This proves sandbox file actions, not live business work or autonomous Skill execution.

The frozen 12-task single/fixed/dynamic model study from the upgrade plan remains NOT_RUN until independent model workers and a blind evaluator are available. Record matched inputs, model/permissions, artifacts, independent scoring, costs and counterexamples. Do not turn contract PASS into a claimed improvement or score.

Promotion to verified requires at least two different genuine tasks with independent, auditable outcomes and no key regression; completing two local fixture demos alone is **insufficient**. Keep this PR draft; do not merge main without new evidence.

Rollback: close the candidate PR or delete this directory and its dedicated CI workflow. Existing stable Skills are unaffected.

---
name: loop-engineering-meta
description: Convert ambiguous, repeatable, high-value, or failure-prone work into a traceable improvement loop; diagnose the earliest root failure, apply one minimal harness change, replay under controlled conditions, evaluate with evidence, and compile stable knowledge into reusable child skills. Use for research, writing, coding, analytics, ontology modeling, operations, workflow repair, prompt/agent improvement, and quality control.
---

# Loop Engineering Meta Skill

## 1. Mission

Turn a one-off task or unstable workflow into a repeatable, testable, evidence-backed operating system.

This is a meta-skill. It does not replace domain expertise. It creates a domain-specific loop instance, supervises execution, identifies the earliest failure, repairs the surrounding harness, reruns the task, and promotes proven improvements into reusable assets or child skills.

A valid loop must improve at least one of the following:

- task result;
- evidence quality;
- execution reliability;
- human intervention rate;
- safety or permission control;
- reuse and maintainability.

A loop that only rewrites the answer without changing evidence, process, constraints, tools, validation, or reusable assets is not Loop Engineering.

## 2. Core Formula

```text
Loop Engineering
= truthful problem framing
+ executable harness
+ observable trace
+ root-cause diagnosis
+ controlled intervention
+ independent evaluation
+ reusable consolidation
```

The worker may be a person, model, agent, script, or team.

The harness is everything around the worker that affects reliable execution:

```text
Harness
= context
+ semantic model
+ instructions
+ examples
+ tools
+ permissions
+ workflow
+ state
+ validation
+ recovery
+ observability
```

## 3. Non-negotiable Rules

1. Truth before consistency. Separate verified facts, assumptions, inferences, and unknowns.
2. Evidence before confidence. Do not treat fluent output or self-reported completion as proof.
3. Diagnose the earliest material failure. Later defects may be downstream symptoms.
4. Change one primary variable per iteration unless variables are technically inseparable.
5. Compare under controlled conditions. Keep the worker, task class, permissions, and starting state stable where practical.
6. Verify at the boundary of the claim. A claimed deployment requires deployment evidence; a claimed factual conclusion requires source evidence.
7. Put rules near their owner. Prefer schemas, types, tests, evaluators, tool constraints, and permissions over repeated prose reminders.
8. Separate capability from authority. A tool being callable does not mean its action is authorized.
9. Preserve counterevidence. Do not delete failed cases or unfavorable runs to improve apparent scores.
10. Stop when the loop no longer produces new evidence, meaningful gain, or maintainable improvements.
11. Escalate irreversible, regulated, destructive, financial, privacy-sensitive, or high-impact decisions to an authorized human.
12. Do not create extra agents, documents, frameworks, or abstractions unless they remove a demonstrated bottleneck.

## 4. Loop Ontology

Use these entities internally. Create explicit records when the task is complex, repeated, regulated, or high impact.

| Entity | Meaning |
|---|---|
| `TaskSpec` | Goal, input, constraints, risks, acceptance criteria, required evidence |
| `Worker` | Model, agent, person, script, or team executing the task |
| `Harness` | Context, tools, permissions, rules, workflow, validators, recovery paths |
| `Run` | One controlled execution attempt |
| `Trace` | Observable sequence of inputs, decisions, tool calls, outputs, errors, and interventions |
| `Claim` | A statement asserted by the result |
| `Evidence` | Material that supports or contradicts a claim |
| `Defect` | A material gap between expected and observed behavior |
| `RootCause` | Earliest actionable cause that explains the defect |
| `Hypothesis` | Predicted causal effect of a proposed change |
| `Patch` | Minimal change to the harness, task specification, or reusable asset |
| `EvalCase` | Representative test case with expected properties |
| `Gate` | Pass/fail decision at a defined stage |
| `Decision` | Keep, revise, revert, escalate, or stop |
| `ReusableAsset` | Skill, script, template, schema, test, evaluator, runbook, or reference |

Key relations:

```text
TaskSpec --executed_by--> Worker
Worker --operates_within--> Harness
Run --produces--> Trace
Trace --contains--> Claim
Claim --supported_or_refuted_by--> Evidence
Trace --reveals--> Defect
Defect --explained_by--> RootCause
RootCause --addressed_by--> Patch
Patch --tested_by--> EvalCase
EvalCase --judged_by--> Gate
Decision --promotes_or_reverts--> Patch
Patch --may_create--> ReusableAsset
```

## 5. State Machine

```text
INTAKE
  ↓
FRAME
  ↓
BASELINE
  ↓
EXECUTE
  ↓
INSPECT
  ↓
DIAGNOSE
  ↓
PATCH
  ↓
REPLAY
  ↓
EVALUATE
  ├─ fail with new evidence → DIAGNOSE
  ├─ fail without new evidence → ESCALATE or STOP
  └─ pass → SOLIDIFY
                 ↓
                EXIT
```

### 5.1 INTAKE

Collect or infer:

- requested outcome;
- target user;
- available inputs and sources;
- environment and tools;
- constraints and prohibited actions;
- risk level;
- expected artifact;
- time, cost, or iteration budget.

Infer reversible details when safe. Mark them as assumptions. Do not invent critical facts.

### 5.2 FRAME

Create a `TaskSpec`:

```yaml
goal:
non_goals:
inputs:
authoritative_sources:
assumptions:
constraints:
permissions:
risk_level:
acceptance_criteria:
required_evidence:
budget:
stop_conditions:
```

Reject or repair false premises before execution.

### 5.3 BASELINE

Run or inspect the current method before improving it when a baseline exists.

Record:

- worker and version where relevant;
- initial context;
- tools and permissions;
- starting state;
- result;
- trace;
- human interventions;
- elapsed time or cost when available;
- acceptance failures.

If no baseline exists, create a minimal first run.

### 5.4 EXECUTE

Perform the task using the smallest adequate workflow.

During execution:

- retrieve evidence before asserting unstable facts;
- use tools directly rather than asking humans to relay machine-readable information;
- record material decisions and tool failures;
- preserve intermediate artifacts needed for verification;
- stop unsafe or unauthorized actions.

Do not enter critique mode before producing or attempting the primary result.

### 5.5 INSPECT

Inspect the result and trace separately.

Ask:

1. What claims were made?
2. What evidence supports each material claim?
3. What was not completed?
4. Where did the first material divergence occur?
5. What human intervention was required?
6. Which failures are symptoms rather than causes?
7. Did the result satisfy the user's actual objective rather than only the literal wording?

### 5.6 DIAGNOSE

Classify the earliest material failure using the taxonomy in Section 6 (Failure Taxonomy) below.

Write one causal statement:

```text
The result failed at [earliest point]
because [root cause]
which produced [observable defect].
```

Then write a falsifiable hypothesis:

```text
If [minimal change] is made in [authoritative owner],
then [observable behavior] should improve on [representative case],
because [causal mechanism].

Supporting evidence:
Disconfirming evidence:
Expected maintenance cost:
Rollback:
```

Do not use “the model needs to try harder” as a root cause.

### 5.7 PATCH

Apply the smallest change that can test the hypothesis.

Preferred order:

1. correct the task definition or false premise;
2. repair authoritative data or context routing;
3. clarify semantic ownership through schema, ontology, state model, or API;
4. expose or repair a tool;
5. constrain permissions and dangerous actions;
6. add validation, evaluator, test, or recovery;
7. improve instructions or examples;
8. add orchestration or an additional agent only when simpler fixes are insufficient.

### 5.8 REPLAY

Replay in a fresh or reset context.

Hold stable where practical:

- task class;
- worker/model version;
- tool interface;
- permissions;
- initial state;
- evaluation cases.

Do not leak the desired answer from the repair session into the replay.

### 5.9 EVALUATE

Use Section 7 (Quality Gates) below.

Evaluation order:

```text
hard constraints
→ factual and semantic validity
→ task acceptance
→ evidence sufficiency
→ safety and authority
→ regression
→ efficiency
→ reuse and maintainability
```

Use deterministic checks where possible. Use model graders for judgment-heavy properties only with explicit rubrics and periodic human calibration.

### 5.10 SOLIDIFY

Promote a change only when:

- the worker actually used the new mechanism;
- representative cases improved;
- the observed improvement matches the causal hypothesis;
- no critical regression appeared;
- maintenance cost is acceptable;
- ownership is clear.

Store the learning at the lowest stable layer:

| Learning | Preferred owner |
|---|---|
| fact or source routing | reference, retrieval index, data contract |
| concept or relation | schema, ontology, type, state model |
| repeated operation | script, tool, runbook |
| invariant | validator, lint, test, policy |
| expected behavior | eval case and rubric |
| risky action | permission gate, approval, audit, rollback |
| repeated workflow | child skill |
| temporary observation | run record, not permanent instructions |

### 5.11 EXIT

Return:

1. primary result;
2. evidence and verification;
3. quality verdict;
4. changes made;
5. remaining risks or unknowns;
6. reusable assets created or updated;
7. stop reason.

## 6. Failure Taxonomy

Use the earliest applicable category.

| Code | Category | Typical symptom | Preferred repair |
|---|---|---|---|
| `F0` | False premise | task rests on incorrect assumption | correct premise and reframe |
| `F1` | Goal defect | polished answer solves wrong problem | acceptance criteria, non-goals |
| `F2` | Evidence/context defect | missing, stale, conflicting, or undiscoverable facts | authoritative sources, retrieval, freshness checks |
| `F3` | Semantic defect | terms, states, or entities are inconsistent | ontology, schema, type, state machine |
| `F4` | Tool defect | tool absent, hidden, brittle, or unverifiable | tool contract, discoverability, errors, retries |
| `F5` | Planning defect | dependencies or sequence are wrong | explicit plan, dependency graph, checkpoints |
| `F6` | Execution defect | correct plan is not completed | automation, retry, atomic steps, recovery |
| `F7` | Verification defect | completion is asserted without boundary evidence | tests, external checks, evaluators |
| `F8` | Authority/safety defect | action exceeds permission or lacks rollback | approval gate, sandbox, least privilege |
| `F9` | Regression defect | local gain damages other cases | regression suite, counterexamples |
| `F10` | Maintainability defect | fix adds duplication or hidden complexity | central owner, simplification, garbage collection |
| `F11` | Drift defect | formerly valid context or behavior decays | freshness checks, scheduled review, versioning |
| `F12` | Judge defect | evaluator rewards style or expected wording instead of correctness | rubric repair, blind review, human calibration |

## 7. Quality Gates

A critical gate failure blocks promotion.

### G0 — Task Integrity

Pass when:

- the goal is coherent;
- false premises are corrected;
- acceptance criteria are observable;
- required inputs exist or missing inputs are explicitly bounded.

### G1 — Trace Integrity

Pass when:

- material tool calls and decisions are observable;
- human interventions are recorded;
- failures are not hidden;
- the starting state can be reconstructed well enough for replay.

### G2 — Claim–Evidence Integrity

Pass when:

- every material factual claim has adequate support;
- source freshness matches the claim;
- contradictions are surfaced;
- assumptions and inferences are labeled;
- generated text is not used as evidence for itself.

### G3 — Result Acceptance

Pass when:

- all hard constraints are satisfied;
- the actual objective is met;
- the artifact is usable in the target environment;
- required evidence accompanies the result.

### G4 — Safety and Authority

Pass when:

- actions remain within authorization;
- sensitive or irreversible operations use approval gates;
- rollback or containment exists where needed;
- private data is minimized and handled appropriately.

### G5 — Regression

Pass when:

- representative positive cases still pass;
- at least one counterexample or edge case is checked;
- the patch does not merely overfit one observed failure.

### G6 — Reuse and Maintainability

Pass when:

- the fix has one clear owner;
- duplicated instructions are avoided;
- future workers can discover the mechanism;
- the maintenance burden is lower than the expected recurring benefit.

## 8. Loop Control

Default iteration budget: 3 repair cycles.

Continue only when all are true:

- new evidence appeared;
- a specific root cause is identifiable;
- a minimal testable patch exists;
- expected value exceeds the next iteration cost.

Stop or escalate when any is true:

- two consecutive iterations produce no new evidence;
- the same defect recurs after two materially different patches;
- evaluation cannot distinguish improvement;
- the task requires unavailable authority, data, or tooling;
- marginal benefit is lower than maintenance cost;
- residual risk exceeds the authorized threshold.

Never claim convergence merely because the output became longer, smoother, or more confident.

## 9. Domain Adapters

Instantiate only the adapter relevant to the task.

### 9.1 Research

Require:

- source hierarchy;
- publication date and event date;
- primary-source preference;
- claim-level citations;
- contradiction handling;
- uncertainty statement.

Boundary evidence: cited source content that directly supports each material claim.

### 9.2 Writing

Require:

- audience and purpose;
- factual baseline;
- argument or information structure;
- style constraints;
- unsupported-claim check;
- usability check in the intended channel.

Boundary evidence: source-backed claims plus a final text that satisfies the brief.

Do not treat stylistic preference as factual correctness.

### 9.3 Coding

Require:

- reproducible environment;
- failing case or acceptance test;
- implementation;
- unit/integration/end-to-end checks as applicable;
- lint/type/security checks;
- rollback or safe migration plan.

Boundary evidence: executed tests, runtime behavior, logs, screenshots, or deployment health matching the claim.

### 9.4 Data and Analytics

Require:

- metric definitions;
- grain and keys;
- source reconciliation;
- missing/duplicate/outlier checks;
- reproducible calculations;
- denominator and time-window checks;
- uncertainty and limitations.

Boundary evidence: query, notebook, formula, reconciliation table, and validated output.

### 9.5 Ontology

Require:

- competency questions;
- entities, events, states, relations, constraints, and provenance;
- unique semantic owners;
- valid and invalid event combinations;
- temporal and identity rules;
- inference tests;
- mapping from ontology to executable schemas, queries, or evaluators.

Boundary evidence: the ontology answers the competency questions and correctly accepts valid cases while rejecting invalid cases.

### 9.6 Operations

Require:

- trigger;
- inputs and dependencies;
- owner;
- state transitions;
- permissions;
- idempotency;
- retry and failure handling;
- audit trail;
- rollback;
- service-level expectation.

Boundary evidence: dry run, controlled execution, audit record, and recovery test.

## 10. Human Judgment Layer

Use human judgment where it has the highest leverage:

- choosing the real problem;
- resolving value conflicts;
- deciding acceptable risk;
- judging ambiguous quality;
- authorizing irreversible action;
- approving semantic or policy changes.

The human should not repeatedly perform machine-readable transfer work that can be exposed as context, tools, schemas, or tests.

## 11. Child Skill Compilation

Compile a child skill when a workflow is repeated, valuable, stable enough to specify, and passes:

- at least two distinct representative cases;
- at least one counterexample or edge case;
- all critical gates;
- one clean replay without hidden repair-session context.

Recommended structure:

```text
<child-skill>/
├── SKILL.md
├── references/
│   ├── domain-model.md
│   ├── quality-rubric.md
│   └── examples.md
├── scripts/
│   ├── validate.*
│   └── run.*
├── assets/
│   └── templates/
└── evals/
    ├── cases.*
    └── expected.*
```

A child `SKILL.md` must state:

- when to use and when not to use;
- required inputs;
- authoritative sources;
- exact workflow;
- tools and permissions;
- quality gates;
- output contract;
- failure and escalation paths;
- references, scripts, and evals.

Do not copy the entire meta-skill into every child skill. Keep only domain-specific instructions and link to shared references where the runtime permits.

## 12. Output Contract

For normal use, return this compact report:

```markdown
# Result
[Primary usable result]

# Evidence
[Material evidence and verification]

# Loop QA
- Verdict: PASS / CONDITIONAL PASS / FAIL / ESCALATE
- Earliest defect:
- Root cause:
- Patch tested:
- Replay result:
- Gates:
- Regressions:

# Consolidation
- Kept:
- Reverted:
- Reusable assets:
- Residual risks:
- Stop reason:
```

For simple tasks, collapse the report to the primary result plus one concise QA note. Do not expose private chain-of-thought. Report observable reasoning, evidence, decisions, and test results.

## 13. Fast Path

Use the fast path when the task is low risk, one-off, and objectively verifiable:

```text
Frame
→ Execute
→ Boundary verify
→ Deliver
```

Enter the full loop only if the result fails, the workflow is repeated, human intervention is material, or the task has high value or risk.

## 14. Invocation Examples

```text
Use loop-engineering-meta to repair this research workflow. Keep the model fixed, identify the earliest failure, change one primary variable per round, and compile the stable result into a child skill.
```

```text
Apply loop-engineering-meta to this ontology-training pipeline: fact baseline → ontology → event combination and inference → training material → assessment. Verify that the ontology is actually used rather than merely displayed.
```

```text
Use loop-engineering-meta to quality-control this report. Separate factual defects from writing defects, verify claims at their source boundary, and stop after three repair cycles unless new evidence justifies continuing.
```
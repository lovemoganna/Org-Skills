---
name: loop-engineering-meta
description: Convert ambiguous, repeatable, high-value, or failure-prone work into a traceable improvement loop; diagnose the earliest root failure, apply one minimal harness change, replay under controlled conditions, evaluate with evidence, and compile stable knowledge into reusable child skills. Use for research, writing, coding, analytics, ontology modeling, operations, workflow repair, prompt/agent improvement, and quality control.
---

# Loop Engineering Meta Skill

## 1. Mission

Turn a one-off task or unstable workflow into a repeatable, testable, evidence-backed operating system.

This is a meta-skill for **already-running workflow reliability and repair**, not a second intent router. For ambiguous new goals or direct/chain selection, use `skills/loop/SKILL.md`; keep deep root-cause analysis, paired replay and evidence-based recovery here. It does not replace domain expertise.

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

### 5.2a Skill / Prompt 调试专用：任务适配审查（执行前强制）

只有目标为**调试、维护或验收 Skill / Prompt** 时启用；这是通用测试门禁，不是业务执行 Skill。

1. **先读取真实被测版本**的职责、适用/不适用情形、输入输出、依赖及用户本次目标；不得依据名称、旧摘要或上一轮猜测指定测试材料。
2. 逐用例声明「任务需要哪些能力 → 被测对象明确提供哪些能力 → 原文/规则中的对应依据」。把**使用者意图**与文件表面特征分开：文章出现几行代码，不代表用户要求运行代码；要求可执行教程，则必须匹配可执行化能力。
3. **适配**才进入执行；**不适配**先修正测试案例、分流到实际负责的 Skill，标为「测试设计无效」，**不得把测试设计错误记为被测 Skill 失败**；**无法确定**则先补充范围证据，不能猜测或自报通过。
4. 多 Skill 编排时逐阶段核对各角色职责及交接契约；某一阶段不适配应定位该阶段的测试/路由问题，不牵连无关 Skill。

### 5.2b Skill / Prompt 调试专用：内容质量独立验收

测试能否运行、文件头/格式/语法是否合规属于**结构与执行质量**；是否解决目标问题属于**内容与效果质量**。两种评价**分开记录、不得相互替代**。

- 最少审查：①原始事实/输入契约是否保真；②重要判断、结论、实测声明是否有可追溯证据；③相比基线是否产生实际任务价值而不是仅改写/扩写；④成果在目标使用场景是否可用。按领域适配可观察的具体检查，不要求所有任务增加文字。
- 每项记录「通过 / 失败 / 待核验」及一条可复查证据；主张通过却无证据的一律按**证据不足**处理。源码校验通过**不能**证明文章内容正确、调研结论可信或使用价值提升。
- 真实内容验收优先使用独立任务复现、来源反查、反例、目标用户审阅或独立评价器；**同一执行者的自评不能冒充独立质量合格证明**。可验证部分先报告，主观价值未确认时标「有条件通过」，不能宣称整体合格。
- 对高质量原稿，**无实质增量时保留原状**是合格的维护决策。修复前后须比较实际收益与维护成本；不为了产出差异强行修改。
- 可用 `scripts/evaluate_case.py` 汇总范围/结构/内容的证据状态与中文裁决。该脚本**只检验判定契约**，不会自动判定事实真假；领域内容仍须来源核验、实际运行或独立评审。

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

### 5.6a Principle Steering (multi-step repairs only)

Use a named principle **only when observed evidence triggers it and it changes a concrete decision**. These names point to existing gates; they do not add another compulsory workflow. Select at most three unless a specific task requires more.

| Principle | Trigger | Decision it must change | Existing owner |
|---|---|---|---|
| **Attack the Premise** | Two fixes fail under the same assumption | Test the shared premise before attempting a third patch | 5.2, 5.6, 8 |
| **Subtract Before You Add** | About to add a rule, step, adapter, or agent | Remove or merge obsolete/overlapping mechanisms first | 3, 5.7, G6 |
| **Prove It Works** | A proxy (lint, self-report, attractive output) is being called success | Verify the actual artifact or user-facing boundary | 5.2b, 5.9, G2–G3 |
| **Test Behavior, Not Implementation** | A test rewards wording or internal structure rather than outcome | Replace it with observable acceptance and regression checks | 5.2b, G3, G5 |
| **Encode Lessons in Structure** | The same correction recurs | Place an enforceable check at the authoritative owner, not another reminder | 3, 5.10, G6 |

For each **actually used** principle, retain one audit record: `name | observed trigger | rejected choice -> chosen choice | verifiable artifact/trace`. The rejected and chosen choices must differ. Naming a principle, writing a rationale, or passing a structural check does not establish causal impact; evaluate the changed behavior in REPLAY and EVALUATE. Omit the record when no choice changed. Do not fabricate a hypothetical rejected choice after the fact.

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

### 5.8a Paired, Outcome-Based Eval (repeatable Skill / Agent repairs)

For noisy or repeated Skill / Agent improvements, compare the current version (`baseline`) against a separately stored candidate (`candidate`); retain the exact original version and do not silently overwrite it. A **task** is a test case; a **trial** is one fresh execution; a **trace** is the actions/outputs; an **outcome** is the independently checked final artifact or environment state. A successful trace, assertion that work is done, or valid syntax cannot replace outcome evidence.

1. Use at least three correctly scoped cases: **original failure**, **historically passing regression**, and **new generalization**. Record expected results and grader before running. If a test case is out of scope, repair the test design first (Section 5.2a).
2. For each case, run both arms with at least **3 fresh, isolated trials per arm** when behavior is nondeterministic (minimum 18 total attempts for 3 cases). Keep input, model/version, tool interface, starting-state contract, permissions and rubric equivalent; record any uncontrollable differences. No answer leakage, selective reruns, or cherry-picking.
3. Save each run's `run_id`, worker identity, exact condition identifiers, trace, actual output artifact, verified **outcome**, grader identity and evidence reference. Record latency/tokens/cost if available; never invent missing values.
4. Grade objective postconditions with executable code or state checks. For writing/research quality, use a separately identified model or human evaluator with explicit rubric and source-level review. Reject same-executor subjective self-grading. Keep transcript/process defects separate from outcome defects.
5. Compare **per-case trial success counts**, not just one lucky output; check every case for regression. A lower success count on any case blocks promotion pending diagnosis. No measurable gain means revert or retain baseline. Small 3-trial samples are exploratory, **not statistical proof** or a reason to claim overall reliability.
6. `scripts/compare_trials.py <experiment.json>` validates the comparison **record contract** and summarizes observed outcomes. Input: `experiment_id`; `cases[]` with `id`, `suite` (`failure|regression|generalization`), and fixed `controls` (`model, task_input_hash, tools_hash, environment_hash, rubric_hash`); `trials.baseline[]` and `trials.candidate[]` containing `run_id, worker_id`, matching controls, `trace_ref, artifact_ref, outcome.passed, outcome.evidence_ref, outcome.verifier.kind/id`, and optionally `cost_usd`. Exit `0` means a **candidate gain in supplied records only**, `1` means no gain/regression, `2` means incomplete/invalid records. The tool cannot open external evidence or independently prove that runs occurred; manually inspect receipts and graders before any real promotion.

If tools, money, human review, or test sessions are unavailable, stop at **unverified candidate / evidence gap**. Never transform simulated contract checks or historical receipts into a claim of a new real A/B experiment.

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

Before promoting a **new named principle**, require a recurring correction or controlled replay demonstrating a distinct decision benefit; merge it with an existing principle if the behavior overlaps. Retire or revert principles that produce no observable benefit, repeatedly fail to steer a decision, or cost more to maintain than they save. Preserve contrary runs.

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

- when testing a Skill/Prompt, the test task fits the **verified target responsibility**; out-of-scope cases are rerouted or marked test-design invalid before blaming the target;

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

- for Skill/Prompt tests, **structural/execution acceptance and semantic/use-value acceptance are separate** with traceable evidence; an unchecked content verdict cannot be promoted by a passing lint or syntax test;
- the user-facing result is understandable, useful and in the reader's language; clarity is a quality gate, not a reason to delete essential constraints;

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

## 12. Output Contract — Reader First

**Internally work precisely; externally speak normally.** Keep the detailed TaskSpec, failed runs, evidence, permissions and replay logs for audits. They are not the default user-facing answer.

- **Result first.** Answer what the user asked. A request for an external prompt gets a *standalone, ready-to-copy prompt*, not a report about how you composed it.
- **Use the reader's language.** Prefer concrete, familiar words; avoid Loop jargon (TaskSpec, D2, MECE, QA gates, node routing, A→B) unless the user requests the engineering details.
- **Cut ceremony, not meaning.** Omit repeated context, fixed stage headings, long tables, framework introductions and self-praise. Preserve the goal, important restrictions, what the AI should actually do, how success is checked, who may authorize changes, and honest uncertainty.
- **Check once before sending:** Can someone act on this after one read? Is any sentence just explaining the assistant's internal workflow? Did shortening delete a safety condition, execution instruction, critical test or failure? Rewrite only when an answer genuinely becomes clearer.

A brief result with the material evidence and outstanding limits is the normal format. If the user explicitly asks for a full audit, technical design or structured record, provide one. High-impact decisions must include the necessary risks and permission conditions even when the answer gets longer.

For Skill/Prompt repairs, retain scope fitness, content quality, reviewer independence, actual trials, negative results and rollback in the inspectable audit record. A good-looking answer or static validator is **not** evidence of independent model behavior.

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
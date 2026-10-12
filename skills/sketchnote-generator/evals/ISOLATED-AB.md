# Sketchnote Isolated A/B — Execution & Review

## Scope

This test compares the pinned old Skill (`efd370c`) to the current PR candidate using six independent stateless OpenAI Responses API requests (three matching prompts × two Skill versions). It tests **prompt-following image output**, not Claude's skill auto-invocation or ChatGPT's in-app rendering path. No output is accepted as a quality pass before review.

## Execution

Run from a full git checkout of the PR branch, with Python 3 and an API key held in your own secure environment. Do not paste the key into the prompt, repository, CI log, or review package.

```bash
python3 skills/sketchnote-generator/evals/isolated_ab.py self-test
python3 skills/sketchnote-generator/evals/isolated_ab.py dry-run --candidate-ref HEAD
# With OPENAI_API_KEY already configured securely in the environment:
python3 skills/sketchnote-generator/evals/isolated_ab.py run --candidate-ref HEAD --model gpt-5.5 --image-model gpt-image-2.5-flare --out /tmp/sketchnote-ab-20261012
python3 skills/sketchnote-generator/evals/isolated_ab.py verify --out /tmp/sketchnote-ab-20261012
```

The `run` operation generates up to **six billable images** and aborts if the key is absent. Use a new output directory each time. An interrupted run keeps partial artifacts; never claim completion from fewer than six records. Responses are separate requests without `previous_response_id`; within a pair the user prompt, model, image model and full source are identical. Only the Skill instructions differ.

## Hard-blocking checks

- The source fixture must hash to Git blob `e9b2b2ff75ce7acf2d182a828130fa257ceba20e`.
- Six image responses must be complete and traceable to unique response IDs, file bytes and SHA-256.
- No incorrect creation/dependency arrows (e.g. *Agent creates Workflow*); `Agent + Workflow` means joint orchestration.
- Workflow's nodes, edges, variables are **coequal elements**, not consecutive execution steps.
- Never label planned Aone capabilities as launched, operating, proven or generally available.
- Classic default should retain notebook handwriting / layout; editorial should not inherit spiral-binding; technical must communicate architecture rather than generic card collage.

## Review protocol

Randomly anonymize all six images before independent scoring. Two reviewers uninvolved in generating the images score: **source fidelity, semantic relationships, Chinese legibility, layout clarity, style compliance** (1–5 each) and write a concrete reason for any blocking error. Reject any image with a critical factual/relationship error regardless of aesthetic score. First compare old and candidate `default-classic` for regressions; evaluate editorial and technical outcomes for distinctness and correctness. A run without two genuine independent reviewers must remain `quality_status=review_pending`. Do not synthesize scores or call this a proven A/B win.

## Evidence and exit condition

Store `manifest.json`, `provenance.json`, six PNGs, both review reports, aggregated decision and the source/Skill commit IDs together. CI `Sketchnote A/B Preflight` only verifies the execution contract; it does not generate paid images. Merge PR #72 only after actual paired runs, semantic review, no blocking errors, and a documented improvement over the default baseline; otherwise leave PR Draft and record the first failed constraint.

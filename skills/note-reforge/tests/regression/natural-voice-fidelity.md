# Regression: natural editorial voice without semantic drift

## Change under test
The final expression pass may remove generic AI-like wording, marketing hype, vague appeals to authority, mechanical parallelism, and repeated sentence patterns. It must not change facts, source attribution, author identity, technical terms, code, or uncertainty. This pass is not a separate reforge mode.

## Baseline and controlled cases
Hold source text and output shape fixed. Compare the previous canonical Skill with the candidate on the same inputs. Inspect both for actual knowledge value, not only word count or style. A rule-presence test is not an independent prose-quality evaluation.

### Case A: expert technical prose with empty rhetoric
Source: 「在持续演变的技术格局中，我们通过读取日志与比对提交记录，揭示了错误发生的核心原因。」
Expected editorial choice: 「比对日志与提交记录后，定位到错误原因。」
Keep: logs + commit records; reported diagnosis. Remove: decorative scene-setting and unsupported importance claims.
Failure: inventing the particular root cause or claiming a test passed.

### Case B: AML uncertainty, evidence and source attribution
Source: 「报告称，该地址可能与欺诈有关；调查尚未完成。」
Expected: retain 「报告称」「可能」「调查尚未完成」 and the identity of the reporting source if present.
Failure: 「该地址涉及欺诈」; claiming proof, enforcement, or a sanctions match.

### Case C: original source or quoted language is protected
Source: 「报告原文写道：『这是一项具有里程碑意义的举措』。」 and an Org code block or verbatim prompt containing the same words.
Expected: preserve quotations, citation identity, and verbatim code/prompt text; optionally remove only the editor's own unsupported rhetoric outside them.
Failure: blanket removal of 「里程碑」 or edits inside code/prompt blocks.

### Case D: already concise source and appropriate rhetorical contrast
Source: 「资金先到 A，再转入 B。不是交易金额异常，而是交易对手受限。」
Expected: leave unchanged when the sequence and contrast carry information.
Failure: mechanical rewriting of 「不是 X，而是 Y」 or artificial first-person anecdotes.

### Case E: procedural note and structural safety
Source: an Org note with #+WIKI_ID, #+RESULTS, original code blocks, and a referenced CUSTOM_ID.
Expected: keep metadata/code/references unchanged; no forced blog-like storytelling, no duplicate title/contents tables, no publication identity reuse in an indexed draft.
Failure: changes to paths, identifiers, factual results, code blocks or user-specified note format.

## Verification and release gate
- Static contract: the canonical Skill includes one scoped editorial rule, explicit protection of facts, and no global forbidden-word list.
- Existing tests: note-reforge checks and full repository CI run on the patch.
- Semantic A/B: at least two representative real input cases and one counterexample need a fresh replay and an independent reviewer or evaluator. Record author voice, knowledge gain, factual/semantic fidelity and source preservation separately.
- Do not call the change an independently verified improvement if only the rule-presence assertions or author's own review passed.
- If naturalness improves but factual fidelity, knowledge gain, or publishing identity regresses, fail and revert.

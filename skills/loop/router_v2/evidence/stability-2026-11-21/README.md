# Work V2 stability evaluation

Tested revision: `af94fbae23326e6ac9626bf525407fcaf59f7659`. This follow-up adds evidence only.

| Frozen case | Single Skill | Fixed Skill chain | Dynamic routing |
|---|---:|---:|---:|
| T · Driver outcomes with explicit GitHub fixtures | 5/5 | 5/5 | 5/5 |
| N · Provenance and operational handoff from real recovery artifacts | 5/5 | 5/5 | 5/5 |
| L · Live GitHub release-evidence review | 5/5 | 5/5 | 5/5 |

The independent judge scored anonymized evidence per frozen case. T is a local fixture test. N checks the archived real failure and recovery. L makes new GitHub connector calls. Dynamic routing met the preregistered non-inferiority and minimum-quality gates. The identical scores do not establish a quality advantage.

A separate one-shot scheduled native Work run completed without interaction. The actual Work driver read both pinned source files through the GitHub connector. The controller independently checked both raw receipts, exact file bytes, Git Blob IDs and receipt SHA-256 values. The driver correctly reported RECEIPTS_RECORDED_UNVERIFIED. This establishes one scheduled read-only run in this host.

The tested revision passed 58 Python checks and the Work driver contract tests. Work V2 is eligible for release review within the read-only GitHub and bounded recovery scope. PR #118 remains draft and targets PR #116's candidate branch. Production MetaLoop scheduling, arbitrary tool execution and general dynamic-chain superiority are outside the demonstrated scope.

- [Raw outputs, tool receipts, frozen inputs, routing map and scheduled run](raw.zip)
- [Independent blind verdict](blind-verdict.json)
- [Router CI](https://github.com/lovemoganna/Org-Skills/actions/runs/44876927347)
- [Repository regression](https://github.com/lovemoganna/Org-Skills/actions/runs/44876927346)

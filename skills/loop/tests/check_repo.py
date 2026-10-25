#!/usr/bin/env python3
"""Loop structural/contract tests. They DO NOT run model golden cases."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: (ROOT / p).read_text(encoding="utf-8")
main = read("SKILL.md")
tests = []
def check(name, condition):
    assert condition, name
    tests.append(name)

check("frontmatter", main.startswith("---\nname: loop\n") and "description:" in main[:1000])
stage = [f"stages/s{i}-{n}.md" for i,n in enumerate(("intent","model","orchestrate","verify","evolve"),1)]
check("stage_files", all((ROOT / p).is_file() for p in stage))
check("templates", all((ROOT / ("templates/" + s + ".md")).is_file() for s in ("intent-card","task-spec","chain-spec","run-report","patch")))
check("task_contract", all(x in read("templates/task-spec.md") for x in ("necessary_conditions","deps","acceptance","scope")))
check("s2_task_contract", "necessary_conditions" in read(stage[1]) and "deps" in read(stage[1]))
check("chain_coverage", "coverage" in read("templates/chain-spec.md") and "direct" in read(stage[2]))
check("stage_local_atoms", "S1/S2" in main and "S3" in main and "跨步骤" in main)
check("independent_limit", "self-check only" in read(stage[3]) and "independent" in read("templates/run-report.md"))
check("meta_boundary", "loop-engineering-meta" in main)
check("goldens", all(f"G{i}" in read("evals/golden.md") for i in range(1, 11)))
names = ("single-question","define-observable","decompose-mece","write-acceptance","verify-against-goal")
atoms = [read("atoms/" + x + ".md") for x in names]
registry = read("registry.md")
check("atom_names_and_registry", all(f"name: {n}" in a and n in registry for n,a in zip(names,atoms)))
check("atom_draft", all("status: draft" in a for a in atoms) and "verified" in registry)
routing = re.compile(r"下一步.{0,20}(?:调用|运行)|然后调用|如果.{0,25}则.{0,15}调用|retry\([0-9]+\)", re.S)
check("no_route_in_atoms", all(not routing.search(a) for a in atoms))
check("no_auto_verified", "跨任务" in read(stage[4]) and "真实" in read(stage[4]))
check("no_fabricated_publish", "权限" in main and "门禁" in main)
print(json.dumps({"result":"STRUCTURAL_PASS_ONLY", "checks":len(tests), "passed":tests, "model_goldens":"NOT_RUN"}, ensure_ascii=False))

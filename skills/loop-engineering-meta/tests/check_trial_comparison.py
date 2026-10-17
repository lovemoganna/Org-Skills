#!/usr/bin/env python3
"""Synthetic contract/mutation tests; never claim these are real agent A/B trials."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("comparison", root / "scripts/compare_trials.py")
mod = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
ctl = {"model": "model-a", "task_input_hash": "sha:1", "tools_hash": "sha:2", "environment_hash": "sha:3", "rubric_hash": "sha:4"}


def trial(case, arm, i, passed):
    return {"run_id": f"{case}-{arm}-{i}", "worker_id": "worker-a", **ctl,
            "trace_ref": f"traces/{case}/{arm}-{i}.json",
            "artifact_ref": f"artifacts/{case}/{arm}-{i}.md",
            "outcome": {"passed": bool(passed),
                        "evidence_ref": f"checks/{case}/{arm}-{i}.json",
                        "verifier": {"kind": "independent_model", "id": "judge-b"}},
            "cost_usd": 0.5}


def make_case(cid, suite, baseline, candidate):
    return {"id": cid, "suite": suite, "controls": ctl,
            "trials": {"baseline": [trial(cid, "baseline", i, v) for i, v in enumerate(baseline)],
                       "candidate": [trial(cid, "candidate", i, v) for i, v in enumerate(candidate)]}}


data = {"experiment_id": "simulated-no-real-agent-runs",
        "cases": [make_case("broken", "failure", [0, 1, 0], [1, 1, 1]),
                  make_case("passed", "regression", [1, 1, 1], [1, 1, 1]),
                  make_case("new", "generalization", [0, 0, 0], [0, 1, 0])]}
assert mod.compare(data)["判定"] == "候选改善（待人工复核）"
assert mod.compare(data)["统计"]["candidate"]["trials"] == 9
checks = []


def reject(name, mutate):
    d = deepcopy(data)
    mutate(d)
    try:
        mod.compare(d)
    except mod.InvalidRecord:
        checks.append(name)
    else:
        raise AssertionError(name)


def verdict(name, mutate, expected):
    d = deepcopy(data)
    mutate(d)
    assert mod.compare(d)["判定"] == expected, name
    checks.append(name)


reject("missing_trace", lambda d: d["cases"][0]["trials"]["candidate"][0].update(trace_ref=""))
reject("self_judge", lambda d: d["cases"][0]["trials"]["candidate"][0]["outcome"]["verifier"].update(id="worker-a"))
reject("unequal_conditions", lambda d: d["cases"][0]["trials"]["candidate"][0].update(model="other"))
reject("missing_outcome", lambda d: d["cases"][0]["trials"]["candidate"][0]["outcome"].pop("passed"))
reject("duplicate_run", lambda d: d["cases"][0]["trials"]["candidate"][0].update(run_id="broken-baseline-0"))
reject("missing_suite", lambda d: d["cases"].pop())
reject("two_trials", lambda d: d["cases"][0]["trials"]["candidate"].pop())
reject("cost_invalid", lambda d: d["cases"][0]["trials"]["candidate"][0].update(cost_usd=-1))
verdict("regression", lambda d: d["cases"][1]["trials"]["candidate"][0]["outcome"].update(passed=False), "发现回归")
verdict("failure_case_degrades", lambda d: [d["cases"][0]["trials"]["candidate"][i]["outcome"].update(passed=False) for i in range(3)], "发现回归")
verdict("no_gain", lambda d: [d["cases"][i]["trials"]["candidate"][j]["outcome"].update(passed=d["cases"][i]["trials"]["baseline"][j]["outcome"]["passed"]) for i in (0, 2) for j in range(3)], "未观察到实质改善")
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "data.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    valid = subprocess.run([sys.executable, str(root / "scripts/compare_trials.py"), str(path)], capture_output=True, text=True)
    assert valid.returncode == 0, (valid.returncode, valid.stdout, valid.stderr)
    path.write_text(json.dumps({}), encoding="utf-8")
    invalid = subprocess.run([sys.executable, str(root / "scripts/compare_trials.py"), str(path)], capture_output=True, text=True)
    assert invalid.returncode == 2 and "证据不足" in invalid.stdout
print(json.dumps({"结论": "模拟契约测试通过，未执行真实 Agent A/B", "反例数": len(checks), "反例": checks}, ensure_ascii=False))

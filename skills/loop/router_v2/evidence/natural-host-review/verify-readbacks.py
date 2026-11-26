"""Independent checks of recorded connector snapshots against Git objects and arithmetic."""
import json
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
evidence = here.parent / "natural-host"


def load(path):
    return json.loads(path.read_bytes())


pre, post = (load(here / f"E02-{side}.json")["reads"] for side in ("before", "after"))
assert pre[0]["values"][1] == [7, 6, "=A2+B2"]
assert pre[1]["values"][1] == [7, 6, 13]
assert post[0]["values"][1] == [7, 6, "=A2*B2"]
assert post[1]["values"][1] == [7, 6, 7 * 6]

metrics = {}
for case in ("e03", "e06"):
    evidence_run = load(evidence / "sql" / (case + ".json"))
    for row in evidence_run["independent_git_reads"]:
        raw = subprocess.check_output(["git", "diff", "--no-ext-diff", "--numstat", row["spec"]], text=True)
        fields = [line.split("\t", 2) for line in raw.splitlines()]
        metrics[row["number"]] = (len(fields), sum(int(f[0]) for f in fields if f[0] != "-"),
                                  sum(int(f[1]) for f in fields if f[1] != "-"))
    assert evidence_run["final_status"] == "VERIFIED"
    assert len(evidence_run["actual_calls"]) == len(evidence_run["independent_git_reads"]) + 1
    actual = evidence_run["actual_calls"][-1]["result"]["rows"]
    if case == "e03":
        totals = [sum(column) for column in zip(*metrics.values())]
        assert actual == [dict(zip(("pr_count", "file_appearances", "additions", "deletions"), [len(metrics), *totals]))]
    else:
        order = sorted((sum(metrics[n][1:]), n) for n in (120, 121))
        assert actual == [{"number": n, "churn": churn} for churn, n in reversed(order)]

e04 = load(here / "E04.json")
commit, file, compare = e04["raw"]
assert commit["commit"]["sha"] == e04["head"]
assert compare["total_commits"] == 1 and compare["merge_base_commit"]["sha"] == e04["base"]
assert [f["filename"] for f in compare["files"]] == [e04["path"]]
assert file["content"] == (evidence / "e04" / "expected.mjs").read_text()
print(json.dumps({"E02": 42, "per_pr_files_additions_deletions": metrics, "E04": e04["head"]}))

pre, post = (load(here / f"E02-exclusive-{side}.json")["reads"] for side in ("before", "after"))
assert pre[0]["values"][1] == [7, 6, "=A2+B2"] and pre[1]["values"][1] == [7, 6, 13]
assert post[0]["values"][1] == [7, 6, "=A2*B2"] and post[1]["values"][1] == [7, 6, 42]

e05 = load(here / "E05.json")
commit, file, compare = e05["raw"]
assert commit["commit"]["sha"] == e05["head"] and e05["base"] == e04["head"]
assert compare["total_commits"] == 1 and compare["merge_base_commit"]["sha"] == e05["base"]
assert [f["filename"] for f in compare["files"]] == [e05["path"]]
assert file["content"] == (evidence / "e05" / "expected.mjs").read_text()
before = load(evidence / "e05" / "fault-provider.json")
after = load(evidence / "e05" / "recovery-provider.json")
assert sum(r["tool"].endswith("update_ref") for r in before) == 1
assert [r["tool"].rsplit("github_", 1)[1] for r in after] == ["fetch_commit", "compare_commits", "fetch_file"]
assert load(evidence / "e05" / "recovered.json")["status"] == "VERIFIED"
print(json.dumps({"E05_head": e05["head"], "ref_updates_before_restart": 1, "ref_updates_after_restart": 0}))

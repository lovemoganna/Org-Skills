#!/usr/bin/env python3
"""Read-only forensic comparison of 16 legacy Dashboard branches."""
import ast
import json
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path.cwd()
MANIFEST = json.loads((ROOT / ".github/dashboard-branch-audit-20261019.json").read_text())
DEST = ROOT / "dashboard-audit"
DEST.mkdir(exist_ok=True)

def git(*args):
    return subprocess.check_output(("git", *args), text=True).strip()

def blob(rev, path):
    result = subprocess.run(("git", "rev-parse", "--verify", rev + ":" + path),
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

def read_file(rev, path):
    result = subprocess.run(("git", "show", rev + ":" + path),
                            capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""

def strings_in_assertions(code):
    try:
        parsed = ast.parse(code)
    except SyntaxError:
        return []
    return sorted({s.value for node in ast.walk(parsed) if isinstance(node, ast.Assert)
                   for s in ast.walk(node.test) if isinstance(s, ast.Constant)
                   and isinstance(s.value, str) and len(s.value) > 5})

def refs():
    return dict((line.split()[1].removeprefix("refs/heads/"), line.split()[0])
                for line in git("ls-remote", "--heads", "origin").splitlines())

actual = refs()
assert actual.get("main") == MANIFEST["main"], "MAIN_DRIFT"
assert len(MANIFEST["targets"]) == 16, "SCOPE_DRIFT"
assert all(actual.get(n) == sha for n, sha in MANIFEST["targets"].items()), "REF_DRIFT"
prefix = "skills/dataset-dashboard-builder/"
current_skill = read_file(MANIFEST["main"], prefix + "SKILL.md")
current_test = read_file(MANIFEST["main"], prefix + "tests/check_repo.py")
current_regression = read_file(MANIFEST["main"], prefix + "tests/regression-cases.md")
old_assertions = strings_in_assertions(current_test)
rows = []
for name, sha in MANIFEST["targets"].items():
    ancestor = git("merge-base", MANIFEST["main"], sha)
    paths = subprocess.check_output(("git", "diff", "--name-only", "-z", ancestor, sha))
    changed = sorted(x.decode() for x in paths.split(b"\0") if x)
    missing = [p for p in changed if blob(MANIFEST["main"], p) is None]
    same = [p for p in changed if blob(MANIFEST["main"], p) == blob(sha, p)]
    different = [p for p in changed if p not in same]
    old_test = read_file(sha, prefix + "tests/check_repo.py")
    old_skill = read_file(sha, prefix + "SKILL.md")
    miss_assertions = [x for x in strings_in_assertions(old_test)
                       if x not in old_assertions and x not in current_skill
                       and x not in current_regression and len(x) < 180]
    headings = re.findall(r"(?m)^#{2,4}\s+(.+)", old_skill)
    missing_headings = [x for x in headings if x not in current_skill]
    rows.append({
        "branch": name, "sha": sha, "ahead": int(git("rev-list", "--count", ancestor+".."+sha)),
        "changed_paths": changed, "not_present_in_main": missing,
        "exact_same_blob_paths": same, "historically_different_paths": different,
        "old_assertion_literals_absent": miss_assertions[:100],
        "old_headings_absent": missing_headings[:70],
        "outcome": "EXACT_CONTENT" if not different else "REQUIRES_SEMANTIC_REVIEW"
    })
with tempfile.TemporaryDirectory() as path:
    checkout = pathlib.Path(path) / "main"
    subprocess.run(("git", "worktree", "add", "--detach", str(checkout),
                    MANIFEST["main"]), check=True, capture_output=True, text=True)
    try:
        proc = subprocess.run(("python3", str(checkout / prefix / "tests/check_repo.py")),
                              capture_output=True, text=True, timeout=90)
        regression = {"exit_code": proc.returncode, "stdout": proc.stdout[-3500:],
                      "stderr": proc.stderr[-3500:]}
    finally:
        subprocess.run(("git", "worktree", "remove", "--force", str(checkout)),
                       check=True, capture_output=True, text=True)
report = {"baseline_main": MANIFEST["main"], "scope": "static audit plus real check_repo",
          "warning": "Matching file paths and literal checks is not proof of semantic equivalence",
          "checked_branches": len(rows), "main_regression": regression, "branches": rows}
(DEST/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
summary = ["DASHBOARD_AUDIT_FINISHED",
           "MAIN " + MANIFEST["main"], f"CHECKED {len(rows)}",
           "MAIN_TEST_EXIT " + str(regression["exit_code"])]
for r in rows:
    summary.append(f"{r['branch']}: changed={len(r['changed_paths'])} "
                   f"same={len(r['exact_same_blob_paths'])} unique={len(r['not_present_in_main'])} "
                   f"old_assert_literals={len(r['old_assertion_literals_absent'])} "
                   f"old_headings={len(r['old_headings_absent'])}")
(DEST/"SUMMARY.txt").write_text("\n".join(summary)+"\n")
print("\n".join(summary))
assert all(not r["not_present_in_main"] for r in rows), "UNMIGRATED_PATH_PRESENT"
assert regression["exit_code"] == 0, "DASHBOARD_MAIN_CHECK_FAILED"

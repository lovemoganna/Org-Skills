#!/usr/bin/env python3
"""Router V2 candidate: safe local execution and evidence, not an LLM executor."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

OPS = {"read_text", "write_text", "replace_text", "assert_contains"}
WRITES = {"write_text", "replace_text"}
CHECKS = {"exists", "contains", "equals", "sha256"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def stamp():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def discover(root):
    """Never execute SKILL.md. Metadata is evidence of existence, not tool binding."""
    root = root.resolve(strict=True)
    found = []
    for f in sorted(root.rglob("SKILL.md")):
        if f.is_symlink() or not f.resolve().is_relative_to(root):
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        if not raw.startswith("---\n") or "\n---" not in raw[4:]:
            continue
        header = raw.split("\n---", 1)[0][4:]
        meta = {}
        for key in ("name", "description"):
            hit = re.search(rf"(?m)^{key}:\s*(.+)$", header)
            if hit:
                v = hit.group(1).strip()
                if len(v) > 1 and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]
                meta[key] = v
        if meta.get("name"):
            found.append({"name": meta["name"], "description": meta.get("description", ""),
                          "path": f.relative_to(root).as_posix(),
                          "source_sha256": sha(f.read_bytes()),
                          "execution_binding": "UNREGISTERED"})
    return found

def match_skills(query, catalog):
    """Lexical candidates only. No semantic accuracy/authorization assertion."""
    words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", query.lower()))
    words -= {"the", "and", "for", "skill", "use", "with", "from"}
    cn = set(re.findall(r"[\u4e00-\u9fff]{2,}", query))
    ranked = []
    for x in catalog:
        name, desc = x["name"].lower(), x["description"].lower()
        exact = name in query.lower()
        hits = sorted(w for w in words if w in name or w in desc)
        hits += sorted(w for w in cn if w in desc)
        score = 10 * exact + len(hits)
        if score:
            ranked.append({"name": x["name"], "score": score,
                           "matched_terms": hits, "exact_name": exact,
                           "execution_binding": "UNREGISTERED", "source_sha256": x["source_sha256"]})
    return sorted(ranked, key=lambda x: (-x["score"], x["name"]))[:5]

def validate_task(t):
    if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"].strip():
        raise ValueError("task id required")
    if not isinstance(t.get("goal"), str) or not t["goal"].strip():
        raise ValueError("goal required")
    actions, checks = t.get("actions"), t.get("acceptance")
    if not isinstance(actions, list) or not actions or len(actions) > 6:
        raise ValueError("1..6 actions required")
    if not isinstance(checks, list) or not checks:
        raise ValueError("acceptance required")
    for label, entries in (("actions", actions), ("acceptance", checks)):
        ids = [v.get("id") for v in entries]
        if any(not isinstance(i, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", i) for i in ids):
            raise ValueError(label + " requires valid ids")
        if len(set(ids)) != len(ids):
            raise ValueError(label + " ids must be unique")
    for i, a in enumerate(actions):
        if a.get("operation") not in OPS or not isinstance(a.get("path"), str):
            raise ValueError("unsupported action")
        deps = a.get("depends_on", [])
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or any(
                d not in {p["id"] for p in actions[:i]} for d in deps):
            raise ValueError("bad dependency: must reference earlier step")
        if a["operation"] == "write_text" and not isinstance(a.get("text"), str):
            raise ValueError("write_text needs text")
        if a["operation"] == "replace_text" and (
                not isinstance(a.get("old"), str) or not a["old"] or
                not isinstance(a.get("new"), str)):
            raise ValueError("replace_text needs old and new")
        if a["operation"] == "assert_contains" and not isinstance(a.get("needle"), str):
            raise ValueError("assert_contains needs needle")
    for c in checks:
        if c.get("kind") not in CHECKS or not isinstance(c.get("path"), str):
            raise ValueError("bad acceptance check")
        if c["kind"] != "exists" and not isinstance(c.get("value"), str):
            raise ValueError("acceptance value required")
    skills = t.get("required_skills", [])
    if not isinstance(skills, list) or any(not isinstance(x, str) or not x for x in skills):
        raise ValueError("required_skills must be names")
    return t

def plan(t, catalog=None):
    validate_task(t)
    a = t["actions"]
    signals = []
    if len(a) >= 3 and any(x.get("depends_on") for x in a):
        signals.append(1)
    if len(t["acceptance"]) > 1 and any(x["operation"] in WRITES for x in a):
        signals.append(2)
    if len({"write" if x["operation"] in WRITES else "read" for x in a}) > 1:
        signals.append(3)
    if sum(len(x.get("text", "")) for x in a) > 8000:
        signals.append(4)
    if t.get("independent_review_requested") is True:
        signals.append(5)
    mode = "chain" if len(signals) >= 2 else "direct"
    requested = t.get("required_skills", [])
    missing = sorted(set(requested) - {s["name"] for s in (catalog or [])})
    state = ("BLOCKED_SKILL_NOT_FOUND" if missing else
             "BLOCKED_SKILL_EXECUTOR" if requested else "PLANNED_NOT_RUN")
    return {"task_id": t["id"], "mode": mode, "reason": signals, "status": state,
            "missing_skills": missing, "required_skills": requested,
            "steps": [{"id": x["id"], "atom": x["operation"],
                       "input_from": x.get("depends_on", []) or "task",
                       "output_name": x["id"] + "_receipt", "check": "tool_receipt",
                       "on_fail": "stop"} for x in a] if mode == "chain" else [],
            "coverage": {x["id"]: {"status": "NOT_VERIFIED", "evidence_ref": None}
                         for x in t["acceptance"]}}

def safe_path(root, rel):
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise ValueError("invalid path")
    p = Path(rel)
    if p.is_absolute() or any(v in (".", "..") for v in rel.split("/")):
        raise ValueError("workspace-relative path required; traversal rejected")
    full = root / p
    if not full.resolve(strict=False).is_relative_to(root.resolve()):
        raise ValueError("path escapes workspace")
    return full

def write_atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".router-v2-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def act(root, a):
    p = safe_path(root, a["path"])
    op = a["operation"]
    if op == "write_text":
        write_atomic(p, a["text"])
    elif op == "replace_text":
        before = p.read_text(encoding="utf-8")
        if a["old"] not in before:
            raise ValueError("old text not found")
        write_atomic(p, before.replace(a["old"], a["new"]))
    elif op == "assert_contains":
        if a["needle"] not in p.read_text(encoding="utf-8"):
            raise AssertionError("needle not found")
    else:
        p.read_text(encoding="utf-8")
    data = p.read_bytes()
    return {"action_id": a["id"], "operation": op, "path": a["path"],
            "sha256": sha(data), "size_bytes": len(data),
            "receipt": "LOCAL_FILESYSTEM_OBSERVED"}

def check(root, c):
    p = safe_path(root, c["path"])
    exists = p.is_file()
    kind = c["kind"]
    if kind == "exists":
        passed = exists
    elif not exists:
        passed = False
    else:
        data = p.read_bytes()
        passed = (sha(data) == c["value"] if kind == "sha256" else
                  data.decode("utf-8") == c["value"] if kind == "equals" else
                  c["value"] in data.decode("utf-8"))
    return {"id": c["id"], "status": "PASS" if passed else "FAIL",
            "path": c["path"], "kind": kind,
            "evidence": {"observed_exists": exists,
                         "sha256": sha(p.read_bytes()) if exists else None}}

def run(t, workspace, run_dir, authorize_write=False, catalog=None):
    route = plan(t, catalog)
    workspace = workspace.resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("workspace must exist")
    run_dir.mkdir(parents=True, exist_ok=False)
    def log(state, **kw):
        with (run_dir / "trace.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": stamp(), "state": state, **kw}, ensure_ascii=False) + "\n")
    log("PLANNED", task_id=t["id"], mode=route["mode"])
    state, reason, receipts = None, None, []
    if route["status"] != "PLANNED_NOT_RUN":
        state, reason = "BLOCKED", route["status"]
    elif any(x["operation"] in WRITES for x in t["actions"]) and not authorize_write:
        state, reason = "BLOCKED", "WRITE_AUTHORIZATION_REQUIRED"
    else:
        log("RUNNING")
        for a in t["actions"]:
            try:
                r = act(workspace, a)
                receipts.append(r)
                log("STEP_OK", action_id=a["id"], path=r["path"], sha256=r["sha256"])
            except (ValueError, OSError, AssertionError, UnicodeError) as exc:
                state, reason = "FAILED", f"{type(exc).__name__}: {exc}"
                log("STEP_FAILED", action_id=a["id"], error=reason)
                break
    verdicts = []
    if state is None:
        try:
            verdicts = [check(workspace, c) for c in t["acceptance"]]
            if all(v["status"] == "PASS" for v in verdicts):
                state = "COMPLETED_UNVERIFIED"
            else:
                state, reason = "FAILED", "ACCEPTANCE_FAILED"
        except (ValueError, OSError, UnicodeError) as exc:
            state, reason = "FAILED", f"CHECK_ERROR: {exc}"
    log(state, failure=reason)
    report = {"task_id": t["id"], "goal": t["goal"], "status": state,
              "reason": reason, "mode": route["mode"], "plan": route,
              "receipts": receipts, "acceptance": verdicts,
              "goal_check": "NOT_INDEPENDENTLY_VERIFIED",
              "independence": "self-check only",
              "side_effects": "not independently assessed",
              "trace_ref": "trace.jsonl", "evidence_scope": "local workspace only",
              "completed_at": stamp()}
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

def recheck(t, root, report):
    validate_task(t)
    if t["id"] != report.get("task_id"):
        raise ValueError("task/report mismatch")
    root = root.resolve(strict=True)
    verdicts = [check(root, c) for c in t["acceptance"]]
    rs = report.get("receipts", [])
    last = {r["path"]: i for i, r in enumerate(rs)}
    integrity = []
    for i, r in enumerate(rs):
        final = last[r["path"]] == i
        p = safe_path(root, r["path"])
        current = sha(p.read_bytes()) if p.is_file() else None
        integrity.append({"action_id": r["action_id"], "superseded": not final,
                          "last_receipt_matches_current": current == r["sha256"] if final else None})
    passed = all(v["status"] == "PASS" for v in verdicts) and all(
        v["last_receipt_matches_current"] is not False for v in integrity)
    return {"task_id": t["id"], "acceptance": verdicts,
            "receipt_integrity": integrity,
            "status": "PASS_LOCAL_RECHECK" if passed else "FAIL_LOCAL_RECHECK",
            "independence": "self-check only",
            "goal_check": "NOT_INDEPENDENTLY_VERIFIED"}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("discover")
    p.add_argument("--skills-root", required=True, type=Path)
    p.add_argument("--query", default="")
    p = sub.add_parser("plan")
    p.add_argument("--task", required=True, type=Path)
    p.add_argument("--skills-root", type=Path)
    p = sub.add_parser("run")
    p.add_argument("--task", required=True, type=Path)
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--skills-root", type=Path)
    p.add_argument("--authorize-write", action="store_true")
    p = sub.add_parser("recheck")
    p.add_argument("--task", required=True, type=Path)
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = ap.parse_args()
    try:
        if args.cmd == "discover":
            skills = discover(args.skills_root)
            result = {"skills_count": len(skills),
                      "skills": match_skills(args.query, skills) if args.query else skills}
        elif args.cmd == "plan":
            result = plan(read_json(args.task),
                          discover(args.skills_root) if args.skills_root else None)
        elif args.cmd == "run":
            result = run(read_json(args.task), args.workspace, args.run_dir,
                         authorize_write=args.authorize_write,
                         catalog=discover(args.skills_root) if args.skills_root else None)
        else:
            result = recheck(read_json(args.task), args.workspace, read_json(args.report))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.cmd == "run":
            return 0 if result["status"] == "COMPLETED_UNVERIFIED" else 1
        if args.cmd == "recheck":
            return 0 if result["status"] == "PASS_LOCAL_RECHECK" else 1
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())

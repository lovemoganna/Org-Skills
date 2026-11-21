#!/usr/bin/env python3
"""Host-mediated Skill Router bridge. Does NOT call language models or host tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine import discover

# A trusted host must make these calls through its own permission mechanism.
# Merely listing a binding here never confers permission or proves availability.
BINDINGS = {
    "github.fetch_file": ("mcp__GitHub__fetch_file", "read"),
    "github.get_pr_info": ("mcp__GitHub__get_pr_info", "read"),
    "github.create_file": ("mcp__GitHub__create_file", "write"),
    "github.update_file": ("mcp__GitHub__update_file", "write"),
    "github.fetch_workflow_run_jobs": ("mcp__GitHub__fetch_workflow_run_jobs", "read"),
}
MAX_STEPS = 6
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan(plan, skill_names):
    if not isinstance(plan, dict) or not isinstance(plan.get("id"), str) or not plan["id"].strip():
        raise ValueError("plan id required")
    if not isinstance(plan.get("goal"), str) or not plan["goal"].strip():
        raise ValueError("goal required")
    steps = plan.get("steps")
    checks = plan.get("acceptance")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError("1..6 executable steps required")
    if not isinstance(checks, list) or not checks:
        raise ValueError("acceptance required")
    ids = set()
    for step in steps:
        sid = step.get("id")
        if not isinstance(sid, str) or not ID_PATTERN.fullmatch(sid) or sid in ids:
            raise ValueError("step id invalid or duplicate")
        if step.get("kind") not in ("skill", "tool"):
            raise ValueError("step kind must be skill or tool")
        if not isinstance(step.get("target"), str):
            raise ValueError("step target required")
        if not isinstance(step.get("args"), dict):
            raise ValueError("step args must be a JSON object")
        deps = step.get("depends_on", [])
        if not isinstance(deps, list) or any(d not in ids for d in deps) or len(set(deps)) != len(deps):
            raise ValueError("dependency must refer to earlier step")
        if step["kind"] == "skill":
            if step["target"] not in skill_names:
                raise ValueError("unavailable Skill: " + step["target"])
        elif step["target"] not in BINDINGS:
            raise ValueError("tool capability not allowlisted: " + step["target"])
        ids.add(sid)
    seen = set()
    for item in checks:
        cid = item.get("id")
        if not isinstance(cid, str) or not ID_PATTERN.fullmatch(cid) or cid in seen:
            raise ValueError("invalid or duplicate acceptance id")
        evidence_from = item.get("evidence_from")
        if not isinstance(evidence_from, list) or not evidence_from or any(s not in ids for s in evidence_from):
            raise ValueError("acceptance must identify executable evidence-producing steps")
        seen.add(cid)
    return plan


def append_trace(folder, event, **details):
    with (folder / "trace.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(canonical({"at": now(), "event": event, **details}) + "\n")


def init_session(folder, plan, skills_root, host_capabilities=None, authorized_writes=False):
    skills = discover(skills_root)
    skill_sources = {s["name"]: s["source_sha256"] for s in skills}
    validate_plan(plan, skill_sources)
    caps = sorted(set(host_capabilities or []))
    unknown = set(caps) - set(BINDINGS)
    if unknown:
        raise ValueError("unknown declared host capability: " + repr(sorted(unknown)))
    folder.mkdir(parents=True, exist_ok=False)
    state = {
        "plan": plan,
        "plan_sha256": digest(plan),
        "skill_source_hashes": {s["target"]: skill_sources[s["target"]] for s in plan["steps"] if s["kind"] == "skill"},
        "host_declared_capabilities": caps,
        "host_write_authorization_declared": bool(authorized_writes),
        "results": {},
        "started_at": now(),
    }
    save_json(folder / "session.json", state)
    append_trace(folder, "INIT", plan_sha256=state["plan_sha256"], steps=len(plan["steps"]))
    return status(state)


def load(folder):
    state = read_json(folder / "session.json")
    if digest(state["plan"]) != state["plan_sha256"]:
        raise ValueError("plan digest mismatch")
    return state


def next_step(state):
    results = state["results"]
    for step in state["plan"]["steps"]:
        if step["id"] in results:
            if results[step["id"]]["status"] == "BLOCKED":
                return None, "HALTED_ON_STEP_BLOCK"
            if results[step["id"]]["status"] != "SUCCESS":
                return None, "HALTED_ON_STEP_FAILURE"
            continue
        if any(results.get(dep, {}).get("status") != "SUCCESS" for dep in step.get("depends_on", [])):
            return None, "BLOCKED_DEPENDENCY"
        if step["kind"] == "tool":
            binding, effect = BINDINGS[step["target"]]
            if step["target"] not in state["host_declared_capabilities"]:
                return None, "BLOCKED_TOOL_CAPABILITY"
            if effect == "write" and not state["host_write_authorization_declared"]:
                return None, "BLOCKED_WRITE_AUTHORIZATION"
        else:
            binding = "NATIVE_HOST_MODEL_SKILL"
            effect = "host"
        request = {
            "step_id": step["id"], "kind": step["kind"], "target": step["target"],
            "executor_binding": binding, "side_effect_class": effect,
            "args": step["args"], "request_sha256": digest(step),
        }
        return request, "AWAITING_HOST_EXECUTION"
    return None, "ALL_STEPS_REPORTED"


def status(state):
    request, phase = next_step(state)
    result = {"task_id": state["plan"]["id"], "phase": phase,
              "completed_step_ids": list(state["results"]),
              "pending_request": request,
              "evidence_trust": "HOST_REPORTED_NOT_INDEPENDENTLY_AUTHENTICATED"}
    if phase == "ALL_STEPS_REPORTED":
        results = state["results"]
        coverage = {c["id"]: {"status": "HOST_REPORTED",
                               "receipt_refs": [results[s]["receipt_ref"] for s in c["evidence_from"]]}
                    for c in state["plan"]["acceptance"]}
        result.update(status="RECEIPTS_RECORDED_UNVERIFIED", acceptance=coverage)
    elif phase == "AWAITING_HOST_EXECUTION":
        result["status"] = "RUNNING" if state["results"] else "PLANNED_NOT_RUN"
    else:
        result["status"] = "FAILED" if phase == "HALTED_ON_STEP_FAILURE" else "BLOCKED"
    result["independence"] = "self-check only"
    return result


def record(folder, report):
    state = load(folder)
    request, phase = next_step(state)
    if request is None or phase != "AWAITING_HOST_EXECUTION":
        raise ValueError("no executable request in current session state: " + phase)
    if not isinstance(report, dict) or report.get("step_id") != request["step_id"]:
        raise ValueError("result must match current step id")
    if report.get("request_sha256") != request["request_sha256"]:
        raise ValueError("stale or mismatched tool request")
    if report.get("status") not in ("SUCCESS", "FAILED", "BLOCKED"):
        raise ValueError("invalid outcome")
    ref = report.get("receipt_ref")
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("host must supply source/tool receipt reference")
    if report["status"] == "SUCCESS":
        if not isinstance(report.get("artifact_ref"), str) or not report["artifact_ref"].strip():
            raise ValueError("successful step needs artifact reference")
    entry = {
        "step_id": request["step_id"], "request_sha256": request["request_sha256"],
        "status": report["status"], "receipt_ref": ref, "artifact_ref": report.get("artifact_ref"),
        "host_observation": report.get("observation", ""),
        "recorded_at": now(),
    }
    # Receipt presence is only syntax validation, never authenticated execution.
    state["results"][request["step_id"]] = entry
    save_json(folder / "session.json", state)
    append_trace(folder, "HOST_RESULT_RECORDED", step_id=request["step_id"],
                 status=entry["status"], receipt_ref=ref)
    return status(state)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init")
    a.add_argument("--plan", required=True, type=Path)
    a.add_argument("--session", required=True, type=Path)
    a.add_argument("--skills-root", required=True, type=Path)
    a.add_argument("--host-capabilities", default="")
    a.add_argument("--authorized-writes", action="store_true")
    a = sub.add_parser("next")
    a.add_argument("--session", required=True, type=Path)
    a = sub.add_parser("record")
    a.add_argument("--session", required=True, type=Path)
    a.add_argument("--result", required=True, type=Path)
    args = ap.parse_args()
    try:
        if args.cmd == "init":
            value = init_session(args.session, read_json(args.plan), args.skills_root,
                                 [x for x in args.host_capabilities.split(",") if x],
                                 args.authorized_writes)
        elif args.cmd == "next":
            value = status(load(args.session))
        else:
            value = record(args.session, read_json(args.result))
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0 if value["status"] in ("RUNNING", "PLANNED_NOT_RUN", "RECEIPTS_RECORDED_UNVERIFIED") else 1
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

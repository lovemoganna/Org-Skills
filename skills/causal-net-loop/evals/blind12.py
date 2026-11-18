#!/usr/bin/env python3
"""No-API, independently runnable two-arm manual evaluation harness.

Subcommands:
  check    Validate frozen task pack and exact original Skill blob hashes.
  prepare  Produce 24 single-case prompts (12 cases x two versions).
  verify   Check 24 submitted model response records; never invent outputs.
  blind    Shuffle labels into a reviewer-only pack; store key separately.
  score    Unblind human reviews, compute pre-registered gates. Never auto-merge.

No model invocation, automatic grader, or self-reported quality claims occur here.
"""
import argparse
import hashlib
import json
import re
import secrets
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
DATA = ROOT / "blind12-2026-11-18.json"
DATA_BLOB = "d4ec6a9972a922968127b5fbb6d1d327f3cd1089"
SKILL_PATH = "skills/causal-net-loop/SKILL.md"
ARMS = ("baseline", "candidate")
DOMAINS = {"crypto-risk", "software", "public-policy", "negative-control"}


def git_blob(text_bytes):
    return hashlib.sha1(b"blob " + str(len(text_bytes)).encode()
                        + b"\0" + text_bytes).hexdigest()


def load_data():
    raw = DATA.read_bytes()
    if git_blob(raw) != DATA_BLOB:
        raise ValueError("Test manifest changed; freeze a new dataset instead of reusing old holdout")
    data = json.loads(raw)
    assert len(data["cases"]) == 12
    ids = [c["id"] for c in data["cases"]]
    assert ids == [f"N{i:02d}" for i in range(1, 13)]
    assert len(set(ids)) == 12
    assert {c["domain"] for c in data["cases"]} == DOMAINS
    assert sum(c["domain"] == "negative-control" for c in data["cases"]) == 2
    for c in data["cases"]:
        assert c["prompt"].strip() and c["pass"] and c["fail"]
    assert sum(data["scoring"]["weights"].values()) == 100
    assert len(data["scoring"]["hard_gates"]) == 4
    return data


def arm_skill(data, arm):
    fr = data["frozen"]
    if arm == "baseline":
        ref, expect = fr["baseline_ref"], fr["baseline_blob"]
        text = subprocess.check_output(
            ["git", "show", f"{ref}:{SKILL_PATH}"], cwd=REPO)
    else:
        expect = fr["candidate_blob"]
        text = (REPO / SKILL_PATH).read_bytes()
    actual = git_blob(text)
    if actual != expect:
        raise ValueError(f"{arm}: expected {expect}, got {actual}; immutable Skill constraint violated")
    return text.decode("utf-8"), actual


def check(data):
    result = {arm: arm_skill(data, arm)[1] for arm in ARMS}
    print(json.dumps({"status": "PASS: dataset and frozen Skill blobs",
                      "cases": len(data["cases"]), "blobs": result,
                      "model_runs": "NOT_VERIFIED"}, ensure_ascii=False, indent=2))


def prepare(data, dest):
    dest.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        skill, _ = arm_skill(data, arm)
        for case in data["cases"]:
            p = dest / f"{case['id']}-{arm}.prompt.md"
            if p.exists():
                raise FileExistsError(f"Refusing to overwrite previously prepared prompt {p}")
            p.write_text(
                "请在一个全新、独立的 ChatGPT GPT-6 对话中仅执行以下任务。"
                "不使用模型 API，不使用外部资料、插件或工具，不参考以前对话。"
                "这里的 Skill 是唯一附加规则；仅输出回答正文，不说明规则，不输出评测或评分。"
                "不得编造事实；尽量简洁。不要读其他案例或任一版本的输出。"
                "\n\n<SKILL>\n" + skill + "\n</SKILL>\n"
                "\n<USER_TASK>\n" + case["prompt"] + "\n</USER_TASK>\n",
                encoding="utf-8")
    print(json.dumps({"status": "PASS: prompts prepared, NO model called",
                      "output_dir": str(dest), "prompt_count": 24}, ensure_ascii=False))


def load_submitted(data, dest):
    outputs = {}
    seen_sessions = set()
    declared_models = set()
    declared_tools = set()
    for arm in ARMS:
        for case in data["cases"]:
            path = dest / arm / (case["id"] + ".json")
            item = json.loads(path.read_text(encoding="utf-8"))
            fields = {"case_id", "skill_blob", "model", "tools", "session_id",
                      "runner_id", "response", "evidence_ref"}
            if not fields.issubset(item):
                raise ValueError(f"{path}: expected keys missing {fields - set(item)}")
            if item["case_id"] != case["id"]:
                raise ValueError(f"{path}: case_id mismatch")
            if item["skill_blob"] != data["frozen"][f"{arm}_blob"]:
                raise ValueError(f"{path}: wrong Skill blob")
            if not item["response"].strip() or len(item["response"]) > 20000:
                raise ValueError(f"{path}: missing/oversized answer")
            if not str(item["evidence_ref"]).strip():
                raise ValueError(f"{path}: no verifiable user-provided session/trace reference")
            declared_models.add(item["model"])
            declared_tools.add(item["tools"])
            if item["session_id"] in seen_sessions or not item["session_id"]:
                raise ValueError(f"{path}: not a distinct reported session ID")
            seen_sessions.add(item["session_id"])
            outputs[(arm, case["id"])] = item
    if len(declared_models) != 1 or len(declared_tools) != 1 or declared_tools != {"none"}:
        raise ValueError(f"Conditions mismatch: models={declared_models}, tools={declared_tools}")
    if not next(iter(declared_models)).startswith("GPT-6"):
        raise ValueError("Manual execution must use ChatGPT GPT-6, not an API or unrelated model")
    return outputs


def verify(data, dest):
    rows = load_submitted(data, dest)
    print(json.dumps({
        "status": "PASS: all 24 submitted output files structurally valid",
        "note": "Session IDs/model names/evidence refs are self-reported, NOT independently authenticated",
        "cases": 12, "outputs": len(rows), "comparison": "NOT_GRADED",
    }, ensure_ascii=False, indent=2))
    return rows


def blind(data, src, reviewer_dest, key_dest):
    rows = verify(data, src)
    reviewer_dest.mkdir(parents=True, exist_ok=False)
    key_dest.mkdir(parents=True, exist_ok=False)
    review = {"dataset_blob": DATA_BLOB, "tasks": [], "instructions":
              "评分前不要打开密钥目录。对两份答案分别评分，并引用答案原文作为证据；不知道哪版 Skill。"}
    key = {"dataset_blob": DATA_BLOB, "assignments": {}, "note":
           "Keep separate from reviewers until their locked scores are saved."}
    for case in data["cases"]:
        id_ = case["id"]
        choices = list(ARMS)
        secrets.SystemRandom().shuffle(choices)
        key["assignments"][id_] = {"A": choices[0], "B": choices[1]}
        review["tasks"].append({
            "id": id_, "domain": case["domain"], "prompt": case["prompt"],
            "pass": case["pass"], "fail": case["fail"],
            "A": rows[(choices[0], id_)]["response"],
            "B": rows[(choices[1], id_)]["response"],
        })
    (reviewer_dest / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (key_dest / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    template = {"reviewer_id": "", "is_blind": True, "scores": {}}
    for case in data["cases"]:
        template["scores"][case["id"]] = {
            label: {"metrics": {k: None for k in data["scoring"]["weights"]},
                    "hard_fail": None, "negative_control_pass": None,
                    "evidence": "", "notes": ""}
            for label in ("A", "B")
        }
    (reviewer_dest / "score-template.json").write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("BLIND PACK READY. Score template requires a separate reviewer; NEVER share the key first.")


def score(data, source_dir, reviewer_file, key_file, out_file):
    rows = verify(data, source_dir)
    review = json.loads(reviewer_file.read_text(encoding="utf-8"))
    key = json.loads(key_file.read_text(encoding="utf-8"))
    if not review["reviewer_id"].strip() or review["is_blind"] is not True:
        raise ValueError("An identified reviewer who did not see version mapping is required")
    runners = {x["runner_id"] for x in rows.values()}
    if review["reviewer_id"] in runners:
        raise ValueError("Reviewer must be different from both arm executors")
    if key["dataset_blob"] != DATA_BLOB:
        raise ValueError("Unblind key does not match frozen dataset")
    weights = data["scoring"]["weights"]
    all_results = []
    for case in data["cases"]:
        cid = case["id"]
        reported = review["scores"][cid]
        row = {"id": cid, "domain": case["domain"]}
        for label in ("A", "B"):
            rec = reported[label]
            arm = key["assignments"][cid][label]
            if arm not in ARMS:
                raise ValueError("Invalid blinded assignment")
            metrics = rec["metrics"]
            if set(metrics) != set(weights) or any(v not in (0, 1, 2) for v in metrics.values()):
                raise ValueError(f"{cid} {label}: metric dimensions/0-2 values missing")
            if type(rec["hard_fail"]) is not bool or not rec["evidence"].strip():
                raise ValueError(f"{cid} {label}: explicit hard gate and cited answer evidence required")
            if rec["evidence"] not in rows[(arm, cid)]["response"]:
                raise ValueError(f"{cid} {label}: evidence must be a verbatim quote in answer")
            if case["domain"] == "negative-control" and type(rec["negative_control_pass"]) is not bool:
                raise ValueError(f"{cid} {label}: negative control verdict missing")
            row[arm] = {
                "score": sum(metrics[k] * weights[k] for k in weights) / 2,
                "hard_fail": rec["hard_fail"],
                "negative_pass": rec["negative_control_pass"],
                "characters": len(rows[(arm, cid)]["response"])
            }
        all_results.append(row)
    causal = [r for r in all_results if r["domain"] != "negative-control"]
    negative = [r for r in all_results if r["domain"] == "negative-control"]
    wins = sum(r["candidate"]["score"] > r["baseline"]["score"] for r in causal)
    losses = sum(r["candidate"]["score"] < r["baseline"]["score"] for r in causal)
    uplift = statistics.mean(r["candidate"]["score"] - r["baseline"]["score"] for r in causal)
    ratios = [r["candidate"]["characters"] / max(1, r["baseline"]["characters"]) for r in causal]
    hard_pass = not any(r[a]["hard_fail"] for r in all_results for a in ARMS)
    negative_pass = all(r["candidate"]["negative_pass"] and r["baseline"]["negative_pass"] for r in negative)
    meets = (hard_pass and negative_pass and wins >= 8 and losses <= 1
             and uplift >= 5 and statistics.median(ratios) <= 1.25)
    result = {
        "status": "ELIGIBLE_FOR_HUMAN_MERGE_REVIEW" if meets else "DO_NOT_PROMOTE",
        "not_proven": "Reviewer independence and model/session claims remain self-reported; scores are not a population estimate",
        "wins_candidate": wins, "losses_candidate": losses,
        "mean_uplift_points": round(uplift, 2),
        "median_length_ratio": round(statistics.median(ratios), 3),
        "hard_gate_pass": hard_pass, "negative_pass": negative_pass,
        "reviewer": review["reviewer_id"], "results": all_results
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "prepare", "verify", "blind", "score"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--reviewer-dir", type=Path)
    parser.add_argument("--key-dir", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--key", type=Path)
    args = parser.parse_args()
    data = load_data()
    if args.action == "check":
        check(data)
    elif args.action == "prepare":
        prepare(data, args.out or Path("/tmp/causal-blind12-prompts"))
    elif args.action == "verify":
        verify(data, args.source or Path("/tmp/causal-blind12-outputs"))
    elif args.action == "blind":
        if not args.reviewer_dir or not args.key_dir:
            parser.error("blind requires --reviewer-dir and --key-dir (separate paths)")
        if args.reviewer_dir.resolve() == args.key_dir.resolve():
            parser.error("Reviewer and key paths must differ")
        blind(data, args.source or Path("/tmp/causal-blind12-outputs"),
              args.reviewer_dir, args.key_dir)
    elif args.action == "score":
        if not args.review or not args.key or not args.out:
            parser.error("score requires --review, --key and --out")
        score(data, args.source or Path("/tmp/causal-blind12-outputs"),
              args.review, args.key, args.out)


if __name__ == "__main__":
    main()

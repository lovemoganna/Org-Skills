#!/usr/bin/env python3
"""Real, stateless image-generation A/B. No credentials = no run. Never declares a quality pass."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import urllib.request

BASE_SHA = "efd370c591bd0bda02123dc9a086fddf63dabce0"
SOURCE_BLOB = "e9b2b2ff75ce7acf2d182a828130fa257ceba20e"
SKILL_PATH = "skills/sketchnote-generator/SKILL.md"
SOURCE_PATH = "skills/sketchnote-generator/evals/fixtures/aone-plan.md"
CASES = {
    "default-classic": "把以下材料制作成中文手绘 Sketchnote 知识图。完整保留对象及关系，不把规划当作已上线。",
    "editorial": "请采用编辑出版风制作一张中文静态知识图解；不要复古笔记本，明确展示对象与关系，不把规划当作已上线。",
    "technical": "请采用技术架构图风格制作一张中文静态知识图解；只为确切依赖画有向箭头，不把并列要素画成执行顺序，不把规划当作已上线。",
}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_read(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"])


def fixture_bytes():
    data = Path(SOURCE_PATH).read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_blob != SOURCE_BLOB:
        raise RuntimeError(f"Fixture hash mismatch: {git_blob}; expected {SOURCE_BLOB}")
    return data


def make_tasks(source, old, new, model, image_model):
    result = []
    for name, instruction in CASES.items():
        user_text = instruction + "\n\n原文（完整固定输入）：\n" + source.decode("utf-8")
        for variant, skill in (("old", old), ("candidate", new)):
            payload = {
                "model": model,
                "instructions": "严格遵循以下 Skill 的任务边界与生成规则：\n\n" + skill.decode("utf-8"),
                "input": user_text,
                "tools": [{"type": "image_generation", "model": image_model}],
                "tool_choice": {"type": "image_generation"},
            }
            result.append({"case": name, "variant": variant, "payload": payload})
    return result


def generate(payload, key):
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        obj = json.load(response)
    calls = [v for v in obj.get("output", []) if v.get("type") == "image_generation_call"]
    if len(calls) != 1 or not calls[0].get("result"):
        raise RuntimeError("Expected exactly one real image_generation_call; no valid image")
    image = base64.b64decode(calls[0]["result"], validate=True)
    if not image.startswith(PNG_MAGIC):
        raise RuntimeError("Expected actual PNG bytes; do not count non-image responses")
    return obj.get("id"), image, calls[0].get("revised_prompt")


def self_test():
    base = make_tasks(b"SOURCE\n", b"OLD\n", b"NEW\n", "test-model", "test-image-model")
    assert len(base) == 6
    for name in CASES:
        pair = [x for x in base if x["case"] == name]
        assert len(pair) == 2
        assert pair[0]["payload"]["input"] == pair[1]["payload"]["input"]
        assert pair[0]["payload"]["instructions"] != pair[1]["payload"]["instructions"]
        assert all("previous_response_id" not in p["payload"] for p in pair)
        assert all(p["payload"]["tool_choice"] == {"type": "image_generation"} for p in pair)
    try:
        bad = {"output": [{"type": "message", "content": "Done"}]}
        def fake_urlopen(request, timeout):
            from io import BytesIO
            class R(BytesIO):
                def __enter__(self): return self
                def __exit__(self, *args): self.close()
            return R(json.dumps(bad).encode())
        original = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            generate(base[0]["payload"], "dummy-key")
            raise AssertionError("Missing actual image was incorrectly accepted")
        except RuntimeError:
            pass
    finally:
        urllib.request.urlopen = original
    print("SELF-TEST PASS: 6 independently prepared requests; identical paired inputs; non-image refused; no conversation-state linkage")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["self-test", "dry-run", "run", "verify"])
    ap.add_argument("--candidate-ref", default="HEAD")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--image-model", default="gpt-image-2.5-flare")
    ap.add_argument("--out", default="/tmp/sketchnote-isolated-ab")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return
    if args.command == "verify":
        d = Path(args.out)
        rows = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        if len(rows) != 6 or {(r["case"], r["variant"]) for r in rows} != {(c, v) for c in CASES for v in ("old", "candidate")}:
            raise RuntimeError("Expected 6 unique old/candidate result records")
        for row in rows:
            raw = (d / row["file"]).read_bytes()
            if not raw.startswith(PNG_MAGIC) or sha256(raw) != row["sha256"] or not row.get("response_id"):
                raise RuntimeError("Image integrity/provenance verification failed: " + row["file"])
        print("6 REAL IMAGE FILES VERIFIED; QUALITY REVIEW PENDING; NOT A PASS")
        return
    src = fixture_bytes()
    old = git_read(BASE_SHA, SKILL_PATH)
    new = git_read(args.candidate_ref, SKILL_PATH)
    tasks = make_tasks(src, old, new, args.model, args.image_model)
    if args.command == "dry-run":
        print(json.dumps({"cases": sorted(CASES), "paired_requests": len(tasks), "baseline_sha": sha256(old), "candidate_sha": sha256(new), "fixture_sha": sha256(src), "isolation": "fresh stateless API request per variant; no previous_response_id", "quality_status": "not_run"}, ensure_ascii=False, indent=2))
        return
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("BLOCK: OPENAI_API_KEY unavailable. No model calls executed. Never treat dry-run/self-test as A/B evidence")
    out = Path(args.out)
    if out.exists():
        raise RuntimeError("Output directory exists; use a fresh path to prevent overwriting baseline evidence")
    out.mkdir(parents=True)
    random.Random(42).shuffle(tasks)
    rows = []
    for task in tasks:
        response_id, img, revised = generate(task["payload"], key)
        fname = f"{task['case']}__{task['variant']}.png"
        (out / fname).write_bytes(img)
        rows.append({"case": task["case"], "variant": task["variant"], "file": fname, "sha256": sha256(img), "response_id": response_id, "revised_prompt": revised, "input_sha256": sha256(task["payload"]["input"].encode()), "instructions_sha256": sha256(task["payload"]["instructions"].encode()), "model": args.model, "image_model": args.image_model, "review": "pending"})
        (out / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "provenance.json").write_text(json.dumps({"fixture_sha256": sha256(src), "baseline_skill_sha256": sha256(old), "candidate_skill_sha256": sha256(new), "baseline_ref": BASE_SHA, "candidate_ref": args.candidate_ref, "result": "REAL_RUN_COMPLETE_QUALITY_NOT_GRADED"}, indent=2), encoding="utf-8")
    print("6 independent API image requests returned real PNGs. RUN COMPLETE; QUALITY REVIEW PENDING; NOT A PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

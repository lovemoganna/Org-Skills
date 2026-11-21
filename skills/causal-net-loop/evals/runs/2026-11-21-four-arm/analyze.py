from pathlib import Path
import hashlib
import json
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parent
ARMS = "ABCD"
RUNNERS = {
    "A": "/root/exec_p",
    "B": "/root/exec_q",
    "C": "/root/exec_r",
    "D": "/root/exec_s",
}

def read(name):
    return json.loads((ROOT / name).read_text())

def write(name, data):
    target = ROOT / name
    with target.open("x") as output:
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write("\n")

def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

def blind():
    cases = read("freeze/cases.json")
    rubric = read("freeze/rubric.json")
    raw = {arm: read(f"raw/{arm}.json") for arm in ARMS}
    expected = {case["id"] for case in cases}
    assert all(set(result) == expected for result in raw.values())
    entries = {}
    seed = random.SystemRandom().getrandbits(128)
    rng = random.Random(seed)
    ids = rng.sample(range(10000, 99999), len(cases) * len(ARMS))
    for index, case in enumerate(cases):
        arms = list(ARMS)
        rng.shuffle(arms)
        answers = []
        case_id = case["id"]
        for arm in arms:
            answer = raw[arm][case_id]
            assert set(answer) == {"I", "R"}
            assert all(isinstance(v, str) and v.strip() for v in answer.values())
            label = str(ids.pop())
            entries[label] = {"case": case_id, "arm": arm}
            answers.append({"id": label, **answer})
        case["answers"] = answers
    review_rubric = {k: v for k, v in rubric.items() if k in
                     {"weights", "scale", "dimensions", "severe"}}
    write("review/batch-j.json", {"rubric": review_rubric, "cases": cases[::2]})
    write("review/batch-k.json", {"rubric": review_rubric, "cases": cases[1::2]})
    write("review/key.json", {"seed": seed, "map": entries})
    write("execution.json", {
        "thread_ids": RUNNERS,
        "launch": "fork_turns=none, same request structure, same inherited Work runtime; no override",
        "exact_deployed_model_id": None, "token_count": None, "billing": None,
        "runs": {a: {"attempts": 1,
                      "raw_sha256": digest(f"raw/{a}.json"),
                      "prompt_sha256": digest(f"prompts/{a}.txt"),
                      "runtime": (ROOT / f"raw/{a}.runtime.txt").read_text()} for a in ARMS},
    })

def describe(records):
    scores = [r["score"] for r in records]
    counts = {}
    for r in records:
        for kind in set(r["severe"]):
            counts[kind] = counts.get(kind, 0) + 1
    return {
        "n": len(scores), "mean": statistics.mean(scores),
        "median": statistics.median(scores), "min": min(scores), "max": max(scores),
        "sd": statistics.stdev(scores), "scores": scores,
        "severe_n": sum(bool(r["severe"]) for r in records), "severe_types": counts,
        "key_hits": sum(r["hits"] for r in records), "key_possible": len(records)*4,
        "length_over_budget": sum(r["over"] for r in records),
    }

def analyze():
    cases = read("freeze/cases.json")
    ids = [c["id"] for c in cases]
    rubric = read("freeze/rubric.json")
    key = read("review/key.json")["map"]
    unlocked = {}
    for suffix in ("j", "k"):
        name = f"review/scores-{suffix}.json"
        batch_ids = {answer["id"] for c in read(f"review/batch-{suffix}.json")["cases"]
                     for answer in c["answers"]}
        scores = read(name)
        assert set(scores) == batch_ids
        assert (ROOT / f"review/locked-{suffix}.sha256").read_text().split()[0] == digest(name)
        unlocked.update(scores)
    assert set(unlocked) == set(key)
    data = {}
    for blind_id, location in key.items():
        a, c = location["arm"], location["case"]
        score = unlocked[blind_id]
        assert set(score) == {"I", "R"}
        answers = read(f"raw/{a}.json")[c]
        for phase in ("I", "R"):
            r = score[phase]
            values = r["v"]
            assert len(values) == 6 and all(type(v) is int and 0 <= v <= 4 for v in values)
            assert len(r["hit"]) == len(set(r["hit"])) and all(x in (1, 2, 3, 4) for x in r["hit"])
            assert len(r["err"]) == len(set(r["err"])) and all(x in range(1, 8) for x in r["err"])
            assert r["why"].strip()
            over = len(answers[phase]) > 500
            values = list(values)
            if over:
                values[-1] = min(1, values[-1])
            data[a, c, phase] = {
                "score": sum(w * v / 4 for w, v in zip(rubric["weights"], values)),
                "hits": len(r["hit"]), "severe": r["err"], "over": over,
            }

    def combine(arm, case):
        i, r = [data[arm, case, p] for p in ("I", "R")]
        return {"score": statistics.mean([i["score"], r["score"]]),
                "hits": (i["hits"]+r["hits"])/2, "severe": list(set(i["severe"]+r["severe"])),
                "over": i["over"] or r["over"]}

    def item(arm, case, phase):
        return combine(arm, case) if phase == "IR" else data[arm, case, phase]

    def compare(left, right, phase):
        pairs = {c: item(left, c, phase)["score"]-item(right, c, phase)["score"] for c in ids}
        ds = list(pairs.values())
        n = len(ds)
        assert n == 12
        mean = statistics.mean(ds)
        margin = 2.200985160082949 * statistics.stdev(ds) / n**0.5
        return {"n": n, "mean": mean, "ci95": [mean-margin, mean+margin],
                "wins": sum(d > 0 for d in ds), "ties": sum(d == 0 for d in ds),
                "losses": sum(d < 0 for d in ds), "pairs": pairs}

    write("result.json", {
        "scores": {f"{a}-{p}": describe([item(a, c, p) for c in ids])
                   for a in ARMS for p in ("I", "R", "IR")},
        "comparisons": {f"{l}-{r}/{p}": compare(l, r, p) for l, r, p in
                        [("B", "A", "I"), ("C", "A", "R"), ("D", "A", "IR"),
                         ("D", "B", "I"), ("D", "C", "R"), ("D", "A", "I"), ("D", "A", "R")]},
        "case_errors": {"|".join(k): v["severe"] for k, v in data.items() if v["severe"]},
        "scores_locked": {s: digest(f"review/scores-{s}.json") for s in ("j", "k")},
        "characters": {a: sum(len(s) for x in read(f"raw/{a}.json").values() for s in x.values())
                       for a in ARMS},
        "prompt_characters": {a: len((ROOT / f"prompts/{a}.txt").read_text()) for a in ARMS},
    })

if __name__ == "__main__":
    {"blind": blind, "analyze": analyze}[sys.argv[1]]()

from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import random
import statistics as stats
import sys

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "2026-11-21-four-arm"
ARMS = "ABCDE"
PHASES = ("I", "R")
CELLS = [("B", "A", "I"), ("C", "A", "R"), ("D", "A", "IR"), ("D", "B", "I"),
         ("D", "C", "R"), ("D", "A", "I"), ("D", "A", "R"), ("E", "A", "IR"), ("E", "D", "IR")]
T = {8: 2.364624251593527, 20: 2.093024054408263}

def read(name, root=ROOT):
    return json.loads((root / name).read_text())

def write(name, data):
    with (ROOT / name).open("x") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

def digest(name, root=ROOT):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()

def blind():
    cases = read("freeze/cases.json")
    ids = {case["id"] for case in cases}
    raw = {arm: read(f"raw/{arm}.json") for arm in ARMS}
    for answers in raw.values():
        assert set(answers) == ids
        for answer in answers.values():
            assert set(answer) == set(PHASES)
            assert all(isinstance(text, str) and text.strip() for text in answer.values())
    seed = random.SystemRandom().getrandbits(128)
    rng = random.Random(seed)
    labels = rng.sample(range(10000, 99999), len(ids) * len(ARMS))
    key = {}
    for case in cases:
        arms = list(ARMS)
        rng.shuffle(arms)
        case["answers"] = []
        for arm in arms:
            label = str(labels.pop())
            key[label] = {"case": case["id"], "arm": arm}
            case["answers"].append({"id": label, **raw[arm][case["id"]]})
    r = read("freeze/rubric.json")
    write("review/anonymous.json", {
        "rubric": {k: r[k] for k in ("weights", "scale", "dimensions", "severe")},
        "target": read("freeze/protocol.json")["target"],
        "cases": cases,
    })
    write("review/key.json", {"seed": seed, "map": key})

def compare(deltas):
    scores = list(deltas.values())
    n = len(scores)
    mean = stats.mean(scores)
    margin = T[n] * stats.stdev(scores) / math.sqrt(n)
    return {
        "n":n, "mean":mean, "ci95":[mean-margin,mean+margin],
        "win_tie_loss":[sum(d>0 for d in scores),sum(d==0 for d in scores),sum(d<0 for d in scores)],
        "cases":deltas,
    }

def describe(scores):
    return {"n":len(scores),"mean":stats.mean(scores),"median":stats.median(scores),
            "range":[min(scores),max(scores)],"sd":stats.stdev(scores),"scores":scores}

def analyze():
    cases = read("freeze/cases.json")
    ids = [c["id"] for c in cases]
    key = read("review/key.json")["map"]
    prior = read("result.json", PRIOR)
    grades = {}
    core = read("freeze/rubric.json")
    raw = {a: read(f"raw/{a}.json") for a in ARMS}
    for name in ("j", "k"):
        file = f"review/scores-{name}.json"
        assert digest(file) == (ROOT / f"review/locked-{name}.sha256").read_text().split()[0]
        grades[name] = {}
        values = read(file)
        assert set(values) == set(key)
        for label, location in key.items():
            a, c = location["arm"], location["case"]
            units = values[label]
            assert set(units) == set(PHASES)
            for p in PHASES:
                unit = units[p]
                v, hit, err, target, why = [unit[k] for k in ("v","hit","err","target","why")]
                assert len(v) == 6 and all(type(x) is int and 0 <= x <= 4 for x in v)
                assert len(hit) == len(set(hit)) and all(x in range(1,5) for x in hit)
                assert len(err) == len(set(err)) and all(x in range(1,8) for x in err)
                assert type(target) is bool and why.strip()
                over = len(raw[a][c][p]) > 500
                if over:
                    v[-1] = min(1, v[-1])
                score = sum(w * x / 4 for w,x in zip(core["weights"],v))
                grades[name][a,c,p] = (score,set(hit),set(err),target,over)
    def get(a, c, p, grade):
        ratings = grades.values() if grade is None else [grades[grade]]
        phases = PHASES if p=="IR" else (p,)
        return stats.mean(items[a,c,q][0] for items in ratings for q in phases)
    def comparison(left, right, phase, grade=None):
        return {c:get(left,c,phase,grade)-get(right,c,phase,grade) for c in ids}

    records = {}
    scores = {}
    for a in ARMS:
        for p in ("I","R","IR"):
            phases = PHASES if p=="IR" else (p,)
            units = [(a,c,q) for c in ids for q in phases]
            scores[f"{a}-{p}"] = {
                **describe([get(a,c,p,None) for c in ids]),
                "key_hit_mean": stats.mean(sum(len(g[u][1]) for u in units) for g in grades.values()),
                "key_possible": len(units)*4,
                "serious_sections": {n:sum(bool(g[u][2]) for u in units) for n,g in grades.items()},
                "serious_consensus_sections":sum(bool(grades["j"][u][2]&grades["k"][u][2]) for u in units),
                "target_per_rater":{n:sum(g[u][3] for u in units) for n,g in grades.items()},
                "target_consensus":sum(all(g[u][3] for g in grades.values()) for u in units),
                "over_limit":sum(grades["j"][u][4] for u in units),
            }
            for n,g in grades.items():
                for u in units:
                    if g[u][2]:
                        records.setdefault(n,{})["|".join(u)] = sorted(g[u][2])
    comparisons = {}
    combined = {}
    for l,r,p in CELLS:
        metric = f"{l}-{r}/{p}"
        ds = comparison(l,r,p)
        comparisons[metric] = {**compare(ds),
                               "by_rater":{n:compare(comparison(l,r,p,n)) for n in grades}}
        if metric in prior["comparisons"]:
            combined[metric] = compare({**prior["comparisons"][metric]["pairs"], **ds})
    full = {k:describe(prior["scores"][k]["scores"]+v["scores"])
            for k,v in scores.items() if k in prior["scores"]}
    j,k = grades["j"],grades["k"]
    keys = list(j)
    severe_types = {n:dict(Counter(e for item in g.values() for e in item[2])) for n,g in grades.items()}
    ratings_agreement = {
        "units":len(keys), "absolute_score_difference":stats.mean(abs(j[u][0]-k[u][0]) for u in keys),
        "per_anchor_agreement":sum((a in j[u][1])==(a in k[u][1]) for u in keys for a in range(1,5))/(4*len(keys)),
        "target_agreement":sum(j[u][3]==k[u][3] for u in keys)/len(keys),
        "severity_agreement":sum(j[u][2]==k[u][2] for u in keys)/len(keys),
    }
    write("result.json", {
        "replication_scores":scores,"replication_comparisons":comparisons,
        "pooled_twenty_scores":full,"pooled_twenty_comparisons":combined,
        "severity_by_section_and_rater":records,"severity_types_by_rater":severe_types,
        "rater_agreement":ratings_agreement,
        "usage":{
            a:{"input_characters":len((ROOT/f"prompts/{a}.txt").read_text()),
               "output_characters":sum(len(x) for item in raw[a].values() for x in item.values()),
               "runtime":(ROOT/f"raw/{a}.runtime.txt").read_text(),
               "native_thread":f"/root/rep_{a.lower()}",
               "prompt_sha256":digest(f"prompts/{a}.txt"),"raw_sha256":digest(f"raw/{a}.json")}
            for a in ARMS},
    })

if __name__ == "__main__":
    {"blind":blind,"analyze":analyze}[sys.argv[1]]()

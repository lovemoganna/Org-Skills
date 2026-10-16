#!/usr/bin/env python3
"""Validate task-based A/B evaluation records; never grade prose or verify reviewer identity.

JSON contract: author, reviewer {id, independent, method}, task_results [task records].
Each task has baseline and candidate with answer, evidence_location, rationale,
and manual grades {facts, decision, action} (integers 0..2). Source truth
and independence must be verified outside this structural checker.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


CATEGORIES = ("facts", "decision", "action")


def adjudicate(data: dict) -> tuple[str, list[str]]:
    author = data.get("author")
    reviewer = data.get("reviewer") or {}
    tasks = data.get("task_results")
    if not isinstance(tasks, list) or len(tasks) < 3:
        return "INVALID", ["At least three real task results required"]
    if not reviewer.get("independent") or not reviewer.get("id") or reviewer["id"] == author:
        return "PENDING", ["No independently completed evaluation declared"]
    if not reviewer.get("method") or not data.get("baseline") or not data.get("candidate"):
        return "PENDING", ["Missing provenance or blind evaluation method"]
    improvements = 0
    failures = []
    for i, case in enumerate(tasks, start=1):
        if not case.get("question") or not case.get("acceptance"):
            return "INVALID", [f"Task {i} lacks an observable question and acceptance standard"]
        results = []
        for version in ("baseline", "candidate"):
            item = case.get(version) or {}
            grades = item.get("grades") or {}
            if not all(isinstance(item.get(k), str) and item[k].strip()
                       for k in ("answer", "evidence_location", "rationale")):
                return "PENDING", [f"Task {i}/{version}: evidence-backed independent answer pending"]
            if any(type(grades.get(k)) is not int or grades[k] not in (0, 1, 2)
                   for k in CATEGORIES):
                return "PENDING", [f"Task {i}/{version}: manual grades missing"]
            results.append(grades)
        base, new = results
        if any(new[k] < base[k] for k in CATEGORIES):
            failures.append(f"Task {i}: a tested capability regressed")
        if sum(new[k] for k in CATEGORIES) > sum(base[k] for k in CATEGORIES):
            improvements += 1
    if failures:
        return "REJECT", failures
    if not improvements:
        return "REJECT", ["No observed task-usefulness gain; prefer minimal edit or NOOP"]
    return "RECORDED", [f"{improvements}/{len(tasks)} task(s) improved without scored regression",
                        "Reviewer identity and substantive scoring remain externally auditable claims"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: evaluate_task_transfer.py <evaluation.json>")
        return 2
    try:
        doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        state, notes = adjudicate(doc)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"INVALID: {exc}")
        return 1
    print(f"{state}: " + "; ".join(notes))
    return {"RECORDED": 0, "PENDING": 2, "INVALID": 1, "REJECT": 1}[state]


if __name__ == "__main__":
    raise SystemExit(main())

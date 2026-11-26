#!/usr/bin/env python3
"""Conservative preflight router; never executes actions or verifies approval provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

OPERATIONS = {"read", "write", "delete", "publish", "transfer", "external"}
IMPACTS = {"low", "medium", "high", "global"}
COSTS = {"none", "bounded", "unbounded"}
SENSITIVE = {"destructive", "regulated", "financial", "privacy", "irreversible", "high_impact"}


def verdict(level: int, reason: str, phase: int) -> dict:
    routes = {0: "AUTO", 1: "EXECUTE_NOTIFY", 2: "ASK_CHOICES", 3: "ASK_APPROVAL", 4: "PAUSE"}
    return {"level": level, "route": routes[level], "may_proceed": level <= 1,
            "reason": reason, "phase": phase}


def evaluate(case: object) -> dict:
    """Evaluate *trusted structured inputs*; does not infer facts from user text."""
    phase = 0
    if not isinstance(case, dict):
        return verdict(4, "invalid_input", phase)
    if "phase" in case:
        if type(case["phase"]) is not int or not 0 <= case["phase"] <= 4:
            return verdict(4, "invalid_phase", 0)
        phase = case["phase"]
    try:
        task_id = case["task_id"]
        operation = case["operation"]
        resource = case["resource"]
        impact = case["impact"]
        cost = case["cost"]
        reversible = case["reversible"]
        rollback_ready = case["rollback_ready"]
        authority = case["authority"]
        unknowns = case["critical_unknowns"]
        contradictions = case["contradictions"]
        flags = case["risk_flags"]
        needs_choice = case["needs_choice"]
    except KeyError:
        return verdict(4, "missing_required_field", phase)
    if (not isinstance(task_id, str) or not task_id.strip()
        or not isinstance(operation, str) or operation not in OPERATIONS
        or not isinstance(resource, str) or not resource.strip()
        or not isinstance(impact, str) or impact not in IMPACTS
        or not isinstance(cost, str) or cost not in COSTS
        or type(reversible) is not bool or type(rollback_ready) is not bool
        or type(needs_choice) is not bool
        or not isinstance(unknowns, list) or not all(isinstance(x, str) and x.strip() for x in unknowns)
        or not isinstance(contradictions, list) or not all(isinstance(x, str) and x.strip() for x in contradictions)
        or not isinstance(flags, list) or not all(isinstance(x, str) and x in SENSITIVE for x in flags)
        or not isinstance(authority, dict)
        or not isinstance(authority.get("operations"), list)
        or not isinstance(authority.get("resources"), list)
        or not all(isinstance(x, str) for x in authority["operations"] + authority["resources"])):
        return verdict(4, "invalid_field_type_or_value", phase)
    if unknowns or contradictions:
        return verdict(4, "unresolved_critical_unknown_or_conflict", phase)
    if operation not in authority["operations"] or resource not in authority["resources"]:
        return verdict(4, "outside_verified_authority", phase)

    risky = (operation in {"delete", "publish", "transfer", "external"}
             or impact in {"high", "global"} or cost == "unbounded"
             or not reversible or bool(flags)
             or (operation != "read" and not rollback_ready))
    if risky:
        approval = case.get("approval")
        # The caller must separately verify the approval's actual origin.
        approved = (isinstance(approval, dict)
                    and approval.get("task_id") == task_id
                    and approval.get("operation") == operation
                    and approval.get("resource") == resource
                    and approval.get("verified") is True)
        if not approved:
            return verdict(3, "fresh_exact_approval_required", phase)
    if needs_choice:
        choices = case.get("choices")
        selected = case.get("recommendation")
        if (not isinstance(choices, list) or not 2 <= len(choices) <= 3
            or not all(isinstance(c, str) and c.strip() for c in choices)
            or len(set(choices)) != len(choices) or selected not in choices):
            return verdict(4, "invalid_decision_options", phase)
        return verdict(2, "material_choice_unresolved", phase)
    if risky or impact == "medium" or cost == "bounded":
        return verdict(1, "permitted_execution_report_required", phase)
    return verdict(0, "permitted_low_risk_fast_path", phase)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
        result = evaluate(case)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
        result = verdict(4, "unreadable_input", 0)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["may_proceed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

import json
import shutil
from pathlib import Path
import yaml

def main():
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "evals" / "note-reforge" / "cases" / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    eval_entries = []
    for idx, c in enumerate(manifest["cases"], 1):
        case_yaml_path = repo_root / c["file"]
        data = yaml.safe_load(case_yaml_path.read_text(encoding="utf-8"))

        expectations = [
            f"决策符合预期: {data['expected_decision']}",
            "受保护内容与原始代码块完整保真",
            data.get("acceptance_criteria", ""),
        ]
        for h in data.get("hard_fail_conditions", []):
            expectations.append(f"禁止: {h}")

        entry = {
            "id": idx,
            "case_id": data["case_id"],
            "case_type": data.get("case_type", "real_historical"),
            "is_held_out": data.get("is_held_out", False),
            "expected_decision": data["expected_decision"],
            "prompt": data["task"],
            "expected_output": data.get("acceptance_criteria", ""),
            "decision_evidence": data.get("decision_evidence", ""),
            "files": [data.get("snapshot_file", "").replace("\\", "/")],
            "expectations": expectations,
            "reader_tasks": data.get("reader_tasks", []),
            "source_sha256": data.get("source_sha256", ""),
        }
        eval_entries.append(entry)

    out_json = {
        "skill_name": "note-reforge",
        "dataset_version": manifest["dataset_version"],
        "total_cases": len(eval_entries),
        "distribution": manifest["distribution"],
        "held_out_count": manifest["held_out_count"],
        "evals": eval_entries,
    }

    evals_target = repo_root / "skills" / "note-reforge" / "evals" / "evals.json"
    evals_target.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {evals_target} with {len(eval_entries)} test cases.")

    # Also copy REPORT.md to skills/note-reforge/evals/REPORT.md
    report_src = repo_root / "evals" / "note-reforge" / "REPORT.md"
    report_dst = repo_root / "skills" / "note-reforge" / "evals" / "REPORT.md"
    shutil.copy2(report_src, report_dst)
    print(f"Copied report to {report_dst}")

if __name__ == "__main__":
    main()

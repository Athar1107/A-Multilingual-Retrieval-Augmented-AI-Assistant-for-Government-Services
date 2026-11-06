"""Merge human manual grading with automated evaluation results.

Computes:
  - Percentage agreement between human grading (correct_0_1_2) and automated PASS/FAIL status.
  - Cohen's Kappa coefficient (inter-rater reliability).
  - Breakdown of discrepancies (Human PASS vs Auto FAIL, and vice versa).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).parent


def calculate_cohen_kappa(contingency: list[list[int]]) -> float:
    """Calculate Cohen's Kappa for a 2x2 matrix: [[TP, FN], [FP, TN]]."""
    total = sum(sum(row) for row in contingency)
    if total == 0:
        return 0.0

    po = (contingency[0][0] + contingency[1][1]) / total

    p_yes_human = sum(contingency[0]) / total
    p_no_human = sum(contingency[1]) / total

    p_yes_auto = (contingency[0][0] + contingency[1][0]) / total
    p_no_auto = (contingency[0][1] + contingency[1][1]) / total

    pe = (p_yes_human * p_yes_auto) + (p_no_human * p_no_auto)

    if math.isclose(pe, 1.0):
        return 1.0
    return round((po - pe) / (1.0 - pe), 3)


def merge_and_evaluate(csv_path: Path, results_path: Path | None = None) -> dict[str, Any]:
    # Load manual grading
    human_rows: list[dict[str, str]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            human_rows.append(row)

    # Load auto results if provided, or search for latest results
    auto_status_map: dict[str, str] = {}
    if results_path and results_path.exists():
        data = json.loads(results_path.read_text(encoding="utf-8"))
        for item in data.get("results", []):
            qid = item.get("id") or item.get("question")
            auto_status_map[qid] = item.get("status", "FAIL")
            # Also map question string
            auto_status_map[item.get("question", "")] = item.get("status", "FAIL")
    else:
        # Search for any results_*.json
        for fpath in EVAL_DIR.glob("results_*.json"):
            if "nllb_proxy" in fpath.name:
                continue
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                for item in data.get("results", []):
                    qid = item.get("id") or item.get("question")
                    auto_status_map[qid] = item.get("status", "FAIL")
                    auto_status_map[item.get("question", "")] = item.get("status", "FAIL")
            except Exception:
                pass

    graded_count = 0
    matrix = [[0, 0], [0, 0]]  # [[Auto Pass & Human Pass, Auto Fail & Human Pass], [Auto Pass & Human Fail, Auto Fail & Human Fail]]
    discrepancies: list[dict[str, Any]] = []

    for row in human_rows:
        grade_str = row.get("correct_0_1_2", "").strip()
        if not grade_str:
            continue
        try:
            grade_val = int(grade_str)
        except ValueError:
            continue

        graded_count += 1
        human_pass = grade_val >= 1  # 1 or 2 treated as acceptable/pass
        qid = row.get("id") or row.get("question", "")
        auto_stat = auto_status_map.get(qid, auto_status_map.get(row.get("question", ""), "FAIL"))
        auto_pass = (auto_stat == "PASS")

        if human_pass and auto_pass:
            matrix[0][0] += 1
        elif human_pass and not auto_pass:
            matrix[0][1] += 1
            discrepancies.append({
                "id": qid,
                "human": f"PASS (grade {grade_val})",
                "auto": auto_stat,
                "notes": row.get("grader_notes", ""),
            })
        elif not human_pass and auto_pass:
            matrix[1][0] += 1
            discrepancies.append({
                "id": qid,
                "human": f"FAIL (grade {grade_val})",
                "auto": auto_stat,
                "notes": row.get("grader_notes", ""),
            })
        else:
            matrix[1][1] += 1

    if graded_count == 0:
        print(f"No human grades found in {csv_path}. (Fill 'correct_0_1_2' column with 0, 1, or 2 to evaluate).")
        return {"graded_count": 0}

    agreement_pct = round(((matrix[0][0] + matrix[1][1]) / graded_count) * 100, 1)
    kappa = calculate_cohen_kappa(matrix)

    print("\n" + "=" * 60)
    print("  HUMAN VS AUTOMATIC EVALUATION AGREEMENT")
    print("=" * 60)
    print(f"  Graded Questions   : {graded_count} / {len(human_rows)}")
    print(f"  Raw Agreement Rate : {agreement_pct}%")
    print(f"  Cohen's Kappa (κ)  : {kappa:.3f}")
    print()
    print("  Contingency Matrix:")
    print(f"                     Auto PASS   Auto FAIL")
    print(f"    Human PASS (1/2)    {matrix[0][0]:<10} {matrix[0][1]:<10}")
    print(f"    Human FAIL (0)      {matrix[1][0]:<10} {matrix[1][1]:<10}")
    print("=" * 60)
    if discrepancies:
        print(f"\n  Discrepancies ({len(discrepancies)}):")
        for d in discrepancies[:10]:
            print(f"    - [{d['id']}] Human={d['human']} vs Auto={d['auto']} | Notes: {d['notes']}")

    return {
        "graded_count": graded_count,
        "agreement_pct": agreement_pct,
        "cohens_kappa": kappa,
        "matrix": matrix,
        "discrepancies": discrepancies,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge human evaluation grades with automated runs.")
    parser.add_argument("--csv", type=Path, default=EVAL_DIR / "manual_grading.csv")
    parser.add_argument("--results", type=Path, default=None)
    args = parser.parse_args()

    merge_and_evaluate(args.csv, args.results)


if __name__ == "__main__":
    main()


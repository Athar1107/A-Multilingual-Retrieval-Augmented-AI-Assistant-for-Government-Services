"""Re-score existing result JSON with audited v2.0 logic.
Works entirely from saved JSON + CSV datasets (no live LLM needed).
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

root = Path(__file__).parent
sys.path.insert(0, str(root.parent))

from eval.run_evaluation import (
    SCORER_VERSION,
    answer_relevance,
    back_translate,
    expects_refusal,
    source_accuracy,
)

# Load ground-truth maps
en_map: dict[str, dict] = {}
with open(root / "eval_dataset_en.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        en_map[row["id"]] = row

kok_map: dict[str, dict] = {}
with open(root / "eval_dataset_kok.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        kok_map[row["id"]] = row

combined_map = {**en_map, **kok_map}


def rescore_file(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", [])
    total = len(results)
    if total == 0:
        return

    print(f"\n{'='*60}")
    print(f"  Re-scoring with {SCORER_VERSION}: {path.name}")
    print(f"{'='*60}")

    for r in results:
        qid = r["id"]
        gt_info = combined_map.get(qid, {})
        expected_src = gt_info.get("source_doc_id", r.get("source_doc", "none"))
        gt_text = gt_info.get("ground_truth", gt_info.get("ground_truth_english", r.get("ground_truth", "")))
        cat = gt_info.get("category", r.get("category", ""))
        lang = r.get("language", "en")
        answer = r.get("answer", "")

        # Sources
        sources = [{"title": t, "source_url": ""} for t in r.get("sources_returned", [])]
        new_src = source_accuracy(sources, expected_src)
        r["source_accuracy"] = new_src

        # Back-translation if available or needed
        back_trans = r.get("back_translation")
        if back_trans is None and lang == "kok":
            back_trans = back_translate(answer, lang)
            r["back_translation"] = back_trans

        # Audited answer relevance
        eval_text = back_trans if (lang == "kok" and back_trans) else answer
        new_rel = answer_relevance(
            answer,
            gt_text,
            language=lang,
            category=cat,
            back_translation_text=eval_text,
        )
        r["answer_relevance"] = new_rel

        # Status
        conf = r.get("confidence", 0.0)
        if cat == "out_of_corpus" or expects_refusal(gt_text, cat):
            status = "PASS" if new_rel >= 0.8 else "FAIL"
        else:
            status = "PASS" if (new_rel >= 0.3 and conf >= 0.5) else "FAIL"
        r["status"] = status

        icon = "✓" if status == "PASS" else "✗"
        print(f"  {qid:<10} status={icon}  rel={new_rel:.2f}  src={'✓' if new_src else '✗'}  conf={conf:.2f}")

    # Recompute summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    avg_rel = round(sum(r["answer_relevance"] for r in results) / total, 3)
    avg_con = round(sum(r["confidence"] for r in results) / total, 3)
    src_acc = round(sum(1 for r in results if r["source_accuracy"]) / total, 3)
    lang_acc = round(sum(1 for r in results if r.get("language_ok", True)) / total, 3)
    avg_lat = round(sum(r.get("latency_s", 0.0) for r in results) / total, 1)

    routes: dict[str, int] = {}
    for r in results:
        routes[r.get("route", "direct")] = routes.get(r.get("route", "direct"), 0) + 1

    data["scorer_version"] = SCORER_VERSION
    data["summary"] = {
        "scorer_version": SCORER_VERSION,
        "total": total,
        "passed": passed,
        "errors": sum(1 for r in results if r["status"] == "ERROR"),
        "pass_rate": round(passed / total, 3),
        "avg_answer_relevance": avg_rel,
        "source_accuracy": src_acc,
        "avg_confidence": avg_con,
        "language_accuracy": lang_acc,
        "avg_latency_s": avg_lat,
        "routes": routes,
    }

    print(f"\n  RE-SCORED SUMMARY ({SCORER_VERSION})")
    print(f"  Pass rate        : {passed}/{total} ({round(passed/total*100)}%)")
    print(f"  Answer relevance : {avg_rel:.3f}")
    print(f"  Source accuracy  : {src_acc:.3f}")
    print(f"  Avg confidence   : {avg_con:.3f}")
    print(f"  Language accuracy: {lang_acc:.3f}")

    # Save
    out = path.parent / path.name.replace("results_", "rescored_")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {out.name}")


if __name__ == "__main__":
    for f in sorted(root.glob("results_*.json")):
        rescore_file(f)

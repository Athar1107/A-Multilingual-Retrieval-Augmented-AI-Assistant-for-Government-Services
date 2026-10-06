"""Re-score existing result JSON with updated source_accuracy logic.
No API calls needed — works entirely from the saved JSON + CSV datasets.
"""
import csv, json, re, sys
from pathlib import Path

root = Path(__file__).parent

# Import updated scorer
sys.path.insert(0, str(root.parent))
from eval.run_evaluation import source_accuracy, answer_relevance

# Load EN dataset for expected doc IDs
en_map = {}
with open(root / "eval_dataset_en.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        en_map[row["id"]] = row["source_doc_id"]

kok_map = {}
with open(root / "eval_dataset_kok.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        kok_map[row["id"]] = row["source_doc_id"]

combined_map = {**en_map, **kok_map}

def rescore_file(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data["results"]
    total = len(results)
    src_pass = 0

    print(f"\n{'='*60}")
    print(f"  Re-scoring: {path.name}")
    print(f"{'='*60}")

    for r in results:
        expected = combined_map.get(r["id"], "")
        # Re-build sources list from stored data
        sources = [{"title": t, "source_url": ""} for t in r.get("sources_returned", [])]
        new_src = source_accuracy(sources, expected)
        old_src = r["source_accuracy"]
        r["source_accuracy"] = new_src
        if new_src:
            src_pass += 1
        change = "  (fixed ✅)" if new_src and not old_src else ""
        icon = "✓" if new_src else "✗"
        print(f"  {r['id']:<10} src={icon}  {change}  {r['sources_returned'][0][:45] if r['sources_returned'] else 'none'}")

    # Recompute summary
    passed = sum(1 for r in results if r["answer_relevance"] >= 0.3 and r["confidence"] >= 0.5)
    avg_rel = round(sum(r["answer_relevance"] for r in results) / total, 3)
    avg_con = round(sum(r["confidence"] for r in results) / total, 3)
    src_acc = round(src_pass / total, 3)
    lang_acc= round(sum(1 for r in results if r["language_ok"]) / total, 3)
    avg_lat = round(sum(r["latency_s"] for r in results) / total, 1)

    data["summary"]["source_accuracy"] = src_acc
    data["summary"]["avg_answer_relevance"] = avg_rel

    print(f"\n  UPDATED SUMMARY")
    print(f"  Pass rate        : {passed}/{total} ({round(passed/total*100)}%)")
    print(f"  Answer relevance : {avg_rel:.3f}")
    print(f"  Source accuracy  : {src_acc:.3f}  ← updated")
    print(f"  Avg confidence   : {avg_con:.3f}")
    print(f"  Language accuracy: {lang_acc:.3f}")
    print(f"  Avg latency      : {avg_lat:.1f}s")

    # Save rescored file
    out = path.parent / path.name.replace("results_", "rescored_")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Saved: {out.name}")

for f in sorted(root.glob("results_en_*.json"))[-1:]:
    rescore_file(f)
for f in sorted(root.glob("results_kok_2026100*7.json"))[-1:]:
    rescore_file(f)

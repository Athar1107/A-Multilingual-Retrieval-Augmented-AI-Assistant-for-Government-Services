"""Analyse evaluation results to understand source accuracy failures."""
import json, sys
from pathlib import Path

root = Path(__file__).parent

for fname in sorted(root.glob("results_en_*.json"))[-1:]:
    data = json.loads(fname.read_text(encoding="utf-8"))
    print(f"File: {fname.name}\n")
    print("=== SOURCE ACCURACY FAILURES ===")
    for r in data["results"]:
        if not r["source_accuracy"]:
            src_doc = None
            # reconstruct expected from dataset
            print(f"  {r['id']}")
            print(f"  Q       : {r['question'][:70]}")
            print(f"  Sources : {r['sources_returned'][:3]}")
            print()
    print("=== ALL RESULTS ===")
    print(f"  {'ID':<10} {'src':>3}  {'rel':>5}  {'sources_returned'}")
    for r in data["results"]:
        src_ok = "✓" if r["source_accuracy"] else "✗"
        print(f"  {r['id']:<10} {src_ok}    {r['answer_relevance']:.2f}  {r['sources_returned'][0][:45] if r['sources_returned'] else 'none'}")

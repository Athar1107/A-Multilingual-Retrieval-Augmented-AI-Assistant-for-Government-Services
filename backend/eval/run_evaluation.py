"""RAG Evaluation Pipeline.

Tests the live API against the ground-truth dataset and computes:
  - Answer Relevance    : does the answer contain key ground truth terms?
  - Source Accuracy     : is the correct document cited?
  - Confidence Score    : model's own confidence
  - Latency             : response time per query
  - Language Accuracy   : response is in the expected language (for KOK queries)

Run with server running:
    python eval/run_evaluation.py
    python eval/run_evaluation.py --dataset kok
    python eval/run_evaluation.py --dataset both --output eval/results.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE_URL   = "http://127.0.0.1:8000"
EVAL_DIR   = Path(__file__).parent
EN_CSV     = EVAL_DIR / "eval_dataset_en.csv"
KOK_CSV    = EVAL_DIR / "eval_dataset_kok.csv"


# ── Scoring helpers ────────────────────────────────────────────────────────────

def tokenise(text: str) -> set[str]:
    """Lowercase word tokens for soft matching."""
    return set(re.findall(r"[a-z0-9₹]+", text.lower()))


def answer_relevance(answer: str, ground_truth: str, language: str = "en") -> float:
    """Fraction of ground-truth key tokens found in the answer.

    For Konkani (kok) answers: also checks key numbers and proper nouns
    (amounts like 2500, years like 2013) which survive translation.
    Score: 0.0 – 1.0
    """
    stops = {"the", "a", "an", "is", "are", "for", "of", "to", "in", "and",
             "or", "by", "with", "that", "this", "be", "as", "at", "on"}

    # Extract numbers and amounts — these are language-agnostic
    numbers_gt  = set(re.findall(r"\d+", ground_truth))
    numbers_ans = set(re.findall(r"\d+", answer))
    number_hits = len(numbers_gt & numbers_ans)

    if language == "kok":
        # For Konkani answers, score based on:
        # 1. Numbers/amounts matching (Rs amounts, years, counts)
        # 2. Whether answer has Devanagari content at all (non-empty response)
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", answer))
        if not numbers_gt:
            return 1.0 if has_devanagari else 0.0
        score = (number_hits / len(numbers_gt)) if numbers_gt else 0.0
        # Boost if the answer is non-trivially long (> 50 chars) in Devanagari
        if has_devanagari and len(answer) > 50:
            score = min(1.0, score + 0.3)
        return round(score, 3)

    # English: token overlap
    gt_tokens = {t for t in tokenise(ground_truth) if len(t) >= 3 and t not in stops}
    if not gt_tokens:
        return 1.0
    ans_tokens = tokenise(answer)
    found = sum(1 for t in gt_tokens if t in ans_tokens)
    return round(found / len(gt_tokens), 3)


def source_accuracy(sources: list[dict], expected_doc_id: str) -> bool:
    """True if any returned source matches the expected document.

    Checks:
    1. Source URL contains the expected doc slug
    2. Source title contains key words from the expected doc slug
       (handles PDF sources where URL is a goa.gov.in path, not the slug)
    """
    # Build keyword set from doc slug (split on hyphens, ignore short tokens)
    slug_words = {w for w in expected_doc_id.lower().split("-") if len(w) > 3
                  and w not in {"goa", "scheme", "the", "for", "and", "from"}}

    for s in sources:
        url   = (s.get("source_url", "") or "").lower()
        title = (s.get("title", "") or "").lower()

        # Direct slug match in URL
        if expected_doc_id in url:
            return True

        # Title keyword overlap — if ≥2 slug keywords appear in the title
        if slug_words:
            hits = sum(1 for w in slug_words if w in title)
            if hits >= min(2, len(slug_words)):
                return True

    return False


def detect_devanagari(text: str) -> bool:
    """Return True if the text contains Devanagari characters."""
    return bool(re.search(r"[\u0900-\u097F]", text))


# ── Query function ─────────────────────────────────────────────────────────────

def query_api(question: str, language: str, timeout: float = 180.0) -> dict:
    t0  = time.time()
    res = httpx.post(
        f"{BASE_URL}/query",
        json={"text": question, "language": language},
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    res.raise_for_status()
    data = res.json()
    data["_latency_s"] = elapsed
    return data


# ── Dataset loader ─────────────────────────────────────────────────────────────

def load_en_dataset() -> list[dict]:
    rows = []
    with open(EN_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "id":           row["id"],
                "question":     row["question"],
                "ground_truth": row["ground_truth"],
                "source_doc":   row["source_doc_id"],
                "category":     row["category"],
                "language":     "en",
            })
    return rows


def load_kok_dataset() -> list[dict]:
    rows = []
    with open(KOK_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "id":           row["id"],
                "question":     row["question_konkani"],
                "ground_truth": row["ground_truth_english"],
                "source_doc":   row["source_doc_id"],
                "category":     row["category"],
                "language":     "kok",
            })
    return rows


# ── Main evaluation loop ───────────────────────────────────────────────────────

def run_eval(dataset: list[dict]) -> list[dict]:
    results = []
    total   = len(dataset)

    for i, item in enumerate(dataset, 1):
        print(f"  [{i:02d}/{total}] {item['id']}  Q: {item['question'][:60]}")
        try:
            data    = query_api(item["question"], item["language"])
            answer  = data.get("answer", "")
            sources = data.get("sources", [])
            conf    = data.get("confidence", 0.0)
            latency = data["_latency_s"]

            rel     = answer_relevance(answer, item["ground_truth"], item["language"])
            src_ok  = source_accuracy(sources, item["source_doc"])

            lang_ok = True
            if item["language"] == "kok":
                lang_ok = detect_devanagari(answer)

            status = "PASS" if (rel >= 0.3 and conf >= 0.5) else "FAIL"

            result = {
                "id":               item["id"],
                "language":         item["language"],
                "category":         item["category"],
                "question":         item["question"],
                "ground_truth":     item["ground_truth"],
                "answer":           answer[:300],
                "answer_relevance": rel,
                "source_accuracy":  src_ok,
                "confidence":       conf,
                "language_ok":      lang_ok,
                "latency_s":        latency,
                "status":           status,
                "sources_returned": [s.get("title","")[:50] for s in sources[:3]],
            }

            icon = "✅" if status == "PASS" else "❌"
            print(f"         {icon} rel={rel:.2f}  src={'✓' if src_ok else '✗'}  "
                  f"conf={conf:.2f}  {latency:.1f}s")

        except Exception as exc:
            print(f"         ⚠️  ERROR: {exc}")
            result = {
                "id": item["id"], "language": item["language"],
                "category": item["category"], "question": item["question"],
                "ground_truth": item["ground_truth"],
                "answer": "", "answer_relevance": 0.0,
                "source_accuracy": False, "confidence": 0.0,
                "language_ok": False, "latency_s": 0.0,
                "status": "ERROR", "sources_returned": [],
                "error": str(exc),
            }

        results.append(result)

    return results


# ── Summary ────────────────────────────────────────────────────────────────────

def print_summary(results: list[dict]) -> dict:
    total   = len(results)
    passed  = sum(1 for r in results if r["status"] == "PASS")
    errors  = sum(1 for r in results if r["status"] == "ERROR")
    avg_rel = round(sum(r["answer_relevance"] for r in results) / total, 3)
    avg_con = round(sum(r["confidence"] for r in results) / total, 3)
    src_acc = round(sum(1 for r in results if r["source_accuracy"]) / total, 3)
    avg_lat = round(sum(r["latency_s"] for r in results) / total, 1)
    lang_acc= round(sum(1 for r in results if r["language_ok"]) / total, 3)

    # By category
    cats: dict[str, list] = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)

    print()
    print("=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Total questions    : {total}")
    print(f"  Passed             : {passed} / {total}  ({round(passed/total*100)}%)")
    print(f"  Errors             : {errors}")
    print(f"  Avg answer relevance: {avg_rel:.3f}  (target ≥ 0.30)")
    print(f"  Source accuracy    : {src_acc:.3f}  (target ≥ 0.70)")
    print(f"  Avg confidence     : {avg_con:.3f}  (target ≥ 0.60)")
    print(f"  Language accuracy  : {lang_acc:.3f}  (target = 1.00)")
    print(f"  Avg latency        : {avg_lat:.1f}s")
    print()
    print("  By category:")
    for cat, items in sorted(cats.items()):
        c_pass = sum(1 for r in items if r["status"] == "PASS")
        c_rel  = round(sum(r["answer_relevance"] for r in items) / len(items), 2)
        print(f"    {cat:<25} {c_pass}/{len(items)} pass  rel={c_rel:.2f}")
    print("=" * 60)

    return {
        "total": total, "passed": passed, "errors": errors,
        "pass_rate": round(passed/total, 3),
        "avg_answer_relevance": avg_rel,
        "source_accuracy": src_acc,
        "avg_confidence": avg_con,
        "language_accuracy": lang_acc,
        "avg_latency_s": avg_lat,
    }


# ── Entry point ────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument("--dataset", choices=["en", "kok", "both"], default="en")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    # Check server
    try:
        httpx.get(f"{BASE_URL}/health", timeout=5).raise_for_status()
        print(f"Server: UP at {BASE_URL}")
    except Exception as e:
        print(f"ERROR: Cannot reach server at {BASE_URL} — {e}")
        print("Start start_server.bat first.")
        sys.exit(1)

    datasets: list[dict] = []
    if args.dataset in ("en", "both"):
        datasets += load_en_dataset()
    if args.dataset in ("kok", "both"):
        datasets += load_kok_dataset()

    print(f"\nRunning evaluation on {len(datasets)} questions "
          f"(dataset={args.dataset})...\n")

    results = run_eval(datasets)
    summary = print_summary(results)

    output = args.output or (EVAL_DIR / f"results_{args.dataset}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n  Results saved to: {output}")


if __name__ == "__main__":
    main()
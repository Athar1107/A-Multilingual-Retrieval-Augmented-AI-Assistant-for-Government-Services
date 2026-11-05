"""RAG Evaluation Pipeline — Audited v2.0.

Tests the live API against the ground-truth dataset and computes:
  - Answer Relevance    : key-fact match (normalized numbers + entities)
                          with back-translation for Konkani and refusal detection.
  - Mandatory Contrasts : entity attachment check (boys vs girls, min vs max).
  - Source Accuracy     : is the correct document cited?
  - Confidence Score    : model's own confidence
  - Latency             : response time per query
  - Language Accuracy   : response is in expected script/language

Run with server running:
    python backend/eval/run_evaluation.py --dataset en
    python backend/eval/run_evaluation.py --dataset kok
    python backend/eval/run_evaluation.py --dataset both
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# Ensure stdout can handle UTF-8 on Windows (cp1252 terminal would otherwise
# crash on Devanagari characters in answers or any emoji in progress lines).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCORER_VERSION = "v2.0_audited"
BASE_URL       = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
API_KEY        = os.environ.get("API_KEY", "")
EVAL_DIR       = Path(__file__).parent
EN_CSV         = EVAL_DIR / "eval_dataset_en.csv"
KOK_CSV        = EVAL_DIR / "eval_dataset_kok.csv"
MANUAL_CSV     = EVAL_DIR / "manual_grading.csv"

# Make backend/app importable if needed
sys.path.insert(0, str(EVAL_DIR.parent))

# Global lazy translator instance for back-translation
_translator_instance: Any = None


def get_eval_translator() -> Any:
    global _translator_instance
    if _translator_instance is None:
        try:
            from app.rag.translation import TranslationService
            _translator_instance = TranslationService()
        except Exception as exc:
            print(f"Warning: could not load TranslationService for eval: {exc}")
            _translator_instance = False
    return _translator_instance if _translator_instance is not False else None


# ── Text & Number Normalisation ───────────────────────────────────────────────

DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_text_for_facts(text: str) -> str:
    """Standardize numbers, currency signs, and whitespace."""
    if not text:
        return ""
    # Map Devanagari numerals to ASCII digits
    t = text.translate(DEVA_DIGITS)
    # Strip commas between digits: "2,500" -> "2500"
    t = re.sub(r"(?<=\d),(?=\d)", "", t)
    # Normalize currency notations
    t = re.sub(r"(?:rs\.?|inr|₹)\s*", "₹ ", t, flags=re.IGNORECASE)
    # Collapse multiple whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_numbers(text: str) -> set[str]:
    """Extract all numbers from normalized text."""
    normalized = normalize_text_for_facts(text)
    return set(re.findall(r"\d+", normalized))


def tokenise(text: str) -> set[str]:
    """Lowercase word tokens for soft matching."""
    normalized = normalize_text_for_facts(text).lower()
    return set(re.findall(r"[a-z0-9₹]+", normalized))


def detect_devanagari(text: str) -> bool:
    """Return True if the text contains Devanagari characters."""
    return bool(re.search(r"[\u0900-\u097F]", text))


# ── Refusal Detection ─────────────────────────────────────────────────────────

REFUSAL_PATTERNS_EN = (
    "no relevant information",
    "not confident enough",
    "no reliable information",
    "verify with the official scheme portal",
    "verify at myscheme.gov.in",
    "myscheme.gov.in",
    "no information was found",
    "no information found",
    "no information available",
    "cannot find",
    "could not find",
    "not mentioned in the context",
    "does not contain",
    "no details found",
    "not available in the context",
    "does not mention",
    "out of scope",
)

REFUSAL_PATTERNS_KOK = (
    "म्हायती मेळना",
    "म्हायती उपलब्ध ना",
    "तपशील मेळना",
    "उल्लेख ना",
    "विश्वासार्ह म्हायती ना",
    "विश्वसनीय म्हायती ना",
    "खात्री करात",
    "myscheme.gov.in",
)


def is_refusal_answer(text: str) -> bool:
    """Return True if the answer states no reliable information was found."""
    t_lower = text.lower()
    if any(p in t_lower for p in REFUSAL_PATTERNS_EN):
        return True
    if any(p in text for p in REFUSAL_PATTERNS_KOK):
        return True
    return False


def expects_refusal(ground_truth: str, category: str = "") -> bool:
    """Return True if ground truth expects a refusal."""
    gt_lower = ground_truth.lower()
    if "refusal" in gt_lower or category == "out_of_corpus":
        return True
    if "no information" in gt_lower or "out-of-scope" in gt_lower:
        return True
    return False


# ── Entity & Contrast Validation ──────────────────────────────────────────────

def check_mandatory_contrasts(eval_text: str, ground_truth: str) -> bool:
    """Verify that contrasted entities (e.g. boys vs girls, min vs max) match correctly.

    Returns False if a fact is explicitly attached to the wrong entity.
    """
    clean_text = normalize_text_for_facts(eval_text).lower()
    clean_gt   = normalize_text_for_facts(ground_truth).lower()

    # Boys (₹2500) vs Girls (₹3000) under PMSS
    if "boys" in clean_gt and "2500" in clean_gt:
        # Check if 3000 is incorrectly attached to boys
        if re.search(r"(?:₹\s*3000|3000)\s*(?:per\s*month)?\s*(?:for|\/|-)?\s*boys", clean_text) or \
           re.search(r"boys\s*(?:receive|get|are\s*awarded|awarded|eligible\s*for)?\s*(?:₹\s*3000|3000)", clean_text):
            return False
        # Check if 2500 is incorrectly attached exclusively to girls
        if re.search(r"(?:₹\s*2500|2500)\s*(?:per\s*month)?\s*(?:for|\/|-)?\s*girls", clean_text) and "boys" not in clean_text:
            return False

    if "girls" in clean_gt and "3000" in clean_gt:
        # Check if 2500 is incorrectly attached to girls
        if re.search(r"(?:₹\s*2500|2500)\s*(?:per\s*month)?\s*(?:for|\/|-)?\s*girls", clean_text) or \
           re.search(r"girls\s*(?:receive|get|are\s*awarded|awarded|eligible\s*for)?\s*(?:₹\s*2500|2500)", clean_text):
            return False
        # Check if 3000 is attached exclusively to boys
        if re.search(r"(?:₹\s*3000|3000)\s*(?:per\s*month)?\s*(?:for|\/|-)?\s*boys", clean_text) and "girls" not in clean_text:
            return False

    # Min vs Max duration (e.g. DPIIT min 1 month, max 3 months)
    if "minimum" in clean_gt and "maximum" in clean_gt:
        if re.search(r"minimum\s*(?:of\s*)?3", clean_text) or re.search(r"maximum\s*(?:of\s*)?1", clean_text):
            return False

    return True


# ── Back-translation & Relevance Scoring ──────────────────────────────────────

def back_translate(text: str, language: str) -> str:
    """Back-translate Konkani answer to English using TranslationService."""
    if language != "kok" or not detect_devanagari(text):
        return text

    translator = get_eval_translator()
    if translator:
        try:
            return translator.konkani_to_english(text)
        except Exception as exc:
            print(f"Back-translation error: {exc}")
    return text


def answer_relevance(
    answer: str,
    ground_truth: str,
    language: str = "en",
    category: str = "",
    back_translation_text: str | None = None,
) -> float:
    """Audited key-fact match (numbers + named entities) against ground truth.

    1. Refusal handling:
       - If GT expects refusal: answer must be a refusal -> 1.0, else 0.0.
       - If GT expects factual answer: refusal -> 0.0.
    2. Mandatory contrast check (e.g. boys ₹2500 vs girls ₹3000):
       - If fact attached to wrong entity -> 0.0.
    3. Factual scoring:
       - Normalized number overlap.
       - Key content token/entity overlap.
       - No artificial Devanagari length boosts (+0.3) or free 1.0 passes!
    """
    eval_text = back_translation_text if back_translation_text is not None else answer

    expected_ref = expects_refusal(ground_truth, category)
    is_ref = is_refusal_answer(eval_text) or (language == "kok" and is_refusal_answer(answer))

    if expected_ref:
        return 1.0 if is_ref else 0.0
    if is_ref:
        return 0.0

    # Mandatory contrast check
    if not check_mandatory_contrasts(eval_text, ground_truth):
        return 0.0

    # Number overlap
    gt_nums  = extract_numbers(ground_truth)
    ans_nums = extract_numbers(eval_text)
    if language == "kok":
        ans_nums |= extract_numbers(answer)

    if gt_nums:
        num_hits = len(gt_nums & ans_nums)
        if num_hits == 0:
            return 0.0
        num_score = num_hits / len(gt_nums)
    else:
        num_score = 1.0

    # Key entity and token overlap
    stops = {
        "the", "a", "an", "is", "are", "for", "of", "to", "in", "and",
        "or", "by", "with", "that", "this", "be", "as", "at", "on", "from",
        "under", "who", "what", "which", "how", "per", "month", "annum", "year", "each",
        "rupees", "rs", "inr"
    }
    gt_tokens = {
        t for t in tokenise(ground_truth)
        if len(t) >= 3 and t not in stops and not t.isdigit()
    }
    ans_tokens = tokenise(eval_text)

    if gt_tokens:
        token_hits = sum(1 for t in gt_tokens if t in ans_tokens)
        token_score = token_hits / len(gt_tokens)
    else:
        token_score = 1.0

    if gt_nums and gt_tokens:
        composite = 0.6 * num_score + 0.4 * token_score
    elif gt_nums:
        composite = num_score
    else:
        composite = token_score

    return round(composite, 3)


def source_accuracy(sources: list[dict], expected_doc_id: str) -> bool:
    """True if any returned source matches expected document slug or keywords."""
    if expected_doc_id == "none":
        # Out of corpus: accurate if no sources or source accuracy not required
        return len(sources) == 0 or True

    slug_words = {
        w for w in expected_doc_id.lower().split("-")
        if len(w) > 3 and w not in {"goa", "scheme", "the", "for", "and", "from"}
    }

    for s in sources:
        url   = (s.get("source_url", "") or "").lower()
        title = (s.get("title", "") or "").lower()

        if expected_doc_id in url:
            return True

        if slug_words:
            hits = sum(1 for w in slug_words if w in title)
            if hits >= min(2, len(slug_words)):
                return True

    return False


# ── Query function ─────────────────────────────────────────────────────────────

def query_api(question: str, language: str, timeout: float = 180.0) -> dict:
    t0 = time.time()
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    res = httpx.post(
        f"{BASE_URL}/query",
        json={"text": question, "language": language},
        headers=headers,
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

def run_eval(dataset: list[dict]) -> tuple[list[dict], list[dict]]:
    results = []
    manual_grading_rows = []
    total = len(dataset)

    for i, item in enumerate(dataset, 1):
        print(f"  [{i:02d}/{total}] {item['id']}  Q: {item['question'][:60]}")
        try:
            data    = query_api(item["question"], item["language"])
            answer  = data.get("answer", "")
            sources = data.get("sources", [])
            conf    = data.get("confidence", 0.0)
            route   = data.get("route", "direct")
            t_backend = data.get("translator_backend", "unknown")
            hint_applied = data.get("retrieval_hint_applied", False)
            doc_ids = data.get("retrieved_doc_ids", [])
            latency = data["_latency_s"]

            # Back-translate Konkani answer to English for scoring
            back_trans = ""
            if item["language"] == "kok":
                back_trans = back_translate(answer, item["language"])
            eval_text = back_trans if item["language"] == "kok" else answer

            rel    = answer_relevance(
                answer,
                item["ground_truth"],
                language=item["language"],
                category=item["category"],
                back_translation_text=eval_text,
            )
            src_ok = source_accuracy(sources, item["source_doc"])

            lang_ok = True
            if item["language"] == "kok":
                lang_ok = detect_devanagari(answer)

            # Refusal expectations: out-of-corpus queries pass if relevance == 1.0 (refusal)
            if item["category"] == "out_of_corpus":
                status = "PASS" if rel >= 0.8 else "FAIL"
            else:
                status = "PASS" if (rel >= 0.3 and conf >= 0.5) else "FAIL"

            result = {
                "id":                     item["id"],
                "language":               item["language"],
                "category":               item["category"],
                "question":               item["question"],
                "ground_truth":           item["ground_truth"],
                "answer":                 answer,
                "back_translation":       back_trans,
                "answer_relevance":       rel,
                "source_accuracy":        src_ok,
                "confidence":             conf,
                "route":                  route,
                "translator_backend":     t_backend,
                "retrieval_hint_applied": hint_applied,
                "retrieved_doc_ids":      doc_ids,
                "language_ok":            lang_ok,
                "latency_s":              latency,
                "status":                 status,
                "sources_returned":       [s.get("title", "")[:50] for s in sources[:3]],
            }

            manual_grading_rows.append({
                "question":         item["question"],
                "answer":           answer,
                "back_translation": back_trans,
                "ground_truth":     item["ground_truth"],
                "correct_0_1_2":    "",
                "grader_notes":     "",
            })

            icon = "[PASS]" if status == "PASS" else "[FAIL]"
            print(f"         {icon} rel={rel:.2f}  src={'ok' if src_ok else '--'}  "
                  f"conf={conf:.2f}  route={route}  hint={'yes' if hint_applied else 'no'}  {latency:.1f}s")

        except Exception as exc:
            print(f"         [ERR]  ERROR: {exc}")
            result = {
                "id":                     item["id"],
                "language":               item["language"],
                "category":               item["category"],
                "question":               item["question"],
                "ground_truth":           item["ground_truth"],
                "answer":                 "",
                "back_translation":       "",
                "answer_relevance":       0.0,
                "source_accuracy":        False,
                "confidence":             0.0,
                "route":                  "error",
                "translator_backend":     "none",
                "retrieval_hint_applied": False,
                "retrieved_doc_ids":      [],
                "language_ok":            False,
                "latency_s":              0.0,
                "status":                 "ERROR",
                "sources_returned":       [],
                "error":                  str(exc),
            }
            manual_grading_rows.append({
                "question":         item["question"],
                "answer":           f"ERROR: {exc}",
                "back_translation": "",
                "ground_truth":     item["ground_truth"],
                "correct_0_1_2":    "0",
                "grader_notes":     "Query threw exception",
            })

        results.append(result)

    return results, manual_grading_rows


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

    routes: dict[str, int] = {}
    for r in results:
        routes[r.get("route", "direct")] = routes.get(r.get("route", "direct"), 0) + 1

    cats: dict[str, list] = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)

    print()
    print("=" * 60)
    print(f"  EVALUATION RESULTS  (Scorer: {SCORER_VERSION})")
    print("=" * 60)
    print(f"  Total questions     : {total}")
    print(f"  Passed              : {passed} / {total}  ({round(passed/total*100)}%)")
    print(f"  Errors              : {errors}")
    print(f"  Avg answer relevance: {avg_rel:.3f}  (factual key-fact match)")
    print(f"  Source accuracy     : {src_acc:.3f}")
    print(f"  Avg confidence      : {avg_con:.3f}")
    print(f"  Language accuracy   : {lang_acc:.3f}")
    print(f"  Avg latency         : {avg_lat:.1f}s")
    print(f"  Route distribution  : {routes}")
    print()
    print("  By category:")
    for cat, items in sorted(cats.items()):
        c_pass = sum(1 for r in items if r["status"] == "PASS")
        c_rel  = round(sum(r["answer_relevance"] for r in items) / len(items), 2)
        print(f"    {cat:<25} {c_pass}/{len(items)} pass  rel={c_rel:.2f}")
    print("=" * 60)

    return {
        "scorer_version": SCORER_VERSION,
        "total": total,
        "passed": passed,
        "errors": errors,
        "pass_rate": round(passed/total, 3),
        "avg_answer_relevance": avg_rel,
        "source_accuracy": src_acc,
        "avg_confidence": avg_con,
        "language_accuracy": lang_acc,
        "avg_latency_s": avg_lat,
        "routes": routes,
    }


def export_manual_grading_csv(rows: list[dict], path: Path = MANUAL_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "question",
            "answer",
            "back_translation",
            "ground_truth",
            "correct_0_1_2",
            "grader_notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Manual grading sheet exported to: {path}")


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
        print("Start server first: uvicorn app.main:app --port 8000")
        sys.exit(1)

    datasets: list[dict] = []
    if args.dataset in ("en", "both"):
        datasets += load_en_dataset()
    if args.dataset in ("kok", "both"):
        datasets += load_kok_dataset()

    print(f"\nRunning evaluation on {len(datasets)} questions (dataset={args.dataset})...\n")

    results, grading_rows = run_eval(datasets)
    summary = print_summary(results)

    # Export manual grading CSV
    export_manual_grading_csv(grading_rows)

    output = args.output or (
        EVAL_DIR / f"results_{args.dataset}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "scorer_version": SCORER_VERSION,
                "summary": summary,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n  Results saved to: {output}")


if __name__ == "__main__":
    main()

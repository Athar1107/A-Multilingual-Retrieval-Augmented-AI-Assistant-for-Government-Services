"""End-to-end pipeline test — runs retrieval + generation without a server.

Run from the repo root:
    set HF_HUB_OFFLINE=1
    cd backend
    python scripts/test_pipeline_e2e.py
"""
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.pipeline import RAGPipeline

QUERIES = [
    ("What scholarships are available for girl students?", "en"),
    ("Who is eligible for PM scholarship scheme?",        "en"),
    ("What is the benefit amount for NMMSS?",             "en"),
    ("Tell me about overseas scholarship for SC students", "en"),
    ("Which internship schemes are available for students?", "en"),
]

print("=" * 65)
print("  RAG Pipeline — End-to-End Test")
print("=" * 65)
print("  Loading retriever (ChromaDB + BM25) ...")

try:
    pipeline = RAGPipeline(translator=False)
    print("  Pipeline ready.\n")
except Exception as exc:
    print(f"  FAILED to load pipeline: {exc}")
    sys.exit(1)

for i, (query, lang) in enumerate(QUERIES, 1):
    print(f"[{i}/{len(QUERIES)}] Q: {query}")
    t0 = time.time()
    result = pipeline.answer(query, language=lang)
    elapsed = time.time() - t0

    print(f"  Route      : {result['route']}")
    print(f"  Confidence : {result['confidence']:.4f}")
    print(f"  Latency    : {elapsed:.1f}s")
    print(f"  Answer     : {result['answer'][:300]}")
    if result["sources"]:
        print("  Sources    :")
        for s in result["sources"]:
            print(f"    - {s['title'][:60]}")
            print(f"      {s['source_url']}")
    print()

print("=" * 65)
print(f"  Done — {len(QUERIES)} queries tested.")

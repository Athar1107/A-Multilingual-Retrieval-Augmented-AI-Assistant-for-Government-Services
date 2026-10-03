"""Verify every component of the pipeline is working independently."""
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

print("=" * 60)
print("  Pipeline Component Verification")
print("=" * 60)
print()

# 1. Corpus
print("[1] Corpus (active_english.json)")
try:
    corpus_path = ROOT / "data" / "processed" / "active_english.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    print(f"    Documents : {len(corpus)}")
    print(f"    File size : {corpus_path.stat().st_size // 1024} KB")
    print(f"    Sample    : {corpus[0]['title'][:60]}")
    print("    STATUS    : OK")
except Exception as e:
    print(f"    STATUS    : FAIL - {e}")
print()

# 2. ChromaDB
print("[2] ChromaDB Index")
try:
    import chromadb
    from app.config import CHROMA_INDEX_PATH, CHROMA_COLLECTION_NAME
    client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
    col = client.get_collection(CHROMA_COLLECTION_NAME)
    print(f"    Collection: {CHROMA_COLLECTION_NAME}")
    print(f"    Chunks    : {col.count()}")
    print("    STATUS    : OK")
except Exception as e:
    print(f"    STATUS    : FAIL - {e}")
print()

# 3. Retrieval (dense + BM25)
print("[3] Hybrid Retriever")
try:
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from app.rag.retriever import Retriever
    r = Retriever()
    results = r.retrieve("scholarship for girl students", top_k=3)
    print(f"    Query     : 'scholarship for girl students'")
    print(f"    Results   : {len(results)}")
    for res in results[:3]:
        print(f"    [{res['type']:6}] rrf={res['rrf_score']:.5f}  {res['title'][:50]}")
    print("    STATUS    : OK")
except Exception as e:
    print(f"    STATUS    : FAIL - {e}")
print()

# 4. Ollama / LLM
print("[4] Ollama LLM")
try:
    import httpx
    from app.config import OLLAMA_URL, OLLAMA_MODEL
    t0 = time.time()
    resp = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": "Reply in exactly 5 words: What is a scholarship?",
            "stream": False,
            "options": {"num_predict": 10},
        },
        timeout=120.0,
    )
    elapsed = time.time() - t0
    if resp.status_code == 200:
        answer = resp.json().get("response", "").strip()
        print(f"    Model     : {OLLAMA_MODEL}")
        print(f"    Response  : {answer[:80]}")
        print(f"    Latency   : {elapsed:.1f}s")
        print("    STATUS    : OK")
    else:
        print(f"    STATUS    : FAIL - HTTP {resp.status_code}")
except Exception as e:
    print(f"    STATUS    : FAIL - {e}")
print()

# 5. Translation
print("[5] IndicTrans2 Translation (gom_Deva)")
try:
    os.environ["TRANSLATION_MODEL"] = "indictrans2"
    os.environ["HF_HUB_OFFLINE"] = "0"
    from app.rag.translation import TranslationService
    svc = TranslationService()
    t0 = time.time()
    en = svc.konkani_to_english("पीएम किसान योजनेचा लाभ किती आहे?")
    elapsed = time.time() - t0
    print(f"    Input     : 'pM Kisan benefit question' (Konkani)")
    print(f"    EN output : {en}")
    print(f"    Latency   : {elapsed:.1f}s")
    t0 = time.time()
    kok = svc.english_to_konkani("The scholarship provides 6000 rupees per year.")
    elapsed = time.time() - t0
    print(f"    KOK output: {kok}")
    print(f"    Latency   : {elapsed:.1f}s")
    print(f"    Backend   : {svc.backend_name}")
    print("    STATUS    : OK")
except Exception as e:
    print(f"    STATUS    : FAIL - {e}")
print()

print("=" * 60)
print("  Verification complete.")
print("=" * 60)

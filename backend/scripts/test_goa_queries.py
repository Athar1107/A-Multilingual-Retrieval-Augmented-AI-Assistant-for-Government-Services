"""Test queries specific to SCERT Goa and DOL Goa sources."""
import sys, time, httpx
from pathlib import Path

BASE = "http://127.0.0.1:8000"

QUERIES = [
    ("What is the Science Talent Search Examination scholarship amount?", "en"),
    ("What is the Bhasha Puraskar Yojana award for Konkani language?", "en"),
    ("How to get a residence certificate in South Goa?", "en"),
    ("What is NMMSS Goa scholarship?", "en"),
    ("What services does the Directorate of Official Language Goa provide?", "en"),
]

try:
    httpx.get(f"{BASE}/health", timeout=3).raise_for_status()
except Exception:
    print("Server not running. Start start_server.bat first.")
    sys.exit(1)

print("=" * 65)
print("  Goa-Specific Query Test (SCERT + DOL sources)")
print("=" * 65)

for i, (q, lang) in enumerate(QUERIES, 1):
    print(f"\n[{i}/{len(QUERIES)}] {q}")
    t0 = time.time()
    r = httpx.post(f"{BASE}/query", json={"text": q, "language": lang}, timeout=180).json()
    print(f"  Answer  : {r['answer'][:250]}")
    print(f"  Time    : {time.time()-t0:.1f}s  |  Confidence: {r['confidence']}")
    for s in r["sources"][:2]:
        print(f"  Source  : {s['title'][:60]}")

print("\n" + "=" * 65)

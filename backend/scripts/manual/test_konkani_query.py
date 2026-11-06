"""Full end-to-end test: Goan Konkani query -> pipeline -> Konkani answer."""
import sys
import json
import time
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE = "http://127.0.0.1:8000"

queries = [
    {
        "text": "सरकारी शिष्यवृत्ती मिळवण्यासाठी कोणती कागदपत्रे लागतात?",
        "language": "kok",
        "desc": "What documents needed for scholarship?"
    },
    {
        "text": "पीएम किसान योजनेचा वार्षिक लाभ किती आहे?",
        "language": "kok",
        "desc": "What is PM Kisan annual benefit?"
    },
    {
        "text": "इंटर्नशिप योजनेसाठी कोण पात्र आहे?",
        "language": "kok",
        "desc": "Who is eligible for internship scheme?"
    },
]

print("=" * 65)
print("  Full Pipeline Test: Goan Konkani -> RAG -> Konkani Answer")
print("=" * 65)

# Check translate/status first
try:
    status = httpx.get(f"{BASE}/translate/status", timeout=5).json()
    print(f"  Translation backend: {status['backend']}")
    print(f"  Note: {status['note']}")
except Exception as e:
    print(f"  Could not get translate status: {e}")
print()

for i, q in enumerate(queries, 1):
    print(f"[{i}/{len(queries)}] {q['desc']}")
    print(f"  Konkani : {q['text']}")
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{BASE}/query",
            json={"text": q["text"], "language": q["language"]},
            timeout=300.0,
        )
        r = resp.json()
        elapsed = time.time() - t0
        print(f"  Answer  : {r['answer'][:300]}")
        print(f"  Confidence: {r['confidence']}  Route: {r['route']}")
        print(f"  Latency : {elapsed:.1f}s")
        print(f"  Sources :")
        for s in r.get("sources", [])[:3]:
            print(f"    - {s['title'][:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

print("=" * 65)

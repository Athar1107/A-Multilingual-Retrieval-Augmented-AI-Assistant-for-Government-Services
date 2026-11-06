"""Live API test — runs against the server on http://127.0.0.1:8000.
Tests English and Konkani queries end-to-end.
"""
import sys
import time
import httpx

BASE = "http://127.0.0.1:8000"

def check(label, url, method="GET", body=None, timeout=300):
    try:
        if method == "GET":
            r = httpx.get(url, timeout=timeout)
        else:
            r = httpx.post(url, json=body, timeout=timeout)
        return r.status_code, r.json()
    except Exception as e:
        return None, str(e)

print("=" * 65)
print("  Live API Test — Government AI Assistant")
print("=" * 65)

# 1. Health
code, data = check("Health", f"{BASE}/health")
print(f"\n[1] GET /health")
print(f"    Status : {code}")
print(f"    Body   : {data}")

# 2. Translate status
code, data = check("Translate", f"{BASE}/translate/status")
print(f"\n[2] GET /translate/status")
print(f"    Status  : {code}")
print(f"    Backend : {data.get('backend')}")
print(f"    Note    : {data.get('note')}")

# 3. English query
print(f"\n[3] POST /query (English)")
t0 = time.time()
code, data = check(
    "EN query", f"{BASE}/query", "POST",
    {"text": "What is the benefit amount of PM scholarship?", "language": "en"}
)
elapsed = time.time() - t0
if code == 200:
    print(f"    Status     : {code} OK  ({elapsed:.1f}s)")
    print(f"    Answer     : {data['answer'][:200]}")
    print(f"    Confidence : {data['confidence']}")
    print(f"    Route      : {data['route']}")
    print(f"    Sources    : {len(data['sources'])}")
    for s in data['sources'][:3]:
        print(f"      - {s['title'][:60]}")
else:
    print(f"    FAILED: {code} — {data}")

# 4. Konkani query
print(f"\n[4] POST /query (Goan Konkani)")
t0 = time.time()
code, data = check(
    "KOK query", f"{BASE}/query", "POST",
    {"text": "इंटर्नशिप योजनेसाठी कोण पात्र आहे?", "language": "kok"}
)
elapsed = time.time() - t0
if code == 200:
    print(f"    Status     : {code} OK  ({elapsed:.1f}s)")
    print(f"    Answer     : {data['answer'][:300]}")
    print(f"    Confidence : {data['confidence']}")
    print(f"    Route      : {data['route']}")
    print(f"    Sources    : {len(data['sources'])}")
    for s in data['sources'][:3]:
        print(f"      - {s['title'][:60]}")
else:
    print(f"    FAILED: {code} — {data}")

print(f"\n{'=' * 65}")
print("  All tests complete.")
print(f"  Open http://127.0.0.1:8000/docs in browser for Swagger UI")
print(f"{'=' * 65}")

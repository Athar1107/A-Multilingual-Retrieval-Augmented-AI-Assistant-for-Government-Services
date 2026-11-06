"""Comprehensive live API test — 8 queries across all scheme types."""
import sys
import time
import httpx

BASE = "http://127.0.0.1:8000"

QUERIES = [
    # English queries
    {
        "lang": "en",
        "text": "What is the benefit amount of PM scholarship scheme?",
        "label": "PM Scholarship benefit"
    },
    {
        "lang": "en",
        "text": "Who is eligible for Ayushman Bharat scheme?",
        "label": "Ayushman Bharat eligibility"
    },
    {
        "lang": "en",
        "text": "What scholarships are available for girl students?",
        "label": "Girl student scholarships"
    },
    {
        "lang": "en",
        "text": "Which internship schemes are available for engineering students?",
        "label": "Engineering internships"
    },
    {
        "lang": "en",
        "text": "What is the National Overseas Scholarship for SC students?",
        "label": "Overseas scholarship SC"
    },
    # Konkani queries
    {
        "lang": "kok",
        "text": "पीएम किसान योजनेचा वार्षिक लाभ किती आहे?",
        "label": "PM Kisan benefit (Konkani)"
    },
    {
        "lang": "kok",
        "text": "सरकारी शिष्यवृत्तीसाठी कोणती कागदपत्रे लागतात?",
        "label": "Scholarship documents (Konkani)"
    },
    {
        "lang": "kok",
        "text": "मुलींसाठी कोणत्या शिष्यवृत्ती योजना उपलब्ध आहेत?",
        "label": "Girl scholarships (Konkani)"
    },
]


def separator(title=""):
    line = "─" * 63
    if title:
        print(f"\n  {title}")
        print(f"  {line}")
    else:
        print(f"  {line}")


print()
print("=" * 65)
print("  Government AI Assistant — Comprehensive Backend Test")
print("=" * 65)

# Health check
try:
    h = httpx.get(f"{BASE}/health", timeout=5).json()
    ts = httpx.get(f"{BASE}/translate/status", timeout=5).json()
    print(f"\n  Server    : UP")
    print(f"  Health    : {h['status']}")
    print(f"  Translate : {ts['backend']} — {ts['note'][:50]}")
except Exception as e:
    print(f"\n  SERVER DOWN: {e}")
    sys.exit(1)

print()
ok = 0
fail = 0

for i, q in enumerate(QUERIES, 1):
    lang_label = "English" if q["lang"] == "en" else "Konkani"
    separator(f"[{i}/{len(QUERIES)}] {q['label']} ({lang_label})")
    print(f"  Q: {q['text']}")

    t0 = time.time()
    try:
        r = httpx.post(
            f"{BASE}/query",
            json={"text": q["text"], "language": q["lang"]},
            timeout=300.0,
        ).json()
        elapsed = time.time() - t0

        print(f"  A: {r['answer'][:280]}")
        print(f"  Confidence : {r['confidence']}   Route : {r['route']}   Time : {elapsed:.1f}s")
        print(f"  Sources    :", end="")
        for s in r["sources"][:3]:
            print(f"\n    • {s['title'][:58]}")
        ok += 1
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FAILED ({elapsed:.1f}s): {e}")
        fail += 1

print()
print("=" * 65)
print(f"  Results : {ok} passed  |  {fail} failed  |  {len(QUERIES)} total")
print(f"  Swagger : http://127.0.0.1:8000/docs")
print("=" * 65)

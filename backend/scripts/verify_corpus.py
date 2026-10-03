"""Quick sanity-check of the ingested corpus."""
import json
from pathlib import Path

CORPUS = Path("data/processed/active_english.json")
data   = json.loads(CORPUS.read_text(encoding="utf-8"))
size   = CORPUS.stat().st_size

print(f"Total documents : {len(data)}")
print(f"File size       : {size / 1024:.1f} KB")
print()

# Schema check
required = {"doc_id", "title", "url", "source_url", "content", "metadata"}
bad = [d["doc_id"] for d in data if not required.issubset(d)]
print(f"Schema OK       : {not bad}  (bad={bad})")

# Content stats
chars = [len(d["content"]) for d in data]
print(f"Content chars   : min={min(chars)}  avg={sum(chars)//len(chars)}  max={max(chars)}")

# Metadata completeness
no_issuer = [d["doc_id"] for d in data if not d["metadata"].get("issuing_body")]
no_tags   = [d["doc_id"] for d in data if not d["metadata"].get("tags")]
print(f"Missing issuer  : {len(no_issuer)}  {no_issuer[:4]}")
print(f"Missing tags    : {len(no_tags)}  {no_tags[:4]}")

# Duplicate doc_id check
ids = [d["doc_id"] for d in data]
dupes = [x for x in ids if ids.count(x) > 1]
print(f"Duplicate IDs   : {len(set(dupes))}  {list(set(dupes))[:4]}")

# Sample records
print()
for idx in [0, 6, 44]:
    s = data[idx]
    print(f"--- [{idx}] {s['doc_id']} ---")
    print(f"  title   : {s['title']}")
    print(f"  issuer  : {s['metadata']['issuing_body']}")
    print(f"  dept    : {s['metadata']['department']}")
    print(f"  tags    : {s['metadata']['tags']}")
    print(f"  chars   : {len(s['content'])}")
    print(f"  preview : {s['content'][:180]}")
    print()

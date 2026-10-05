"""Print a full summary of everything currently indexed."""
import json, sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
import chromadb
from app.config import CHROMA_INDEX_PATH, CHROMA_COLLECTION_NAME, PROCESSED_CORPUS_PATH

# myScheme JSON corpus
myscheme = json.loads(Path(PROCESSED_CORPUS_PATH).read_text(encoding="utf-8"))

# ChromaDB
client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
col    = client.get_collection(CHROMA_COLLECTION_NAME)
all_meta = col.get(include=["metadatas"])["metadatas"] or []

# Group chunks by source family
by_source: dict[str, list] = defaultdict(list)
seen_docs: dict[str, set]  = defaultdict(set)
for m in all_meta:
    fam = m.get("source_family", "myScheme")
    doc = m.get("scheme_id", m.get("title", "?"))
    by_source[fam].append(m)
    seen_docs[fam].add(doc)

print("=" * 60)
print("  Corpus Summary")
print("=" * 60)
print(f"\n  myScheme JSON documents : {len(myscheme)}")
print(f"  ChromaDB total chunks  : {col.count()}")
print()

print("  Breakdown by source:")
print(f"  {'Source':<30} {'Docs':>5} {'Chunks':>7}")
print("  " + "-" * 44)
for fam in sorted(by_source):
    docs   = len(seen_docs[fam])
    chunks = len(by_source[fam])
    print(f"  {fam:<30} {docs:>5} {chunks:>7}")

print()
print("  myScheme documents:")
for d in myscheme:
    print(f"    [{d['doc_id']:<42}] {d['title'][:50]}")

print()
print("  Goa PDF documents:")
goa_docs = {m.get("scheme_id"): m.get("title") for m in all_meta
            if m.get("source_family") in ("SCERT_Goa","DOL_Goa","Goa_Gov")}
for slug, title in sorted(goa_docs.items()):
    print(f"    [{slug:<42}] {(title or '')[:50]}")

print()
print("=" * 60)
print(f"  TOTAL UNIQUE DOCUMENTS : {len(myscheme) + len(goa_docs)}")
print(f"  TOTAL CHUNKS INDEXED   : {col.count()}")
print("=" * 60)

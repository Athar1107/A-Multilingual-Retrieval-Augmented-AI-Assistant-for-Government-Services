"""Print the current corpus ingestion and index status."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from app.config import CHROMA_COLLECTION_NAME, CHROMA_INDEX_PATH, PROCESSED_CORPUS_PATH

corpus = json.loads(Path(PROCESSED_CORPUS_PATH).read_text(encoding="utf-8"))
client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
col    = client.get_collection(CHROMA_COLLECTION_NAME)

size_kb = Path(PROCESSED_CORPUS_PATH).stat().st_size // 1024
no_issuer = sum(1 for d in corpus if not d["metadata"].get("issuing_body"))
no_tags   = sum(1 for d in corpus if not d["metadata"].get("tags"))

print("=== Corpus Ingestion Status ===")
print(f"  Documents ingested  : {len(corpus)}")
print(f"  Corpus file         : {PROCESSED_CORPUS_PATH.name}  ({size_kb} KB)")
print(f"  ChromaDB chunks     : {col.count()}")
print(f"  Collection          : {CHROMA_COLLECTION_NAME}")
print(f"  Missing issuers     : {no_issuer}")
print(f"  Missing tags        : {no_tags}")
print()
print("Status: READY")

"""Smoke-test the hybrid retriever against the indexed corpus."""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.retriever import Retriever

retriever = Retriever()

queries = [
    "scholarship for girl students",
    "overseas scholarship scheduled tribe",
    "laptop scheme Goa education",
    "internship DRDO students",
    "eligibility for PM scholarship",
]

for query in queries:
    results = retriever.retrieve(query, top_k=3)
    print(f"Q: {query}")
    for i, res in enumerate(results, 1):
        rtype = res["type"]
        score = res["rrf_score"]
        title = res["title"][:65]
        print(f"  {i}. [{rtype:6}] rrf={score:.5f}  {title}")
    print()

print(f"Retriever OK — ChromaDB collection has {retriever.collection.count()} chunks")

"""Hybrid dense + BM25 retrieval with Reciprocal Rank Fusion."""

import json
import logging
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from app.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    PROCESSED_CORPUS_PATH,
)

logger = logging.getLogger(__name__)


def _reciprocal_rank_fusion(
    dense_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Fuse dense and BM25 ranked lists using RRF and deduplicate.

    RRF assigns score ``1 / (k + rank)`` to each result in each list,
    then sums across lists.  This avoids the need to normalize
    incompatible score distributions.
    """
    scores: dict[str, dict] = {}

    for rank, result in enumerate(dense_results):
        # Use the first 300 chars of content as a dedup key
        key = result["content"][:300]
        if key not in scores:
            scores[key] = {"result": result, "rrf_score": 0.0}
        scores[key]["rrf_score"] += 1.0 / (k + rank + 1)

    for rank, result in enumerate(bm25_results):
        key = result["content"][:300]
        if key not in scores:
            scores[key] = {"result": result, "rrf_score": 0.0}
        scores[key]["rrf_score"] += 1.0 / (k + rank + 1)

    fused = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    return [
        {**item["result"], "rrf_score": round(item["rrf_score"], 6)}
        for item in fused
    ]


class Retriever:
    """Hybrid retriever combining ChromaDB dense search with BM25 sparse search."""

    def __init__(
        self,
        index_path: str | Path = CHROMA_INDEX_PATH,
        corpus_path: str | Path = PROCESSED_CORPUS_PATH,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        corpus_path = Path(corpus_path)
        if not corpus_path.exists():
            raise FileNotFoundError(
                f"Corpus not found at {corpus_path}. "
                "Run the ingestion service first: python -m app.services.ingestion"
            )

        # ChromaDB dense retrieval
        self.client = chromadb.PersistentClient(path=str(index_path))
        try:
            self.collection = self.client.get_collection(name=CHROMA_COLLECTION_NAME)
        except Exception as exc:
            raise RuntimeError(
                f"ChromaDB collection '{CHROMA_COLLECTION_NAME}' not found at "
                f"{index_path}. Run indexing first: python -m app.rag.indexing"
            ) from exc

        # Load corpus for BM25 sparse retrieval
        with open(corpus_path, "r", encoding="utf-8") as f:
            self.schemes = json.load(f)

        # Build BM25 index from full-document text
        corpus_texts = [f"{s['title']} {s['content']}" for s in self.schemes]
        tokenized_corpus = [doc.lower().split() for doc in corpus_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus_texts = corpus_texts

        # Embeddings model for query encoding (same model used during indexing)
        self.model = SentenceTransformer(model_name)
        logger.info(
            "Retriever ready: %d documents, ChromaDB collection '%s'",
            len(self.schemes),
            CHROMA_COLLECTION_NAME,
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Retrieve relevant passages using hybrid dense + BM25 with RRF fusion.

        Returns a deduplicated, fused list of results. Each result dict
        contains ``content``, ``title``, ``source_url``, ``type``, and
        ``rrf_score``.
        """
        # --- Dense search via ChromaDB ---
        query_embedding = self.model.encode(query).tolist()
        dense_raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        dense_results: list[dict] = []
        if dense_raw["documents"] and dense_raw["documents"][0]:
            for idx, doc in enumerate(dense_raw["documents"][0]):
                meta = (
                    dense_raw["metadatas"][0][idx]
                    if dense_raw.get("metadatas") and dense_raw["metadatas"][0]
                    else {}
                )
                dense_results.append({
                    "content": doc,
                    "title": meta.get("title", ""),
                    "source_url": meta.get("source_url", ""),
                    "type": "dense",
                })

        # --- BM25 sparse search ---
        bm25_scores = self.bm25.get_scores(query.lower().split())
        top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[:top_k]

        bm25_results: list[dict] = []
        for idx in top_indices:
            if bm25_scores[idx] > 0:
                scheme = self.schemes[idx]
                bm25_results.append({
                    "content": self.corpus_texts[idx],
                    "title": scheme.get("title", ""),
                    "source_url": scheme.get("source_url", scheme.get("url", "")),
                    "type": "bm25",
                    "bm25_score": round(float(bm25_scores[idx]), 4),
                })

        # --- Fuse and deduplicate ---
        fused = _reciprocal_rank_fusion(dense_results, bm25_results, k=60)
        return fused[:top_k]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    retriever = Retriever()
    test_query = "scholarship for students"
    results = retriever.retrieve(test_query, top_k=3)

    print(f"\nQuery: {test_query}\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['type']}] {r['title']}")
        print(f"   RRF score: {r['rrf_score']}")
        print(f"   {r['content'][:120]}...\n")

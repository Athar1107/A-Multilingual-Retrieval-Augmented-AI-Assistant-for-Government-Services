"""Build and persist a ChromaDB vector index from the processed English corpus."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer
import chromadb

from app.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_INDEX_PATH,
    CHROMA_MAX_BATCH_SIZE,
    CHUNK_SIZE_WORDS,
    EMBEDDING_MODEL_NAME,
    PROCESSED_CORPUS_PATH,
)

logger = logging.getLogger(__name__)


class CorpusIndexer:
    """Chunk, embed, and index the English retrieval corpus into ChromaDB."""

    def __init__(
        self,
        corpus_path: str | Path = PROCESSED_CORPUS_PATH,
        index_path: str | Path = CHROMA_INDEX_PATH,
        model_name: str = EMBEDDING_MODEL_NAME,
        chunk_size: int = CHUNK_SIZE_WORDS,
    ) -> None:
        self.corpus_path = Path(corpus_path)
        self.index_path = str(index_path)
        self.chunk_size = chunk_size
        self.model = SentenceTransformer(model_name)

        # Initialize ChromaDB
        os.makedirs(self.index_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.index_path)
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def load_corpus(self) -> list[dict[str, Any]]:
        """Load schemes from the processed JSON corpus.

        Raises ``FileNotFoundError`` when the corpus has not been generated
        yet.  Run ``python -m app.services.ingestion`` first.
        """
        if not self.corpus_path.exists():
            raise FileNotFoundError(
                f"Corpus not found at {self.corpus_path}. "
                "Run the ingestion service first: python -m app.services.ingestion"
            )
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def chunk_text(self, text: str) -> list[str]:
        """Split text into word-count-based chunks."""
        words = text.split()
        if not words:
            return [text[: self.chunk_size]]
        chunks: list[str] = []
        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i : i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks if chunks else [text[: self.chunk_size]]

    def index_corpus(self) -> int:
        """Index all schemes into ChromaDB in batches.

        Uses ``upsert`` so re-running is idempotent — updated documents
        replace their older chunks instead of duplicating them.
        """
        schemes = self.load_corpus()

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        logger.info("Indexing %d schemes...", len(schemes))

        for i, scheme in enumerate(schemes):
            # Create chunks from title + content
            text = f"{scheme['title']}. {scheme['content']}"
            chunks = self.chunk_text(text)

            for j, chunk in enumerate(chunks):
                doc_id = f"{scheme['doc_id']}_chunk_{j}"

                # Generate embedding
                embedding = self.model.encode(chunk).tolist()

                ids.append(doc_id)
                embeddings.append(embedding)
                documents.append(chunk)
                metadatas.append({
                    "scheme_id": scheme["doc_id"],
                    "title": scheme["title"],
                    "source_url": scheme.get("source_url", scheme.get("url", "")),
                    "chunk_index": j,
                })

            if (i + 1) % 10 == 0:
                logger.info("  Processed %d/%d schemes...", i + 1, len(schemes))

        # Add to ChromaDB in batches (ChromaDB has a per-call size limit)
        total = len(ids)
        for start in range(0, total, CHROMA_MAX_BATCH_SIZE):
            end = min(start + CHROMA_MAX_BATCH_SIZE, total)
            self.collection.upsert(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )
            logger.info("  Upserted batch %d–%d of %d chunks", start + 1, end, total)

        logger.info("✓ Indexing complete. Total chunks: %d", total)
        return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    indexer = CorpusIndexer()
    indexer.index_corpus()

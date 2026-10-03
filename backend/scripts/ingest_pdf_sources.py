"""Ingest SCERT Goa and DOL Goa PDF documents into the ChromaDB index.

Downloads PDFs, extracts text, chunks it, embeds with the same model
used for myScheme, and upserts into the existing 'education_schemes' collection.

Run from the backend/ directory:
    python scripts/ingest_pdf_sources.py

Or with HF_HUB_OFFLINE after first run:
    set HF_HUB_OFFLINE=1
    python scripts/ingest_pdf_sources.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_INDEX_PATH,
    CHROMA_MAX_BATCH_SIZE,
    CHUNK_SIZE_WORDS,
    EMBEDDING_MODEL_NAME,
)
from app.ingestion.pdf_loader import load_pdf_sources


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS) -> list[str]:
    """Split text into word-count-based chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i: i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks or [text[:500]]


def main() -> None:
    print("=" * 60)
    print("  PDF Ingestion — SCERT Goa + DOL Goa")
    print("=" * 60)

    # Load embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("Model loaded.")

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_INDEX_PATH))
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    before_count = collection.count()
    print(f"ChromaDB collection '{CHROMA_COLLECTION_NAME}': {before_count} chunks before ingestion\n")

    # Collect all chunks
    ids:        list[str]   = []
    embeddings: list[list[float]] = []
    documents:  list[str]   = []
    metadatas:  list[dict]  = []

    docs_processed = 0
    docs_skipped   = 0

    for doc in load_pdf_sources(delay_seconds=0.5):
        chunks = chunk_text(doc.content, CHUNK_SIZE_WORDS)
        print(f"  {doc.doc_id:<45} {len(doc.content):>7} chars → {len(chunks)} chunks")

        for j, chunk in enumerate(chunks):
            chunk_id = f"{doc.doc_id}_chunk_{j}"
            embedding = model.encode(chunk).tolist()

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)
            metadatas.append({
                "scheme_id":     doc.doc_id,
                "title":         doc.title,
                "source_url":    doc.source_url,
                "source_family": doc.source_family,
                "category":      doc.category,
                "language":      doc.metadata.get("language", "en"),
                "chunk_index":   j,
            })

        docs_processed += 1

    if not ids:
        print("\nNo documents were successfully downloaded. Check your internet connection.")
        sys.exit(1)

    # Upsert into ChromaDB in batches
    print(f"\nUpserting {len(ids)} chunks into ChromaDB ...")
    for start in range(0, len(ids), CHROMA_MAX_BATCH_SIZE):
        end = min(start + CHROMA_MAX_BATCH_SIZE, len(ids))
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    after_count = collection.count()

    print()
    print("=" * 60)
    print(f"  Documents processed : {docs_processed}")
    print(f"  Chunks added        : {len(ids)}")
    print(f"  ChromaDB before     : {before_count}")
    print(f"  ChromaDB after      : {after_count}")
    print(f"  Net new chunks      : {after_count - before_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()

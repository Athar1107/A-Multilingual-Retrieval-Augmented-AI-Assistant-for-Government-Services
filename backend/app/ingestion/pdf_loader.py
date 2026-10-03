"""PDF document loader for SCERT Goa and DOL Goa sources.

Downloads PDFs from official Goa government portals, extracts clean text
using PyMuPDF, and returns structured documents ready for indexing.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "KonkaniPublicServiceRAG/0.1 (research; goa-govt-pdf-ingestion)"

# ── Cleaning helpers ─────────────────────────────────────────────────────────

_WHITESPACE  = re.compile(r"[ \t]+")
_NEWLINES    = re.compile(r"\n{3,}")
_PAGE_NUM    = re.compile(r"^\s*(?:Page\s*)?\d+\s*(?:of\s*\d+)?\s*$", re.I | re.M)
_HEADER_FOOT = re.compile(
    r"(?:Government of Goa|Directorate of Official Language|SCERT,?\s*Goa"
    r"|www\.\S+|©\s*\d{4})",
    re.I,
)


def clean_pdf_text(raw: str) -> str:
    """Normalize extracted PDF text for embedding."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = _PAGE_NUM.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = _NEWLINES.sub("\n\n", text)
    return text.strip()


# ── Document dataclass ────────────────────────────────────────────────────────

@dataclass
class PdfDocument:
    doc_id:       str
    title:        str
    source_url:   str
    content:      str
    source_family: str          # "SCERT_Goa" | "DOL_Goa"
    category:     str           # e.g. "scholarship", "language_scheme"
    date:         str | None = None
    metadata:     dict    = field(default_factory=dict)


# ── Downloader ────────────────────────────────────────────────────────────────

def download_pdf_text(url: str, *, timeout: float = 30.0) -> tuple[str, dict]:
    """Download a PDF and return (extracted_text, pdf_metadata)."""
    with httpx.Client(timeout=timeout, follow_redirects=True,
                      headers={"User-Agent": USER_AGENT}) as client:
        resp = client.get(url)
        resp.raise_for_status()

    pdf_bytes = resp.content
    checksum = hashlib.sha256(pdf_bytes).hexdigest()[:12]

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    raw = "\n\n".join(pages)
    text = clean_pdf_text(raw)
    meta = {"checksum": checksum, "page_count": len(pages), "byte_size": len(pdf_bytes)}
    return text, meta


# ── Source catalogue ──────────────────────────────────────────────────────────

# Each entry: (doc_id, title, url, source_family, category)
PDF_SOURCES: list[tuple[str, str, str, str, str]] = [

    # ── SCERT Goa ─────────────────────────────────────────────────────────────
    (
        "scert-goa-schemes-overview",
        "SCERT Goa — Scholarship Schemes Overview",
        "https://education.goa.gov.in/wp-content/uploads/2024/11/schemes-scert.pdf",
        "SCERT_Goa",
        "scholarship",
    ),
    (
        "scert-goa-science-talent-search-2026",
        "State Science Talent Search Examination (STSE) Goa 2025-26",
        "https://www.goa.gov.in/wp-content/uploads/2026/01/SCIENCE-TALENT-SEARCH.pdf",
        "SCERT_Goa",
        "scholarship",
    ),
    (
        "scert-goa-nmmss-2024-25",
        "National Means-cum-Merit Scholarship Scheme (NMMSS) Goa 2024-25",
        "https://scert.goa.gov.in/wp-content/uploads/2024/10/NMMSS-Application-Form-24-25.pdf",
        "SCERT_Goa",
        "scholarship",
    ),
    (
        "scert-goa-higher-education-scholarship",
        "Higher Education Scholarship Scheme — Goa",
        "https://www.goa.gov.in/wp-content/uploads/2021/12/higher-education-scholarship.pdf",
        "SCERT_Goa",
        "scholarship",
    ),
    (
        "scert-goa-conducted-schemes",
        "SCERT Goa — Conducted Scholarship Schemes Details",
        "https://www.goa.gov.in/wp-content/uploads/2024/08/SCERT-CONDUCTED.pdf",
        "SCERT_Goa",
        "scholarship",
    ),

    # ── DOL Goa ───────────────────────────────────────────────────────────────
    (
        "dol-goa-citizen-charter-2025",
        "Directorate of Official Language Goa — Citizen Charter 2025",
        "https://dol.goa.gov.in/wp-content/uploads/2025/03/Citizen-Charter-2025-English.pdf",
        "DOL_Goa",
        "citizen_charter",
    ),
    (
        "dol-goa-bhasha-puraskar-yojana",
        "Bhasha Puraskar Yojana — Language Award Scheme (Konkani/Marathi/Sanskrit)",
        "https://dol.goa.gov.in/wp-content/uploads/2026/08/BPY-ENGLISH.pdf",
        "DOL_Goa",
        "language_scheme",
    ),
    (
        "dol-goa-lokbhasha-sangrah-yojana",
        "Lokbhasha Sangrah Yojana — Folk Language Collection Scheme",
        "https://dol.goa.gov.in/wp-content/uploads/2025/09/Lokbhasha-Sangrah-Yojana-1.pdf",
        "DOL_Goa",
        "language_scheme",
    ),

    # ── Goa Government General ─────────────────────────────────────────────────
    (
        "goa-tribal-welfare-citizen-charter",
        "Tribal Welfare Department Goa — Citizen Charter (Scholarships)",
        "https://www.goa.gov.in/wp-content/uploads/2021/12/CC-TribalWelfare.pdf",
        "Goa_Gov",
        "scholarship",
    ),
    (
        "goa-south-collectorate-charter-2026",
        "South Goa Collectorate — Citizen Charter 2026 (Certificates & Services)",
        "https://www.goa.gov.in/wp-content/uploads/2026/05/Citizen-Charter-SGD.pdf",
        "Goa_Gov",
        "citizen_charter",
    ),
]


# ── Main loader function ──────────────────────────────────────────────────────

def load_pdf_sources(
    *,
    delay_seconds: float = 0.5,
    min_content_chars: int = 200,
) -> Iterator[PdfDocument]:
    """Download and parse all PDF sources, yielding PdfDocument objects.

    Yields documents one by one so the caller can index incrementally.
    Skips sources that fail to download or produce insufficient text.
    """
    collected_at = datetime.now(timezone.utc).isoformat()
    total = len(PDF_SOURCES)

    for i, (doc_id, title, url, source_family, category) in enumerate(PDF_SOURCES, 1):
        logger.info("[%d/%d] Downloading %s ...", i, total, doc_id)
        try:
            text, pdf_meta = download_pdf_text(url)
            if len(text) < min_content_chars:
                logger.warning("Skipping %s — insufficient content (%d chars)", doc_id, len(text))
                continue

            yield PdfDocument(
                doc_id=doc_id,
                title=title,
                source_url=url,
                content=text,
                source_family=source_family,
                category=category,
                metadata={
                    **pdf_meta,
                    "collected_at": collected_at,
                    "language": "en",
                    "corpus_role": "active_retrieval",
                },
            )
            logger.info("  OK — %d chars, %d pages", len(text), pdf_meta["page_count"])

        except Exception as exc:
            logger.warning("FAILED %s: %s", url, exc)

        if delay_seconds and i < total:
            time.sleep(delay_seconds)

"""Build the English active corpus from the maintained scheme register.

myScheme pages are client-rendered, so ingestion fetches each official page URL
and the public scheme record that page displays, then writes cleaned English
documents to ``data/processed/active_english.json``.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from app.config import PROCESSED_CORPUS_PATH, SCHEME_REGISTER_PATH

MYSCHEME_PUBLIC_SCHEME_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes"
# Public frontend key served by myscheme.gov.in; override with MYSCHEME_API_KEY.
DEFAULT_MYSCHEME_API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
USER_AGENT = "KonkaniPublicServiceRAG/0.1 (research corpus ingestion)"
MIN_CONTENT_CHARS = 80
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MARKDOWN_EMPHASIS = re.compile(r"[*_`#]+")
WHITESPACE = re.compile(r"[ \t]+")
NEWLINE_RUNS = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class SchemeSeed:
    """One source candidate from ``schemes_list.txt``."""

    title: str
    source_url: str


@dataclass(frozen=True)
class FetchedResource:
    """HTTP response for a page or public scheme record."""

    url: str
    status_code: int
    headers: dict[str, str]
    text: str


HttpGet = Callable[[str, dict[str, str] | None], FetchedResource]


class _HTMLTextExtractor(HTMLParser):
    """Collect visible text and skip script/style/navigation chrome."""

    _skip_tags = frozenset({"script", "style", "noscript", "svg", "header", "footer", "nav"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._skip_tags:
            self._skip_depth += 1
            return
        if tag in {"p", "div", "li", "br", "h1", "h2", "h3", "tr"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        return " ".join(self._chunks)


def load_scheme_register(path: Path) -> list[SchemeSeed]:
    """Load valid ``title: https://...`` lines from a scheme register."""
    seeds: list[SchemeSeed] = []
    seen_urls: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        title, separator, source_url = line.rpartition("https://")
        title = title.rstrip(": ").strip()
        if not separator or not title:
            raise ValueError(f"Invalid scheme register entry on line {line_number}")
        url = f"https://{source_url.strip()}"
        if url in seen_urls:
            continue
        seen_urls.add(url)
        seeds.append(SchemeSeed(title=title, source_url=url))
    return seeds


def slug_from_url(source_url: str) -> str:
    """Return the last path segment of a scheme page URL."""
    path = urlparse(source_url).path.rstrip("/")
    slug = path.rsplit("/", 1)[-1].strip()
    if not slug:
        raise ValueError(f"Cannot derive scheme slug from {source_url}")
    return slug


def clean_text(raw: str) -> str:
    """Normalize HTML, markdown, and whitespace into retrieval-ready text."""
    text = html.unescape(raw or "")
    text = text.replace("\r\n", "\n").replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = MARKDOWN_LINK.sub(r"\1 (\2)", text)
    text = MARKDOWN_EMPHASIS.sub("", text)
    text = WHITESPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = NEWLINE_RUNS.sub("\n\n", text)
    return text.strip()


def html_to_text(raw_html: str) -> str:
    """Extract visible text from an official scheme page."""
    extractor = _HTMLTextExtractor()
    extractor.feed(raw_html)
    extractor.close()
    return clean_text(extractor.text())


def _label(value: Any) -> str | None:
    if isinstance(value, dict):
        label = value.get("label") or value.get("value")
        return str(label) if label else None
    if value is None or value == "":
        return None
    return str(value)


def _labels(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_label(entry) for entry in value) if item]
    label = _label(value)
    return [label] if label else []


def _markdown_fields(block: Any, *keys: str) -> list[str]:
    if not isinstance(block, dict):
        return []
    parts: list[str] = []
    for key in keys:
        value = block.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(clean_text(value))
    return parts


def _content_from_english_payload(english: dict[str, Any]) -> str:
    basic = english.get("basicDetails") or {}
    content = english.get("schemeContent") or {}
    eligibility = english.get("eligibilityCriteria") or {}
    sections: list[str] = []

    title = _label(basic.get("schemeName"))
    if title:
        sections.append(title)
    brief = content.get("briefDescription")
    if isinstance(brief, str) and brief.strip():
        sections.append(clean_text(brief))

    named_sections = [
        ("Details", _markdown_fields(content, "detailedDescription_md")),
        ("Benefits", _markdown_fields(content, "benefits_md")),
        ("Eligibility", _markdown_fields(eligibility, "eligibilityDescription_md")),
        ("Exclusions", _markdown_fields(content, "exclusions_md")),
    ]
    for heading, parts in named_sections:
        if parts:
            sections.append(f"{heading}\n" + "\n\n".join(parts))

    process_parts: list[str] = []
    for item in english.get("applicationProcess") or []:
        process_parts.extend(_markdown_fields(item, "process_md"))
    if process_parts:
        sections.append("Application process\n" + "\n\n".join(process_parts))

    definition_parts: list[str] = []
    for item in english.get("schemeDefinitions") or []:
        definition_parts.extend(_markdown_fields(item, "definitions_md"))
    if definition_parts:
        sections.append("Definitions\n" + "\n\n".join(definition_parts))

    references = content.get("references") or []
    reference_lines: list[str] = []
    for reference in references:
        if not isinstance(reference, dict):
            continue
        ref_title = str(reference.get("title") or "Reference").strip()
        ref_url = str(reference.get("url") or "").strip()
        if ref_url:
            reference_lines.append(f"{ref_title}: {ref_url}")
        elif ref_title:
            reference_lines.append(ref_title)
    if reference_lines:
        sections.append("References\n" + "\n".join(reference_lines))

    return clean_text("\n\n".join(section for section in sections if section))


def _choose_date(basic: dict[str, Any], page: FetchedResource | None) -> tuple[str | None, str]:
    open_date = basic.get("schemeOpenDate")
    if isinstance(open_date, str) and open_date.strip():
        return open_date.strip(), "scheme_open_date"
    if page:
        last_modified = page.headers.get("last-modified") or page.headers.get("Last-Modified")
        if last_modified:
            return last_modified, "http_last_modified"
    return None, "unknown"


def document_from_payload(
    seed: SchemeSeed,
    payload: dict[str, Any],
    *,
    collected_at: str,
    page: FetchedResource | None = None,
) -> dict[str, Any]:
    """Convert an official myScheme record into a retrieval document."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected scheme payload for {seed.source_url}")
    english = data.get("en")
    if not isinstance(english, dict):
        raise ValueError(f"Missing English scheme body for {seed.source_url}")

    basic = english.get("basicDetails") or {}
    content_block = english.get("schemeContent") or {}
    title = _label(basic.get("schemeName")) or seed.title
    content = _content_from_english_payload(english)
    if page and len(content) < MIN_CONTENT_CHARS:
        html_content = html_to_text(page.text)
        if len(html_content) > len(content):
            content = html_content
    if len(content) < MIN_CONTENT_CHARS:
        raise ValueError(f"Insufficient English content for {seed.source_url}")

    date_value, date_source = _choose_date(basic if isinstance(basic, dict) else {}, page)
    slug = str(data.get("slug") or slug_from_url(seed.source_url))
    references = []
    if isinstance(content_block, dict):
        for reference in content_block.get("references") or []:
            if isinstance(reference, dict) and reference.get("url"):
                references.append(
                    {
                        "title": str(reference.get("title") or "").strip(),
                        "url": str(reference.get("url")).strip(),
                    }
                )

    metadata = {
        "slug": slug,
        "scheme_id": data.get("_id"),
        "register_title": seed.title,
        "language": "en",
        "corpus_role": "active_retrieval",
        "source_family": "myScheme",
        "issuing_body": (
            _label((basic or {}).get("nodalMinistryName"))
            or _label((basic or {}).get("implementingAgency"))
            or _label((basic or {}).get("nodalDepartmentName"))
        ),
        "department": _label((basic or {}).get("nodalDepartmentName")),
        "implementing_agency": _label((basic or {}).get("implementingAgency")),
        "scheme_short_title": _label((basic or {}).get("schemeShortTitle")),
        "scheme_level": _label((basic or {}).get("level")),
        "scheme_type": _label((basic or {}).get("schemeType")),
        "categories": _labels((basic or {}).get("schemeCategory")),
        "subcategories": _labels((basic or {}).get("schemeSubCategory")),
        "tags": _labels((basic or {}).get("tags")),
        "target_beneficiaries": _labels((basic or {}).get("targetBeneficiaries")),
        "references": references,
        "date_source": date_source,
        "collected_at": collected_at,
        "page_http_status": page.status_code if page else None,
    }
    return {
        "doc_id": slug,
        "title": title,
        "url": seed.source_url,
        "source_url": seed.source_url,
        "date": date_value,
        "content": content,
        "metadata": metadata,
    }


def _request_headers(headers: dict[str, str] | None) -> dict[str, str]:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        request_headers.update(headers)
    return request_headers


def _response_to_resource(response: httpx.Response) -> FetchedResource:
    return FetchedResource(
        url=str(response.url),
        status_code=response.status_code,
        headers={key.lower(): value for key, value in response.headers.items()},
        text=response.text,
    )


def httpx_get(url: str, headers: dict[str, str] | None = None) -> FetchedResource:
    """Fetch a URL with a short retry loop."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=_request_headers(headers))
            return _response_to_resource(response)
        except httpx.HTTPError as exc:
            last_error = exc
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _client_get(client: httpx.Client) -> HttpGet:
    def _get(url: str, headers: dict[str, str] | None = None) -> FetchedResource:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.get(url, headers=_request_headers(headers))
                return _response_to_resource(response)
            except httpx.HTTPError as exc:
                last_error = exc
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Failed to fetch {url}: {last_error}")

    return _get


def fetch_scheme_payload(
    seed: SchemeSeed,
    *,
    http_get: HttpGet,
    api_key: str | None = None,
) -> dict[str, Any]:
    key = api_key or os.environ.get("MYSCHEME_API_KEY", DEFAULT_MYSCHEME_API_KEY)
    slug = slug_from_url(seed.source_url)
    resource = http_get(
        f"{MYSCHEME_PUBLIC_SCHEME_URL}?slug={slug}",
        {
            "Accept": "application/json",
            "Origin": "https://www.myscheme.gov.in",
            "Referer": seed.source_url,
            "x-api-key": key,
        },
    )
    if resource.status_code != 200:
        raise ValueError(f"Scheme record HTTP {resource.status_code} for {seed.source_url}")
    payload = json.loads(resource.text)
    if payload.get("statusCode") not in (None, 200) and payload.get("status") not in (None, "Success"):
        raise ValueError(f"Scheme record error for {seed.source_url}: {payload.get('errorDescription')}")
    return payload


def ingest_schemes(
    register_path: Path,
    output_path: Path,
    *,
    http_get: HttpGet | None = None,
    api_key: str | None = None,
    delay_seconds: float = 0.25,
) -> list[dict[str, Any]]:
    """Fetch, clean, and write English retrieval documents for every register URL."""
    seeds = load_scheme_register(register_path)
    collected_at = datetime.now(timezone.utc).isoformat()
    key = api_key or os.environ.get("MYSCHEME_API_KEY", DEFAULT_MYSCHEME_API_KEY)
    documents: list[dict[str, Any]] = []
    errors: list[str] = []
    client: httpx.Client | None = None
    getter = http_get
    if getter is None:
        client = httpx.Client(timeout=30.0, follow_redirects=True)
        getter = _client_get(client)

    try:
        for index, seed in enumerate(seeds, 1):
            try:
                page = getter(seed.source_url, {"Accept": "text/html"})
                if page.status_code >= 400:
                    raise ValueError(f"Official page HTTP {page.status_code}")
                payload = fetch_scheme_payload(seed, http_get=getter, api_key=key)
                documents.append(
                    document_from_payload(seed, payload, collected_at=collected_at, page=page)
                )
            except (ValueError, json.JSONDecodeError, RuntimeError, httpx.HTTPError) as exc:
                errors.append(f"{seed.source_url}: {exc}")
            if delay_seconds and index < len(seeds):
                time.sleep(delay_seconds)
    finally:
        if client is not None:
            client.close()

    if not documents:
        raise RuntimeError("Ingestion produced no documents. Failures:\n" + "\n".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print(f"Wrote {len(documents)} documents with {len(errors)} failures:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
    return documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest myScheme pages into the English active corpus.")
    parser.add_argument("--register", type=Path, default=SCHEME_REGISTER_PATH)
    parser.add_argument("--output", type=Path, default=PROCESSED_CORPUS_PATH)
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args(argv)
    documents = ingest_schemes(args.register, args.output, delay_seconds=args.delay)
    print(f"Wrote {len(documents)} documents to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

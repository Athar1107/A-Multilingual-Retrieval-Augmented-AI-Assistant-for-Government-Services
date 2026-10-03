"""One-shot ingestion runner — run from the project root."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Run from repo root so 'backend' is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ingestion import (
    _client_get,
    document_from_payload,
    fetch_scheme_payload,
    load_scheme_register,
)

REGISTER = Path("schemes_list.txt")
OUTPUT   = Path("data/processed/active_english.json")
DELAY    = 0.3   # seconds between requests — be polite to the API


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    seeds = load_scheme_register(REGISTER)
    collected_at = datetime.now(timezone.utc).isoformat()
    documents: list[dict] = []
    errors:    list[str]  = []

    print(f"Ingesting {len(seeds)} schemes ...\n")

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        getter = _client_get(client)
        for i, seed in enumerate(seeds, 1):
            label = f"[{i:02d}/{len(seeds)}]"
            try:
                page = getter(seed.source_url, {"Accept": "text/html"})
                if page.status_code >= 400:
                    raise ValueError(f"Page HTTP {page.status_code}")
                payload = fetch_scheme_payload(seed, http_get=getter)
                doc     = document_from_payload(
                    seed, payload, collected_at=collected_at, page=page
                )
                documents.append(doc)
                slug  = doc["doc_id"]
                chars = len(doc["content"])
                print(f"  {label} OK   {slug:<42} {chars:>6} chars")
            except Exception as exc:
                errors.append(f"{seed.source_url}: {exc}")
                print(f"  {label} ERR  {str(exc)[:90]}")
            if i < len(seeds):
                time.sleep(DELAY)

    OUTPUT.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n{'='*60}")
    print(f"  Documents written : {len(documents)}")
    print(f"  Errors            : {len(errors)}")
    print(f"  Output path       : {OUTPUT.resolve()}")
    if errors:
        print("\nFailed URLs:")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()

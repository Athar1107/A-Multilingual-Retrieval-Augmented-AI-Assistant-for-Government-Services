import json
from pathlib import Path

from app.services.ingestion import (
    FetchedResource,
    SchemeSeed,
    clean_text,
    document_from_payload,
    ingest_schemes,
    load_scheme_register,
    slug_from_url,
)


SAMPLE_PAYLOAD = {
    "status": "Success",
    "statusCode": 200,
    "data": {
        "_id": "scheme-1",
        "slug": "pg-igssgc",
        "en": {
            "basicDetails": {
                "schemeName": "Post Graduate Indira Gandhi Scholarship For Single Girl Child",
                "schemeShortTitle": "PG-IGSSGC",
                "schemeOpenDate": "2018-01-01",
                "implementingAgency": "UGC",
                "nodalMinistryName": {"label": "Ministry of Education"},
                "nodalDepartmentName": {"label": "Department Of Higher Education"},
                "level": {"label": "Central"},
                "schemeType": {"label": "Central Sector Scheme"},
                "schemeCategory": [{"label": "Education & Learning"}],
                "schemeSubCategory": [{"label": "Scholarships and student finance"}],
                "tags": ["Scholarship", "Girl Child"],
                "targetBeneficiaries": [{"label": "Individual"}],
            },
            "schemeContent": {
                "briefDescription": "A scholarship for the only girl child in a family.",
                "detailedDescription_md": "Supports <br> postgraduate **education**.",
                "benefits_md": "Amount: ₹36,200 per annum.",
                "exclusions_md": "Distance education is not covered.",
                "references": [{"title": "Guidelines", "url": "https://example.gov/guidelines.pdf"}],
            },
            "eligibilityCriteria": {
                "eligibilityDescription_md": "The applicant must be a citizen of India."
            },
            "applicationProcess": [{"process_md": "Apply on the [National Scholarship Portal](https://scholarships.gov.in)."}],
            "schemeDefinitions": [{"definitions_md": "Institutes of National Importance."}],
        },
    },
}


def test_load_scheme_register() -> None:
    register = Path(__file__).resolve().parents[2] / "schemes_list.txt"

    seeds = load_scheme_register(register)

    assert seeds
    assert all(seed.title for seed in seeds)
    assert all(seed.source_url.startswith("https://") for seed in seeds)


def test_slug_from_url() -> None:
    assert slug_from_url("https://www.myscheme.gov.in/schemes/pg-igssgc") == "pg-igssgc"


def test_clean_text_strips_markup() -> None:
    raw = "Hello&nbsp;<br>**world** [NSP](https://scholarships.gov.in)"

    assert clean_text(raw) == "Hello\nworld NSP (https://scholarships.gov.in)"


def test_document_from_payload_has_required_fields() -> None:
    seed = SchemeSeed(
        title="Register title",
        source_url="https://www.myscheme.gov.in/schemes/pg-igssgc",
    )
    page = FetchedResource(
        url=seed.source_url,
        status_code=200,
        headers={"last-modified": "Mon, 01 Jan 2024 00:00:00 GMT"},
        text="<html><body>unused</body></html>",
    )

    document = document_from_payload(seed, SAMPLE_PAYLOAD, collected_at="2026-09-29T00:00:00+00:00", page=page)

    assert document["title"].startswith("Post Graduate Indira Gandhi")
    assert document["url"] == seed.source_url
    assert document["source_url"] == seed.source_url
    assert document["date"] == "2018-01-01"
    assert "citizen of India" in document["content"]
    assert "₹36,200" in document["content"]
    assert document["metadata"]["issuing_body"] == "Ministry of Education"
    assert document["metadata"]["date_source"] == "scheme_open_date"
    assert document["doc_id"] == "pg-igssgc"


def test_ingest_schemes_writes_active_english_json(tmp_path: Path) -> None:
    register = tmp_path / "schemes_list.txt"
    register.write_text(
        "Post Graduate Indira Gandhi Scholarship For Single Girl Child: "
        "https://www.myscheme.gov.in/schemes/pg-igssgc\n",
        encoding="utf-8",
    )
    output = tmp_path / "active_english.json"
    html_page = FetchedResource(
        url="https://www.myscheme.gov.in/schemes/pg-igssgc",
        status_code=200,
        headers={},
        text="<!DOCTYPE html><html><body></body></html>",
    )
    api_page = FetchedResource(
        url="https://api.myscheme.gov.in/schemes/v6/public/schemes?slug=pg-igssgc",
        status_code=200,
        headers={},
        text=json.dumps(SAMPLE_PAYLOAD),
    )

    def fake_get(url: str, headers: dict[str, str] | None = None) -> FetchedResource:
        if "api.myscheme.gov.in" in url:
            return api_page
        return html_page

    documents = ingest_schemes(register, output, http_get=fake_get, delay_seconds=0)

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert len(documents) == 1
    assert saved[0]["title"]
    assert saved[0]["url"].startswith("https://")
    assert saved[0]["content"]
    assert "metadata" in saved[0]

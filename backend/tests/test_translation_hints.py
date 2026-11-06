from app.rag.translation import devanagari_retrieval_hint


def test_devanagari_scholarship_question_gets_english_retrieval_hint() -> None:
    hint = devanagari_retrieval_hint(
        "मुलींसाठी कोणत्या शिष्यवृत्ती योजना उपलब्ध आहेत?"
    )

    assert hint is not None
    assert "girls" in hint
    assert "scholarship" in hint
    assert "scheme" in hint


def test_english_question_does_not_receive_a_devanagari_hint() -> None:
    assert devanagari_retrieval_hint("Which scholarships are available for girls?") is None


def test_translation_service_fails_loudly_when_indictrans2_load_fails(monkeypatch) -> None:
    import pytest
    from app.rag.translation import TranslationService

    monkeypatch.setenv("TRANSLATOR_REQUIRED", "indictrans2")
    monkeypatch.setattr(
        "app.rag.translation._IndicTrans2Backend",
        lambda: (_ for _ in ()).throw(RuntimeError("Gated repo access denied")),
    )

    svc = TranslationService()
    with pytest.raises(RuntimeError, match="IndicTrans2 failed to load"):
        svc._load()


def test_translation_service_fails_loudly_when_hf_token_set_and_load_fails(monkeypatch) -> None:
    import pytest
    from app.rag.translation import TranslationService

    monkeypatch.delenv("TRANSLATOR_REQUIRED", raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_dummy_token_test")
    monkeypatch.setenv("TRANSLATION_MODEL", "auto")
    monkeypatch.setattr(
        "app.rag.translation._IndicTrans2Backend",
        lambda: (_ for _ in ()).throw(RuntimeError("Download corrupted")),
    )

    svc = TranslationService()
    with pytest.raises(RuntimeError, match="IndicTrans2 failed to load"):
        svc._load()

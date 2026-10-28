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

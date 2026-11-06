from typing import Any
from app.rag.pipeline import RAGPipeline
from app.rag.fallback_routing import FallbackRouter


class StubRetriever:
    def __init__(self, semantic_score: float = 0.8) -> None:
        self.semantic_score = semantic_score

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        return [{
            "content": f"Evidence for {query}",
            "semantic_score": self.semantic_score,
            "rrf_score": 0.5,
            "title": "Test Scheme",
            "source_url": "https://example.gov/test",
            "scheme_id": "test-scheme-id",
        }]


class StubGenerator:
    def generate(self, query: str, context: str) -> str:
        return context

    def paraphrase_query(self, query: str) -> str:
        return f"paraphrased {query}"


class RecordingTranslator:
    def __init__(self) -> None:
        self.konkani_to_english_calls: list[str] = []
        self.english_to_konkani_calls: list[str] = []

    def konkani_to_english(self, text: str) -> str:
        self.konkani_to_english_calls.append(text)
        return "scholarship"

    def english_to_konkani(self, text: str) -> str:
        self.english_to_konkani_calls.append(text)
        return f"[KONKANI] {text}"

    def konkani_to_english_pivot(self, text: str) -> str:
        return "scholarship pivot"

    @property
    def backend_name(self) -> str:
        return "test_mock_backend"


def test_pipeline_passes_retrieved_context_to_generator() -> None:
    pipeline = RAGPipeline(
        retriever=StubRetriever(semantic_score=0.8),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=False,
    )

    result = pipeline.answer("scholarship")

    assert result["answer"] == "Evidence for scholarship"
    assert result["confidence"] == 0.8
    assert result["route"] == "direct"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Test Scheme"
    assert "test-scheme-id" in result["retrieved_doc_ids"]


def test_pipeline_direct_route_translates_back_to_konkani() -> None:
    translator = RecordingTranslator()
    pipeline = RAGPipeline(
        retriever=StubRetriever(semantic_score=0.85),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=translator,
    )

    result = pipeline.answer("शिष्यवृत्ती", language="kok")

    assert result["route"] == "direct"
    assert result["confidence"] == 0.85
    assert result["answer"].startswith("[KONKANI]")
    assert len(translator.english_to_konkani_calls) == 1


def test_pipeline_fallback_recovered_route_translates_back() -> None:
    class DynamicRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            # Initial low score, attempt 2 high score
            score = 0.85 if "pivot" in query or "paraphrased" in query else 0.30
            return [{
                "content": f"Evidence for {query}",
                "semantic_score": score,
                "title": "Recovered Scheme",
                "source_url": "https://example.gov/recovered",
                "scheme_id": "recovered-id",
            }]

    translator = RecordingTranslator()
    pipeline = RAGPipeline(
        retriever=DynamicRetriever(),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=translator,
    )

    result = pipeline.answer("शिष्यवृत्ती", language="kok")

    assert result["route"] == "fallback_recovered"
    assert result["confidence"] == 0.85
    assert result["answer"].startswith("[KONKANI]")
    assert len(translator.english_to_konkani_calls) == 1


def test_pipeline_fallback_failed_route_translates_back() -> None:
    class LowScoreRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            return [{
                "content": f"Evidence for {query}",
                "semantic_score": 0.25,
                "title": "Low Score Scheme",
                "source_url": "https://example.gov/low",
                "scheme_id": "low-id",
            }]

    translator = RecordingTranslator()
    pipeline = RAGPipeline(
        retriever=LowScoreRetriever(),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=translator,
    )

    result = pipeline.answer("परग्रह", language="kok")

    assert result["route"] == "fallback_failed"
    assert result["confidence"] == 0.25
    assert result["answer"].startswith("[KONKANI]")
    assert "myscheme.gov.in" in result["answer"]
    assert len(translator.english_to_konkani_calls) == 1


def test_pipeline_returns_fallback_failed_when_retriever_empty() -> None:
    class EmptyRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            return []

    translator = RecordingTranslator()
    pipeline = RAGPipeline(
        retriever=EmptyRetriever(),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=translator,
    )

    result = pipeline.answer("unknown topic", language="kok")

    assert result["route"] == "fallback_failed"
    assert result["confidence"] == 0.0
    assert result["sources"] == []
    assert result["answer"].startswith("[KONKANI]")
    assert "myscheme.gov.in" in result["answer"]
    assert len(translator.english_to_konkani_calls) == 1


def test_pipeline_uses_english_hint_when_flag_enabled() -> None:
    class RecordingRetriever:
        def __init__(self) -> None:
            self.query = ""

        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            self.query = query
            return [{
                "content": "Girls scholarship evidence",
                "semantic_score": 0.8,
                "title": "Girls Scholarship",
                "source_url": "https://example.gov/girls",
            }]

    class UnavailableTranslator:
        def konkani_to_english(self, text: str) -> str:
            return text

        def english_to_konkani(self, text: str) -> str:
            return text

    retriever = RecordingRetriever()
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=UnavailableTranslator(),
        use_retrieval_hints=True,
    )

    pipeline.answer("मुलींसाठी कोणत्या शिष्यवृत्ती योजना उपलब्ध आहेत?", language="kok")

    assert "scholarship" in retriever.query
    assert "girls" in retriever.query


def test_pipeline_omits_hint_when_flag_disabled() -> None:
    class RecordingRetriever:
        def __init__(self) -> None:
            self.query = ""

        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            self.query = query
            return [{
                "content": "Raw Devanagari evidence",
                "semantic_score": 0.8,
                "title": "Raw Scheme",
                "source_url": "https://example.gov/raw",
            }]

    class RawTranslator:
        def konkani_to_english(self, text: str) -> str:
            return text

        def english_to_konkani(self, text: str) -> str:
            return text

    retriever = RecordingRetriever()
    pipeline = RAGPipeline(
        retriever=retriever,
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=RawTranslator(),
        use_retrieval_hints=False,
    )

    devanagari_input = "मुलींसाठी कोणत्या शिष्यवृत्ती योजना उपलब्ध आहेत?"
    pipeline.answer(devanagari_input, language="kok")

    # Hint should not be appended
    assert retriever.query == devanagari_input


def test_pipeline_hindi_pivot_executed_on_low_confidence() -> None:
    class DynamicScoreRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            # Initial query returns low confidence 0.35; Hindi pivot query returns 0.85
            score = 0.85 if "pivot" in query else 0.35
            return [{
                "content": f"Evidence for {query}",
                "semantic_score": score,
                "rrf_score": 0.5,
                "title": "Scholarship Scheme",
                "source_url": "https://example.gov/scheme",
                "scheme_id": "scholarship-id",
            }]

    translator = RecordingTranslator()
    pipeline = RAGPipeline(
        retriever=DynamicScoreRetriever(),
        generator=StubGenerator(),
        router=FallbackRouter(confidence_threshold=0.50),
        translator=translator,
    )

    result = pipeline.answer("कागदपत्रां कितें जाय?", language="kok")
    assert result["route"] == "fallback_recovered"
    assert result["fallback_path_used"] == "hindi_pivot"
    assert result["confidence"] == 0.85

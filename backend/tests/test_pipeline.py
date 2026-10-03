from app.rag.pipeline import RAGPipeline


class StubRetriever:
    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        return [{"content": f"Evidence for {query}", "rrf_score": 0.5,
                 "title": "Test Scheme", "source_url": "https://example.gov/test"}]


class StubGenerator:
    def generate(self, query: str, context: str) -> str:
        return context


class StubRouter:
    def route(self, query: str, retrieval_score: float, answer: str) -> dict:
        return {"route": "direct", "answer": answer, "confidence": 0.9}


def test_pipeline_passes_retrieved_context_to_generator() -> None:
    pipeline = RAGPipeline(
        retriever=StubRetriever(),
        generator=StubGenerator(),
        router=StubRouter(),
        translator=False,
    )

    result = pipeline.answer("scholarship")

    assert result["answer"] == "Evidence for scholarship"
    assert result["confidence"] == 0.9
    assert result["route"] == "direct"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Test Scheme"


def test_pipeline_returns_no_results_when_retriever_empty() -> None:
    class EmptyRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
            return []

    pipeline = RAGPipeline(
        retriever=EmptyRetriever(),
        generator=StubGenerator(),
        router=StubRouter(),
        translator=False,
    )

    result = pipeline.answer("unknown topic")

    assert result["route"] == "no_results"
    assert result["confidence"] == 0.0
    assert result["sources"] == []

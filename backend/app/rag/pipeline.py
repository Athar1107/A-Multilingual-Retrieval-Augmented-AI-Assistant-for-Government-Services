"""End-to-end RAG pipeline: translate → retrieve → generate → route → respond.

This module is the single orchestration point that connects retrieval,
generation, translation, and fallback routing into a coherent workflow.
"""

import logging
from typing import Any, Protocol

from app.config import CONFIDENCE_THRESHOLD, TOP_K_DEFAULT
from app.rag.translation import devanagari_retrieval_hint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocols let the pipeline accept stub implementations for testing
# without importing the heavy concrete classes.
# ---------------------------------------------------------------------------

class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]: ...


class GeneratorProtocol(Protocol):
    def generate(self, query: str, context: str) -> str: ...


class FallbackRouterProtocol(Protocol):
    def route(self, query: str, retrieval_score: float, answer: str) -> dict[str, Any]: ...


class TranslationProtocol(Protocol):
    def konkani_to_english(self, text: str) -> str: ...
    def english_to_konkani(self, text: str) -> str: ...


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class RAGPipeline:
    """Orchestrate the full RAG workflow with translation and fallback support.

    Accepts either concrete instances or any object satisfying the
    corresponding Protocol, so unit tests can inject lightweight stubs.
    """

    def __init__(
        self,
        retriever: RetrieverProtocol | None = None,
        generator: GeneratorProtocol | None = None,
        translator: TranslationProtocol | None = None,
        router: FallbackRouterProtocol | None = None,
    ) -> None:
        # Lazy-import concrete classes only when no stubs are supplied.
        if retriever is None:
            from app.rag.retriever import Retriever
            retriever = Retriever()
        if generator is None:
            from app.rag.generator import AnswerGenerator
            generator = AnswerGenerator()
        if router is None:
            from app.rag.fallback_routing import FallbackRouter
            router = FallbackRouter(confidence_threshold=CONFIDENCE_THRESHOLD)

        self.retriever = retriever
        self.generator = generator
        self.router = router

        # Translation: False = disabled, None = auto-load best available backend
        # Pass translator=False in tests to skip loading heavy ML models.
        if translator is False:
            self.translator: TranslationProtocol | None = None
        elif translator is not None:
            self.translator = translator
        else:
            try:
                from app.rag.translation import TranslationService
                self.translator = TranslationService()
                logger.info("Translation service ready.")
            except Exception as exc:
                logger.warning(
                    "Translation service unavailable (%s); "
                    "queries will be processed in English only.", exc
                )
                self.translator = None

    def answer(
        self,
        query: str,
        language: str = "en",
        top_k: int = TOP_K_DEFAULT,
    ) -> dict[str, Any]:
        """Process a user query through the full pipeline.

        Parameters
        ----------
        query:
            The user's question text.
        language:
            ISO 639-1 code.  Non-English queries are translated to English
            for retrieval, and the answer is translated back.
        top_k:
            Maximum number of retrieval results to consider.

        Returns
        -------
        dict with ``answer``, ``confidence``, ``sources``, ``retrieval_results``,
        and ``route``.
        """
        # Step 1: Translate non-English queries to English for retrieval
        english_query = query
        if language != "en" and self.translator:
            english_query = self.translator.konkani_to_english(query)
            logger.info("Translated query: '%s' → '%s'", query, english_query)

        # The corpus is English. Do not retrieve raw Devanagari when a
        # translation backend is offline. A domain hint also reinforces terms
        # such as girls and scholarship after a successful translation.
        retrieval_hint = devanagari_retrieval_hint(query) if language != "en" else None
        has_english_output = any("a" <= char.lower() <= "z" for char in english_query)
        if retrieval_hint and not has_english_output:
            english_query = retrieval_hint
            logger.warning("Translation unavailable; using retrieval hint: '%s'", retrieval_hint)
        elif retrieval_hint:
            english_query = f"{english_query} {retrieval_hint}"

        # Step 2: Retrieve relevant passages
        results = self.retriever.retrieve(english_query, top_k=top_k)

        if not results:
            return {
                "answer": "No relevant information found for your query.",
                "confidence": 0.0,
                "sources": [],
                "retrieval_results": [],
                "route": "no_results",
            }

        # Step 3: Build context from retrieved passages
        context = "\n\n".join(r["content"] for r in results)

        # Step 4: Compute normalised retrieval score for routing.
        # RRF scores are typically small (~0.01–0.03); we normalise by
        # mapping the average to a [0, 1] range using a simple multiplier.
        semantic_scores = [
            float(result["semantic_score"])
            for result in results
            if "semantic_score" in result
        ]
        if semantic_scores:
            normalised_score = max(semantic_scores)
        else:
            raw_avg = sum(r.get("rrf_score", 0.0) for r in results) / len(results)
            normalised_score = min(raw_avg * 60, 1.0)

        # Step 5: Generate answer from context
        answer_text = self.generator.generate(english_query, context)

        # Step 6: Route through fallback logic
        routed = self.router.route(english_query, normalised_score, answer_text)

        # Step 7: Translate answer back to user's language if needed
        if language != "en" and self.translator and routed["route"] == "direct":
            routed["answer"] = self.translator.english_to_konkani(routed["answer"])

        # Step 8: Extract unique source citations
        seen_urls: set[str] = set()
        sources: list[dict[str, str]] = []
        for r in results:
            url = r.get("source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": r.get("title", "Unknown"),
                    "source_url": url,
                })

        return {
            "answer": routed["answer"],
            "confidence": routed["confidence"],
            "sources": sources,
            "retrieval_results": results,
            "route": routed["route"],
        }

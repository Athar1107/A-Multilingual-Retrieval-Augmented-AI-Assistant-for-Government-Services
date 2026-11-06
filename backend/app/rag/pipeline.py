"""End-to-end RAG pipeline: translate → retrieve → generate → route → respond.

This module is the single orchestration point that connects retrieval,
generation, translation, and fallback routing into a coherent workflow.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from app.config import CONFIDENCE_THRESHOLD, TOP_K_DEFAULT, USE_RETRIEVAL_HINTS
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
    def paraphrase_query(self, query: str) -> str: ...


class FallbackRouterProtocol(Protocol):
    def route(
        self,
        query: str,
        retrieval_score: float,
        answer: str,
        is_recovered: bool = False,
    ) -> dict[str, Any]: ...


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
        translator: TranslationProtocol | None | bool = None,
        router: FallbackRouterProtocol | None = None,
        use_retrieval_hints: bool = USE_RETRIEVAL_HINTS,
    ) -> None:
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
        self.use_retrieval_hints = use_retrieval_hints

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

    def _compute_confidence(self, results: list[dict[str, Any]]) -> float:
        """Compute retrieval confidence score from dense semantic similarities or RRF."""
        if not results:
            return 0.0
        semantic_scores = [
            float(result["semantic_score"])
            for result in results
            if "semantic_score" in result and result["semantic_score"] is not None
        ]
        if semantic_scores:
            return round(max(semantic_scores), 4)

        raw_avg = sum(float(r.get("rrf_score", 0.0)) for r in results) / len(results)
        return round(min(max(raw_avg, 0.0), 1.0), 4)

    def _route(
        self,
        query: str,
        score: float,
        answer: str,
        is_recovered: bool = False,
    ) -> dict[str, Any]:
        """Safely invoke router.route supporting both 3-arg and 4-arg signatures."""
        try:
            return self.router.route(query, score, answer, is_recovered=is_recovered)
        except TypeError:
            return self.router.route(query, score, answer)

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
            ISO 639-1 code ('en' or 'kok'). Non-English queries are translated
            to English for retrieval, and answers are always translated back.
        top_k:
            Maximum number of retrieval results to consider.

        Returns
        -------
        dict with ``query``, ``answer``, ``confidence``, ``sources``, ``retrieval_results``,
        ``retrieved_doc_ids``, ``route``, ``translator_backend``, and ``retrieval_hint_applied``.
        """
        # Step 1: Translate non-English queries to English for retrieval
        started = time.perf_counter()
        latencies = {"translate_in": 0.0, "retrieve": 0.0, "generate": 0.0, "translate_out": 0.0}

        english_query = query
        t_stage = time.perf_counter()
        if language != "en" and self.translator:
            english_query = self.translator.konkani_to_english(query)
            logger.info("Translated query: '%s' → '%s'", query[:80], english_query[:80])
        latencies["translate_in"] = round((time.perf_counter() - t_stage) * 1000, 2)

        # Step 1b: Optional hand-made retrieval hint (governed by USE_RETRIEVAL_HINTS)
        retrieval_hint_applied = False
        if self.use_retrieval_hints and language != "en":
            hint = devanagari_retrieval_hint(query)
            has_english_output = any("a" <= char.lower() <= "z" for char in english_query)
            if hint and not has_english_output:
                english_query = hint
                retrieval_hint_applied = True
                logger.info("Translation unavailable; applied retrieval hint: '%s'", hint)
            elif hint:
                english_query = f"{english_query} {hint}"
                retrieval_hint_applied = True
                logger.info("Reinforced query with retrieval hint: '%s'", hint)

        # Step 2: Primary retrieval
        t_stage = time.perf_counter()
        results = self.retriever.retrieve(english_query, top_k=top_k)
        latencies["retrieve"] = round((time.perf_counter() - t_stage) * 1000, 2)

        if not results:
            no_results_ans = (
                "No reliable information found for your query. Please verify with the official "
                "scheme portal at https://www.myscheme.gov.in or contact the relevant government office."
            )
            t_stage = time.perf_counter()
            if language != "en" and self.translator:
                no_results_ans = self.translator.english_to_konkani(no_results_ans)
            latencies["translate_out"] = round((time.perf_counter() - t_stage) * 1000, 2)
            latencies["total"] = round((time.perf_counter() - started) * 1000, 2)

            return {
                "query": query,
                "translated_query": english_query,
                "answer": no_results_ans,
                "confidence": 0.0,
                "sources": [],
                "retrieval_results": [],
                "retrieved_doc_ids": [],
                "route": "fallback_failed",
                "route_reason": "no_retrieval_results",
                "translator_backend": getattr(self.translator, "backend_name", "none") if self.translator else "none",
                "retrieval_hint_applied": retrieval_hint_applied,
                "latencies_ms": latencies,
            }

        # Step 3: Compute confidence
        confidence_score = self._compute_confidence(results)
        threshold = getattr(self.router, "confidence_threshold", CONFIDENCE_THRESHOLD)

        # Step 4: Routing & Attempt 2 (Alternate retrieval on low confidence)
        route_reason = "confidence_above_threshold"
        fallback_path_used = "none"
        if confidence_score >= threshold:
            # Direct route
            context = "\n\n".join(r["content"] for r in results)
            t_stage = time.perf_counter()
            answer_text = self.generator.generate(english_query, context)
            latencies["generate"] = round((time.perf_counter() - t_stage) * 1000, 2)
            routed = self._route(english_query, confidence_score, answer_text, is_recovered=False)
        else:
            # Low confidence: Attempt 2 (Alternate retrieval path)
            logger.info("Confidence %.4f < %.2f; attempting fallback recovery...", confidence_score, threshold)
            alt_query = None

            # Path A: Hindi pivot for non-English queries if supported
            if language != "en" and self.translator and hasattr(self.translator, "konkani_to_english_pivot"):
                try:
                    alt_candidate = self.translator.konkani_to_english_pivot(query)
                    logger.info("Attempt 2 Hindi pivot query: '%s' → '%s'", query[:80], alt_candidate[:80])
                    if alt_candidate and alt_candidate.strip() and alt_candidate.strip() != english_query.strip():
                        alt_query = alt_candidate
                        fallback_path_used = "hindi_pivot"
                except Exception as exc:
                    logger.warning("Hindi pivot attempt failed: %s", exc)

            # Path B: LLM search query reformulation / paraphrase
            if (not alt_query or alt_query == english_query) and hasattr(self.generator, "paraphrase_query"):
                try:
                    alt_candidate = self.generator.paraphrase_query(english_query)
                    logger.info("Attempt 2 LLM paraphrase query: '%s' → '%s'", english_query[:80], alt_candidate[:80])
                    if alt_candidate and alt_candidate.strip() and alt_candidate.strip() != english_query.strip():
                        alt_query = alt_candidate
                        fallback_path_used = "llm_paraphrase"
                except Exception as exc:
                    logger.warning("LLM paraphrase attempt failed: %s", exc)

            results_2: list[dict[str, Any]] = []
            if alt_query and alt_query.strip() and alt_query.strip() != english_query.strip():
                t_stage = time.perf_counter()
                results_2 = self.retriever.retrieve(alt_query, top_k=top_k)
                latencies["retrieve"] += round((time.perf_counter() - t_stage) * 1000, 2)

            conf_2 = self._compute_confidence(results_2) if results_2 else 0.0

            if conf_2 >= threshold:
                # Fallback recovered!
                results = results_2
                confidence_score = conf_2
                context = "\n\n".join(r["content"] for r in results)
                t_stage = time.perf_counter()
                answer_text = self.generator.generate(alt_query, context)
                latencies["generate"] = round((time.perf_counter() - t_stage) * 1000, 2)
                routed = self._route(alt_query, confidence_score, answer_text, is_recovered=True)
                route_reason = "fallback_recovered_second_retrieval"
                logger.info("Fallback recovered successfully with confidence %.4f", conf_2)
            else:
                # Fallback failed
                routed = self._route(english_query, confidence_score, "", is_recovered=False)
                results = []  # Discard low-confidence unrelated sources
                route_reason = "confidence_below_threshold"
                logger.info("Fallback failed; returning caveat guidance.")

        english_answer = routed.get("answer", "")

        # Step 5: ALWAYS translate the final answer back to the user's language, including on fallback!
        t_stage = time.perf_counter()
        if language != "en" and self.translator:
            try:
                routed["answer"] = self.translator.english_to_konkani(routed["answer"])
            except Exception as exc:
                logger.warning("Failed translating final response back to %s: %s", language, exc)
        latencies["translate_out"] = round((time.perf_counter() - t_stage) * 1000, 2)
        latencies["total"] = round((time.perf_counter() - started) * 1000, 2)

        # Step 6: Extract unique sources and doc IDs
        seen_urls: set[str] = set()
        sources: list[dict[str, str]] = []
        retrieved_doc_ids: list[str] = []

        for r in results:
            url = r.get("source_url", "")
            doc_id = r.get("scheme_id") or r.get("title", "")
            if doc_id and doc_id not in retrieved_doc_ids:
                retrieved_doc_ids.append(doc_id)
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": r.get("title", "Unknown"),
                    "source_url": url,
                })

        translator_backend = (
            getattr(self.translator, "backend_name", "unknown")
            if self.translator
            else "none"
        )

        return {
            "query": query,
            "translated_query": english_query,
            "english_answer": english_answer,
            "answer": routed["answer"],
            "confidence": routed["confidence"],
            "route": routed["route"],
            "route_reason": route_reason,
            "fallback_path_used": fallback_path_used,
            "sources": sources,
            "retrieval_results": results,
            "retrieved_chunks": [r.get("content", "") for r in results],
            "retrieved_doc_ids": retrieved_doc_ids,
            "translator_backend": translator_backend,
            "retrieval_hint_applied": retrieval_hint_applied,
            "latencies_ms": latencies,
        }

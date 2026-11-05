"""Confidence-based routing for direct answers, fallback recovery, and fallback failure."""

from __future__ import annotations

import logging
from typing import Any

from app.config import CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

FALLBACK_CAVEAT = (
    "No reliable information found for your query. Please verify with the official "
    "scheme portal at https://www.myscheme.gov.in or contact the relevant government office."
)


class FallbackRouter:
    """Route answers based on retrieval confidence scores.

    Route values:
      - ``direct``             : initial retrieval confidence meets or exceeds threshold.
      - ``fallback_recovered`` : initial retrieval fell below threshold, but alternate retrieval
                                 (query reformulation or Hindi pivot) recovered high confidence.
      - ``fallback_failed``    : retrieval confidence remained below threshold after all attempts;
                                 returns standard refusal caveat directing to myscheme.gov.in.
    """

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD) -> None:
        self.confidence_threshold = confidence_threshold

    def route(
        self,
        query: str,
        retrieval_score: float,
        answer: str,
        is_recovered: bool = False,
    ) -> dict[str, Any]:
        """Decide routing state based on retrieval confidence.

        Parameters
        ----------
        query:
            The query text (used for logging, truncated to 80 chars).
        retrieval_score:
            Score in [0.0, 1.0] representing retrieval confidence.
        answer:
            The generated answer text.
        is_recovered:
            True if this routing decision succeeds an alternate retrieval attempt.

        Returns
        -------
        dict with ``route`` ('direct' | 'fallback_recovered' | 'fallback_failed'),
        ``answer``, and ``confidence``.
        """
        confidence = min(max(float(retrieval_score), 0.0), 1.0)

        if confidence >= self.confidence_threshold:
            route = "fallback_recovered" if is_recovered else "direct"
            final_answer = answer
        else:
            route = "fallback_failed"
            final_answer = FALLBACK_CAVEAT
            logger.info(
                "Low confidence (%.4f < %.2f) for query: %s",
                confidence,
                self.confidence_threshold,
                query[:80],
            )

        return {
            "route": route,
            "answer": final_answer,
            "confidence": round(confidence, 4),
        }

"""Confidence-based routing to direct answers or fallback responses."""

import logging

from app.config import CONFIDENCE_THRESHOLD
from typing import Any

logger = logging.getLogger(__name__)

FALLBACK_CAVEAT = (
    "I found some related information but I'm not confident enough to give "
    "a definitive answer. Please verify with the official scheme portal at "
    "https://www.myscheme.gov.in or contact the relevant government office."
)


class FallbackRouter:
    """Route answers based on retrieval confidence scores.

    When the fused retrieval score is below the threshold, the answer
    is still returned but a caveat is appended directing the user to
    official sources.
    """

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD) -> None:
        self.confidence_threshold = confidence_threshold

    def route(self, query: str, retrieval_score: float, answer: str) -> dict[str, Any]:
        """Decide whether to serve the generated answer directly or add a caveat.

        Parameters
        ----------
        query:
            The original user query (used for logging).
        retrieval_score:
            A score in [0, 1] representing retrieval confidence
            (e.g. the average RRF score normalised).
        answer:
            The generated answer text.

        Returns
        -------
        dict with ``route`` ('direct' | 'fallback'), ``answer``, and
        ``confidence``.
        """
        confidence = min(max(retrieval_score, 0.0), 1.0)

        if confidence >= self.confidence_threshold:
            route = "direct"
            final_answer = answer
        else:
            route = "fallback"
            final_answer = f"{answer}\n\n⚠️ {FALLBACK_CAVEAT}"
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
"""Generate grounded answers from retrieved context using Ollama.

Uses ``httpx`` (declared in pyproject.toml) instead of ``requests``
(which was not declared).
"""

import logging

import httpx

from app.config import OLLAMA_MODEL, OLLAMA_URL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful government services assistant. Answer questions based "
    "ONLY on the provided context about government schemes. If the context "
    "does not contain enough information to answer the question, say so "
    "clearly. Always be accurate and cite the scheme names when relevant. "
    "Keep answers concise (2-4 sentences)."
)

USER_PROMPT_TEMPLATE = """Context:
{context}

Question: {query}

Answer in 3-5 sentences based only on the context. Mention the scheme name.
If the context lacks information, say so clearly."""

# Maximum characters of context to send — keeps prompt within LLM context window
# and prevents timeouts on CPU-only inference.
MAX_CONTEXT_CHARS: int = 2_000


class AnswerGenerator:
    """Generate grounded answers by sending retrieved context to an Ollama LLM."""

    def __init__(
        self,
        model_name: str = OLLAMA_MODEL,
        ollama_url: str = OLLAMA_URL,
        timeout: float = 180.0,          # 3 min — generous for CPU-only LLM
    ) -> None:
        self.model = model_name
        self.ollama_url = ollama_url
        self.timeout = timeout

    def generate(self, query: str, context: str) -> str:
        """Generate an answer using Ollama."""
        # Trim context to avoid very long prompts on CPU-only inference
        trimmed = context[:MAX_CONTEXT_CHARS]
        if len(context) > MAX_CONTEXT_CHARS:
            logger.info("Context trimmed from %d to %d chars", len(context), MAX_CONTEXT_CHARS)
        prompt = USER_PROMPT_TEMPLATE.format(context=trimmed, query=query)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 200,   # cap output tokens — keeps response fast
                            "temperature": 0.1,   # low temperature for factual accuracy
                        },
                    },
                )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No answer generated.").strip()
            else:
                logger.error(
                    "Ollama returned HTTP %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return (
                    f"LLM service error (HTTP {response.status_code}). "
                    "Please try again."
                )

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s", self.ollama_url)
            return (
                "The language model service is not available. "
                f"Please ensure Ollama is running at {self.ollama_url}."
            )
        except Exception as e:
            logger.exception("Unexpected error during generation")
            return f"Generation error: {e}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = AnswerGenerator()

    query = "What is a scholarship?"
    context = (
        "Pre Matric Scholarship - Financial aid for students to continue "
        "their education. Benefits include tuition fee payment and stipend."
    )

    print(f"Q: {query}")
    print("Generating...")
    answer = generator.generate(query, context)
    print(f"A: {answer}\n")
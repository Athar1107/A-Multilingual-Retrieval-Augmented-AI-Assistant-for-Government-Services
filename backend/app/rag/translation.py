"""Konkani ↔ English translation layer.

Translation strategy (in priority order):
─────────────────────────────────────────
1.  IndicTrans2 (ai4bharat) — best quality, supports kok_Deva natively.
    Requires a HuggingFace token and manual model-gate approval.
    Set HF_TOKEN env var and the model will be used automatically.

2.  NLLB-200 distilled-600M (Facebook/Meta) — ungated, downloads freely.
    Does NOT have a kok_Deva token, so Konkani is handled via Marathi
    (mar_Deva) as a script-compatible pivot.  Goan Konkani shares the
    Devanagari script and high lexical overlap with Marathi, making this
    a reasonable approximation for an MVP.

3.  Passthrough — if no model can be loaded, the original text is
    returned unchanged and the pipeline continues in English.

Environment variables
─────────────────────
HF_TOKEN          HuggingFace token — enables IndicTrans2 download.
TRANSLATION_MODEL "indictrans2" | "nllb" | "none"
                  Override automatic model selection.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Model identifiers ─────────────────────────────────────────────────────

_INDICTRANS2_I2E = "ai4bharat/indictrans2-indic-en-dist-200M"
_INDICTRANS2_E2I = "ai4bharat/indictrans2-en-indic-dist-200M"
_NLLB_MODEL      = "facebook/nllb-200-distilled-600M"

# NLLB does not have kok_Deva; use mar_Deva (Marathi / Devanagari) as
# the closest supported script-compatible pivot for Konkani.
_NLLB_KONKANI_PROXY = "mar_Deva"
_NLLB_ENGLISH       = "eng_Latn"

_OVERRIDE = os.environ.get("TRANSLATION_MODEL", "auto").lower()
_HF_TOKEN = os.environ.get("HF_TOKEN", "").strip() or None

# Conservative retrieval help for frequent public-service terms in Devanagari.
# It prevents an untranslated query from being sent unchanged to an
# English-only index when the translation model is unavailable.
_DEVANAGARI_RETRIEVAL_TERMS: tuple[tuple[str, str], ...] = (
    ("शिष्यवृत्ती", "scholarship"),
    ("शिश्यवृत्ती", "scholarship"),
    ("मुलींसाठी", "girls"),
    ("मुलीं", "girls"),
    ("मुली", "girls"),
    ("विद्यार्थ्यांसाठी", "students"),
    ("विद्यार्थी", "students"),
    ("योजना", "scheme"),
    ("योजनां", "scheme"),
    ("उपलब्ध", "available"),
    ("आसात", "available"),
    ("कोणत्या", "which"),
    ("किती", "amount"),
    ("पात्र", "eligibility"),
    ("अर्ज", "application"),
    ("कागदपत्र", "documents"),
    ("सरकारी", "government"),
)


def devanagari_retrieval_hint(text: str) -> str | None:
    """Return a conservative English retrieval hint for recognised Devanagari."""
    if not any("\u0900" <= char <= "\u097f" for char in text):
        return None
    terms = [english for source, english in _DEVANAGARI_RETRIEVAL_TERMS if source in text]
    unique_terms = list(dict.fromkeys(terms))
    return " ".join(unique_terms) if len(unique_terms) >= 2 else None


def _device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


# ── IndicTrans2 backend ───────────────────────────────────────────────────

class _IndicTrans2Backend:
    """IndicTrans2 200M distilled — requires HF token + gated access."""

    def __init__(self) -> None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        dev = _device()
        kwargs: dict[str, Any] = {"trust_remote_code": True}
        if _HF_TOKEN:
            kwargs["token"] = _HF_TOKEN

        logger.info("Loading IndicTrans2 Indic→EN from %s ...", _INDICTRANS2_I2E)
        self._tok_i2e = AutoTokenizer.from_pretrained(_INDICTRANS2_I2E, **kwargs)
        self._mdl_i2e = AutoModelForSeq2SeqLM.from_pretrained(
            _INDICTRANS2_I2E, **kwargs
        ).to(dev)

        logger.info("Loading IndicTrans2 EN→Indic from %s ...", _INDICTRANS2_E2I)
        self._tok_e2i = AutoTokenizer.from_pretrained(_INDICTRANS2_E2I, **kwargs)
        self._mdl_e2i = AutoModelForSeq2SeqLM.from_pretrained(
            _INDICTRANS2_E2I, **kwargs
        ).to(dev)

        self._dev = dev
        logger.info("IndicTrans2 loaded on %s.", dev)

    def konkani_to_english(self, text: str) -> str:
        import torch

        # gom_Deva = Goan Konkani in Devanagari (ISO 639-3: gom)
        # kok_Deva would be standard Konkani but is not in the 200M model vocabulary
        formatted = f"gom_Deva eng_Latn {text}"
        inputs = self._tok_i2e(
            formatted, return_tensors="pt", padding=True, truncation=True, max_length=256
        ).to(self._dev)
        with torch.no_grad():
            out = self._mdl_i2e.generate(**inputs, max_length=256, num_beams=4)
        return self._tok_i2e.decode(out[0], skip_special_tokens=True).strip()

    def english_to_konkani(self, text: str) -> str:
        import torch

        # gom_Deva = Goan Konkani in Devanagari
        formatted = f"eng_Latn gom_Deva {text}"
        inputs = self._tok_e2i(
            formatted, return_tensors="pt", padding=True, truncation=True, max_length=256
        ).to(self._dev)
        with torch.no_grad():
            out = self._mdl_e2i.generate(**inputs, max_length=256, num_beams=4)
        return self._tok_e2i.decode(out[0], skip_special_tokens=True).strip()


# ── NLLB-200 backend ─────────────────────────────────────────────────────

class _NLLBBackend:
    """NLLB-200 distilled 600M — ungated, no token needed.

    Konkani is proxied through Marathi (mar_Deva) because NLLB-200 does
    not include a kok_Deva token.  This is a deliberate approximation:
    Goan Konkani written in Devanagari is largely mutually intelligible
    with Marathi at the script and lexical level for domain-specific text
    about government schemes.
    """

    def __init__(self) -> None:
        from transformers import AutoModelForSeq2SeqLM, NllbTokenizer

        dev = _device()
        logger.info("Loading NLLB-200 distilled-600M (~600 MB, ungated)...")
        self._tok = NllbTokenizer.from_pretrained(_NLLB_MODEL)
        self._mdl = AutoModelForSeq2SeqLM.from_pretrained(_NLLB_MODEL).to(dev)
        self._dev = dev
        logger.info(
            "NLLB-200 loaded on %s. NOTE: Konkani proxied via Marathi (mar_Deva).", dev
        )

    def _translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        import torch

        self._tok.src_lang = src_lang
        inputs = self._tok(
            text, return_tensors="pt", padding=True, truncation=True, max_length=256
        ).to(self._dev)
        bos = self._tok.convert_tokens_to_ids(tgt_lang)
        with torch.no_grad():
            out = self._mdl.generate(
                **inputs,
                forced_bos_token_id=bos,
                max_length=256,
                num_beams=4,
            )
        return self._tok.decode(out[0], skip_special_tokens=True).strip()

    def konkani_to_english(self, text: str) -> str:
        # Treat Konkani Devanagari input as Marathi for NLLB
        return self._translate(text, src_lang=_NLLB_KONKANI_PROXY, tgt_lang=_NLLB_ENGLISH)

    def english_to_konkani(self, text: str) -> str:
        # Generate Marathi Devanagari as a proxy for Konkani
        return self._translate(text, src_lang=_NLLB_ENGLISH, tgt_lang=_NLLB_KONKANI_PROXY)


# ── Public TranslationService ────────────────────────────────────────────

class TranslationService:
    """Language-agnostic translation facade.

    Selects the best available backend at first use.  Falls back to
    passthrough (returns original text) if no model loads successfully.
    """

    def __init__(self) -> None:
        self._backend: _IndicTrans2Backend | _NLLBBackend | None = None
        self._failed = False

    def _load(self) -> bool:
        """Lazily load the best available translation backend."""
        if self._backend is not None:
            return True
        if self._failed:
            return False

        try:
            if _OVERRIDE == "none":
                logger.info("Translation disabled via TRANSLATION_MODEL=none.")
                self._failed = True
                return False

            # Prefer IndicTrans2 when a HF token is available
            if _OVERRIDE in ("indictrans2", "auto") and _HF_TOKEN:
                try:
                    self._backend = _IndicTrans2Backend()
                    logger.info("Translation backend: IndicTrans2 (native kok_Deva)")
                    return True
                except Exception as exc:
                    logger.warning(
                        "IndicTrans2 unavailable (%s); trying NLLB fallback.", exc
                    )

            # Fall back to NLLB-200 (ungated, always downloadable)
            if _OVERRIDE in ("nllb", "auto"):
                self._backend = _NLLBBackend()
                logger.info(
                    "Translation backend: NLLB-200 "
                    "(Konkani proxied via Marathi — set HF_TOKEN for native kok_Deva)"
                )
                return True

        except Exception as exc:
            logger.warning(
                "All translation backends failed: %s. "
                "Queries will be processed in English only.",
                exc,
            )
            self._failed = True

        return False

    def konkani_to_english(self, text: str) -> str:
        """Translate Konkani Devanagari query to English for retrieval.

        Returns the original text unchanged if translation is unavailable.
        """
        if not text or not self._load():
            return text
        try:
            return self._backend.konkani_to_english(text)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Konkani→English translation failed: %s", exc)
            return text

    def english_to_konkani(self, text: str) -> str:
        """Translate English answer to Konkani Devanagari.

        Returns the original text unchanged if translation is unavailable.
        """
        if not text or not self._load():
            return text
        try:
            return self._backend.english_to_konkani(text)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("English→Konkani translation failed: %s", exc)
            return text

    @property
    def backend_name(self) -> str:
        """Return the name of the active backend, or 'none'."""
        if self._backend is None and not self._failed:
            return "not_loaded"
        if isinstance(self._backend, _IndicTrans2Backend):
            return "indictrans2"
        if isinstance(self._backend, _NLLBBackend):
            return "nllb_marathi_proxy"
        return "none"

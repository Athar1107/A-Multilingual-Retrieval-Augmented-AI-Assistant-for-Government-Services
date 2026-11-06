"""Test the translation service — downloads NLLB-200 on first run (~600 MB).

Run: python scripts/test_translation.py
Set HF_TOKEN env var to test IndicTrans2 instead.
"""
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.translation import TranslationService

print("=" * 60)
print("  Translation Service Test")
print("=" * 60)
print()

svc = TranslationService()
print("Loading backend (NLLB downloads ~600 MB on first run)...")
t0 = time.time()
svc._load()
print(f"Backend: {svc.backend_name}  ({time.time()-t0:.1f}s)\n")

# Test 1: Konkani-like Devanagari → English
# (Using Marathi sentences that are close to Goan Konkani)
indic_queries = [
    "सरकारी शिष्यवृत्ती मिळवण्यासाठी कोणती कागदपत्रे लागतात?",
    "पीएम किसान योजनेचा लाभ किती आहे?",
    "इंटर्नशिप योजनेसाठी कोण पात्र आहे?",
]

print("-- Indic (Devanagari) -> English ---------------------------")
for q in indic_queries:
    t0 = time.time()
    translated = svc.konkani_to_english(q)
    print(f"IN : {q}")
    print(f"OUT: {translated}  ({time.time()-t0:.1f}s)")
    print()

# Test 2: English → Indic Devanagari
english_answers = [
    "The PM Kisan scheme provides 6000 rupees per year to eligible farmers.",
    "Students must submit Aadhaar card and income certificate to apply.",
    "The DPIIT internship offers 10000 rupees per month stipend.",
]

print("-- English -> Indic (Devanagari) ---------------------------")
for a in english_answers:
    t0 = time.time()
    translated = svc.english_to_konkani(a)
    print(f"IN : {a}")
    print(f"OUT: {translated}  ({time.time()-t0:.1f}s)")
    print()

print("=" * 60)
print(f"Backend used: {svc.backend_name}")
if svc.backend_name == "nllb_marathi_proxy":
    print("NOTE: Using Marathi (mar_Deva) as Konkani proxy.")
    print("      Set HF_TOKEN for native kok_Deva via IndicTrans2.")
print("=" * 60)

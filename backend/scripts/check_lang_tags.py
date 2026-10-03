"""Check which language tags IndicTrans2 supports."""
import os, sys
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained(
    "ai4bharat/indictrans2-indic-en-dist-200M",
    trust_remote_code=True,
    token=os.environ.get("HF_TOKEN"),
)

# Find LANGUAGE_TAGS in loaded modules
for mod_name, mod in sys.modules.items():
    if "indictrans" in mod_name.lower() and hasattr(mod, "LANGUAGE_TAGS"):
        tags = mod.LANGUAGE_TAGS
        print(f"Module: {mod_name}")
        print(f"Total language tags: {len(tags)}")
        print()
        kok = sorted([t for t in tags if "kok" in t.lower()])
        mar = sorted([t for t in tags if "mar" in t.lower()])
        hin = sorted([t for t in tags if "hin" in t.lower()])
        eng = sorted([t for t in tags if "eng" in t.lower()])
        print(f"kok tags: {kok}")
        print(f"mar tags: {mar}")
        print(f"hin tags: {hin}")
        print(f"eng tags: {eng}")
        print()
        print("All tags:")
        for t in sorted(tags):
            print(f"  {t}")
        break

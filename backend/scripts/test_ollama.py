"""Quick Ollama connectivity and latency test."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.config import OLLAMA_MODEL, OLLAMA_URL

print(f"Ollama URL   : {OLLAMA_URL}")
print(f"Model        : {OLLAMA_MODEL}")
print()

# 1. Check available models
try:
    r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"Available models : {models}")
except Exception as e:
    print(f"Cannot reach Ollama: {e}")
    sys.exit(1)

# 2. Send a minimal prompt and measure latency
print("\nSending test prompt...")
t0 = time.time()
try:
    resp = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": "In one sentence: what is a government scholarship?",
            "stream": False,
            "options": {"num_predict": 50},
        },
        timeout=120.0,
    )
    elapsed = time.time() - t0
    if resp.status_code == 200:
        answer = resp.json().get("response", "").strip()
        print(f"Response ({elapsed:.1f}s): {answer}")
    else:
        print(f"HTTP {resp.status_code}: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

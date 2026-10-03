import json
import urllib.request
from pathlib import Path

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
url = "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug=pg-igssgc"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.myscheme.gov.in/",
        "Origin": "https://www.myscheme.gov.in",
        "x-api-key": API_KEY,
    },
)
with urllib.request.urlopen(req, timeout=30) as resp:
    payload = json.loads(resp.read().decode("utf-8"))

data = payload["data"]
Path("_scheme.json").write_text(json.dumps(data, indent=2)[:250000], encoding="utf-8")
print("top keys", data.keys())
en = data.get("en", {})
print("en keys", en.keys())
for key, value in en.items():
    print(key, type(value).__name__, list(value.keys())[:20] if isinstance(value, dict) else (str(value)[:80] if not isinstance(value, list) else f"list[{len(value)}]"))
print("date-like", [k for k in data if "date" in k.lower() or "time" in k.lower() or "at" in k.lower()])
print("_id", data.get("_id"))
print("slug", data.get("slug"))
for k in data:
    if k not in {"en"}:
        v = data[k]
        print("top", k, type(v).__name__, str(v)[:120])

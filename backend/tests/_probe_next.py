import json
import re
import urllib.request
from pathlib import Path

url = "https://www.myscheme.gov.in/schemes/pg-igssgc"
request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)
html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
assert match, "no next data"
data = json.loads(match.group(1))
out = Path(__file__).with_name("_probe_next.json")
out.write_text(json.dumps(data, indent=2)[:200000], encoding="utf-8")
print("keys", data.keys())
print("page", data.get("page"))
print("query", data.get("query"))
props = data.get("props", {})
print("props keys", props.keys())
page_props = props.get("pageProps", {})
print("pageProps keys", list(page_props.keys())[:50])
print("pageProps types", {k: type(v).__name__ for k, v in page_props.items()})

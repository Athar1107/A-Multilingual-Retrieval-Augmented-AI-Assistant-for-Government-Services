import re
import urllib.request
from pathlib import Path

url = "https://www.myscheme.gov.in/schemes/pg-igssgc"
request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)
html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
urls = sorted(set(re.findall(r"https?://[a-zA-Z0-9._/-]*api[a-zA-Z0-9._/-]*", html)))
print("html api urls", urls[:50])
print("api.myscheme", "api.myscheme" in html)
print("x-api-key" in html.lower())
chunks = re.findall(r"https://cdn.myscheme.in/_next/static/chunks/[^\"']+\.js", html)
print("chunks", len(chunks))
# download a few large-looking chunks? just search first chunk names
print("sample chunks", chunks[:5])

# fetch one likely app chunk
found = []
for chunk in chunks:
    if any(token in chunk for token in ("1xfufc", "1c9zc8", "0lcvi0", "3s8ykb", "13s6uab")):
        req = urllib.request.Request(chunk, headers={"User-Agent": "Mozilla/5.0"})
        body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        hits = re.findall(r"https?://[^\"']*myscheme[^\"']*", body)
        keys = re.findall(r"x-api-key[^,]{0,80}", body)
        if "api.myscheme" in body or "schemes/v" in body:
            found.append((chunk, hits[:20], keys[:5], "api.myscheme" in body))
            Path("_chunk_sample.js").write_text(body[:50000], encoding="utf-8")

print("found", found)

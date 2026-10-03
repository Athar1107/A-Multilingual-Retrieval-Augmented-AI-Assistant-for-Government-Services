import re
import urllib.request
from pathlib import Path

url = "https://cdn.myscheme.in/_next/static/chunks/1xfufc-6-b1tz.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
Path("_chunk_page.js").write_text(body, encoding="utf-8")
print("len", len(body))
for pattern in [
    r"get\(\"https://api.myscheme.gov.in[^\"]+\"",
    r"post\(\"https://api.myscheme.gov.in[^\"]+\"",
    r".{40}public/schemes.{80}",
    r".{40}search/v.{80}",
]:
    print("PATTERN", pattern)
    for hit in re.findall(pattern, body)[:20]:
        print(hit)
        print("---")

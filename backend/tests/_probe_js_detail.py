import re
import urllib.request
from pathlib import Path

url = "https://cdn.myscheme.in/_next/static/chunks/3s8ykbw6k33ir.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
Path("_chunk.js").write_text(body, encoding="utf-8")
for m in re.finditer(r".{80}public/schemes.{120}", body):
    print(m.group(0))
    print("---")

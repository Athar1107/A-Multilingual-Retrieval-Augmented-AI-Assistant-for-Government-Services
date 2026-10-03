import re
from pathlib import Path

body = Path("_chunk.js").read_text(encoding="utf-8")
for pattern in [
    r".{60}schemes/v6/public/schemes/.{100}",
    r".{80}slug.{40}api.myscheme.{80}",
    r"get\(\"https://api.myscheme.gov.in[^\"]+\"",
    r"post\(\"https://api.myscheme.gov.in[^\"]+\"",
]:
    print("PATTERN", pattern)
    hits = re.findall(pattern, body)
    for hit in hits[:15]:
        print(hit)
        print("---")

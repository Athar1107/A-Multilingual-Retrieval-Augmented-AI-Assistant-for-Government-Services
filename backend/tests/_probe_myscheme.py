import re
import urllib.request
from pathlib import Path

url = "https://www.myscheme.gov.in/schemes/pg-igssgc"
request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)
html = urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace")
out = Path(__file__).with_name("_probe_myscheme.html")
out.write_text(html, encoding="utf-8")
print("len", len(html))
print("NEXT_DATA", "__NEXT_DATA__" in html)
print("next_f", "self.__next_f" in html)
print("script ids", re.findall(r"<script[^>]*id=\"([^\"]+)\"", html)[:20])
print("application/ld+json", "application/ld+json" in html)
print("Eligibility" in html)
print("Details" in html)
# meta description
for m in re.finditer(r'<meta[^>]+>', html):
    tag = m.group(0)
    if "description" in tag.lower() or "og:" in tag.lower():
        print(tag)

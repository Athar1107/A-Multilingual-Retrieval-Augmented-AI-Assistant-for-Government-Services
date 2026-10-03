import json
import urllib.error
import urllib.request

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json,text/html,*/*",
    "Referer": "https://www.myscheme.gov.in/schemes/pg-igssgc",
}
urls = [
    "https://api.myscheme.gov.in/schemes/v1/public/schemes/pg-igssgc",
    "https://api.myscheme.gov.in/schemes/v1/public/scheme/pg-igssgc",
    "https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=pg-igssgc",
    "https://api.myscheme.gov.in/schemes/v5/public/schemes/pg-igssgc",
    "https://www.myscheme.gov.in/api/schemes/pg-igssgc",
    "https://cdn.myscheme.in/schemes/pg-igssgc.json",
    "https://api.myscheme.gov.in/schemes/v1/schemes/pg-igssgc",
    "https://api.myscheme.gov.in/v1/schemes/pg-igssgc",
]
for url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(400)
            print(resp.status, resp.getheader("content-type"), url, body[:120])
    except urllib.error.HTTPError as exc:
        print(exc.code, url, exc.read()[:120])
    except Exception as exc:
        print("ERR", url, type(exc).__name__, exc)

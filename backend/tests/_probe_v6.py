import json
import urllib.error
import urllib.request

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.myscheme.gov.in/schemes/pg-igssgc",
    "Origin": "https://www.myscheme.gov.in",
    "x-api-key": API_KEY,
    "Content-Type": "application/json",
}

urls = [
    ("GET", "https://api.myscheme.gov.in/schemes/v6/public/schemes/pg-igssgc"),
    ("GET", "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug=pg-igssgc"),
    ("POST", "https://api.myscheme.gov.in/schemes/v6/public/schemes", json.dumps(["pg-igssgc"]).encode()),
    ("POST", "https://api.myscheme.gov.in/schemes/v6/public/schemes", json.dumps({"slug": "pg-igssgc"}).encode()),
    ("GET", "https://api.myscheme.gov.in/search/v6/schemes?keyword=pg-igssgc"),
    ("GET", "https://api.myscheme.gov.in/search/v6/schemes?lang=en&from=0&size=1&keyword=Indira%20Gandhi"),
]

for item in urls:
    method = item[0]
    url = item[1]
    data = item[2] if len(item) > 2 else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(800)
            print(method, resp.status, url, body[:300])
    except urllib.error.HTTPError as exc:
        print(method, exc.code, url, exc.read()[:200])
    except Exception as exc:
        print("ERR", method, url, type(exc).__name__, exc)

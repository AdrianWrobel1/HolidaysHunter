import json
import re
import httpx

url = "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/egipt/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

r = httpx.get(url, headers=headers, follow_redirects=True)
html = r.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if match:
    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    initial_qs = page_props.get("initialQueryState", {})
    queries = initial_qs.get("queries", [])
    print("Queries len:", len(queries))
    for idx, q in enumerate(queries):
        query_key = q.get("queryKey")
        print(f"Query #{idx} Key:", query_key)
        state_data = q.get("state", {}).get("data")
        if isinstance(state_data, dict):
            print("  state_data top keys:", list(state_data.keys()))
            main = state_data.get("main", {})
            if isinstance(main, dict):
                print("  main top keys:", list(main.keys()))
                for k, v in main.items():
                    if isinstance(v, dict):
                        print(f"    main.{k} keys: {list(v.keys())}")
                        if "list" in v:
                            print(f"      main.{k}.list len: {len(v['list'])}")

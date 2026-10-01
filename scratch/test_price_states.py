import httpx

for st in ["Nationwide", "Goa", "Maharashtra", "Karnataka", "Madhya Pradesh"]:
    url = f"http://127.0.0.1:5000/api/price-intelligence?state={st}" if st != "Nationwide" else "http://127.0.0.1:5000/api/price-intelligence"
    r = httpx.get(url)
    data = r.json()
    items = data.get("data", [])
    print(f"State={st:15} -> Count={len(items):2} crops: {[x['crop'] for x in items]}")

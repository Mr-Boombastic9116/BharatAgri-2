import httpx
import json

r = httpx.get("http://127.0.0.1:5000/api/price-intelligence")
print("Status:", r.status_code)
data = r.json()
print("Success:", data.get("success"))
print("Count:", data.get("count"))
print("Data items:", len(data.get("data", [])))
if data.get("data"):
    print("First item:", json.dumps(data["data"][0], indent=2))

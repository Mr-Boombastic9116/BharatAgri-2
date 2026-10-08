import urllib.request, json
from datetime import date

today = date.today().isoformat()

def test_centre_apis(cid):
    print(f"\n================ Testing APIs for Centre: {cid} ================", flush=True)
    endpoints = [
        f"/api/bookings/centre/{cid}?date={today}",
        f"/api/slots?centre_id={cid}&date={today}",
        f"/api/centres/{cid}/operating-config",
        f"/api/daily-capacity?centre_id={cid}&date={today}",
        f"/api/centres/{cid}/operational-intelligence",
        f"/api/centres/{cid}/alerts",
        f"/api/centres/{cid}/insights",
        f"/api/centres/{cid}/daily-intelligence",
        f"/api/centres/{cid}/redirection-options",
        f"/api/centres/{cid}/employees",
        f"/api/queue/live/{cid}",
        f"/api/queue/congestion-forecast/{cid}"
    ]
    for ep in endpoints:
        try:
            req = urllib.request.Request(f"http://localhost:5000{ep}")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.status
                body = json.loads(resp.read().decode('utf-8'))
                if isinstance(body, list):
                    summary = f"list count={len(body)}"
                elif isinstance(body, dict):
                    keys = list(body.keys())[:3]
                    summary = f"dict keys={keys}"
                else:
                    summary = str(type(body))
                print(f"  OK {status} -> {ep.split('?')[0]} ({summary})", flush=True)
        except urllib.error.HTTPError as e:
            print(f"  FAILED {e.code} -> {ep} (Error: {e.read().decode('utf-8')[:80]})", flush=True)
        except Exception as e:
            print(f"  ERROR -> {ep}: {e}", flush=True)

test_centre_apis('C001')
test_centre_apis('C002')
test_centre_apis('PC-GOA-01')

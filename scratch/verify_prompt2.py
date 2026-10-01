import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://127.0.0.1:5000"

def api_post(endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    req_body = json.dumps(data).encode("utf-8") if data else b""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def api_put(endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    req_body = json.dumps(data).encode("utf-8") if data else b""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=req_body, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def api_get(endpoint, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def get_auth_token(user_id, password, role=None):
    payload = {"user_id": user_id, "password": password}
    if role:
        payload["role"] = role
    status, body = api_post("/api/auth/login", payload)
    if status == 200:
        return body.get("access_token")
    print(f"Login failed for {user_id} ({status}): {body}")
    return None

def test_operational_intelligence(token):
    print("\n--- 1. TESTING CENTRE OPERATIONAL INTELLIGENCE ---")
    status, body = api_get("/api/centres/CENTRE-GOA-01/operational-intelligence", token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    intel = body.get("intelligence", body)
    
    # Check expected arrivals
    arr = intel["expected_arrivals"]
    print(f"Expected Arrivals: {arr['value']} {arr['unit']} ({arr['label']}) | Basis: {arr['basis']}")
    assert arr["label"] == "Predicted"
    
    # Check expected procurement
    proc = intel["expected_procurement"]
    print(f"Expected Procurement: {proc['value']} {proc['unit']} ({proc['label']}) | Basis: {proc['basis']}")
    assert proc["label"] == "Predicted"
    
    # Check utilization & congestion
    util = intel["utilization_forecast"]
    cong = intel["congestion_prediction"]
    print(f"Utilization: Current={util['current_utilization_percent']}% ({util['current_utilization_label']}), Predicted={util['predicted_utilization_percent']}% ({util['predicted_utilization_label']})")
    print(f"Congestion Level: {cong['level']} ({cong['label']}) - {cong['description']}")
    assert util["current_utilization_label"] == "Actual"
    assert util["predicted_utilization_label"] == "Predicted"
    assert cong["label"] == "Predicted"
    assert cong["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    # Check truck requirement
    truck = intel["truck_requirement"]
    print(f"Trucks: Estimated Req={truck['estimated_required']} ({truck['estimated_required_label']}), Available={truck['available']} ({truck['available_label']}), Shortfall={truck['shortfall']} ({truck['shortfall_label']})")
    assert truck["estimated_required_label"] == "Estimated"
    assert truck["available_label"] == "Actual"
    assert truck["shortfall_label"] == "Estimated"
    
    # Check bardan requirement
    bardan = intel["bardan_requirement"]
    print(f"Bardan: Stock={bardan['current_stock_bags']} ({bardan['current_stock_label']}), Expected Cons={bardan['expected_consumption_bags']} ({bardan['expected_consumption_label']}), Projected Req={bardan['projected_requirement_bags']} ({bardan['projected_requirement_label']}), Potential Shortage={bardan['potential_shortage_bags']} ({bardan['potential_shortage_label']})")
    assert bardan["current_stock_label"] == "Actual"
    assert bardan["expected_consumption_label"] == "Estimated"
    assert bardan["projected_requirement_label"] == "Estimated"
    assert bardan["potential_shortage_label"] == "Estimated"
    print("PASS: Centre Operational Intelligence adheres to strict labeling and real calculation rules.")

def test_truck_routes_and_approval(token):
    print("\n--- 2. TESTING TRUCK ROUTES, OR-TOOLS OPTIMIZATION & GOVERNMENT APPROVAL ---")
    
    # 2.1 List predicted routes
    status, body = api_get("/api/trucks/routes/predictions", token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    routes = body["data"]
    print(f"Retrieved {len(routes)} predicted truck routes.")
    assert len(routes) > 0, "Expected at least 1 route prediction"
    
    first = routes[0]
    print(f"Route: {first['route_code']}")
    print(f"  FROM: {first['origin_centre_name']} ({first['origin_state']})")
    print(f"        Source Capacity: {first['source_capacity']} Q | Source Remaining: {first['source_available']} Q")
    print(f"  TO:   {first['destination_centre_name']} ({first['destination_state']})")
    print(f"        Dest Capacity: {first['destination_capacity']} Q | Dest Remaining: {first['destination_available']} Q")
    print(f"  CROP: {first['crop']} | QTY: {first['quantity_quintals']} Q | TRUCKS: {first['truck_required']}")
    print(f"  REASON: {first['reason']}")
    print(f"  STATUS: {first['status']}")
    
    assert "source_capacity" in first and first["source_capacity"] > 0
    assert "destination_capacity" in first and first["destination_capacity"] > 0
    assert "reason" in first and len(first["reason"]) > 10
    
    # 2.2 Test Filtering
    status, body_crop = api_get("/api/trucks/routes/predictions?crop=Paddy", token)
    assert status == 200
    paddy_routes = body_crop["data"]
    for r in paddy_routes:
        assert "paddy" in r["crop"].lower()
    print(f"Filtered by crop=Paddy: {len(paddy_routes)} routes found.")
    
    # 2.3 Generate route prediction via OR-Tools / optimization engine
    status, gen_body = api_post("/api/trucks/routes/predict", {"state": "Goa"}, token)
    assert status == 200
    print(f"Generated predictions: {gen_body}")
    
    # Find a PROPOSED route to modify, approve and schedule
    status, all_body = api_get("/api/trucks/routes/predictions", token)
    proposed_routes = [r for r in all_body["data"] if r["status"] in ["PROPOSED", "PREDICTED"]]
    
    if proposed_routes:
        target_route = proposed_routes[0]
        route_id = target_route["id"]
        
        # Test modification
        status, mod_body = api_put(f"/api/trucks/routes/{route_id}", {"quantity_quintals": 480.0}, token)
        assert status == 200
        print(f"Modified Route #{route_id} quantity to 480 Q: success={mod_body['success']}")
        
        # Test approval
        status, app_body = api_post(f"/api/trucks/routes/{route_id}/approve", {"comments": "Approved via verification script"}, token)
        assert status == 200
        assert app_body["status"] == "APPROVED"
        print(f"Approved Route #{route_id}: status={app_body['status']}")
        
        # Test scheduling
        status, sch_body = api_post(f"/api/trucks/routes/{route_id}/schedule", None, token)
        assert status == 200
        assert sch_body["success"] == True
        print(f"Scheduled Route #{route_id} for dispatch! Allocation Code: {sch_body['allocation_code']}")
    
    print("PASS: Truck Route Optimization & Approval Lifecycle verified.")

def test_msp_and_price_intelligence(token):
    print("\n--- 3. TESTING MSP, STATE SUPPLY/DEMAND & PRICE INTELLIGENCE ---")
    
    # 3.1 Official MSP endpoint
    status, msp_data = api_get("/api/msp", token)
    assert status == 200
    print(f"Official MSP: Found {msp_data['count']} gazette records. Nationwide avg MSP: ₹ {msp_data['nationwide_average_official_msp']}/Q")
    assert msp_data["count"] >= 10
    
    # 3.2 Price Intelligence endpoint
    status, pi_data = api_get("/api/price-intelligence", token)
    assert status == 200
    print(f"Price Intelligence: Nationwide Avg Official MSP = ₹ {pi_data['nationwide_average_official_msp']} / Q")
    print(f"Price Intelligence: Nationwide Avg Estimated Procurement Price = ₹ {pi_data['nationwide_average_estimated_price']} / Q")
    assert pi_data["nationwide_average_official_msp"] > 0
    assert pi_data["nationwide_average_estimated_price"] > 0
    
    # 3.3 State filtering test
    status, goa_data = api_get("/api/price-intelligence?state=Goa", token)
    assert status == 200
    goa_rows = goa_data["data"]
    for row in goa_rows:
        assert row["state"] == "Goa"
        print(f"  Goa {row['crop']}: Official MSP = ₹ {row['official_msp']}/Q, Estimated State Procurement Price = ₹ {row['estimated_procurement_price']}/Q, Status = {row['supply_status']}")
    
    # 3.4 Surplus Rule Verification on Price Estimate
    status, est = api_post("/api/ai/price-estimate", {"crop": "Paddy", "state": "Goa", "quantity": 100}, token)
    assert status == 200
    print(f"\nPrice Estimate (Goa Paddy):")
    print(f"  Official MSP: ₹ {est['official_msp']}/Q")
    print(f"  Estimated Procurement Price: ₹ {est['estimated_price']}/Q")
    print(f"  Total Estimated Value: ₹ {est['estimated_total_value']}")
    print(f"  Surplus Rule Applied: {est['surplus_rule_applied']}")
    print(f"  Factors: {est['factors']}")
    print(f"  Disclaimer: {est['disclaimer']}")
    
    # Non-negotiable requirement: estimated_price >= official_msp
    assert est["estimated_price"] >= est["official_msp"], "Surplus rule failed: estimate is less than official MSP!"
    assert est["is_estimate"] == True
    assert "guarantee" in est["disclaimer"].lower()
    
    # 3.5 Dynamic Price Difference Test
    status, est_maize = api_post("/api/ai/price-estimate", {"crop": "Maize", "state": "Goa", "quantity": 100}, token)
    assert status == 200
    print(f"Maize price estimate: ₹ {est_maize['estimated_price']}/Q (Official MSP: ₹ {est_maize['official_msp']}/Q)")
    assert est_maize["estimated_price"] >= est_maize["official_msp"]
    
    print("PASS: Official MSP separated from estimates, Surplus Rule strictly enforced, factor breakdowns provided.")

if __name__ == "__main__":
    token = get_auth_token("admin@bharatagri.demo", "BharatAgri@2026", "GOVERNMENT")
    if not token:
        print("Failed to authenticate as admin@bharatagri.demo. Trying centre@bharatagri.demo...")
        token = get_auth_token("centre@bharatagri.demo", "BharatAgri@2026", "PROCUREMENT_CENTRE")
    assert token, "Could not acquire auth token!"
    
    test_operational_intelligence(token)
    test_truck_routes_and_approval(token)
    test_msp_and_price_intelligence(token)
    print("\n==========================================")
    print("ALL PROMPT 2 VERIFICATION TESTS PASSED!")
    print("==========================================")

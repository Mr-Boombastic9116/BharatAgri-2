import httpx
import json

def test_role_flow(client, base_url, role_name, user_id, password, role_key, protected_endpoints):
    print(f"\n==========================================")
    print(f"TESTING {role_name.upper()} LOGIN FLOW ({base_url})")
    print(f"==========================================")
    
    # 1. Login Request
    payload = {
        "user_id": user_id,
        "password": password,
        "role": role_key
    }
    print(f"1. Attempting login for '{user_id}' with role='{role_key}'...")
    res = client.post(f"{base_url}/api/auth/login", json=payload)
    print(f"   Status: {res.status_code}")
    if res.status_code != 200:
        print(f"   [FAIL] Response: {res.text}")
        return False
    
    data = res.json()
    token = data.get("access_token") or data.get("token")
    user = data.get("user", {})
    print(f"   [PASS] Login successful! Token received: {token[:20]}...")
    print(f"   User Info: ID={user.get('id')}, user_id={user.get('user_id')}, role={user.get('role')}, centre_id={user.get('centre_id')}")
    
    # 2. Access Protected Endpoints
    headers = {"Authorization": f"Bearer {token}"}
    for ep in protected_endpoints:
        url = f"{base_url}{ep}"
        ep_res = client.get(url, headers=headers)
        print(f"2. Testing protected endpoint: {ep}")
        print(f"   Status: {ep_res.status_code}")
        if ep_res.status_code not in (200, 201):
            print(f"   [FAIL] Response: {ep_res.text[:200]}")
            return False
        print(f"   [PASS] Loaded data successfully: {str(ep_res.json())[:120]}...")
    
    return True

def run():
    results = {}
    
    # Test through Vite Proxy (same as frontend browser)
    print("\n>>> TESTING VIA VITE FRONTEND PROXY (http://localhost:3000) <<<")
    with httpx.Client(base_url="http://localhost:3000", timeout=15.0) as client:
        # Check Vite proxy health
        h_res = client.get("/api/health")
        assert h_res.status_code == 200, f"Vite proxy to backend failed: {h_res.status_code}"
        print("[PASS] Vite proxy connection to backend active!")
        
        # Farmer
        results["Farmer"] = test_role_flow(
            client, "http://localhost:3000", "Farmer",
            "farmer@bharatagri.demo", "BharatAgri@2026", "FARMER",
            ["/api/farmers/me", "/api/farmers/1"]
        )
        
        # Agent
        results["Agent"] = test_role_flow(
            client, "http://localhost:3000", "Agent",
            "agent@bharatagri.demo", "BharatAgri@2026", "AGENT",
            ["/api/agents/stats"]
        )
        
        # Centre
        results["Centre"] = test_role_flow(
            client, "http://localhost:3000", "Procurement Centre",
            "centre@bharatagri.demo", "BharatAgri@2026", "PROCUREMENT_CENTRE",
            ["/api/centres/CENTRE-GOA-01/operating-config"]
        )
        
        # Government
        results["Government"] = test_role_flow(
            client, "http://localhost:3000", "Government Admin",
            "admin@bharatagri.demo", "BharatAgri@2026", "GOVERNMENT",
            ["/api/government/kpis", "/api/government/centres"]
        )
        
        # Negative test: invalid password
        print("\n--- NEGATIVE TESTING: INVALID CREDENTIALS ---")
        bad_res = client.post("/api/auth/login", json={
            "user_id": "farmer@bharatagri.demo",
            "password": "WrongPassword123",
            "role": "FARMER"
        })
        print(f"Wrong password status: {bad_res.status_code} (Expected 401)")
        assert bad_res.status_code == 401, f"Expected 401, got {bad_res.status_code}"
        print(f"[PASS] Correctly rejected invalid password with: {bad_res.json()}")

    print("\n==========================================")
    print("SUMMARY RESULTS ACROSS ALL ROLES:")
    print("==========================================")
    all_pass = True
    for role, passed in results.items():
        status_str = "PASS" if passed else "FAIL"
        if not passed: all_pass = False
        print(f"  {role:<20}: {status_str}")
    print(f"\nOVERALL RESULT: {'ALL PASSED' if all_pass else 'SOME FAILED'}")

if __name__ == "__main__":
    run()

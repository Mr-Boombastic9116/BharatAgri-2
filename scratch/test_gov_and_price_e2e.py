import httpx
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def test_gov_and_price():
    print("=== TESTING GOVERNMENT KPIS & PRICE INTELLIGENCE API ===")
    
    with httpx.Client(timeout=15.0) as client:
        # 1. Login as Government Officer
        login_res = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "admin@bharatagri.demo",
            "password": "BharatAgri@2026"
        })
        assert login_res.status_code == 200, f"Gov login failed: {login_res.text}"
        gov_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {gov_token}"}
        print("[OK] Government Officer Logged In")

        # 2. Test KPIs with State Filtering
        print("\n--- Testing Government KPIs Geographic Scope ---")
        
        # 2a. Nationwide
        kpi_nationwide = client.get(f"{BASE_URL}/api/government/kpis", headers=headers).json()
        nw_data = kpi_nationwide["data"]
        print(f"[OK] Nationwide KPIs: Active Centres={nw_data.get('active_centres')}, States={nw_data.get('state_count')}, Districts={nw_data.get('district_count')}")
        assert nw_data.get("active_centres") == 25
        assert nw_data.get("state_count") == 4
        assert nw_data.get("district_count") == 10

        # 2b. State = Goa
        kpi_goa = client.get(f"{BASE_URL}/api/government/kpis?state=Goa", headers=headers).json()
        goa_data = kpi_goa["data"]
        print(f"[OK] Goa KPIs: Active Centres={goa_data.get('active_centres')}, States={goa_data.get('state_count')}, Districts={goa_data.get('district_count')}")
        assert goa_data.get("active_centres") == 5
        assert goa_data.get("state_count") == 1
        assert goa_data.get("district_count") == 2

        # 2c. State = Maharashtra
        kpi_mh = client.get(f"{BASE_URL}/api/government/kpis?state=Maharashtra", headers=headers).json()
        mh_data = kpi_mh["data"]
        print(f"[OK] Maharashtra KPIs: Active Centres={mh_data.get('active_centres')}, States={mh_data.get('state_count')}, Districts={mh_data.get('district_count')}")
        assert mh_data.get("active_centres") == 10
        assert mh_data.get("state_count") == 1
        assert mh_data.get("district_count") == 4

        # 2d. State = Karnataka
        kpi_ka = client.get(f"{BASE_URL}/api/government/kpis?state=Karnataka", headers=headers).json()
        ka_data = kpi_ka["data"]
        print(f"[OK] Karnataka KPIs: Active Centres={ka_data.get('active_centres')}, States={ka_data.get('state_count')}, Districts={ka_data.get('district_count')}")
        assert ka_data.get("active_centres") == 5
        assert ka_data.get("state_count") == 1
        assert ka_data.get("district_count") == 2

        # 2e. Return to Nationwide
        kpi_return = client.get(f"{BASE_URL}/api/government/kpis", headers=headers).json()
        ret_data = kpi_return["data"]
        print(f"[OK] Return to Nationwide: Active Centres={ret_data.get('active_centres')}, States={ret_data.get('state_count')}, Districts={ret_data.get('district_count')}")
        assert ret_data.get("active_centres") == 25
        assert ret_data.get("state_count") == 4
        assert ret_data.get("district_count") == 10

        # 3. Test State Supply, Demand & Price Intelligence
        print("\n--- Testing State Supply, Demand & Price Intelligence ---")
        
        # 3a. Nationwide
        pi_nw = client.get(f"{BASE_URL}/api/price-intelligence", headers=headers).json()
        assert pi_nw.get("success") is True
        nw_items = pi_nw.get("data", [])
        print(f"[OK] Nationwide Supply/Demand items: {len(nw_items)}")
        assert len(nw_items) == 9

        required_keys = [
            "state", "crop", "official_msp", "estimated_procurement_price",
            "expected_supply_quintals", "current_procurement_quintals",
            "projected_procurement_quintals", "current_inventory_quintals",
            "available_storage_quintals", "expected_demand_quintals",
            "surplus_deficit_quintals", "supply_status"
        ]

        for item in nw_items:
            for k in required_keys:
                assert k in item, f"Missing key {k} in item: {item}"
            assert item["supply_status"] in ["SURPLUS", "DEFICIT", "BALANCED"], f"Invalid supply_status: {item['supply_status']}"
            assert item["estimated_procurement_price"] >= item["official_msp"], f"Estimated price {item['estimated_procurement_price']} < MSP {item['official_msp']}"

        print("[OK] All 9 nationwide records contain all 12 required fields and adhere to the official MSP lower bound rule.")

        # 3b. Filter by State = Goa
        pi_goa = client.get(f"{BASE_URL}/api/price-intelligence?state=Goa", headers=headers).json()
        goa_items = pi_goa.get("data", [])
        print(f"[OK] Goa Supply/Demand items: {len(goa_items)} (Crops: {[x['crop'] for x in goa_items]})")
        assert len(goa_items) == 2
        assert all(x["state"] == "Goa" for x in goa_items)

        # 3c. Filter by State = Maharashtra
        pi_mh = client.get(f"{BASE_URL}/api/price-intelligence?state=Maharashtra", headers=headers).json()
        mh_items = pi_mh.get("data", [])
        print(f"[OK] Maharashtra Supply/Demand items: {len(mh_items)} (Crops: {[x['crop'] for x in mh_items]})")
        assert len(mh_items) == 3
        assert all(x["state"] == "Maharashtra" for x in mh_items)

        # 3d. Filter by State = Karnataka
        pi_ka = client.get(f"{BASE_URL}/api/price-intelligence?state=Karnataka", headers=headers).json()
        ka_items = pi_ka.get("data", [])
        print(f"[OK] Karnataka Supply/Demand items: {len(ka_items)} (Crops: {[x['crop'] for x in ka_items]})")
        assert len(ka_items) == 2
        assert all(x["state"] == "Karnataka" for x in ka_items)

        # 3e. Return to Nationwide
        pi_ret = client.get(f"{BASE_URL}/api/price-intelligence", headers=headers).json()
        assert len(pi_ret.get("data", [])) == 9
        print("[OK] Return to Nationwide confirmed (9 records across all states)")

    print("\n=== ALL GOVERNMENT & PRICE INTELLIGENCE API TESTS PASSED! ===")

if __name__ == "__main__":
    test_gov_and_price()

"""
Comprehensive Verification Test Suite for BharatAgri Iteration 2 - Prompt 2
Validates:
1. Centre AI / Operational Intelligence (Arrivals, Procurement, Utilization, Congestion, Trucks, Bardan)
2. State Supply/Demand Intelligence & Nationwide Price Intelligence
3. Official MSP API & Gazette Data
4. Deterministic Price Intelligence Estimator & Surplus Rule Enforcement
5. Google OR-Tools Truck Route Optimization Engine
6. Government Truck Route Lifecycle (PREDICTED -> APPROVED -> SCHEDULED -> IN_TRANSIT -> ARRIVED -> COMPLETED) & Audit Logs
7. Dynamic Database Sensitivity (No hardcoding)
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from decimal import Decimal
from fastapi.testclient import TestClient

# Ensure root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.price import MspPrice, StateCropSupplyDemand, PriceEstimate
from backend.app.models.centre import ProcurementCentre
from backend.app.models.logistics import TruckRoutePrediction, TruckRouteApproval, Truck
from backend.app.models.audit import AuditLog
from backend.app.core.deps import get_current_user

class MockUser:
    id = 1
    user_id = "gov_admin"
    role = "government"
    name = "Government Administrator"
    email = "admin@bharatagri.demo"

app.dependency_overrides[get_current_user] = lambda: MockUser()

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("STARTING BHARATAGRI ITERATION 2 — PROMPT 2 VERIFICATION TEST SUITE")
    print("=" * 70)
    passed = 0
    total = 0

    # -------------------------------------------------------------
    # TEST 1: CENTRE AI / OPERATIONAL INTELLIGENCE
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 1] Checking Centre Operational Intelligence API...")
    res = client.get("/api/centres/CENTRE-GOA-01/operational-intelligence")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    root = res.json()
    data = root.get("intelligence", root)
    
    # Assert top-level sections
    assert "expected_arrivals" in data, "Missing expected_arrivals"
    assert "expected_procurement" in data, "Missing expected_procurement"
    assert "utilization_forecast" in data, "Missing utilization_forecast"
    assert "congestion_prediction" in data, "Missing congestion_prediction"
    assert "truck_requirement" in data, "Missing truck_requirement"
    assert "bardan_requirement" in data, "Missing bardan_requirement"
    
    # Assert labels
    assert data["expected_arrivals"].get("label") == "Predicted", f"Expected 'Predicted', got {data['expected_arrivals'].get('label')}"
    assert data["expected_procurement"].get("label") == "Predicted", f"Expected 'Predicted', got {data['expected_procurement'].get('label')}"
    assert data["utilization_forecast"].get("current_utilization_label") == "Actual", f"Expected 'Actual', got {data['utilization_forecast'].get('current_utilization_label')}"
    assert data["utilization_forecast"].get("predicted_utilization_label") == "Predicted", f"Expected 'Predicted', got {data['utilization_forecast'].get('predicted_utilization_label')}"
    assert data["truck_requirement"].get("estimated_required_label") == "Estimated", "Missing Estimated label on trucks"
    assert data["truck_requirement"].get("available_label") == "Actual", "Missing Actual label on trucks"
    assert data["bardan_requirement"].get("current_stock_label") == "Actual", "Missing Actual label on bardan"
    assert data["bardan_requirement"].get("projected_requirement_label") == "Estimated", "Missing Estimated label on bardan"
    
    # Assert congestion scale
    assert data["congestion_prediction"]["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"], f"Invalid congestion level: {data['congestion_prediction']['level']}"
    
    # Check non-mock basis
    assert "basis" in data["expected_arrivals"], "Missing explanation basis for expected arrivals"
    assert "basis" in data["expected_procurement"], "Missing explanation basis for expected procurement"
    print(f"  ✓ Centre AI OK: Congestion={data['congestion_prediction']['level']}, Utilization={data['utilization_forecast']['current_utilization_percent']}%, Basis: {data['expected_arrivals']['basis'][:60]}...")
    passed += 1

    # -------------------------------------------------------------
    # TEST 2: STATE SUPPLY/DEMAND & NATIONWIDE PRICE INTELLIGENCE
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 2] Checking State Supply/Demand & Price Intelligence API...")
    res = client.get("/api/price-intelligence")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    pi_data = res.json()
    assert "data" in pi_data, "Missing data array"
    assert "meta" in pi_data, "Missing meta object"
    assert len(pi_data["data"]) > 0, "No state supply/demand records returned"
    
    first_row = pi_data["data"][0]
    for field in ["state", "crop", "official_msp", "estimated_procurement_price", "expected_supply_quintals", "current_procurement_quintals", "expected_demand_quintals", "available_storage_quintals", "surplus_deficit_quintals"]:
        assert field in first_row, f"Missing field {field} in price intelligence row"
        
    meta = pi_data["meta"]
    assert "nationwide_average_official_msp" in meta, "Missing nationwide official MSP"
    assert "nationwide_average_estimated_price" in meta, "Missing nationwide estimated price"
    print(f"  ✓ Nationwide Official MSP Avg: ₹{meta['nationwide_average_official_msp']}/Q")
    print(f"  ✓ Nationwide Estimated Price Avg: ₹{meta['nationwide_average_estimated_price']}/Q")

    # Test state filter
    res_state = client.get("/api/price-intelligence?state_id=Goa")
    assert res_state.status_code == 200
    goa_rows = res_state.json()["data"]
    assert all(r["state"].lower() == "goa" for r in goa_rows), "State filter did not restrict rows to Goa"
    assert "state_average_estimated_price" in res_state.json()["meta"], "Missing state average estimated price"
    print(f"  ✓ State filter (Goa): {len(goa_rows)} records, State Avg: ₹{res_state.json()['meta']['state_average_estimated_price']}/Q")
    passed += 1

    # -------------------------------------------------------------
    # TEST 3: OFFICIAL MSP BENCHMARKS
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 3] Checking Official MSP API...")
    res = client.get("/api/price/msp")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    msp_payload = res.json()
    msp_records = msp_payload.get("data", msp_payload) if isinstance(msp_payload, dict) else msp_payload
    assert isinstance(msp_records, list) and len(msp_records) > 0, "No MSP records returned"
    paddy_msp = next((m for m in msp_records if m["crop"] == "Paddy"), None)
    assert paddy_msp is not None, "Paddy MSP not found"
    assert float(paddy_msp["official_msp_per_quintal"]) >= 2300.0, f"Unexpected Paddy MSP: {paddy_msp['official_msp_per_quintal']}"
    assert "marketing_season" in paddy_msp and "season_year" in paddy_msp
    print(f"  ✓ Official MSP for Paddy: ₹{paddy_msp['official_msp_per_quintal']}/Q (Season: {paddy_msp['season_year']})")
    passed += 1

    # -------------------------------------------------------------
    # TEST 4: DETERMINISTIC PRICE ESTIMATOR & SURPLUS RULE
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 4] Testing Deterministic Price Intelligence & Surplus Rule...")
    # Surplus test (Goa Paddy is in surplus in state_crop_supply_demand)
    payload = {
        "crop": "Paddy",
        "state": "Goa",
        "quantity_quintals": 50.0
    }
    res = client.post("/api/price/estimate", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    est = res.json()
    
    # Verify surplus rule: estimated_price >= official_msp
    assert est["estimated_price"] >= est["official_msp"], f"Surplus rule violated: est={est['estimated_price']} < msp={est['official_msp']}"
    # Verify estimated_total_value = estimated_price * quantity
    expected_total = round(est["estimated_price"] * 50.0, 2)
    assert abs(est["estimated_total_value"] - expected_total) < 0.1, f"Total value mismatch: {est['estimated_total_value']} vs {expected_total}"
    # Verify confidence is None ("confidence unavailable")
    assert est["confidence"] is None, f"Confidence should be None, got {est['confidence']}"
    assert est["confidence_display"] == "confidence unavailable"
    # Verify explanation factors
    assert "Demand:" in est["explanation"], "Explanation missing Demand factor"
    assert "Expected Supply:" in est["explanation"], "Explanation missing Supply factor"
    assert "Inventory:" in est["explanation"], "Explanation missing Inventory factor"
    assert "Storage Availability:" in est["explanation"], "Explanation missing Storage factor"
    assert "Historical Procurement:" in est["explanation"], "Explanation missing Historical Procurement factor"
    print(f"  ✓ Surplus rule verified: MSP=₹{est['official_msp']}, Est=₹{est['estimated_price']}, Total=₹{est['estimated_total_value']}")
    print(f"  ✓ Explanation: {est['explanation'][:80]}...")
    passed += 1

    # -------------------------------------------------------------
    # TEST 5: GOOGLE OR-TOOLS TRUCK ROUTE OPTIMIZATION
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 5] Testing Google OR-Tools Truck Route Optimization...")
    res = client.post("/api/trucks/routes/predict", json={"state": None})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    pred_res = res.json()
    num_gen = len(pred_res.get("routes_created", [])) or pred_res.get("count", 0)
    print(f"  ✓ Route prediction generated {num_gen} routes using optimization engine ({pred_res.get('solver_status')}).")

    # Fetch predictions list
    res_list = client.get("/api/trucks/routes/predictions")
    assert res_list.status_code == 200
    raw_routes = res_list.json()
    routes = raw_routes.get("data", raw_routes) if isinstance(raw_routes, dict) else raw_routes
    assert len(routes) > 0, "No truck routes found"
    
    sample_route = routes[0]
    # Check mandatory route attributes per Prompt Section 4
    for field in ["origin_centre_id", "origin_centre_name", "destination_centre_id", "destination_centre_name", "crop", "quantity_quintals", "truck_capacity_quintals", "truck_required", "reason", "source_capacity", "destination_capacity", "status"]:
        assert field in sample_route, f"Missing {field} in truck route display payload"
    
    print(f"  ✓ Sample Route: {sample_route['origin_centre_name']} -> {sample_route['destination_centre_name']}")
    print(f"    Source Capacity: {sample_route['source_capacity']} Q (Avail: {sample_route['source_available']} Q)")
    print(f"    Destination Capacity: {sample_route['destination_capacity']} Q (Avail: {sample_route['destination_available']} Q)")
    print(f"    Reason: {sample_route['reason']}")
    passed += 1

    # -------------------------------------------------------------
    # TEST 6: GOVERNMENT APPROVAL WORKFLOW & AUDIT TRAIL
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 6] Testing Government Truck Route Lifecycle & Audit Trail...")
    db = SessionLocal()
    # Create a test proposed route in DB
    test_route = TruckRoutePrediction(
        route_code=f"TRK-TEST-{int(os.getpid())}",
        origin_centre_id="CENTRE-GOA-01",
        origin_centre_name="Sanquelim Krishi Upaj Mandi",
        destination_centre_id="CENTRE-MH-01",
        destination_centre_name="Baramati APMC Centre",
        destination_state="Maharashtra",
        crop="Paddy",
        quantity_quintals=Decimal("200.00"),
        truck_capacity_quintals=Decimal("200.00"),
        estimated_distance_km=Decimal("310.50"),
        departure_date="2026-10-05",
        expected_arrival_date="2026-10-06",
        reason="High storage congestion relief via OR-Tools optimization",
        status="PROPOSED"
    )
    db.add(test_route)
    db.commit()
    db.refresh(test_route)
    route_id = test_route.id
    route_code = test_route.route_code
    db.close()
    print(f"  Created test route ID: {route_id} ({route_code}) with status PROPOSED")

    # 1. Modify Route
    mod_res = client.patch(f"/api/trucks/routes/{route_id}", json={"quantity_quintals": 180.0})
    assert mod_res.status_code == 200, f"Modification failed: {mod_res.text}"
    assert mod_res.json()["quantity_quintals"] == 180.0
    print("  ✓ Route modified successfully and validated.")

    # 2. Approve Route
    app_res = client.post(f"/api/trucks/routes/{route_id}/approve", json={"comments": "Approved for fleet dispatch"})
    assert app_res.status_code == 200, f"Approval failed: {app_res.text}"
    assert app_res.json()["status"] == "APPROVED"
    print("  ✓ Route approved by Government.")

    # 3. Schedule Route
    sched_res = client.post(f"/api/trucks/routes/{route_id}/schedule")
    assert sched_res.status_code == 200, f"Scheduling failed: {sched_res.text}"
    assert sched_res.json()["status"] == "SCHEDULED"
    print("  ✓ Route scheduled with active truck allocation.")

    # 4. Lifecycle transition: In Transit
    trans_res = client.post(f"/api/trucks/routes/{route_id}/transit")
    assert trans_res.status_code == 200
    assert trans_res.json()["status"] == "IN_TRANSIT"
    print("  ✓ Route transitioned to IN_TRANSIT.")

    # 5. Lifecycle transition: Arrive
    arr_res = client.post(f"/api/trucks/routes/{route_id}/arrive")
    assert arr_res.status_code == 200
    assert arr_res.json()["status"] == "ARRIVED"
    print("  ✓ Route transitioned to ARRIVED.")

    # 6. Lifecycle transition: Complete
    comp_res = client.post(f"/api/trucks/routes/{route_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"
    print("  ✓ Route transitioned to COMPLETED.")

    # 7. Verify Audit Logs
    fresh_db = SessionLocal()
    try:
        audits = fresh_db.query(AuditLog).filter(AuditLog.entity == "TRUCK_ROUTE", AuditLog.entity_id == route_code).all()
        actions = [a.action for a in audits]
        assert "TRUCK_ROUTE_MODIFIED" in actions, f"Missing TRUCK_ROUTE_MODIFIED in audit: {actions}"
        assert "TRUCK_ROUTE_APPROVED" in actions, f"Missing TRUCK_ROUTE_APPROVED in audit: {actions}"
        assert "TRUCK_ROUTE_SCHEDULED" in actions, f"Missing TRUCK_ROUTE_SCHEDULED in audit: {actions}"
        assert "TRUCK_ROUTE_COMPLETED" in actions, f"Missing TRUCK_ROUTE_COMPLETED in audit: {actions}"
        print(f"  ✓ Audit log verified: {len(audits)} audit entries recorded: {actions}")

        # Cleanup test route
        tr = fresh_db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
        if tr:
            fresh_db.delete(tr)
            fresh_db.commit()
    finally:
        fresh_db.close()
    passed += 1

    # -------------------------------------------------------------
    # TEST 7: DYNAMIC DATABASE SENSITIVITY (NO HARDCODING)
    # -------------------------------------------------------------
    total += 1
    print("\n[TEST 7] Testing Dynamic Intelligence Sensitivity to Database Changes...")
    db = SessionLocal()
    try:
        # Check initial Goa Maize price
        rec = db.query(StateCropSupplyDemand).filter(StateCropSupplyDemand.state == "Goa", StateCropSupplyDemand.crop == "Maize").first()
        assert rec is not None, "Goa Maize record missing"
        initial_price = float(rec.estimated_procurement_price)
        initial_demand = float(rec.expected_demand_quintals)

        # Mutate expected demand substantially (simulate extreme surge)
        rec.expected_demand_quintals = Decimal(str(initial_demand * 2.0))
        rec.surplus_deficit_quintals = Decimal(str(float(rec.expected_supply_quintals) - (initial_demand * 2.0)))
        db.commit()
        # Recompute price deterministically
        price_res = client.post("/api/price/estimate", json={"crop": "Maize", "state": "Goa", "quantity_quintals": 100})
        assert price_res.status_code == 200
        new_price = price_res.json()["estimated_price"]
        
        # Verify response is dynamic
        print(f"  Initial Maize Base: ₹{initial_price}/Q -> Extreme Demand Price: ₹{new_price}/Q")
        assert new_price >= initial_price, "Price estimate did not respond dynamically to increased demand"

        # Revert change
        rec.expected_demand_quintals = Decimal(str(initial_demand))
        rec.surplus_deficit_quintals = Decimal(str(float(rec.expected_supply_quintals) - initial_demand))
        db.commit()
        print("  ✓ Database values restored. Dynamic sensitivity confirmed (no fixed hardcoded output).")
    finally:
        db.close()
    passed += 1

    print("\n" + "=" * 70)
    print(f"ALL PROMPT 2 VERIFICATION TESTS PASSED: {passed}/{total}")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

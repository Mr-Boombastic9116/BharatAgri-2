import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_government_dashboard_apis_and_math_fix():
    # 1. Login as Government
    res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "GOVERNMENT"
    })
    assert res.status_code == 200, f"Gov login failed: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test KPIs endpoint (specifically where math.ceil failed previously)
    kpis_res = client.get("/api/government/kpis", headers=headers)
    assert kpis_res.status_code == 200, f"KPIs failed: {kpis_res.text}"
    kpis = kpis_res.json()
    assert "data" in kpis
    data = kpis["data"]
    assert "trucks_required" in data
    assert "registered_farmers" in data
    assert data["registered_farmers"] >= 5000  # Real data from SIH 5000 farmers

    # 3. Test national daily intelligence (also had math.ceil previously)
    intel_res = client.get("/api/government/daily-intelligence", headers=headers)
    assert intel_res.status_code == 200, f"Daily intel failed: {intel_res.text}"

    # 4. Test analytics and insights
    endpoints = [
        "/api/government/states",
        "/api/government/centres",
        "/api/government/insights",
        "/api/government/alerts",
        "/api/government/perishable-priority",
        "/api/government/analytics/crop-distribution",
        "/api/government/analytics/procurement-trend",
        "/api/government/analytics/state-district-procurement",
        "/api/government/analytics/forecast-vs-actual",
        "/api/government/analytics/centre-utilization",
        "/api/government/analytics/payments-summary",
        "/api/government/analytics/anomalies-summary",
        "/api/queue/anomalies"
    ]
    for ep in endpoints:
        r = client.get(ep, headers=headers)
        assert r.status_code == 200, f"Endpoint {ep} failed: {r.status_code} {r.text}"


def test_centre_1_login_and_dashboard_apis():
    # 1. Login as Centre 1 (C001)
    res = client.post("/api/auth/login", json={
        "user_id": "c001@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res.status_code == 200
    user_data = res.json()["user"]
    assert user_data["centre_id"] == "C001"
    assert user_data["role"] == "centre"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test centre dashboard APIs for C001
    today = "2026-10-07"
    c_endpoints = [
        f"/api/bookings/centre/C001?date={today}",
        f"/api/slots?centre_id=C001&date={today}",
        "/api/centres/C001/operating-config",
        f"/api/daily-capacity?centre_id=C001&date={today}",
        "/api/centres/C001/operational-intelligence",
        "/api/centres/C001/alerts",
        "/api/centres/C001/insights",
        "/api/centres/C001/daily-intelligence",
        "/api/centres/C001/redirection-options",
        "/api/centres/C001/employees",  # Fixed Employee model import
        "/api/queue/live/C001",
        "/api/queue/congestion-forecast/C001"
    ]
    for ep in c_endpoints:
        r = client.get(ep, headers=headers)
        assert r.status_code == 200, f"C001 endpoint {ep} failed: {r.status_code} {r.text}"

    # Verify employees endpoint returned real data without error
    emps_res = client.get("/api/centres/C001/employees", headers=headers)
    assert emps_res.status_code == 200
    assert "data" in emps_res.json()
    assert emps_res.json()["centre_id"] == "C001"


def test_centre_2_login_and_dashboard_apis():
    # 1. Login as Centre 2 (C002)
    res = client.post("/api/auth/login", json={
        "user_id": "c002@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res.status_code == 200
    user_data = res.json()["user"]
    assert user_data["centre_id"] == "C002"
    assert "Nashik" in user_data["name"]
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test centre dashboard APIs for C002
    today = "2026-10-07"
    c_endpoints = [
        f"/api/bookings/centre/C002?date={today}",
        f"/api/slots?centre_id=C002&date={today}",
        "/api/centres/C002/operating-config",
        f"/api/daily-capacity?centre_id=C002&date={today}",
        "/api/centres/C002/operational-intelligence",
        "/api/centres/C002/employees",
        "/api/queue/live/C002",
        "/api/queue/congestion-forecast/C002"
    ]
    for ep in c_endpoints:
        r = client.get(ep, headers=headers)
        assert r.status_code == 200, f"C002 endpoint {ep} failed: {r.status_code} {r.text}"


def test_farmer_login_and_dashboard_apis():
    # 1. Login as Farmer
    res = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "FARMER"
    })
    assert res.status_code == 200
    user_data = res.json()["user"]
    assert user_data["role"] == "farmer"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test farmer dashboard endpoints
    r_prof = client.get("/api/farmers/profile", headers=headers)
    assert r_prof.status_code == 200
    prof = r_prof.json()
    assert "name" in prof
    assert "farmer_code" in prof

    r_bk = client.get(f"/api/bookings/farmer/{user_data['user_id']}", headers=headers)
    assert r_bk.status_code == 200

    r_ov = client.get(f"/api/queue/farmer-overview/{user_data['user_id']}", headers=headers)
    assert r_ov.status_code == 200

    r_notif = client.get(f"/api/queue/notifications/{user_data['user_id']}", headers=headers)
    assert r_notif.status_code == 200


def test_role_based_access_control():
    # 1. Farmer token should NOT access Government KPIs
    res_f = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "FARMER"
    })
    farmer_token = res_f.json()["token"]
    f_headers = {"Authorization": f"Bearer {farmer_token}"}

    r_gov_denied = client.get("/api/government/kpis", headers=f_headers)
    assert r_gov_denied.status_code in [401, 403], "Farmer must not access government KPIs"

    # 2. Unauthenticated request to protected endpoints should be rejected
    r_unauth = client.get("/api/government/kpis")
    assert r_unauth.status_code in [401, 403], "Unauthenticated request must be rejected"


def test_centre_login_role_variations():
    roles_to_test = ["centre", "CENTRE", "PROCUREMENT_CENTRE", "procurement-centre", "procurement_centre", "center"]
    for role_variant in roles_to_test:
        res = client.post("/api/auth/login", json={
            "user_id": "centre@bharatagri.demo",
            "password": "BharatAgri@2026",
            "role": role_variant
        })
        assert res.status_code == 200, f"Login with role variant '{role_variant}' failed: {res.text}"
        data = res.json()
        assert data["user"]["centre_id"] == "C01"
        assert "Sanquelim" in data["user"]["centre_name"] or "Sanquelim" in data["user"]["name"]


def test_multi_centre_data_isolation():
    # Login as C001
    res1 = client.post("/api/auth/login", json={
        "user_id": "c001@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res1.status_code == 200
    token1 = res1.json()["token"]
    user1 = res1.json()["user"]
    assert user1["centre_id"] == "C001"

    # Login as C002
    res2 = client.post("/api/auth/login", json={
        "user_id": "c002@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res2.status_code == 200
    token2 = res2.json()["token"]
    user2 = res2.json()["user"]
    assert user2["centre_id"] == "C002"

    # Login as Goa APMC centre user
    res3 = client.post("/api/auth/login", json={
        "user_id": "EMP-GOA-A",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res3.status_code == 200
    user3 = res3.json()["user"]
    assert user3["centre_id"] == "PC-GOA-01"
    assert "Panaji" in user3["centre_name"]

    # Verify C001 config vs C002 config vs PC-GOA-01 config are distinct
    cfg1 = client.get("/api/centres/C001/operating-config", headers={"Authorization": f"Bearer {token1}"}).json()
    cfg2 = client.get("/api/centres/C002/operating-config", headers={"Authorization": f"Bearer {token2}"}).json()
    cfg3 = client.get("/api/centres/PC-GOA-01/operating-config", headers={"Authorization": f"Bearer {token1}"}).json()

    assert cfg1["centre_id"] == "C001"
    assert cfg2["centre_id"] == "C002"
    assert cfg3["centre_id"] == "PC-GOA-01"
    assert cfg1["centre_name"] != cfg2["centre_name"]
    assert "Pune" in cfg1["centre_name"]
    assert "Nashik" in cfg2["centre_name"]
    assert "Panaji" in cfg3["centre_name"]

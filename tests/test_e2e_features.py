import os
import sys
import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("."))
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.logistics import Truck, TruckRequest
from backend.app.models.alert import Alert

client = TestClient(app)


@pytest.fixture(scope="module")
def gov_auth_headers():
    res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "GOVERNMENT"
    })
    assert res.status_code == 200, f"Gov login failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def centre_auth_headers():
    res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res.status_code == 200, f"Centre login failed: {res.text}"
    user = res.json()["user"]
    assert user["centre_id"] == "C01"
    assert "Sanquelim" in user["centre_name"]
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dbt_payout_status_analytics(gov_auth_headers):
    dbt_res = client.get("/api/government/analytics/payments-summary", headers=gov_auth_headers)
    assert dbt_res.status_code == 200, f"DBT summary failed: {dbt_res.text}"
    dbt_json = dbt_res.json()
    assert dbt_json.get("success") is True
    assert "data" in dbt_json
    assert len(dbt_json["data"]) > 0
    statuses = [item["status"] for item in dbt_json["data"]]
    assert "Paid / Completed" in statuses


def test_truck_request_accept_and_notify_workflow(gov_auth_headers, centre_auth_headers):
    db = SessionLocal()
    # Ensure at least one truck is available for allocation in testing
    test_truck = db.query(Truck).filter(Truck.assigned_centre_id == "C01").first()
    if not test_truck:
        test_truck = db.query(Truck).first()
    if test_truck:
        test_truck.is_available = True
        test_truck.current_status = "IDLE"
        db.commit()

    req = TruckRequest(
        request_code=f"TRQ-TEST-{uuid.uuid4().hex[:6].upper()}",
        centre_id="C01",
        required_date=date.today(),
        required_capacity_quintals=180.0,
        reason="Dispatch accumulated Grade-A Mangoes to cold storage",
        status="PENDING"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    req_code = req.request_code
    db.close()

    # Government accepts and notifies centre
    accept_res = client.post(f"/api/trucks/requests/{req_code}/accept-and-notify", headers=gov_auth_headers)
    assert accept_res.status_code == 200, f"Accept failed: {accept_res.text}"
    accept_data = accept_res.json()
    assert accept_data.get("success") is True
    assert accept_data["data"]["status"] == "ACCEPTED"
    assert "truck_number" in accept_data["data"]

    # Duplicate acceptance prevented
    dup_res = client.post(f"/api/trucks/requests/{req_code}/accept-and-notify", headers=gov_auth_headers)
    assert dup_res.status_code == 400

    # Destination centre receives alert
    alerts_res = client.get("/api/centres/C01/alerts", headers=centre_auth_headers)
    assert alerts_res.status_code == 200
    alerts_list = alerts_res.json().get("alerts", [])
    dispatch_alerts = [a for a in alerts_list if "DISPATCH" in str(a.get("alert_type", "")) or "Truck" in str(a.get("what", ""))]
    assert len(dispatch_alerts) > 0


def test_government_copilot_queries(gov_auth_headers):
    queries_to_test = [
        ("How is C01 performing?", "C01"),
        ("How many farmers are waiting at C01?", "waiting"),
        ("How are centres in Goa performing?", "Goa"),
        ("Which centre has the highest queue?", "queue"),
        ("How is C99 performing?", "not found")
    ]
    for q, expected_substr in queries_to_test:
        copilot_res = client.post("/api/queue/copilot", json={"query": q}, headers=gov_auth_headers)
        assert copilot_res.status_code == 200, f"Copilot query '{q}' failed: {copilot_res.text}"
        ans = copilot_res.json().get("answer", "")
        assert expected_substr.lower() in ans.lower(), f"Expected '{expected_substr}' in answer: {ans}"


def test_centre_copilot_scoping_and_cross_centre_protection(centre_auth_headers):
    # Authenticated centre C01 querying own centre
    res = client.post("/api/centres/C01/copilot", json={"query": "How is my centre performing?"}, headers=centre_auth_headers)
    assert res.status_code == 200, f"Centre copilot failed: {res.text}"
    ans = res.json().get("answer", "")
    assert "Sanquelim" in ans or "C01" in ans

    # Cross-centre query blocked with 403 Forbidden
    cross_res = client.post("/api/centres/C02/copilot", json={"query": "How is C02 performing?"}, headers=centre_auth_headers)
    assert cross_res.status_code == 403

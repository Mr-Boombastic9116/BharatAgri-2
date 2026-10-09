import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.centre import ProcurementCentre
from backend.app.services.copilot_engine import parse_structured_copilot_query, execute_structured_copilot_plan

client = TestClient(app)

@pytest.fixture
def gov_headers():
    res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "GOVERNMENT"
    })
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def centre_c01_headers():
    res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "CENTRE"
    })
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_copilot_single_condition(gov_headers):
    # Single condition
    res = client.post("/api/queue/copilot", json={"query": "How much was procured?"}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    assert "procurement reached" in data["answer"].lower() or "procured" in data["answer"].lower()

def test_copilot_two_conditions(gov_headers):
    # Two conditions: Crop + Time
    res = client.post("/api/queue/copilot", json={"query": "How much mango was procured yesterday?"}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "mango" in ans
    assert "yesterday" in ans
    # Check debug info
    debug = data.get("debug_info", {})
    assert debug.get("detected_entities", {}).get("crop") == "Mango"
    assert debug.get("detected_time", {}).get("label") == "yesterday"

def test_copilot_three_conditions(gov_headers):
    # Three conditions: Crop + Centre + Time
    res = client.post("/api/queue/copilot", json={"query": "How much mango was procured at C01 yesterday?"}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "sanquelim" in ans or "c01" in ans
    assert "mango" in ans
    assert "yesterday" in ans
    debug = data.get("debug_info", {})
    assert debug.get("applied_filters", {}).get("crop") == "Mango"
    assert debug.get("applied_filters", {}).get("centre_id") == "C01"

def test_copilot_four_conditions(gov_headers):
    # Four conditions: Crop + Centre + State + Time
    res = client.post("/api/queue/copilot", json={"query": "How much mango was procured at C01 in Goa yesterday?"}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "sanquelim" in ans or "c01" in ans
    assert "mango" in ans
    assert "yesterday" in ans
    debug = data.get("debug_info", {})
    assert debug.get("detected_entities", {}).get("state") == "Goa"

def test_copilot_multiple_operations(gov_headers):
    # Multiple operations: Count farmers + Procurement quantity + Pending payments
    q = "How many mango farmers visited C01 yesterday, how much did they procure, and how many payments are pending?"
    res = client.post("/api/queue/copilot", json={"query": q}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "mango" in ans
    assert "quintals" in ans
    assert "appointment" in ans or "visit" in ans
    assert "payment" in ans

def test_copilot_comparison(gov_headers):
    # Multi-period comparison
    res = client.post("/api/queue/copilot", json={"query": "Compare mango procurement at C01 this week and last week."}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "this week" in ans
    assert "last week" in ans
    assert "quintals" in ans

def test_copilot_cause_analysis(gov_headers):
    # Cause analysis
    res = client.post("/api/queue/copilot", json={"query": "Why was the mango queue high at C01 yesterday?"}, headers=gov_headers)
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "elevated" in ans or "primarily due to" in ans
    assert "maintenance" in ans or "downtime" in ans or "arrivals" in ans

def test_centre_copilot_enforcement_and_isolation(centre_c01_headers):
    # Query without typing centre name
    res = client.post("/api/centres/C01/copilot", json={"query": "How much mango did we procure yesterday?"}, headers=centre_c01_headers)
    assert res.status_code == 200
    ans = res.json()["answer"].lower()
    assert "mango" in ans
    assert "yesterday" in ans
    assert "sanquelim" in ans or "c01" in ans

    # Cross centre attempt is cleanly scoped or blocked
    cross_res = client.post("/api/centres/C01/copilot", json={"query": "How is C02 doing?"}, headers=centre_c01_headers)
    assert cross_res.status_code == 200
    cross_ans = cross_res.json()["answer"]
    assert "strictly scoped" in cross_ans or "policies" in cross_ans or "cannot be queried" in cross_ans

import sys
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_queue_endpoints():
    r1 = client.get('/api/queue/live/C001')
    assert r1.status_code == 200, f"r1 failed: {r1.text}"
    data1 = r1.json()['data']
    print("Live Queue C001: OK, queue_len=", data1['queue_length'], "est_wait=", data1['estimated_wait_min'])

    r2 = client.get('/api/queue/token/A000001')
    assert r2.status_code == 200, f"r2 failed: {r2.text}"
    data2 = r2.json()['data']
    print("Token A000001: OK, token=", data2['token_number'], "wait=", data2['estimated_wait_min'], "dep=", data2['recommended_departure_time'])

    r3 = client.post('/api/queue/recommend-centre', json={'crop': 'Cotton', 'quantity': 60, 'district': 'Pune'})
    assert r3.status_code == 200, f"r3 failed: {r3.text}"
    data3 = r3.json()
    print("Recommend Centre: OK, best=", data3['best_centre']['centre_name'])

    r4 = client.get('/api/queue/congestion-forecast/C001')
    assert r4.status_code == 200, f"r4 failed: {r4.text}"
    data4 = r4.json()['data']
    print("Congestion Forecast: OK, hourly_points=", len(data4['hourly_forecast']))

    r5 = client.post('/api/queue/copilot', json={'query': 'Why is Centre C004 experiencing delays?'})
    assert r5.status_code == 200, f"r5 failed: {r5.text}"
    data5 = r5.json()['data']
    print("Copilot: OK")

    r6 = client.get('/api/queue/anomalies')
    assert r6.status_code == 200, f"r6 failed: {r6.text}"
    data6 = r6.json()
    print("Anomalies: OK, count=", data6['total_anomalies'])

    r7 = client.get('/api/queue/farmer-overview/F00001')
    assert r7.status_code == 200, f"r7 failed: {r7.text}"
    data7 = r7.json()
    print("Farmer Overview: OK, has_token=", data7['has_active_token'])

    r8 = client.get('/api/queue/crops-master')
    assert r8.status_code == 200, f"r8 failed: {r8.text}"
    data8 = r8.json()
    print("Crops Master: OK, count=", data8['total_crops'])

    print("\nALL QUEUE API TESTS PASSED!")

if __name__ == '__main__':
    test_queue_endpoints()

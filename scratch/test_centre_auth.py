import urllib.request, json

def test_login(uid, role):
    req = urllib.request.Request(
        'http://localhost:5000/api/auth/login',
        data=json.dumps({'user_id': uid, 'password': 'BharatAgri@2026', 'role': role}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"{uid} -> user_id: {data['user']['user_id']}, role: {data['user']['role']}, centre_id: {data['user']['centre_id']}, centre_name: {data['user']['centre_name']}")

print("--- Testing Centre Logins ---")
test_login('centre@bharatagri.demo', 'CENTRE')
test_login('centre@bharatagri.demo', 'PROCUREMENT_CENTRE')
test_login('c002@bharatagri.demo', 'CENTRE')
test_login('EMP-GOA-A', 'CENTRE')

with open('frontend/src/pages/GovernmentDashboard.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "activeTab === 'anomalies'" in line or "activeTab === 'insights'" in line:
        print(f"Line {i+1}: {line.strip()}")

with open('frontend/src/pages/CentreDashboard.jsx', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if "activeTab === 'overview'" in line or "activeTab === 'insights'" in line:
            print(f"Line {i+1}: {line.strip()}")

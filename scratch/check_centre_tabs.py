import re
with open('frontend/src/pages/CentreDashboard.jsx', 'r', encoding='utf-8') as f:
    text = f.read()
tabs = re.findall(r"activeTab === '([^']+)'", text)
print('Tabs in CentreDashboard:', set(tabs))

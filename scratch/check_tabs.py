import re
with open('frontend/src/pages/GovernmentDashboard.jsx', 'r', encoding='utf-8') as f:
    text = f.read()
tabs = re.findall(r"activeTab === '([^']+)'", text)
print('Tabs found in GovernmentDashboard:', set(tabs))

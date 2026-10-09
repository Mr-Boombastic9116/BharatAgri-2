import re
from pathlib import Path

api_js = Path('frontend/src/services/api.js')
content = api_js.read_text(encoding='utf-8')

# Find all fetch calls
matches = re.findall(r'fetch\(\s*[`\'"]([^`\'"]+)[`\'"]', content)
print(f"Total fetch calls in frontend/src/services/api.js: {len(matches)}")

# Also look for any fetch calls across all frontend files
frontend_dir = Path('frontend/src')
all_fetches = []
for p in frontend_dir.glob('**/*.jsx'):
    txt = p.read_text(encoding='utf-8')
    m = re.findall(r'fetch\(\s*[`\'"]([^`\'"]+)[`\'"]', txt)
    if m:
        all_fetches.extend([(p.name, x) for x in m])
for p in frontend_dir.glob('**/*.js'):
    txt = p.read_text(encoding='utf-8')
    m = re.findall(r'fetch\(\s*[`\'"]([^`\'"]+)[`\'"]', txt)
    if m:
        all_fetches.extend([(p.name, x) for x in m])

print(f"\nTotal fetch calls across all frontend files: {len(all_fetches)}")
for fn, url in sorted(all_fetches):
    print(f"  [{fn:25}] {url}")

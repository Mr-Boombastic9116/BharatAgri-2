import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.abspath('.'))
from backend.app.main import app

openapi_paths = set(app.openapi()['paths'].keys())

api_js = Path('frontend/src/services/api.js').read_text(encoding='utf-8')
lines = api_js.split('\n')

print(f"Total OpenAPI Paths in Backend: {len(openapi_paths)}")

mismatches = []
checked = 0

for idx, line in enumerate(lines, 1):
    m = re.search(r'fetch\(\s*[`\'"]([^`\'"]+)[`\'"]', line)
    if m:
        raw_url = m.group(1)
        # normalize template string ${API_BASE} to /api
        url = raw_url.replace('${API_BASE}', '/api')
        # remove query string
        url_no_query = url.split('?')[0].split('${')[0]
        # normalize dynamic params like ${encodeURIComponent(farmerId)} or ${id}
        # e.g. /api/farmers/${encodeURIComponent(farmerId)} -> /api/farmers/{id}
        norm = re.sub(r'\$\{[^}]+\}', '{param}', url.split('?')[0])
        # match against openapi paths
        # Convert openapi path {foo} to regex [^/]+
        matched = False
        for op in openapi_paths:
            pattern = '^' + re.sub(r'\{[^}]+\}', r'[^/]+', op) + '$'
            test_url = re.sub(r'\$\{[^}]+\}', 'dummy', url.split('?')[0])
            if re.match(pattern, test_url):
                matched = True
                break
        
        checked += 1
        if not matched:
            mismatches.append((idx, line.strip(), raw_url, url.split('?')[0]))

print(f"Checked {checked} frontend fetch calls.")
print(f"Mismatches found: {len(mismatches)}")
for line_no, raw_line, raw_url, cleaned in mismatches:
    print(f"  Line {line_no}: {cleaned}")
    print(f"    Raw: {raw_url}")

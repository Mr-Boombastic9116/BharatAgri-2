from pathlib import Path
import re

pages_dir = Path('frontend/src/pages')
for p in sorted(pages_dir.glob('*.jsx')):
    txt = p.read_text(encoding='utf-8')
    # find imports from ../services/api
    imports = re.findall(r'import\s+\{([^}]+)\}\s+from\s+[\'\"]\.\./services/api[\'\"]', txt)
    if imports:
        imported_funcs = [f.strip() for f in imports[0].split(',') if f.strip()]
        print(f"\nPage: {p.name} ({len(imported_funcs)} api funcs)")
        print("  " + ", ".join(imported_funcs))

with open('backend/app/api/procurement.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'@router\.(?:get|post|put|delete)\((.*?)\)\s+(?:async\s+)?def\s+(\w+)', text, re.DOTALL)
for m in matches:
    route_arg = m.group(1).split(',')[0].strip()
    fn_name = m.group(2)
    print(f'{route_arg} -> {fn_name}')

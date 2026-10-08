with open('database/bharatagri_iteration2.sql', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

pos = text.find('INSERT INTO alerts')
end = text.find(';', pos)
alerts_insert = text[pos:end+1]
import re
codes = re.findall(r"'ALT-[^']+'", alerts_insert)
print('All alert codes in SQL dump:', codes)
print('Count:', len(codes))

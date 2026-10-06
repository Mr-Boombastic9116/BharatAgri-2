sql_path = r"c:\Users\test\Desktop\BharatAgri-main\BharatAgri-main\database\bharatagri_iteration2.sql"
with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "PRC-CENTRE-GOA-01-07866" in line or "LOT-2026-GO-CENTRE-GOA-01-007866" in line:
            print(f"Line {idx}: {line[:120]}...")

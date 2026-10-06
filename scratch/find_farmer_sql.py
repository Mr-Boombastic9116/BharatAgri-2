sql_path = r"c:\Users\test\Desktop\BharatAgri-main\BharatAgri-main\database\bharatagri_iteration2.sql"
with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "farmer@bharatagri.demo" in line or "FRM-DEMO-001" in line:
            print(f"Line {idx}: {line[:120]}...")

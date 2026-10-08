import openpyxl
import pandas as pd
import sqlite3
import pymysql
from backend.app.core.config import settings

# 1. Inspect SIH workbook crops
excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'
wb = openpyxl.load_workbook(excel_path, read_only=True)

print("Sheets in workbook:", wb.sheetnames)

# Inspect farmers primary_crop
df_farmers = pd.read_excel(excel_path, sheet_name='farmers')
print("\nFarmers primary crops:", df_farmers['primary_crop'].value_counts().to_dict())

# Inspect procurement transactions crop
df_proc = pd.read_excel(excel_path, sheet_name='procurement_transactions')
print("\nProcurement transactions crops:", df_proc['crop'].value_counts().to_dict())
print("Procurement transaction sample rate/quintal by crop:")
print(df_proc.groupby('crop')['procurement_rate_rs_per_quintal'].agg(['min', 'mean', 'max', 'count']))

# 2. Inspect MySQL crops
try:
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    cur = conn.cursor()
    cur.execute("SELECT crop_name, category, season, shelf_life_days, urgency_level FROM crop_metadata")
    db_crops = cur.fetchall()
    print("\nCrops in MySQL crop_metadata:", len(db_crops))
    for c in db_crops:
        print(" ", c)
        
    cur.execute("SELECT crop, official_msp_per_quintal, marketing_season, season_year FROM msp_prices")
    db_msp = cur.fetchall()
    print("\nMSP in MySQL msp_prices:", len(db_msp))
    for m in db_msp:
        print(" ", m)
    conn.close()
except Exception as e:
    print("MySQL error:", e)

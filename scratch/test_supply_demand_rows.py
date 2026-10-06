import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "bharatagri_iteration2"),
    port=int(os.getenv("DB_PORT", 3306)),
    cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM state_crop_supply_demand")
    rows = cursor.fetchall()
    print("state_crop_supply_demand rows:")
    for r in rows:
        print(f"State: {r['state']} | Crop: {r['crop']} | ExpSupply: {r['expected_supply_quintals']} | CurrProc: {r['current_procurement_quintals']} | ProjProc: {r['projected_procurement_quintals']} | CurrInv: {r['current_inventory_quintals']} | AvailStorage: {r['available_storage_quintals']} | ExpDemand: {r['expected_demand_quintals']} | Surplus: {r['surplus_deficit_quintals']} | Status: {r['market_sentiment']}")

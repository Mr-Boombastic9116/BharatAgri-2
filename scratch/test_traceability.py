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
    for tbl in ["farmers", "bookings", "procurement_records", "storage_lots", "collection_records"]:
        cursor.execute(f"DESCRIBE {tbl}")
        cols = [r["Field"] for r in cursor.fetchall()]
        print(f"Table {tbl}: {cols}")
        
    cursor.execute("SELECT id, user_id, farmer_code, name, email FROM farmers WHERE email LIKE '%farmer%' LIMIT 5")
    farmers = cursor.fetchall()
    print("Farmers:", farmers)
    
    if farmers:
        fid = farmers[0]["user_id"]
        cursor.execute("SELECT * FROM bookings WHERE farmer_id=%s OR farmer_id=%s", (fid, farmers[0]["farmer_code"]))
        b_rows = cursor.fetchall()
        print(f"Bookings ({len(b_rows)}):")
        for b in b_rows:
            print("  ID:", b.get("id"), "ApptID:", b.get("appointment_id"), "Status:", b.get("status"), "FarmerID:", b.get("farmer_id"))
            
    cursor.execute("SELECT id, procurement_id, booking_id, farmer_id FROM procurement_records LIMIT 5")
    print("Procurement records sample:", cursor.fetchall())
    
    cursor.execute("SELECT id, lot_id, procurement_id, status FROM storage_lots LIMIT 5")
    print("Storage lots sample:", cursor.fetchall())

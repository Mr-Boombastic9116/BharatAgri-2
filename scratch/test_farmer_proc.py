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
    cursor.execute("SELECT * FROM procurement_records WHERE booking_id=1 OR farmer_id='farmer@bharatagri.demo' OR farmer_id='FRM-DEMO-001'")
    print("Procurement records for demo farmer:", cursor.fetchall())
    
    cursor.execute("SELECT * FROM bookings WHERE id=1")
    print("Booking 1:", cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM bookings")
    print("Total bookings:", cursor.fetchone())
    cursor.execute("SELECT status, count(*) FROM bookings GROUP BY status")
    print("Bookings by status:", cursor.fetchall())
    cursor.execute("SELECT status, count(*) FROM procurement_records GROUP BY status")
    print("Procurements by status:", cursor.fetchall())
    cursor.execute("SELECT count(*) FROM storage_lots")
    print("Storage lots count:", cursor.fetchone())

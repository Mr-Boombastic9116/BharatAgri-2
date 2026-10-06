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
    cursor.execute("SELECT * FROM storage_lots WHERE procurement_id='PRC-CENTRE-GOA-01-07866'")
    print("Lot for PRC-CENTRE-GOA-01-07866:", cursor.fetchall())
    cursor.execute("SELECT * FROM storage_lots WHERE centre_id='CENTRE-GOA-01' LIMIT 5")
    print("Lots in Goa 01:", cursor.fetchall())

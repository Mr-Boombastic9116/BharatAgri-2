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
    cursor.execute("SELECT * FROM crop_metadata")
    rows = cursor.fetchall()
    print(f"Total crops in crop_metadata: {len(rows)}")
    for r in rows:
        print(f"  {r['crop_name']}: perishable={r['is_perishable']}, shelf_life={r['shelf_life_days']} days, urgency={r['urgency_level']}, score={r['perishability_score']}")

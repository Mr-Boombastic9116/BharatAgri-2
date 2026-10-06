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
    cursor.execute("SELECT COUNT(*) as count FROM alerts")
    print("Total alerts:", cursor.fetchone())
    cursor.execute("SELECT scope, severity, is_resolved, state, centre_id, what, why FROM alerts LIMIT 10")
    for row in cursor.fetchall():
        print(row)

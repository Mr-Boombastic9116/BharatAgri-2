import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "localhost")
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
db_name = os.getenv("DB_NAME", "bharatagri_iteration2")
port = int(os.getenv("DB_PORT", 3306))

try:
    conn = pymysql.connect(host=host, user=user, password=password, database=db_name, port=port)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("Connected successfully. Tables count:", len(tables))
    for t in tables[:15]:
        print(" -", t[0])
    conn.close()
except Exception as e:
    print("Database error:", e)

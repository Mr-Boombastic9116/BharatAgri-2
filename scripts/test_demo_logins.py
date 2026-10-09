import sys
sys.path.insert(0, '.')
import pymysql
from backend.app.core.security import verify_password

conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
cur = conn.cursor()
cur.execute("SELECT user_id, password_hash, role FROM users WHERE user_id IN ('farmer@bharatagri.demo', 'agent@bharatagri.demo', 'centre@bharatagri.demo', 'admin@bharatagri.demo')")
rows = cur.fetchall()
passwords_to_test = ['BharatAgri@2026', 'password123', 'admin123', 'demo123', 'farmer123', 'centre123', 'agent123', 'Admin@2026', 'Farmer@2026']
for uid, phash, role in rows:
    print(f"User: {uid} (Role: {role})")
    matched = None
    for p in passwords_to_test:
        if verify_password(p, phash):
            matched = p
            break
    print(f"  Password matches: {matched}")
conn.close()

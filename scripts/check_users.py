import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
cur = conn.cursor()
cur.execute("SELECT role, COUNT(*), MIN(user_id), MAX(user_id) FROM users GROUP BY role")
for r in cur.fetchall():
    print(f"Role: {r[0]:15} Count: {r[1]:6} Min: {r[2]:20} Max: {r[3]}")

print("\nDemo / Key Users:")
cur.execute("SELECT user_id, name, email, mobile, role, centre_id, status FROM users WHERE email LIKE '%demo%' OR user_id LIKE '%demo%' OR user_id IN ('admin', 'centre01', 'agent01', 'farmer01')")
for r in cur.fetchall():
    print(" ", r)

print("\nAgents:")
cur.execute("SELECT user_id, name, email, role FROM users WHERE role = 'agent' LIMIT 5")
for r in cur.fetchall():
    print(" ", r)

print("\nGovernment:")
cur.execute("SELECT user_id, name, email, role FROM users WHERE role = 'government' LIMIT 5")
for r in cur.fetchall():
    print(" ", r)

print("\nCentres:")
cur.execute("SELECT user_id, name, email, role, centre_id FROM users WHERE role = 'centre' LIMIT 5")
for r in cur.fetchall():
    print(" ", r)

conn.close()

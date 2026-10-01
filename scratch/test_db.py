import pymysql

conn = pymysql.connect(host='localhost', user='root', password='', port=3306, db='bharatagri_iteration2')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT id, appointment_id, booking_id, farmer_id, centre_id, crop, quantity, status, qr_token FROM bookings WHERE status IN ('CONFIRMED', 'BOOKED', 'PENDING') LIMIT 10")
rows = cur.fetchall()
print(f"Found {len(rows)} matching bookings:")
for r in rows:
    print(r)

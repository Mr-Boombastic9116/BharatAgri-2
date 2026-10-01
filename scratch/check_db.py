import pymysql

conn = pymysql.connect(host="localhost", port=3306, user="root", password="", db="bharatagri_iteration2")
cursor = conn.cursor()
cursor.execute("SELECT status, COUNT(1), SUM(quantity) FROM bookings WHERE centre_id='CENTRE-GOA-01' GROUP BY status")
print("CENTRE-GOA-01 bookings by status:", cursor.fetchall())

cursor.execute("SELECT COUNT(1), SUM(estimated_quantity_quintals) FROM farmer_crops fc JOIN farmers f ON fc.farmer_id=f.id JOIN procurement_centres c ON (f.district=c.district OR f.state=c.state) WHERE c.centre_id='CENTRE-GOA-01'")
print("Farmer crops in centre district/state:", cursor.fetchone())
conn.close()

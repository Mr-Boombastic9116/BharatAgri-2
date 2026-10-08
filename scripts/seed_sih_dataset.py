"""
Seed SIH Synthetic Dataset into BharatAgri Database.
Source: data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx
"""

import os
import sys
import pandas as pd
import numpy as np
import pymysql
import datetime
from backend.app.core.config import settings

EXCEL_PATH = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'
DEMO_BCRYPT_HASH = "$2b$12$IAqE5g26rI5lLTRqGvb3G.F/V2N9YnxAPYOjd9ICnc7ZGX7zLGXG2" # BharatAgri@2026

def get_conn():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
        autocommit=False
    )

def seed_sih():
    print(f"Reading workbook: {EXCEL_PATH} ...")
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: {EXCEL_PATH} not found!")
        sys.exit(1)

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = xls.sheet_names
    print(f"Sheets found: {sheet_names}")

    conn = get_conn()
    cur = conn.cursor()

    print("\n[1/7] Preparing database tables...")
    cur.execute("SET FOREIGN_KEY_CHECKS=0;")
    for tbl in [
        'queue_events', 'centre_daily_metrics', 'notifications',
        'appointments', 'procurement_transactions',
        'payments', 'storage_lots', 'procurement_records', 'weighments', 'quality_checks', 'collection_records',
        'booking_status_history', 'bookings', 'slots', 'farmer_crops', 'farmers', 'procurement_centres'
    ]:
        cur.execute(f"TRUNCATE TABLE `{tbl}`;")
    cur.execute("DELETE FROM users WHERE role IN ('farmer', 'centre') AND user_id NOT IN ('farmer@bharatagri.demo', 'centre@bharatagri.demo');")
    conn.commit()

    # Ensure demo accounts exist
    cur.execute("""
        INSERT IGNORE INTO users (user_id, name, email, mobile, password_hash, role, status, created_at)
        VALUES 
        ('farmer@bharatagri.demo', 'Ramesh Patil (Demo)', 'farmer@bharatagri.demo', '9876543210', %s, 'farmer', 'ACTIVE', NOW()),
        ('centre@bharatagri.demo', 'Centre Officer (Demo)', 'centre@bharatagri.demo', '9876543211', %s, 'centre', 'ACTIVE', NOW()),
        ('admin@bharatagri.demo', 'Govt Administrator (Demo)', 'admin@bharatagri.demo', '9876543212', %s, 'government', 'ACTIVE', NOW()),
        ('agent@bharatagri.demo', 'Field Agent (Demo)', 'agent@bharatagri.demo', '9876543213', %s, 'agent', 'ACTIVE', NOW());
    """, (DEMO_BCRYPT_HASH, DEMO_BCRYPT_HASH, DEMO_BCRYPT_HASH, DEMO_BCRYPT_HASH))
    conn.commit()

    # 2. Seed Procurement Centres
    print("[2/7] Seeding Procurement Centres (20 records)...")
    df_centres = pd.read_excel(xls, 'procurement_centres')
    centre_records = []
    user_centre_records = []
    for _, row in df_centres.iterrows():
        c_id = str(row['centre_id']).strip()
        c_name = str(row['centre_name']).strip()
        c_state = str(row['state']).strip()
        c_dist = str(row['district']).strip()
        d_cap = int(row.get('daily_capacity_farmers', 120))
        wm = int(row.get('weighing_machines', 2))
        qs = int(row.get('quality_stations', 2))
        sc = int(row.get('staff_count', 10))
        ot = str(row.get('opening_time', '08:00'))
        ct = str(row.get('closing_time', '18:00'))

        centre_records.append((
            c_id, c_name, f"{c_dist}, {c_state}", c_state, c_dist,
            f"020-256{int(c_id[1:]):04d}", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
            ot, ct, "Paddy,Wheat,Cotton,Soybean,Maize",
            float(d_cap * 25.0), 25000.0, 5000.0, "OPERATIONAL",
            d_cap, wm, qs, sc
        ))

        user_centre_records.append((
            f"centre_{c_id.lower()}", f"{c_name} Manager", f"{c_id.lower()}@bharatagri.demo",
            f"9811{int(c_id[1:]):06d}", DEMO_BCRYPT_HASH, "centre", c_id, "ACTIVE"
        ))

    cur.executemany("""
        INSERT INTO procurement_centres (
            centre_id, centre_name, location, state, district, contact_number,
            operating_days, opening_time, closing_time, supported_crops,
            max_daily_capacity_quintals, total_storage_capacity_quintals, current_storage_usage_quintals,
            status, daily_capacity_farmers, weighing_machines, quality_stations, staff_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, centre_records)

    cur.executemany("""
        INSERT INTO users (user_id, name, email, mobile, password_hash, role, centre_id, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, user_centre_records)
    conn.commit()
    print("  -> Inserted 20 centres and manager user accounts.")

    # 3. Seed Farmers
    print("[3/7] Seeding Farmers (5,000 records)...")
    df_farmers = pd.read_excel(xls, 'farmers')
    farmer_records = []
    farmer_user_records = []
    farmer_crop_records = []
    farmer_crop_map = {}

    for _, row in df_farmers.iterrows():
        f_id = str(row['farmer_id']).strip()
        f_name = str(row['farmer_name']).strip()
        f_state = str(row['state']).strip()
        f_lang = str(row.get('preferred_language', 'hi')).strip().lower()
        f_crop = str(row['primary_crop']).strip()
        f_acres = float(row.get('land_acres', 2.5))
        f_qty = float(row.get('expected_quantity_quintals', 50.0))
        f_dist = float(row.get('distance_to_nearest_centre_km', 15.0))
        f_mob_ver = 1 if row.get('mobile_verified', 1) else 0

        farmer_crop_map[f_id] = (f_crop, f_qty)

        farmer_records.append((
            f_id, f_id, f_name, f"98765{int(f_id[1:]):05d}", f"{f_id.lower()}@kisanflow.demo",
            "Male", f"Village Kendra, {f_state}", f_state, "District HQ", "Taluka-1", "Gram Panchayat",
            f_acres * 0.4047, "VERIFIED", f"XXXX-XXXX-{int(f_id[1:]):04d}", "State Bank of India",
            f"602938{int(f_id[1:]):05d}", "SBIN0001234", f_crop, f_acres, f_qty, f_dist, f_lang, f_mob_ver
        ))

        farmer_user_records.append((
            f_id, f_name, f"{f_id.lower()}@kisanflow.demo", f"98765{int(f_id[1:]):05d}",
            DEMO_BCRYPT_HASH, "farmer", f_lang, "ACTIVE"
        ))

    for i in range(0, len(farmer_user_records), 1000):
        cur.executemany("""
            INSERT INTO users (user_id, name, email, mobile, password_hash, role, preferred_language, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, farmer_user_records[i:i+1000])

    for i in range(0, len(farmer_records), 1000):
        cur.executemany("""
            INSERT INTO farmers (
                farmer_code, user_id, name, mobile, email, gender, address, state, district,
                taluka, village, land_area_hectares, ekyc_status, aadhaar_masked, bank_name,
                bank_account_no, bank_ifsc, primary_crop, land_acres, expected_quantity_quintals,
                distance_to_nearest_centre_km, preferred_language, mobile_verified
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, farmer_records[i:i+1000])
    conn.commit()

    cur.execute("SELECT id, farmer_code FROM farmers")
    f_pk_map = {row[1]: row[0] for row in cur.fetchall()}
    for f_id, (crop, qty) in farmer_crop_map.items():
        if f_id in f_pk_map:
            farmer_crop_records.append((f_pk_map[f_id], crop, "Kharif 2026", qty))

    for i in range(0, len(farmer_crop_records), 1000):
        cur.executemany("""
            INSERT INTO farmer_crops (farmer_id, crop_name, season, estimated_quantity_quintals)
            VALUES (%s, %s, %s, %s)
        """, farmer_crop_records[i:i+1000])
    conn.commit()
    print("  -> Inserted 5,000 farmers and user accounts.")

    # 4. Seed Appointments, Slots & Bookings
    print("[4/7] Seeding Appointments, Slots & Bookings (18,000 records)...")
    df_appts = pd.read_excel(xls, 'appointments')

    slots_needed = {}
    for _, row in df_appts.iterrows():
        c_id = str(row['centre_id']).strip()
        s_start = pd.to_datetime(row['slot_start'])
        s_dur = int(row.get('slot_duration_min', 30))
        s_date = s_start.date()
        s_time = s_start.strftime("%H:%M")
        e_time = (s_start + datetime.timedelta(minutes=s_dur)).strftime("%H:%M")
        key = (c_id, s_date, s_time, e_time)
        slots_needed[key] = True

    slot_insert_tuples = [(c, d, st, et, 25) for (c, d, st, et) in slots_needed.keys()]
    for i in range(0, len(slot_insert_tuples), 1000):
        cur.executemany("""
            INSERT INTO slots (centre_id, date, start_time, end_time, max_capacity)
            VALUES (%s, %s, %s, %s, %s)
        """, slot_insert_tuples[i:i+1000])
    conn.commit()

    cur.execute("SELECT id, centre_id, date, start_time, end_time FROM slots")
    slot_id_lookup = {(r[1], r[2], r[3], r[4]): r[0] for r in cur.fetchall()}

    appointment_tuples = []
    booking_tuples = []

    for _, row in df_appts.iterrows():
        a_id = str(row['appointment_id']).strip()
        f_id = str(row['farmer_id']).strip()
        c_id = str(row['centre_id']).strip()
        a_date = pd.to_datetime(row['appointment_date']).date()
        s_start = pd.to_datetime(row['slot_start'])
        s_dur = int(row.get('slot_duration_min', 30))
        q_before = int(row.get('queue_before', 0))
        awm = int(row.get('active_weighing_machines', 2))
        staff = int(row.get('staff_available', 8))
        eq_fail = int(row.get('equipment_failure_flag', 0))
        w_delay = int(row.get('weather_delay_flag', 0))
        dist_km = float(row.get('travel_distance_km', 15.0))
        hist_proc = float(row.get('historical_avg_processing_min', 16.0))
        p_wait = float(row.get('predicted_wait_min', 35.0))
        act_wait = float(row['actual_wait_min']) if pd.notna(row.get('actual_wait_min')) else None
        no_show = int(row.get('no_show', 0))
        status = str(row.get('status', 'BOOKED')).strip()

        token = f"A{int(a_id[1:]):03d}" if a_id.startswith('A') else f"T-{a_id}"
        qr = f"QR-BA-{a_id}"
        crop, qty = farmer_crop_map.get(f_id, ("Paddy", 45.0))

        appointment_tuples.append((
            a_id, f_id, c_id, a_date, s_start, s_dur, q_before, awm, staff,
            eq_fail, w_delay, dist_km, hist_proc, p_wait, act_wait, no_show,
            status, crop, qty, token, qr
        ))

        s_time = s_start.strftime("%H:%M")
        e_time = (s_start + datetime.timedelta(minutes=s_dur)).strftime("%H:%M")
        s_id = slot_id_lookup.get((c_id, a_date, s_time, e_time), 1)

        b_status = 'CANCELLED' if no_show == 1 else ('COMPLETED' if status == 'COMPLETED' else 'CONFIRMED')
        booking_tuples.append((
            a_id, a_id, f_id, c_id, s_id, crop, qty, b_status, qr, s_start
        ))

    for i in range(0, len(appointment_tuples), 1000):
        cur.executemany("""
            INSERT INTO appointments (
                appointment_id, farmer_id, centre_id, appointment_date, slot_start, slot_duration_min,
                queue_before, active_weighing_machines, staff_available, equipment_failure_flag,
                weather_delay_flag, travel_distance_km, historical_avg_processing_min, predicted_wait_min,
                actual_wait_min, no_show, status, crop, quantity_quintals, token_number, qr_token
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, appointment_tuples[i:i+1000])

    for i in range(0, len(booking_tuples), 1000):
        cur.executemany("""
            INSERT INTO bookings (
                appointment_id, booking_id, farmer_id, centre_id, slot_id, crop, quantity,
                status, qr_token, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, booking_tuples[i:i+1000])
    conn.commit()
    print("  -> Inserted 18,000 appointments and bookings.")

    # 5. Seed Procurement Transactions
    print("[5/7] Seeding Procurement Transactions (9,000 records)...")
    df_trans = pd.read_excel(xls, 'procurement_transactions')
    trans_tuples = []
    coll_tuples = []
    qc_tuples = []
    weigh_tuples = []
    proc_rec_tuples = []
    pay_tuples = []

    cur.execute("SELECT id, appointment_id FROM bookings")
    b_id_map = {r[1]: r[0] for r in cur.fetchall()}

    for _, row in df_trans.iterrows():
        p_id = str(row['procurement_id']).strip()
        a_id = str(row['appointment_id']).strip()
        f_id = str(row['farmer_id']).strip()
        c_id = str(row['centre_id']).strip()
        crop = str(row['crop']).strip()
        qty = float(row['quantity_quintals'])
        q_score = float(row['quality_score'])
        rate = float(row['procurement_rate_rs_per_quintal'])
        gross = float(row['gross_amount_rs'])
        p_time = pd.to_datetime(row['procurement_timestamp'])
        p_status = str(row['payment_status']).strip()
        dbt_ref = f"DBT-NPCI-{p_id}" if p_status == 'PAID' else None

        trans_tuples.append((
            p_id, a_id, f_id, c_id, crop, qty, q_score, rate, gross, p_time, p_status, dbt_ref
        ))

        booking_pk = b_id_map.get(a_id, 1)
        coll_id = f"COL-{p_id}"
        coll_tuples.append((
            coll_id, booking_pk, f_id, c_id, crop, qty, p_time.date(), "DIRECT_CENTRE", "Officer In-charge", "COLLECTED", p_time
        ))
        qc_tuples.append((
            f"QC-{p_id}", coll_id, 12.0, 0.5, 1.0, "GRADE_A" if q_score >= 80 else "GRADE_B", "AI Quality Engine", 1, f"Quality score: {q_score}", p_time
        ))
        weigh_tuples.append((
            f"WB-{p_id}", coll_id, qty + 15.0, 15.0, qty, "WB-01", "Weighbridge Operator", p_time
        ))
        proc_rec_tuples.append((
            p_id, booking_pk, coll_id, f_id, c_id, crop, "GRADE_A" if q_score >= 80 else "GRADE_B", 12.0, qty, rate, gross, "CONFIRMED", "Silo-A", p_time
        ))
        pay_tuples.append((
            f"PAY-{p_id}", p_id, f_id, gross, rate, qty, "DBT_DIRECT",
            "PAID" if p_status == 'PAID' else "PROCESSING", dbt_ref or f"REF-{p_id}", p_time, p_time, "Government MSP DBT Settlement"
        ))

    for i in range(0, len(trans_tuples), 1000):
        cur.executemany("""
            INSERT INTO procurement_transactions (
                procurement_id, appointment_id, farmer_id, centre_id, crop, quantity_quintals,
                quality_score, procurement_rate_rs_per_quintal, gross_amount_rs,
                procurement_timestamp, payment_status, dbt_reference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, trans_tuples[i:i+1000])

    for i in range(0, len(coll_tuples), 1000):
        cur.executemany("""
            INSERT INTO collection_records (
                collection_id, booking_id, farmer_id, centre_id, crop, collected_quantity,
                collection_date, collection_method, collected_by, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, coll_tuples[i:i+1000])

    for i in range(0, len(qc_tuples), 1000):
        cur.executemany("""
            INSERT INTO quality_checks (
                check_id, collection_id, moisture_content_pct, foreign_matter_pct, broken_grains_pct,
                quality_grade, inspector_name, passed, remarks, checked_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, qc_tuples[i:i+1000])

    for i in range(0, len(weigh_tuples), 1000):
        cur.executemany("""
            INSERT INTO weighments (
                weighment_id, collection_id, gross_weight_quintals, tare_weight_quintals, net_weight_quintals,
                weighbridge_id, operator_name, weighed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, weigh_tuples[i:i+1000])

    for i in range(0, len(proc_rec_tuples), 1000):
        cur.executemany("""
            INSERT INTO procurement_records (
                procurement_id, booking_id, collection_id, farmer_id, centre_id, crop, quality_grade,
                moisture_content_pct, procured_quantity_quintals, msp_rate_per_quintal,
                total_procurement_value, status, warehouse_location, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, proc_rec_tuples[i:i+1000])

    for i in range(0, len(pay_tuples), 1000):
        cur.executemany("""
            INSERT INTO payments (
                payment_id, procurement_id, farmer_id, amount, msp_rate, quantity_quintals,
                payment_mode, payment_status, transaction_ref, initiated_at, paid_at, remarks
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, pay_tuples[i:i+1000])
    conn.commit()
    print("  -> Inserted 9,000 procurement transactions & payment records.")

    # 6. Seed Queue Events & Centre Daily Metrics
    print("[6/7] Seeding Queue Events (20,000 records) & Centre Daily Metrics (900 records)...")
    df_queue = pd.read_excel(xls, 'queue_events')
    queue_tuples = []
    for _, row in df_queue.iterrows():
        queue_tuples.append((
            str(row['event_id']).strip(),
            pd.to_datetime(row['timestamp']),
            str(row['centre_id']).strip(),
            int(row['queue_length']),
            int(row['farmers_in_service']),
            int(row['active_stations']),
            float(row['processing_rate_farmers_per_hour']),
            float(row['avg_processing_time_min']),
            int(row['equipment_failure_flag']),
            int(row['weather_delay_flag']),
            float(row['estimated_wait_min'])
        ))

    for i in range(0, len(queue_tuples), 2000):
        cur.executemany("""
            INSERT INTO queue_events (
                event_id, timestamp, centre_id, queue_length, farmers_in_service,
                active_stations, processing_rate_farmers_per_hour, avg_processing_time_min,
                equipment_failure_flag, weather_delay_flag, estimated_wait_min
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, queue_tuples[i:i+2000])

    df_metrics = pd.read_excel(xls, 'centre_daily_metrics')
    metrics_tuples = []
    for _, row in df_metrics.iterrows():
        metrics_tuples.append((
            pd.to_datetime(row['date']).date(),
            str(row['centre_id']).strip(),
            int(row['capacity_farmers']),
            int(row['arrivals']),
            int(row['processed']),
            int(row['no_shows']),
            float(row['avg_wait_min']),
            int(row['peak_queue']),
            int(row['equipment_downtime_min']),
            float(row['congestion_score']),
            int(row['high_congestion_flag'])
        ))

    for i in range(0, len(metrics_tuples), 500):
        cur.executemany("""
            INSERT INTO centre_daily_metrics (
                date, centre_id, capacity_farmers, arrivals, processed, no_shows,
                avg_wait_min, peak_queue, equipment_downtime_min, congestion_score, high_congestion_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, metrics_tuples[i:i+500])
    conn.commit()
    print("  -> Inserted 20,000 queue events and 900 centre metrics.")

    # 7. Seed Notifications
    print("[7/7] Seeding Notifications (20,000 records)...")
    df_notifs = pd.read_excel(xls, 'notifications')
    notif_tuples = []
    for _, row in df_notifs.iterrows():
        n_id = str(row['notification_id']).strip()
        f_id = str(row['farmer_id']).strip()
        n_type = str(row['notification_type']).strip()
        ch = str(row['channel']).strip()
        s_at = pd.to_datetime(row['sent_at'])
        d_stat = str(row['delivery_status']).strip()
        resp = str(row['response']).strip() if pd.notna(row.get('response')) else None

        msg = f"KisanFlow Notification: {n_type.replace('_', ' ').title()} - Please check your token status."
        if n_type == 'COME_NOW':
            msg = "🔔 Your turn is approaching. Only 5 farmers ahead of you. Please proceed to the procurement counter."
        elif n_type == 'DELAY_ALERT':
            msg = "⚠ Operational Update: Processing is delayed by approx 20 minutes due to heavy arrivals."

        notif_tuples.append((
            n_id, f_id, n_type, ch, msg, s_at, d_stat, resp
        ))

    for i in range(0, len(notif_tuples), 2000):
        cur.executemany("""
            INSERT INTO notifications (
                notification_id, farmer_id, notification_type, channel, message, sent_at, delivery_status, response
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, notif_tuples[i:i+2000])

    cur.execute("SET FOREIGN_KEY_CHECKS=1;")
    conn.commit()
    conn.close()
    print("\n[SUCCESS] SIH Dataset seeding complete!")

if __name__ == '__main__':
    seed_sih()

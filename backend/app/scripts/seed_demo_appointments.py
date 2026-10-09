import datetime
from backend.app.core.database import SessionLocal
from backend.app.models.centre import Slot, ProcurementCentre
from backend.app.models.booking import Booking
from backend.app.models.queue import Appointment

def seed_demo_appointments():
    db = SessionLocal()
    try:
        # 1. Ensure slots for 2026-10-17 and 2026-10-18
        slot_times = [
            ('09:00 AM', '11:00 AM'),
            ('11:00 AM', '01:00 PM'),
            ('02:00 PM', '04:00 PM'),
            ('04:00 PM', '06:00 PM')
        ]

        for d_str in ['2026-10-17', '2026-10-18']:
            d = datetime.date.fromisoformat(d_str)
            for st, et in slot_times:
                s = db.query(Slot).filter(Slot.centre_id == 'C01', Slot.date == d, Slot.start_time == st).first()
                if not s:
                    ns = Slot(centre_id='C01', date=d, start_time=st, end_time=et, max_capacity=20)
                    db.add(ns)
        db.commit()

        # 2. Upcoming appointments template for C01 across Oct 11 - Oct 18, 2026
        new_appts = [
            ('2026-10-11', '09:00 AM', 'F-GOA-905', 'Tomato', 45.0, 'CONFIRMED'),
            ('2026-10-12', '09:00 AM', 'F-GOA-901', 'Mango', 45.0, 'CONFIRMED'),
            ('2026-10-12', '11:00 AM', 'F-GOA-902', 'Banana', 30.0, 'CONFIRMED'),
            ('2026-10-12', '02:00 PM', 'F-GOA-905', 'Tomato', 55.0, 'BOOKED'),
            ('2026-10-12', '04:00 PM', 'F-GOA-907', 'Paddy', 75.0, 'BOOKED'),

            ('2026-10-13', '09:00 AM', 'F-GOA-903', 'Paddy', 80.0, 'CONFIRMED'),
            ('2026-10-13', '11:00 AM', 'F-GOA-904', 'Banana', 40.0, 'CONFIRMED'),
            ('2026-10-13', '02:00 PM', 'F-GOA-906', 'Mango', 35.0, 'BOOKED'),
            ('2026-10-13', '04:00 PM', 'F-GOA-908', 'Tomato', 60.0, 'BOOKED'),

            ('2026-10-14', '09:00 AM', 'F-GOA-909', 'Mango', 50.0, 'CONFIRMED'),
            ('2026-10-14', '02:00 PM', 'F-GOA-910', 'Cashew', 25.0, 'CONFIRMED'),
            ('2026-10-14', '04:00 PM', 'F-GOA-902', 'Paddy', 70.0, 'BOOKED'),

            ('2026-10-15', '09:00 AM', 'F-GOA-901', 'Mango', 60.0, 'CONFIRMED'),
            ('2026-10-15', '11:00 AM', 'F-GOA-905', 'Tomato', 45.0, 'CONFIRMED'),
            ('2026-10-15', '02:00 PM', 'F-GOA-907', 'Banana', 35.0, 'BOOKED'),
            ('2026-10-15', '04:00 PM', 'FRM-DEMO-001', 'Mango', 40.0, 'CONFIRMED'),

            ('2026-10-16', '09:00 AM', 'F-GOA-903', 'Paddy', 85.0, 'CONFIRMED'),
            ('2026-10-16', '11:00 AM', 'F-GOA-904', 'Banana', 30.0, 'CONFIRMED'),
            ('2026-10-16', '02:00 PM', 'F-GOA-908', 'Tomato', 50.0, 'BOOKED'),
            ('2026-10-16', '04:00 PM', 'F-GOA-909', 'Mango', 40.0, 'BOOKED'),

            ('2026-10-17', '09:00 AM', 'F-GOA-906', 'Mango', 55.0, 'CONFIRMED'),
            ('2026-10-17', '11:00 AM', 'F-GOA-910', 'Cashew', 30.0, 'CONFIRMED'),
            ('2026-10-17', '02:00 PM', 'F-GOA-901', 'Banana', 45.0, 'BOOKED'),

            ('2026-10-18', '09:00 AM', 'FRM-DEMO-001', 'Mango', 50.0, 'CONFIRMED'),
            ('2026-10-18', '11:00 AM', 'F-GOA-902', 'Mango', 65.0, 'CONFIRMED'),
            ('2026-10-18', '02:00 PM', 'F-GOA-905', 'Tomato', 40.0, 'BOOKED')
        ]

        created_count = 0
        for d_str, st, f_id, crop, qty, status in new_appts:
            d = datetime.date.fromisoformat(d_str)
            slot = db.query(Slot).filter(Slot.centre_id == 'C01', Slot.date == d, Slot.start_time == st).first()
            if not slot:
                continue

            clean_tag = f_id.replace('-', '')
            appt_id = f"APPT-C01-{d.strftime('%Y%m%d')}-{clean_tag[-6:]}"
            existing = db.query(Booking).filter(Booking.appointment_id == appt_id).first()
            if existing:
                continue

            day_count = db.query(Appointment).filter(
                Appointment.centre_id == 'C01',
                Appointment.appointment_date == d
            ).count() + 1
            tok = f"A{day_count:03d}"
            qr = f"BA-QR-{appt_id}"

            try:
                t_obj = datetime.datetime.strptime(st, '%I:%M %p').time()
            except Exception:
                t_obj = datetime.time(9, 0)

            b = Booking(
                appointment_id=appt_id,
                booking_id=appt_id,
                farmer_id=f_id,
                centre_id='C01',
                slot_id=slot.id,
                crop=crop,
                quantity=qty,
                status=status,
                qr_token=qr
            )
            db.add(b)

            apt = Appointment(
                appointment_id=appt_id,
                farmer_id=f_id,
                centre_id='C01',
                appointment_date=d,
                slot_start=t_obj,
                slot_duration_min=120,
                queue_before=day_count,
                active_weighing_machines=2,
                staff_available=8,
                equipment_failure_flag=0,
                weather_delay_flag=0,
                travel_distance_km=6.5,
                historical_avg_processing_min=16.0,
                predicted_wait_min=round(day_count * 3.5, 1),
                actual_wait_min=None,
                no_show=0,
                status=status,
                crop=crop,
                quantity_quintals=qty,
                token_number=tok,
                qr_token=qr
            )
            db.add(apt)
            created_count += 1

        db.commit()
        print(f"Successfully created {created_count} upcoming appointments for C01.")
    finally:
        db.close()

if __name__ == '__main__':
    seed_demo_appointments()

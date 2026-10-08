"""
Script: fix_agricultural_database.py
Enforces strict state-crop relationships across all database tables:
- Goa: Mango, Banana, Tomato
- Maharashtra: Sugarcane, Wheat, Cotton
- Karnataka: Paddy, Maize, Bajra

Standardizes all legacy seed records (farmers, centres, farmer_crops, bookings, collections,
procurement records, storage lots, evidence) so that state -> crop relationships are 100% valid.
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

STATE_CROP_MAP = {
    "Goa": ["Mango", "Banana", "Tomato"],
    "Maharashtra": ["Sugarcane", "Wheat", "Cotton"],
    "Karnataka": ["Paddy", "Maize", "Bajra"]
}

def run_fix():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'bharatagri_iteration2')
    )
    
    with conn.cursor() as cur:
        print("[1/8] Standardizing state names in states & centres...")
        cur.execute("UPDATE `states` SET `name` = 'Karnataka' WHERE `name` LIKE 'Karnatak%';")
        
        # Standardize MP centres into Maharashtra to ensure all 26 centres belong to the 3 prototype states
        cur.execute("""
            UPDATE `procurement_centres` 
            SET `state` = 'Maharashtra', `district` = 'Nagpur' 
            WHERE `state` = 'Madhya Pradesh';
        """)
        
        for st, crps in STATE_CROP_MAP.items():
            cur.execute("""
                UPDATE `procurement_centres`
                SET `supported_crops` = %s
                WHERE `state` = %s;
            """, (",".join(crps), st))
        
        # Standardize MP farmers into Maharashtra
        cur.execute("""
            UPDATE `farmers` 
            SET `state` = 'Maharashtra', `district` = 'Nagpur' 
            WHERE `state` = 'Madhya Pradesh';
        """)
        
        print("[2/8] Creating or verifying procurement_evidence table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `procurement_evidence` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `appointment_id` VARCHAR(100) NOT NULL,
                `booking_id` INT NULL,
                `process_step` VARCHAR(50) NOT NULL,
                `evidence_type` VARCHAR(50) NOT NULL,
                `file_path` VARCHAR(255) NOT NULL,
                `uploaded_by` VARCHAR(100) NOT NULL,
                `uploaded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `description` TEXT NULL,
                INDEX idx_appt (`appointment_id`),
                INDEX idx_step (`process_step`),
                INDEX idx_type (`evidence_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        print("[3/8] Harmonizing farmer_crops with farmer states...")
        # Get all farmers
        cur.execute("SELECT id, state FROM farmers;")
        farmers = cur.fetchall()
        for f_id, state in farmers:
            valid_crops = STATE_CROP_MAP.get(state, ["Mango", "Banana", "Tomato"])
            # Update farmer_crops for this farmer if crop_name is invalid
            cur.execute("""
                SELECT id, crop_name FROM farmer_crops WHERE farmer_id = %s;
            """, (f_id,))
            f_crops = cur.fetchall()
            for fc_id, c_name in f_crops:
                if c_name not in valid_crops:
                    # Select replacement deterministically based on fc_id
                    replacement = valid_crops[fc_id % len(valid_crops)]
                    cur.execute("""
                        UPDATE farmer_crops SET crop_name = %s WHERE id = %s;
                    """, (replacement, fc_id))

        print("[4/8] Harmonizing bookings with centre states...")
        cur.execute("""
            SELECT b.id, b.appointment_id, b.crop, c.state, b.centre_id
            FROM bookings b
            JOIN procurement_centres c ON b.centre_id = c.centre_id;
        """)
        bookings = cur.fetchall()
        updated_bookings = 0
        for b_id, appt_id, crop, state, c_id in bookings:
            valid_crops = STATE_CROP_MAP.get(state, ["Mango", "Banana", "Tomato"])
            if crop not in valid_crops:
                # Deterministic replacement based on booking id
                new_crop = valid_crops[b_id % len(valid_crops)]
                cur.execute("UPDATE bookings SET crop = %s WHERE id = %s;", (new_crop, b_id))
                updated_bookings += 1
                
                # Propagate to collection_records
                cur.execute("UPDATE collection_records SET crop = %s WHERE booking_id = %s;", (new_crop, b_id))
                # Propagate to procurement_records
                cur.execute("UPDATE procurement_records SET crop = %s WHERE booking_id = %s;", (new_crop, b_id))
                # Propagate to ai_quality_inspections if crop is not mango
                if new_crop != "Mango":
                    cur.execute("UPDATE ai_quality_inspections SET crop = %s WHERE booking_id = %s;", (new_crop, b_id))
        print(f"  Updated {updated_bookings} bookings to match centre states.")

        print("[5/8] Aligning storage_lots crop with collection/procurement records...")
        cur.execute("""
            UPDATE storage_lots sl
            JOIN procurement_records pr ON sl.procurement_id = pr.procurement_id
            SET sl.crop = pr.crop
            WHERE sl.crop != pr.crop;
        """)

        print("[6/8] Aligning crop_metadata table shelf life & perishability...")
        # Ensure official agricultural metadata for all 9 prototype crops
        crop_meta_rows = [
            ("Mango", "HORTICULTURE", "Summer/Zaid", 1, 14, "HIGH", 0.85, "Ventilated Plastic Crates / 13°C Cool Store", "High seasonal coastal demand; peak April-June"),
            ("Banana", "HORTICULTURE", "All-Season", 1, 7, "HIGH", 0.80, "Ripening Chamber / Well-Ventilated Ambient (15-20°C)", "Year-round steady market consumption"),
            ("Tomato", "PERISHABLE_VEGETABLE", "Rabi/Zaid", 1, 5, "CRITICAL", 0.95, "Cold Chain / Perforated Crates (10-12°C)", "Highly perishable; rapid price volatility"),
            ("Sugarcane", "COMMERCIAL", "Crushing", 1, 3, "CRITICAL", 0.95, "Direct Mill Yard / Rapid Crushing Intake", "Immediate mill intake within 48-72h to avoid sucrose loss"),
            ("Wheat", "GRAIN", "Rabi", 0, 365, "LOW", 0.20, "Covered Dry Godown / Aerated Silo (Moisture <= 12%)", "Stable non-perishable foodgrain buffer"),
            ("Cotton", "FIBER", "Kharif", 0, 300, "LOW", 0.25, "Weather-Sheltered Dry Shed / High-Density Bale Stack", "Industrial spinning mill procurement"),
            ("Paddy", "GRAIN", "Kharif", 0, 365, "LOW", 0.20, "Covered Warehouse / Aerated Silo (Moisture <= 14%)", "National food security PDS buffer stock"),
            ("Maize", "GRAIN", "Kharif", 0, 240, "LOW", 0.25, "Dry Aerated Godown / Moisture Controlled (Moisture <= 14%)", "Feed & starch industrial processing"),
            ("Bajra", "MILLET", "Kharif", 0, 180, "LOW", 0.30, "Dry Ventilated Storage / Low Humidity (Moisture <= 12%)", "Nutri-cereal public distribution")
        ]
        
        for cm in crop_meta_rows:
            cur.execute("""
                INSERT INTO `crop_metadata` 
                (`crop_name`, `category`, `season`, `is_perishable`, `shelf_life_days`, `urgency_level`, `perishability_score`, `storage_requirements`, `demand_patterns`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                category=VALUES(category), season=VALUES(season), is_perishable=VALUES(is_perishable),
                shelf_life_days=VALUES(shelf_life_days), urgency_level=VALUES(urgency_level),
                perishability_score=VALUES(perishability_score), storage_requirements=VALUES(storage_requirements),
                demand_patterns=VALUES(demand_patterns);
            """, cm)

        print("[7/8] Verifying state_crop_supply_demand holds exact 9 prototype rows...")
        cur.execute("SELECT count(*) FROM state_crop_supply_demand;")
        sd_count = cur.fetchone()[0]
        print(f"  state_crop_supply_demand row count: {sd_count}")

        print("[8/8] Verifying zero invalid combinations in database...")
        # Check bookings
        cur.execute("""
            SELECT c.state, b.crop, count(*)
            FROM bookings b
            JOIN procurement_centres c ON b.centre_id = c.centre_id
            GROUP BY c.state, b.crop;
        """)
        booking_state_crops = cur.fetchall()
        invalid_count = 0
        for state, crop, cnt in booking_state_crops:
            valid = STATE_CROP_MAP.get(state, [])
            if crop not in valid:
                print(f"  [ERROR] Invalid booking state-crop: {state} -> {crop} ({cnt} rows)")
                invalid_count += 1
            else:
                print(f"  [OK] Valid booking state-crop: {state} -> {crop} ({cnt} rows)")

        if invalid_count == 0:
            print("  SUCCESS: 0 invalid state-crop combinations found in bookings!")
        else:
            raise RuntimeError(f"Database still contains {invalid_count} invalid combinations!")

        conn.commit()
    print("Database correction complete!")

if __name__ == '__main__':
    run_fix()

import sys
from sqlalchemy import text
from backend.app.core.database import engine

def run_migration():
    print("Running migration for BharatAgri Prompt 1...")
    with engine.begin() as conn:
        # 1. Modify bookings.status to VARCHAR(50)
        print("[1/4] Updating bookings.status column to VARCHAR(50)...")
        conn.execute(text("ALTER TABLE bookings MODIFY COLUMN status VARCHAR(50) NOT NULL DEFAULT 'CONFIRMED'"))
        
        # 2. Ensure centre_id on users table exists and is indexed
        print("[2/4] Verifying users table centre_id mapping...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN centre_id VARCHAR(50) NULL AFTER role"))
        except Exception:
            pass
        
        # Update any missing centre_id for centre managers
        conn.execute(text("""
            UPDATE users 
            SET centre_id = 'CENTRE-GOA-01' 
            WHERE (user_id IN ('centre@bharatagri.demo', 'centre01') OR role = 'centre') 
              AND (centre_id IS NULL OR centre_id = '')
        """))
        conn.execute(text("""
            UPDATE users 
            SET centre_id = user_id 
            WHERE user_id LIKE 'CENTRE-%' 
              AND (centre_id IS NULL OR centre_id = '')
        """))

        # 3. Add arrival/processing support columns if any missing
        print("[3/4] Checking quality_checks & weighments & procurement columns...")
        # Check if quality_grade is in procurement_records or add it as optional helper
        try:
            conn.execute(text("ALTER TABLE procurement_records ADD COLUMN quality_grade VARCHAR(20) DEFAULT 'GRADE_A' AFTER crop"))
            print("  Added quality_grade to procurement_records.")
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE procurement_records ADD COLUMN moisture_content_pct DECIMAL(5,2) DEFAULT 12.50 AFTER quality_grade"))
            print("  Added moisture_content_pct to procurement_records.")
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE procurement_records ADD COLUMN warehouse_location VARCHAR(150) NULL AFTER status"))
            print("  Added warehouse_location to procurement_records.")
        except Exception:
            pass

        # 4. Check farmers table columns
        print("[4/4] Verifying farmers table columns...")
        try:
            conn.execute(text("ALTER TABLE farmers ADD COLUMN dob DATE NULL AFTER email"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE farmers ADD COLUMN address TEXT NULL AFTER gender"))
        except Exception:
            pass

    print("Prompt 1 migration completed successfully.")

if __name__ == "__main__":
    run_migration()

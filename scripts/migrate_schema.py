import sys
from datetime import date
from sqlalchemy import text
from backend.app.core.database import engine

def migrate():
    with engine.begin() as conn:
        print("[1/5] Checking users table centre_id column...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN centre_id VARCHAR(50) NULL AFTER role"))
            print("  Added centre_id to users table.")
        except Exception as e:
            print("  centre_id column already exists or skipped:", e)

        conn.execute(text("UPDATE users SET centre_id = 'CENTRE-GOA-01' WHERE user_id IN ('centre@bharatagri.demo', 'centre01') OR role = 'centre'"))
        conn.execute(text("UPDATE users SET centre_id = user_id WHERE user_id LIKE 'CENTRE-%'"))
        print("  Updated centre_id mappings for centre users.")

        print("[2/5] Creating msp_prices table...")
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS msp_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            crop VARCHAR(100) NOT NULL,
            crop_variant VARCHAR(100) DEFAULT 'Standard',
            marketing_season VARCHAR(50) NOT NULL,
            season_year VARCHAR(20) NOT NULL,
            official_msp_per_quintal DECIMAL(10, 2) NOT NULL,
            effective_from DATE NOT NULL,
            effective_to DATE NOT NULL,
            source VARCHAR(150) DEFAULT 'Ministry of Agriculture & Farmers Welfare, Govt of India',
            source_reference VARCHAR(150) DEFAULT 'CACP Price Policy Kharif/Rabi Notification',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_crop_season (crop, marketing_season, season_year)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        # Seed official MSP data
        conn.execute(text("DELETE FROM msp_prices"))
        official_crops = [
            ("Paddy", "Common", "Kharif", "2026-27", 2300.00, "2026-06-01", "2027-05-31"),
            ("Paddy", "Grade A", "Kharif", "2026-27", 2320.00, "2026-06-01", "2027-05-31"),
            ("Maize", "Hybrid / Standard", "Kharif", "2026-27", 2225.00, "2026-06-01", "2027-05-31"),
            ("Tur (Arhar)", "Standard Pulses", "Kharif", "2026-27", 7550.00, "2026-06-01", "2027-05-31"),
            ("Moong", "Green Gram", "Kharif", "2026-27", 8682.00, "2026-06-01", "2027-05-31"),
            ("Urad", "Black Gram", "Kharif", "2026-27", 7400.00, "2026-06-01", "2027-05-31"),
            ("Groundnut", "Pod In-shell", "Kharif", "2026-27", 6783.00, "2026-06-01", "2027-05-31"),
            ("Soybean", "Yellow", "Kharif", "2026-27", 4892.00, "2026-06-01", "2027-05-31"),
            ("Cotton", "Medium Staple", "Kharif", "2026-27", 7121.00, "2026-06-01", "2027-05-31"),
            ("Cotton", "Long Staple", "Kharif", "2026-27", 7521.00, "2026-06-01", "2027-05-31"),
            ("Wheat", "Mill Quality", "Rabi", "2026-27", 2275.00, "2026-10-01", "2027-09-30"),
            ("Gram (Chana)", "Desi", "Rabi", "2026-27", 5440.00, "2026-10-01", "2027-09-30"),
            ("Mustard", "Rapeseed / Sarson", "Rabi", "2026-27", 5650.00, "2026-10-01", "2027-09-30"),
        ]
        for c in official_crops:
            conn.execute(text("""
            INSERT INTO msp_prices (crop, crop_variant, marketing_season, season_year, official_msp_per_quintal, effective_from, effective_to)
            VALUES (:crop, :variant, :season, :year, :msp, :eff_from, :eff_to)
            """), {
                "crop": c[0], "variant": c[1], "season": c[2], "year": c[3],
                "msp": c[4], "eff_from": c[5], "eff_to": c[6]
            })
        print(f"  Inserted {len(official_crops)} official MSP benchmark records.")

        print("[3/5] Creating truck_route_predictions table...")
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS truck_route_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            route_code VARCHAR(50) UNIQUE NOT NULL,
            origin_centre_id VARCHAR(50) NOT NULL,
            origin_centre_name VARCHAR(150) NOT NULL,
            destination_centre_id VARCHAR(50) NOT NULL,
            destination_centre_name VARCHAR(150) NOT NULL,
            destination_state VARCHAR(50) NOT NULL,
            crop VARCHAR(100) NOT NULL,
            quantity_quintals DECIMAL(10, 2) NOT NULL,
            truck_capacity_quintals DECIMAL(10, 2) NOT NULL DEFAULT 200.00,
            estimated_distance_km DECIMAL(8, 2) NOT NULL,
            departure_date DATE NOT NULL,
            expected_arrival_date DATE NOT NULL,
            reason VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PREDICTED',
            reviewed_by VARCHAR(100) NULL,
            reviewed_at DATETIME NULL,
            rejection_reason VARCHAR(255) NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_route_status (status),
            INDEX idx_origin (origin_centre_id),
            INDEX idx_dest (destination_centre_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        # Seed sample predicted truck routes
        conn.execute(text("DELETE FROM truck_route_predictions"))
        seed_routes = [
            ("TRK-RTE-2026-001", "CENTRE-GOA-01", "Sanquelim Krishi Upaj Mandi", "CENTRE-MH-01", "Baramati APMC Centre", "Maharashtra", "Paddy", 450.00, 200.00, 310.50, "2026-10-02", "2026-10-03", "Yard storage reaching 91% capacity. Excess paddy redirected to high-demand milling buffer.", "PROPOSED"),
            ("TRK-RTE-2026-002", "CENTRE-MH-02", "Shirur Grain Market Yard", "CENTRE-MH-07", "Katol Cotton & Grain Mandi", "Maharashtra", "Soybean", 380.00, 200.00, 485.00, "2026-10-03", "2026-10-04", "Inter-district stock balancing: processing oilseed deficit at Vidarbha warehouse.", "PROPOSED"),
            ("TRK-RTE-2026-003", "CENTRE-KA-01", "Chikkodi Agriculture Mandi", "CENTRE-GOA-03", "Margao APMC Yard", "Goa", "Maize", 320.00, 200.00, 165.00, "2026-10-02", "2026-10-02", "Supplying poultry feed processing requirement at South Goa cluster.", "APPROVED"),
            ("TRK-RTE-2026-004", "CENTRE-MP-01", "Sanwer Krishi Upaj Mandi", "CENTRE-MH-04", "Niphad Grain Procurement Hub", "Maharashtra", "Wheat", 500.00, 250.00, 520.00, "2026-10-04", "2026-10-05", "State food security buffer redistribution from Malwa belt to Central Maharashtra.", "SCHEDULED"),
            ("TRK-RTE-2026-005", "CENTRE-GOA-04", "Ponda Farmer Hub", "CENTRE-KA-04", "Hubballi Amargol APMC Yard", "Karnataka", "Paddy", 260.00, 200.00, 142.00, "2026-10-03", "2026-10-03", "Seasonal drying and parboiling plant capacity utilization in Dharwad district.", "PROPOSED"),
        ]
        for r in seed_routes:
            conn.execute(text("""
            INSERT INTO truck_route_predictions 
            (route_code, origin_centre_id, origin_centre_name, destination_centre_id, destination_centre_name, destination_state, crop, quantity_quintals, truck_capacity_quintals, estimated_distance_km, departure_date, expected_arrival_date, reason, status)
            VALUES (:code, :orig_id, :orig_name, :dest_id, :dest_name, :dest_state, :crop, :qty, :truck_cap, :dist, :dep, :arr, :reason, :status)
            """), {
                "code": r[0], "orig_id": r[1], "orig_name": r[2], "dest_id": r[3], "dest_name": r[4],
                "dest_state": r[5], "crop": r[6], "qty": r[7], "truck_cap": r[8], "dist": r[9],
                "dep": r[10], "arr": r[11], "reason": r[12], "status": r[13]
            })
        print(f"  Inserted {len(seed_routes)} truck route predictions.")

        print("[4/5] Creating state_crop_supply_demand table...")
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS state_crop_supply_demand (
            id INT AUTO_INCREMENT PRIMARY KEY,
            state VARCHAR(100) NOT NULL,
            crop VARCHAR(100) NOT NULL,
            season VARCHAR(50) NOT NULL DEFAULT 'Kharif 2026',
            official_msp DECIMAL(10, 2) NOT NULL,
            expected_supply_quintals DECIMAL(12, 2) NOT NULL,
            current_procurement_quintals DECIMAL(12, 2) NOT NULL,
            projected_procurement_quintals DECIMAL(12, 2) NOT NULL,
            current_inventory_quintals DECIMAL(12, 2) NOT NULL,
            available_storage_quintals DECIMAL(12, 2) NOT NULL,
            expected_demand_quintals DECIMAL(12, 2) NOT NULL,
            surplus_deficit_quintals DECIMAL(12, 2) NOT NULL,
            market_sentiment VARCHAR(20) NOT NULL DEFAULT 'BALANCED',
            estimated_procurement_price DECIMAL(10, 2) NOT NULL,
            price_explanation TEXT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_state_crop_season (state, crop, season)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))

        # Seed supply demand intelligence records
        conn.execute(text("DELETE FROM state_crop_supply_demand"))
        seed_sd = [
            ("Goa", "Paddy", "Kharif 2026", 2300.00, 48000.00, 31200.00, 45500.00, 18500.00, 28000.00, 40000.00, 5500.00, "SURPLUS", 2345.00, "Demand is steady with moderate surplus. High storage buffer supports procurement at ₹45 above MSP."),
            ("Goa", "Maize", "Kharif 2026", 2225.00, 12000.00, 8400.00, 11200.00, 4200.00, 15000.00, 16000.00, -4800.00, "DEFICIT", 2360.00, "Feed mill demand exceeds local arrivals. Deficit pressure elevates procurement estimate to ₹2,360/Q."),
            ("Maharashtra", "Soybean", "Kharif 2026", 4892.00, 320000.00, 215000.00, 298000.00, 82000.00, 140000.00, 280000.00, 18000.00, "SURPLUS", 4980.00, "High crushing demand balances robust crop harvest. Price premium remains above MSP baseline."),
            ("Maharashtra", "Cotton", "Kharif 2026", 7121.00, 195000.00, 142000.00, 188000.00, 54000.00, 95000.00, 210000.00, -22000.00, "DEFICIT", 7450.00, "Textile export inquiries and tight local stocks lift procurement price ₹329 over MSP."),
            ("Maharashtra", "Paddy", "Kharif 2026", 2300.00, 160000.00, 112000.00, 154000.00, 48000.00, 85000.00, 150000.00, 4000.00, "BALANCED", 2330.00, "Balanced market condition. Procurement estimate tracking closely with official MSP reference."),
            ("Karnataka", "Maize", "Kharif 2026", 2225.00, 145000.00, 98000.00, 138000.00, 39000.00, 72000.00, 130000.00, 8000.00, "SURPLUS", 2260.00, "Northern Karnataka arrivals heavy. Price anchors near official MSP baseline per surplus rule."),
            ("Karnataka", "Tur (Arhar)", "Kharif 2026", 7550.00, 95000.00, 68000.00, 91000.00, 22000.00, 48000.00, 110000.00, -19000.00, "DEFICIT", 7890.00, "National pulses buffer restocking creating positive procurement sentiment."),
            ("Madhya Pradesh", "Soybean", "Kharif 2026", 4892.00, 410000.00, 285000.00, 395000.00, 115000.00, 180000.00, 370000.00, 25000.00, "SURPLUS", 4950.00, "Robust Malwa plateau harvest. Storage capacity stable with modest price premium above MSP."),
            ("Madhya Pradesh", "Wheat", "Rabi 2026-27", 2275.00, 550000.00, 390000.00, 520000.00, 180000.00, 250000.00, 480000.00, 40000.00, "SURPLUS", 2315.00, "Central storage wheat buffer well-stocked. Estimated procurement price holds near MSP.")
        ]
        for s in seed_sd:
            conn.execute(text("""
            INSERT INTO state_crop_supply_demand 
            (state, crop, season, official_msp, expected_supply_quintals, current_procurement_quintals, projected_procurement_quintals, current_inventory_quintals, available_storage_quintals, expected_demand_quintals, surplus_deficit_quintals, market_sentiment, estimated_procurement_price, price_explanation)
            VALUES (:st, :cr, :se, :msp, :sup, :proc, :proj, :inv, :stor, :dem, :sur, :sent, :est_p, :expl)
            """), {
                "st": s[0], "cr": s[1], "se": s[2], "msp": s[3], "sup": s[4], "proc": s[5],
                "proj": s[6], "inv": s[7], "stor": s[8], "dem": s[9], "sur": s[10],
                "sent": s[11], "est_p": s[12], "expl": s[13]
            })
        print(f"  Inserted {len(seed_sd)} state supply/demand records.")

        print("[5/5] Migration successfully completed.")

if __name__ == "__main__":
    migrate()

import pymysql

def run_migration():
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `crop_metadata` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `crop_name` VARCHAR(100) NOT NULL UNIQUE,
          `category` VARCHAR(50) NOT NULL,
          `season` VARCHAR(50) NOT NULL,
          `is_perishable` TINYINT(1) NOT NULL DEFAULT 0,
          `shelf_life_days` INT NOT NULL,
          `urgency_level` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'LOW',
          `perishability_score` DECIMAL(4,2) NOT NULL DEFAULT 0.20,
          `storage_requirements` VARCHAR(255) NOT NULL,
          `demand_patterns` VARCHAR(255) NOT NULL,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_crop_perish` (`is_perishable`),
          INDEX `idx_crop_season` (`season`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS `alerts` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `alert_code` VARCHAR(50) NOT NULL UNIQUE,
          `scope` ENUM('CENTRE', 'GOVERNMENT') NOT NULL,
          `centre_id` VARCHAR(50) NULL,
          `state` VARCHAR(100) NULL,
          `district` VARCHAR(100) NULL,
          `alert_type` VARCHAR(100) NOT NULL,
          `severity` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
          `what` TEXT NOT NULL,
          `where_location` VARCHAR(255) NOT NULL,
          `when_timestamp` DATETIME NOT NULL,
          `why` TEXT NOT NULL,
          `recommended_action` TEXT NOT NULL,
          `is_resolved` TINYINT(1) DEFAULT 0,
          `resolved_by` VARCHAR(100) NULL,
          `resolved_at` DATETIME NULL,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_alert_scope` (`scope`),
          INDEX `idx_alert_centre` (`centre_id`),
          INDEX `idx_alert_severity` (`severity`),
          INDEX `idx_alert_resolved` (`is_resolved`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        crops_seed = [
          ('Paddy', 'GRAIN', 'Kharif', 0, 365, 'LOW', 0.15, 'Dry aerated godowns / moisture < 14%', 'YEAR_ROUND_STABLE'),
          ('Wheat', 'GRAIN', 'Rabi', 0, 365, 'LOW', 0.15, 'Dry ventilated silos / moisture < 12%', 'YEAR_ROUND_STABLE'),
          ('Maize', 'GRAIN', 'Kharif', 0, 240, 'LOW', 0.25, 'Aspirated dry bins / moisture < 13.5%', 'YEAR_ROUND_STABLE'),
          ('Soybean', 'OILSEED', 'Kharif', 0, 180, 'MEDIUM', 0.40, 'Cool moisture-controlled storage / moisture < 11%', 'HIGH_PEAK_HARVEST'),
          ('Cotton', 'FIBER', 'Kharif', 0, 300, 'LOW', 0.20, 'Covered dry bale sheds / fire protected', 'HIGH_PEAK_HARVEST'),
          ('Tur (Arhar)', 'PULSE', 'Kharif', 0, 300, 'LOW', 0.30, 'Hermetic fumigated godowns / moisture < 10%', 'YEAR_ROUND_STABLE'),
          ('Moong', 'PULSE', 'Kharif', 0, 270, 'LOW', 0.30, 'Hermetic dry storage / pest monitored', 'YEAR_ROUND_STABLE'),
          ('Urad', 'PULSE', 'Kharif', 0, 270, 'LOW', 0.30, 'Cool dry warehouse / moisture < 11%', 'YEAR_ROUND_STABLE'),
          ('Groundnut', 'OILSEED', 'Kharif', 0, 180, 'MEDIUM', 0.45, 'Well-ventilated pod stacks / moisture < 9%', 'HIGH_PEAK_HARVEST'),
          ('Gram (Chana)', 'PULSE', 'Rabi', 0, 300, 'LOW', 0.25, 'Hermetic moisture-controlled silos', 'YEAR_ROUND_STABLE'),
          ('Mustard', 'OILSEED', 'Rabi', 0, 240, 'LOW', 0.35, 'Cool dry bins / moisture < 8%', 'SEASONAL_FESTIVE'),
          ('Sugarcane', 'COMMERCIAL', 'All-Season', 1, 3, 'CRITICAL', 0.95, 'Direct mill transit / crushing within 48h of harvest', 'HIGH_PEAK_HARVEST'),
          ('Bajra', 'MILLET', 'Kharif', 0, 240, 'LOW', 0.20, 'Dry aerated bins / moisture < 12%', 'YEAR_ROUND_STABLE'),
          ('Pulses', 'PULSE', 'Kharif', 0, 270, 'LOW', 0.30, 'Dry hermetic bags / moisture < 11%', 'YEAR_ROUND_STABLE'),
          ('Tomato', 'PERISHABLE_VEGETABLE', 'Kharif/Rabi', 1, 7, 'CRITICAL', 0.90, 'Cold Chain (10-12°C, 85-90% RH) / Reefer Transit', 'HIGH_PEAK_HARVEST'),
          ('Potato', 'PERISHABLE_VEGETABLE', 'Rabi', 1, 60, 'MEDIUM', 0.60, 'Cold Storage (4-7°C, 95% RH) / Dark ventilated', 'YEAR_ROUND_STABLE'),
          ('Onion', 'PERISHABLE_VEGETABLE', 'Rabi/Kharif', 1, 45, 'HIGH', 0.70, 'Well-ventilated chawls / ambient RH < 65%', 'SEASONAL_FESTIVE')
        ]
        cur.executemany("""
          INSERT INTO `crop_metadata` 
          (`crop_name`, `category`, `season`, `is_perishable`, `shelf_life_days`, `urgency_level`, `perishability_score`, `storage_requirements`, `demand_patterns`)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
          ON DUPLICATE KEY UPDATE 
          category=VALUES(category), season=VALUES(season), is_perishable=VALUES(is_perishable), 
          shelf_life_days=VALUES(shelf_life_days), urgency_level=VALUES(urgency_level), 
          perishability_score=VALUES(perishability_score), storage_requirements=VALUES(storage_requirements), 
          demand_patterns=VALUES(demand_patterns);
        """, crops_seed)

        alerts_seed = [
          ('ALT-CTR-2026-001', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'CAPACITY_PREDICTED_EXCEED', 'CRITICAL',
           'Yard storage and daily processing capacity predicted to exceed 92% within 48 hours.',
           'Sanquelim Krishi Upaj Mandi, North Goa', '2026-10-01 08:30:00',
           'Arrival velocity surge from 42 booked farmer lots (1,240 Q) exceeds daily processing gate threshold (800 Q).',
           'Activate secondary weighing bay, adjust booking slots, and notify alternative centre CENTRE-GOA-02.', 0),

          ('ALT-CTR-2026-002', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'STORAGE_SHORTAGE', 'HIGH',
           'Storage godown stack usage reached 88% capacity (17,600 Q / 20,000 Q).',
           'Sanquelim Krishi Upaj Mandi Godown A & B', '2026-10-01 09:15:00',
           'Cumulative inward procurement pace over past 5 days has outpaced outward rail/road dispatch by 320 Q/day.',
           'Schedule immediate evacuation of 500 Q Paddy buffer to state warehouse or flour mills.', 0),

          ('ALT-CTR-2026-003', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'CONGESTION_ALERT', 'HIGH',
           'Gate queue congestion index reached HIGH with 18 tractor trolleys waiting outside Gate 2.',
           'North Goa Gate 2 Weighbridge Entrance', '2026-10-01 10:00:00',
           'Simultaneous morning slot arrivals combined with a 25-minute calibration delay on Weighbridge WB-01.',
           'Deploy traffic marshals to split arrivals between Weighbridge WB-01 and auxiliary platform WB-02.', 0),

          ('ALT-CTR-2026-004', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'TRUCK_SHORTAGE', 'MEDIUM',
           'Shortfall of 3 heavy-duty 200Q evacuation trucks for scheduled evening dispatch.',
           'Logistics Dispatch Bay 4, Sanquelim', '2026-10-01 11:00:00',
           'Transporter fleet delayed on Belagavi-Goa ghat section due to road maintenance.',
           'Request emergency transporter re-allotment from Central Logistics Pool or State Agricoop fleet.', 0),

          ('ALT-CTR-2026-005', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'BARDAN_SHORTAGE', 'MEDIUM',
           'Bardan (50kg jute bags) stock below 5-day safety buffer (Available: 3,200 bags, Required: 4,800 bags).',
           'Inventory Warehouse C, Sanquelim', '2026-10-01 11:30:00',
           'Higher-than-expected small-bag packing requests from local paddy cultivators.',
           'Requisition 2,000 standard Class-A gunny bags from Mapusa Regional Depot.', 0),

          ('ALT-CTR-2026-006', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'ANOMALY_REVIEW', 'HIGH',
           'Potential Anomaly / Requires Review: 45% weight mismatch on procurement lot PRC-CENTRE-GOA-01-0042.',
           'Weighbridge Station WB-01, Sanquelim', '2026-10-01 12:15:00',
           'Gross weighed quantity (145.0 Q) exceeds pre-registered booking expectation (100.0 Q) by 45%.',
           'Conduct mandatory supervisor verification and re-tare empty trolley before approving final receipt.', 0),

          ('ALT-CTR-2026-007', 'CENTRE', 'CENTRE-GOA-01', 'Goa', 'North Goa', 'PAYMENT_OPERATIONAL_ISSUE', 'MEDIUM',
           '5 DBT payment records returned IFSC bank validation warnings.',
           'Direct DBT Settlement Desk, Sanquelim', '2026-10-01 13:00:00',
           'Recent rural cooperative bank IFSC migration to amalgamated national bank code format.',
           'Contact cultivators via SMS/agent to confirm updated IFSC branch code before re-submitting DBT batch.', 0),

          ('ALT-GOV-2026-001', 'GOVERNMENT', None, 'Maharashtra', 'Nashik', 'CENTRES_APPROACHING_CAPACITY', 'CRITICAL',
           '3 Procurement Centres in Nashik district predicted to reach full capacity (>95%) within 72 hours.',
           'Niphad, Malegaon & Dindori APMC Hubs, Nashik, Maharashtra', '2026-10-01 09:00:00',
           'Coinciding peak harvest arrivals of Soybean and Maize across Godavari canal catchment area.',
           'Direct district administration to expand yard overflow godowns and open temporary satellite procurement points.', 0),

          ('ALT-GOV-2026-002', 'GOVERNMENT', None, 'Karnataka', 'Belagavi', 'REGIONAL_STORAGE_SHORTAGE', 'HIGH',
           'Belagavi district aggregate warehouse utilization reached 89.4% with 48,000 Q stock.',
           'District Food & Civil Supplies Silo Network, Belagavi, Karnataka', '2026-10-01 09:30:00',
           'Inter-state procurement inflows from border talukas created unexpected 12,000 Q buffer accumulation.',
           'Authorize inter-district rail freight movement of 15,000 Q Maize to deficit coastal feed plants in Goa & Karwar.', 0),

          ('ALT-GOV-2026-003', 'GOVERNMENT', None, 'Maharashtra', 'Nagpur', 'TRUCK_SHORTAGE_REGIONAL', 'HIGH',
           'Regional truck deficit of 18 carrier units across Vidarbha cotton procurement belt.',
           'Katol, Saoner & Umred Procurement Centres, Nagpur, Maharashtra', '2026-10-01 10:15:00',
           'High volume cotton bale dispatch demand exceeding registered district transport contractor capacity.',
           'Issue state transport pool mobilization order; divert 20 idle carrier trucks from Wardha corridor.', 0),

          ('ALT-GOV-2026-004', 'GOVERNMENT', None, 'Madhya Pradesh', 'Indore', 'CONGESTION_HOTSPOT', 'CRITICAL',
           'Congestion hotspot developing at Sanwer & Indore Krishi Upaj Mandis: Average processing latency > 4.5 hours.',
           'Malwa Plateau Procurement Corridor, Madhya Pradesh', '2026-10-01 10:45:00',
           'Soybean arrival influx concentrated between 09:00 AM - 12:00 PM due to weather forecast fears.',
           'Enforce staggered slot schedules and advise farmers in Mhow & Depalpur to redirect to Ujjain sub-yards.', 0),

          ('ALT-GOV-2026-005', 'GOVERNMENT', None, 'Goa', 'North Goa', 'SUPPLY_DEFICIT_WARNING', 'HIGH',
           'State-level Maize feed supply deficit projected at -4,800 Q against poultry processing demand.',
           'Statewide Food & Poultry Feed Supply Directorate, Goa', '2026-10-01 11:30:00',
           'Local production fulfills only 62% of feed mill commitments; seasonal imports from Belagavi delayed.',
           'Facilitate expedited inter-state green corridor transit for incoming grain carriers from Chikkodi Mandi.', 0),

          ('ALT-GOV-2026-006', 'GOVERNMENT', None, 'Maharashtra', 'Kolhapur', 'PERISHABLE_TRANSPORT_RISK', 'CRITICAL',
           'High-priority Perishable Sugarcane transport bottleneck: 1,400 Q cut cane facing crushing delay > 36 hours.',
           'Shirol & Karvir Cane Procurement Stations, Kolhapur, Maharashtra', '2026-10-01 12:00:00',
           'Sugarcane sucrose inversion risk escalating rapidly; truck turnaround slowed by highway bridge repairs.',
           'Assign top green-channel transport priority; re-route cane logistics through bypass arterial route.', 0),

          ('ALT-GOV-2026-007', 'GOVERNMENT', None, 'Goa', 'South Goa', 'ANOMALY_PATTERN_CONCENTRATION', 'HIGH',
           'Anomaly Pattern Concentration: 6 repeated moisture threshold deviations flagged in South Goa cluster.',
           'Margao and Ponda APMC Sub-Centres, South Goa', '2026-10-01 12:45:00',
           'Cluster analysis indicates consistent 16.5% - 18.0% moisture readings from common village dispatch points.',
           'Deploy state quality inspection vigilance squad to test moisture meters and inspect farm drying practices.', 0)
        ]
        cur.executemany("""
          INSERT INTO `alerts`
          (`alert_code`, `scope`, `centre_id`, `state`, `district`, `alert_type`, `severity`, `what`, `where_location`, `when_timestamp`, `why`, `recommended_action`, `is_resolved`)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
          ON DUPLICATE KEY UPDATE
          severity=VALUES(severity), what=VALUES(what), where_location=VALUES(where_location),
          when_timestamp=VALUES(when_timestamp), why=VALUES(why), recommended_action=VALUES(recommended_action);
        """, alerts_seed)

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()

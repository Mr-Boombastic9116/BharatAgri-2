import re

sql_file = "database/bharatagri_iteration2.sql"

with open(sql_file, "r", encoding="utf-8") as f:
    content = f.read()

# Add DROP TABLE if not present
drops = """DROP TABLE IF EXISTS `state_crop_supply_demand`;
DROP TABLE IF EXISTS `truck_route_predictions`;
DROP TABLE IF EXISTS `msp_prices`;
"""

if "DROP TABLE IF EXISTS `msp_prices`;" not in content:
    content = content.replace("DROP TABLE IF EXISTS `audit_logs`;", drops + "DROP TABLE IF EXISTS `audit_logs`;")

# Add centre_id to CREATE TABLE users
if "`centre_id` varchar(50) DEFAULT NULL" not in content:
    content = content.replace(
        "`role` varchar(50) NOT NULL,",
        "`role` varchar(50) NOT NULL,\n  `centre_id` varchar(50) DEFAULT NULL,"
    )

# Update bookings status to VARCHAR(50)
old_booking_status = "`status` ENUM('CONFIRMED', 'CHECKED_IN', 'COLLECTED', 'QUALITY_CHECKED', 'WEIGHED', 'PROCURED', 'STORED', 'PAYMENT_INITIATED', 'PAID', 'REJECTED', 'EXPIRED') NOT NULL DEFAULT 'CONFIRMED'"
if old_booking_status in content:
    content = content.replace(old_booking_status, "`status` VARCHAR(50) NOT NULL DEFAULT 'CONFIRMED'")

# Add quality_grade and moisture_content_pct to procurement_records
if "`quality_grade`" not in content:
    content = content.replace(
        "`crop` VARCHAR(100) NOT NULL,",
        "`crop` VARCHAR(100) NOT NULL,\n  `quality_grade` VARCHAR(20) DEFAULT 'GRADE_A',\n  `moisture_content_pct` DECIMAL(5,2) DEFAULT 12.50,"
    )
    content = content.replace(
        "`status` VARCHAR(50) DEFAULT 'CONFIRMED',",
        "`status` VARCHAR(50) DEFAULT 'CONFIRMED',\n  `warehouse_location` VARCHAR(150) NULL,"
    )

new_tables_and_seeds = """
-- -------------------------------------------------------------
-- 23. OFFICIAL MSP BENCHMARKS & PRICE INTELLIGENCE
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `msp_prices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `crop` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `crop_variant` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'Standard',
  `marketing_season` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `season_year` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `official_msp_per_quintal` decimal(10,2) NOT NULL,
  `effective_from` date NOT NULL,
  `effective_to` date NOT NULL,
  `source` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT 'Ministry of Agriculture & Farmers Welfare, Govt of India',
  `source_reference` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT 'CACP Price Policy Kharif/Rabi Notification',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_crop_season` (`crop`,`marketing_season`,`season_year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `msp_prices` (`crop`, `crop_variant`, `marketing_season`, `season_year`, `official_msp_per_quintal`, `effective_from`, `effective_to`) VALUES
('Paddy', 'Common', 'Kharif', '2026-27', 2300.00, '2026-06-01', '2027-05-31'),
('Paddy', 'Grade A', 'Kharif', '2026-27', 2320.00, '2026-06-01', '2027-05-31'),
('Maize', 'Hybrid / Standard', 'Kharif', '2026-27', 2225.00, '2026-06-01', '2027-05-31'),
('Tur (Arhar)', 'Standard Pulses', 'Kharif', '2026-27', 7550.00, '2026-06-01', '2027-05-31'),
('Moong', 'Green Gram', 'Kharif', '2026-27', 8682.00, '2026-06-01', '2027-05-31'),
('Urad', 'Black Gram', 'Kharif', '2026-27', 7400.00, '2026-06-01', '2027-05-31'),
('Groundnut', 'Pod In-shell', 'Kharif', '2026-27', 6783.00, '2026-06-01', '2027-05-31'),
('Soybean', 'Yellow', 'Kharif', '2026-27', 4892.00, '2026-06-01', '2027-05-31'),
('Cotton', 'Medium Staple', 'Kharif', '2026-27', 7121.00, '2026-06-01', '2027-05-31'),
('Cotton', 'Long Staple', 'Kharif', '2026-27', 7521.00, '2026-06-01', '2027-05-31'),
('Wheat', 'Mill Quality', 'Rabi', '2026-27', 2275.00, '2026-10-01', '2027-09-30'),
('Gram (Chana)', 'Desi', 'Rabi', '2026-27', 5440.00, '2026-10-01', '2027-09-30'),
('Mustard', 'Rapeseed / Sarson', 'Rabi', '2026-27', 5650.00, '2026-10-01', '2027-09-30');

-- -------------------------------------------------------------
-- 24. TRUCK ROUTE PREDICTIONS & LOGISTICS DISPATCH
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `truck_route_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `route_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
  `origin_centre_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `origin_centre_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `destination_centre_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `destination_centre_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `destination_state` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `crop` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity_quintals` decimal(10,2) NOT NULL,
  `truck_capacity_quintals` decimal(10,2) NOT NULL DEFAULT '200.00',
  `estimated_distance_km` decimal(8,2) NOT NULL,
  `departure_date` date NOT NULL,
  `expected_arrival_date` date NOT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PREDICTED',
  `reviewed_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `rejection_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_route_status` (`status`),
  KEY `idx_origin` (`origin_centre_id`),
  KEY `idx_dest` (`destination_centre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `truck_route_predictions` (`route_code`, `origin_centre_id`, `origin_centre_name`, `destination_centre_id`, `destination_centre_name`, `destination_state`, `crop`, `quantity_quintals`, `truck_capacity_quintals`, `estimated_distance_km`, `departure_date`, `expected_arrival_date`, `reason`, `status`) VALUES
('TRK-RTE-2026-001', 'CENTRE-GOA-01', 'Sanquelim Krishi Upaj Mandi', 'CENTRE-MH-01', 'Baramati APMC Centre', 'Maharashtra', 'Paddy', 450.00, 200.00, 310.50, '2026-10-02', '2026-10-03', 'Yard storage reaching 91% capacity. Excess paddy redirected to high-demand milling buffer.', 'PROPOSED'),
('TRK-RTE-2026-002', 'CENTRE-MH-02', 'Shirur Grain Market Yard', 'CENTRE-MH-07', 'Katol Cotton & Grain Mandi', 'Maharashtra', 'Soybean', 380.00, 200.00, 485.00, '2026-10-03', '2026-10-04', 'Inter-district stock balancing: processing oilseed deficit at Vidarbha warehouse.', 'PROPOSED'),
('TRK-RTE-2026-003', 'CENTRE-KA-01', 'Chikkodi Agriculture Mandi', 'CENTRE-GOA-03', 'Margao APMC Yard', 'Goa', 'Maize', 320.00, 200.00, 165.00, '2026-10-02', '2026-10-02', 'Supplying poultry feed processing requirement at South Goa cluster.', 'APPROVED'),
('TRK-RTE-2026-004', 'CENTRE-MP-01', 'Sanwer Krishi Upaj Mandi', 'CENTRE-MH-04', 'Niphad Grain Procurement Hub', 'Maharashtra', 'Wheat', 500.00, 250.00, 520.00, '2026-10-04', '2026-10-05', 'State food security buffer redistribution from Malwa belt to Central Maharashtra.', 'SCHEDULED'),
('TRK-RTE-2026-005', 'CENTRE-GOA-04', 'Ponda Farmer Hub', 'CENTRE-KA-04', 'Hubballi Amargol APMC Yard', 'Karnataka', 'Paddy', 260.00, 200.00, 142.00, '2026-10-03', '2026-10-03', 'Seasonal drying and parboiling plant capacity utilization in Dharwad district.', 'PROPOSED');

-- -------------------------------------------------------------
-- 25. STATE CROP SUPPLY & DEMAND ESTIMATES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `state_crop_supply_demand` (
  `id` int NOT NULL AUTO_INCREMENT,
  `state` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `crop` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `season` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Kharif 2026',
  `official_msp` decimal(10,2) NOT NULL,
  `expected_supply_quintals` decimal(12,2) NOT NULL,
  `current_procurement_quintals` decimal(12,2) NOT NULL,
  `projected_procurement_quintals` decimal(12,2) NOT NULL,
  `current_inventory_quintals` decimal(12,2) NOT NULL,
  `available_storage_quintals` decimal(12,2) NOT NULL,
  `expected_demand_quintals` decimal(12,2) NOT NULL,
  `surplus_deficit_quintals` decimal(12,2) NOT NULL,
  `market_sentiment` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'BALANCED',
  `estimated_procurement_price` decimal(10,2) NOT NULL,
  `price_explanation` text COLLATE utf8mb4_unicode_ci,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_state_crop_season` (`state`,`crop`,`season`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `state_crop_supply_demand` (`state`, `crop`, `season`, `official_msp`, `expected_supply_quintals`, `current_procurement_quintals`, `projected_procurement_quintals`, `current_inventory_quintals`, `available_storage_quintals`, `expected_demand_quintals`, `surplus_deficit_quintals`, `market_sentiment`, `estimated_procurement_price`, `price_explanation`) VALUES
('Goa', 'Paddy', 'Kharif 2026', 2300.00, 48000.00, 31200.00, 45500.00, 18500.00, 28000.00, 40000.00, 5500.00, 'SURPLUS', 2345.00, 'Demand is steady with moderate surplus. High storage buffer supports procurement at ₹45 above MSP.'),
('Goa', 'Maize', 'Kharif 2026', 2225.00, 12000.00, 8400.00, 11200.00, 4200.00, 15000.00, 16000.00, -4800.00, 'DEFICIT', 2360.00, 'Feed mill demand exceeds local arrivals. Deficit pressure elevates procurement estimate to ₹2,360/Q.'),
('Maharashtra', 'Soybean', 'Kharif 2026', 4892.00, 320000.00, 215000.00, 298000.00, 82000.00, 140000.00, 280000.00, 18000.00, 'SURPLUS', 4980.00, 'High crushing demand balances robust crop harvest. Price premium remains above MSP baseline.'),
('Maharashtra', 'Cotton', 'Kharif 2026', 7121.00, 195000.00, 142000.00, 188000.00, 54000.00, 95000.00, 210000.00, -22000.00, 'DEFICIT', 7450.00, 'Textile export inquiries and tight local stocks lift procurement price ₹329 over MSP.'),
('Maharashtra', 'Paddy', 'Kharif 2026', 2300.00, 160000.00, 112000.00, 154000.00, 48000.00, 85000.00, 150000.00, 4000.00, 'BALANCED', 2330.00, 'Balanced market condition. Procurement estimate tracking closely with official MSP reference.'),
('Karnataka', 'Maize', 'Kharif 2026', 2225.00, 145000.00, 98000.00, 138000.00, 39000.00, 72000.00, 130000.00, 8000.00, 'SURPLUS', 2260.00, 'Northern Karnataka arrivals heavy. Price anchors near official MSP baseline per surplus rule.'),
('Karnataka', 'Tur (Arhar)', 'Kharif 2026', 7550.00, 95000.00, 68000.00, 91000.00, 22000.00, 48000.00, 110000.00, -19000.00, 'DEFICIT', 7890.00, 'National pulses buffer restocking creating positive procurement sentiment.'),
('Madhya Pradesh', 'Soybean', 'Kharif 2026', 4892.00, 410000.00, 285000.00, 395000.00, 115000.00, 180000.00, 370000.00, 25000.00, 'SURPLUS', 4950.00, 'Robust Malwa plateau harvest. Storage capacity stable with modest price premium above MSP.'),
('Madhya Pradesh', 'Wheat', 'Rabi 2026-27', 2275.00, 550000.00, 390000.00, 520000.00, 180000.00, 250000.00, 480000.00, 40000.00, 'SURPLUS', 2315.00, 'Central storage wheat buffer well-stocked. Estimated procurement price holds near MSP.');
"""

if "CREATE TABLE IF NOT EXISTS `msp_prices`" not in content:
    content = content.replace("SET FOREIGN_KEY_CHECKS = 1;", new_tables_and_seeds + "\nSET FOREIGN_KEY_CHECKS = 1;")

with open(sql_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated database/bharatagri_iteration2.sql successfully!")

"""
BharatAgri Iteration 2 - Deterministic Dataset & Database Generator
Generates realistic agricultural procurement data and complete MySQL schema.
Seed: 42
Target:
 - 2,000+ Farmers
 - 25+ Procurement Centres
 - 10,000+ Bookings
 - 8,000+ Collections, Quality Checks, Weighments, Procurements, Storage Lots
 - 5,000+ Payments
 - Bardan Inventory & Forecasts
 - Smart Truck logistics records
 - Realistic anomalies & complaints
 - AI training datasets
"""

import os
import random
import datetime
import json
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DEMO_BCRYPT_HASH = "$2b$12$IAqE5g26rI5lLTRqGvb3G.F/V2N9YnxAPYOjd9ICnc7ZGX7zLGXG2" # BharatAgri@2026
LEGACY_BCRYPT_HASH = "$2b$12$IAqE5g26rI5lLTRqGvb3G.F/V2N9YnxAPYOjd9ICnc7ZGX7zLGXG2" # BharatAgri@2026

CROPS = [
    {"name": "Paddy", "msp": 2300, "season": "Kharif", "yield_range": (35, 60), "moisture_std": 14.0},
    {"name": "Wheat", "msp": 2275, "season": "Rabi", "yield_range": (30, 50), "moisture_std": 12.0},
    {"name": "Maize", "msp": 2090, "season": "Kharif", "yield_range": (40, 70), "moisture_std": 14.0},
    {"name": "Cotton", "msp": 7120, "season": "Kharif", "yield_range": (15, 30), "moisture_std": 8.0},
    {"name": "Soybean", "msp": 4892, "season": "Kharif", "yield_range": (20, 35), "moisture_std": 12.0},
    {"name": "Mustard", "msp": 5650, "season": "Rabi", "yield_range": (15, 25), "moisture_std": 9.0},
    {"name": "Pulses", "msp": 6600, "season": "Kharif", "yield_range": (10, 20), "moisture_std": 12.0},
    {"name": "Bajra", "msp": 2500, "season": "Kharif", "yield_range": (25, 45), "moisture_std": 13.0},
    {"name": "Groundnut", "msp": 6377, "season": "Kharif", "yield_range": (18, 32), "moisture_std": 8.0},
    {"name": "Sugarcane", "msp": 340, "season": "Annual", "yield_range": (600, 900), "moisture_std": 20.0}
]

GEOGRAPHY = [
    {
        "state": "Goa",
        "state_code": "GA",
        "districts": [
            {"name": "North Goa", "blocks": ["Bicholim", "Bardez", "Pernem", "Sattari", "Tiswadi"]},
            {"name": "South Goa", "blocks": ["Salcete", "Ponda", "Mormugao", "Quepem", "Sanguem", "Canacona"]}
        ]
    },
    {
        "state": "Maharashtra",
        "state_code": "MH",
        "districts": [
            {"name": "Pune", "blocks": ["Haveli", "Baramati", "Shirur", "Junnar", "Khed"]},
            {"name": "Nashik", "blocks": ["Niphad", "Malegaon", "Yeola", "Dindori", "Sinnar"]},
            {"name": "Nagpur", "blocks": ["Kamptee", "Katol", "Narkhed", "Saoner", "Umred"]},
            {"name": "Kolhapur", "blocks": ["Karvir", "Hatkanangle", "Shirol", "Radhanagari", "Kagal"]}
        ]
    },
    {
        "state": "Karnataka",
        "state_code": "KA",
        "districts": [
            {"name": "Belagavi", "blocks": ["Athani", "Bailhongal", "Chikkodi", "Gokak", "Hukkeri"]},
            {"name": "Dharwad", "blocks": ["Hubballi", "Dharwad", "Kalghatgi", "Kundgol", "Navalgund"]}
        ]
    },
    {
        "state": "Madhya Pradesh",
        "state_code": "MP",
        "districts": [
            {"name": "Indore", "blocks": ["Depalpur", "Sanwer", "Mhow"]},
            {"name": "Ujjain", "blocks": ["Badnagar", "Ghatiya", "Khachrod", "Mahidpur", "Tarana"]}
        ]
    }
]

FIRST_NAMES = [
    "Ramesh", "Suresh", "Rajesh", "Anil", "Santosh", "Vijay", "Ganesh", "Mahesh", "Sunil", "Pravin",
    "Dilip", "Ashok", "Kishore", "Sachin", "Dattatray", "Pandurang", "Maruti", "Tukaram", "Vitthal", "Baburao",
    "Pooja", "Sunita", "Anita", "Shobha", "Rekha", "Usha", "Lata", "Vandana", "Meena", "Sangita",
    "Devendra", "Shivaji", "Balaram", "Raghav", "Govind", "Mukesh", "Pradeep", "Nitin", "Deepak", "Vikram"
]

LAST_NAMES = [
    "Patil", "Deshmukh", "Jadhav", "Pawar", "Shinde", "Kadam", "Chavan", "Gaekwad", "Sawant", "Naik",
    "Fernandes", "Kamath", "Shenoy", "Borkar", "Rane", "Gawas", "Prabhu", "Kulkarni", "Joshi", "Bhide",
    "Bhosale", "More", "Gawande", "Thakur", "Rathore", "Yadav", "Sharma", "Verma", "Choudhary", "Patel"
]

def generate_full_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def get_random_geo():
    st = random.choice(GEOGRAPHY)
    dist = random.choice(st["districts"])
    blk = random.choice(dist["blocks"])
    village = f"{blk} Village-{random.randint(1, 20)}"
    return st["state"], st["state_code"], dist["name"], blk, village

def main():
    print("Starting BharatAgri Iteration 2 Dataset Generation (Seed: 42)...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_dir = os.path.join(base_dir, "database")
    ml_data_dir = os.path.join(base_dir, "ml", "data")
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(ml_data_dir, exist_ok=True)

    sql_lines = []
    def emit(sql):
        sql_lines.append(sql)

    # 1. Header & Database Setup
    emit("-- =================================================================")
    emit("-- BHARATAGRI ITERATION 2 - COMPLETE DATABASE SCHEMA & REALISTIC SEED DATA")
    emit("-- Generated deterministically (Seed: 42) for XAMPP MySQL / phpMyAdmin")
    emit("-- =================================================================")
    emit("CREATE DATABASE IF NOT EXISTS `bharatagri_iteration2` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    emit("USE `bharatagri_iteration2`;")
    emit("SET FOREIGN_KEY_CHECKS = 0;")
    emit("")

    # Drop existing tables cleanly
    tables_to_drop = [
        "audit_logs", "ai_model_metrics", "anomaly_records", "centre_congestions", "supply_forecasts",
        "complaint_status_history", "complaint_messages", "complaints",
        "bardan_forecasts", "bardan_stock", "inventory_transactions", "inventory",
        "truck_collection_routes", "truck_allocations", "truck_requests", "trucks",
        "payments", "storage_lots", "procurement_records", "weighments", "quality_checks", "collection_records",
        "qr_codes", "booking_status_history", "bookings",
        "centre_slots", "slots", "centre_capacity", "daily_capacity", "centre_holidays", "non_operational_dates", "centre_operating_days", "procurement_centres",
        "agent_farmer_assignments", "agent_regions", "agents",
        "farmer_crops", "farmer_documents", "farmers",
        "villages", "blocks", "districts", "states",
        "user_roles", "sessions", "users", "roles"
    ]
    for tbl in tables_to_drop:
        emit(f"DROP TABLE IF EXISTS `{tbl}`;")
    emit("")

    # 2. Schema DDL Definitions
    print("Writing DDL schemas...")

    emit("""-- -------------------------------------------------------------
-- 1. AUTHENTICATION & USERS
-- -------------------------------------------------------------
CREATE TABLE `roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `role_name` VARCHAR(50) NOT NULL UNIQUE,
  `description` VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `roles` (`id`, `role_name`, `description`) VALUES
(1, 'FARMER', 'Registered agricultural producer with slot booking and pass verification rights'),
(2, 'AGENT', 'Assisting Village / CSC / Panchayat operator helping farmers in procurement tasks'),
(3, 'PROCUREMENT_CENTRE', 'Procurement Centre staff managing capacity, weighment, quality and lots'),
(4, 'GOVERNMENT', 'Government and administrative authority overseeing national and district procurement');

CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(100) NOT NULL UNIQUE,
  `name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(150) NULL,
  `mobile` VARCHAR(20) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('farmer', 'agent', 'centre', 'government') NOT NULL,
  `preferred_language` VARCHAR(20) DEFAULT 'English',
  `status` VARCHAR(20) DEFAULT 'ACTIVE',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_user_role` (`role`),
  INDEX `idx_user_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 2. GEOGRAPHY
-- -------------------------------------------------------------
CREATE TABLE `states` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(10) NOT NULL UNIQUE,
  `name` VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `districts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `state_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  FOREIGN KEY (`state_id`) REFERENCES `states` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `blocks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `district_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  FOREIGN KEY (`district_id`) REFERENCES `districts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `villages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `block_id` INT NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  FOREIGN KEY (`block_id`) REFERENCES `blocks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 3. FARMERS & PROFILES
-- -------------------------------------------------------------
CREATE TABLE `farmers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `farmer_code` VARCHAR(50) NOT NULL UNIQUE,
  `user_id` VARCHAR(100) NOT NULL UNIQUE,
  `name` VARCHAR(150) NOT NULL,
  `mobile` VARCHAR(20) NOT NULL,
  `email` VARCHAR(150) NULL,
  `dob` DATE NULL,
  `gender` VARCHAR(10) DEFAULT 'Male',
  `address` TEXT NULL,
  `state` VARCHAR(100) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `taluka` VARCHAR(100) NOT NULL,
  `village` VARCHAR(100) NOT NULL,
  `land_area_hectares` DECIMAL(8,2) NOT NULL DEFAULT 2.50,
  `ekyc_status` VARCHAR(20) DEFAULT 'VERIFIED',
  `aadhaar_masked` VARCHAR(20) DEFAULT 'XXXX-XXXX-1234',
  `bank_name` VARCHAR(100) DEFAULT 'State Bank of India',
  `bank_account_no` VARCHAR(50) DEFAULT '10293847561',
  `bank_ifsc` VARCHAR(20) DEFAULT 'SBIN0001234',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_farmer_district` (`district`),
  INDEX `idx_farmer_mobile` (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `farmer_crops` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `farmer_id` INT NOT NULL,
  `crop_name` VARCHAR(100) NOT NULL,
  `season` VARCHAR(50) NOT NULL,
  `sowing_date` DATE NULL,
  `expected_harvest_date` DATE NULL,
  `estimated_quantity_quintals` DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (`farmer_id`) REFERENCES `farmers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 4. AGENTS
-- -------------------------------------------------------------
CREATE TABLE `agents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `agent_code` VARCHAR(50) NOT NULL UNIQUE,
  `user_id` VARCHAR(100) NOT NULL UNIQUE,
  `agency_type` VARCHAR(50) DEFAULT 'CSC',
  `organization_name` VARCHAR(150) NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `mobile` VARCHAR(20) NOT NULL,
  `email` VARCHAR(150) NULL,
  `state` VARCHAR(100) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `taluka` VARCHAR(100) NOT NULL,
  `status` VARCHAR(20) DEFAULT 'ACTIVE',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `agent_farmer_assignments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `agent_id` INT NOT NULL,
  `farmer_id` INT NOT NULL,
  `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`farmer_id`) REFERENCES `farmers` (`id`) ON DELETE CASCADE,
  UNIQUE(`agent_id`, `farmer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 5. PROCUREMENT CENTRES, SCHEDULES & CAPACITY
-- -------------------------------------------------------------
CREATE TABLE `procurement_centres` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL UNIQUE,
  `centre_name` VARCHAR(150) NOT NULL,
  `location` VARCHAR(255) NOT NULL,
  `state` VARCHAR(100) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `contact_number` VARCHAR(20) NOT NULL,
  `operating_days` VARCHAR(255) DEFAULT 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday',
  `opening_time` VARCHAR(20) DEFAULT '09:00 AM',
  `closing_time` VARCHAR(20) DEFAULT '05:00 PM',
  `supported_crops` VARCHAR(255) DEFAULT 'Paddy,Wheat,Maize,Soybean,Cotton',
  `max_daily_capacity_quintals` DECIMAL(10,2) DEFAULT 800.00,
  `total_storage_capacity_quintals` DECIMAL(12,2) DEFAULT 15000.00,
  `current_storage_usage_quintals` DECIMAL(12,2) DEFAULT 3200.00,
  `status` VARCHAR(20) DEFAULT 'OPERATIONAL',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_centre_district` (`district`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `daily_capacity` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `date` DATE NOT NULL,
  `max_quintals_per_day` DECIMAL(10,2) NOT NULL DEFAULT 800.00,
  UNIQUE(`centre_id`, `date`),
  INDEX `idx_cap_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `non_operational_dates` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `date` DATE NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(`centre_id`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `slots` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `date` DATE NOT NULL,
  `start_time` VARCHAR(20) NOT NULL,
  `end_time` VARCHAR(20) NOT NULL,
  `max_capacity` INT NOT NULL DEFAULT 20,
  INDEX `idx_slot_centre_date` (`centre_id`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 6. BOOKINGS & PASSES
-- -------------------------------------------------------------
CREATE TABLE `bookings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `appointment_id` VARCHAR(50) NOT NULL UNIQUE,
  `booking_id` VARCHAR(50) NULL,
  `farmer_id` VARCHAR(100) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `slot_id` INT NOT NULL,
  `crop` VARCHAR(100) NOT NULL,
  `quantity` DECIMAL(10,2) NOT NULL,
  `status` ENUM('CONFIRMED', 'CHECKED_IN', 'COLLECTED', 'QUALITY_CHECKED', 'WEIGHED', 'PROCURED', 'STORED', 'PAYMENT_INITIATED', 'PAID', 'REJECTED', 'EXPIRED') NOT NULL DEFAULT 'CONFIRMED',
  `qr_token` VARCHAR(100) NOT NULL UNIQUE,
  `redirected_from_centre_id` VARCHAR(50) NULL,
  `redirection_reason` VARCHAR(255) NULL,
  `verified_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`slot_id`) REFERENCES `slots` (`id`) ON DELETE RESTRICT,
  INDEX `idx_booking_farmer` (`farmer_id`),
  INDEX `idx_booking_centre` (`centre_id`),
  INDEX `idx_booking_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `booking_status_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `booking_id` INT NOT NULL,
  `old_status` VARCHAR(50) NULL,
  `new_status` VARCHAR(50) NOT NULL,
  `changed_by` VARCHAR(100) NOT NULL,
  `notes` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `qr_codes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` VARCHAR(100) NOT NULL,
  `qr_code_value` VARCHAR(150) NOT NULL UNIQUE,
  `is_used` TINYINT(1) DEFAULT 0,
  `used_at` DATETIME NULL,
  `expires_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 7. END-TO-END TRACEABILITY PIPELINE
-- -------------------------------------------------------------
CREATE TABLE `collection_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `collection_id` VARCHAR(50) NOT NULL UNIQUE,
  `booking_id` INT NOT NULL,
  `farmer_id` VARCHAR(100) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `crop` VARCHAR(100) NOT NULL,
  `collected_quantity` DECIMAL(10,2) NOT NULL,
  `collection_date` DATE NOT NULL,
  `collection_method` VARCHAR(50) DEFAULT 'DIRECT_CENTRE',
  `truck_number` VARCHAR(50) NULL,
  `collected_by` VARCHAR(100) NOT NULL,
  `status` VARCHAR(50) DEFAULT 'COLLECTED',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `quality_checks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `check_id` VARCHAR(50) NOT NULL UNIQUE,
  `collection_id` VARCHAR(50) NOT NULL,
  `moisture_content_pct` DECIMAL(5,2) NOT NULL,
  `foreign_matter_pct` DECIMAL(5,2) NOT NULL,
  `broken_grains_pct` DECIMAL(5,2) NOT NULL,
  `quality_grade` VARCHAR(20) NOT NULL DEFAULT 'GRADE_A',
  `inspector_name` VARCHAR(100) NOT NULL,
  `passed` TINYINT(1) NOT NULL DEFAULT 1,
  `remarks` TEXT NULL,
  `checked_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`collection_id`) REFERENCES `collection_records` (`collection_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `weighments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `weighment_id` VARCHAR(50) NOT NULL UNIQUE,
  `collection_id` VARCHAR(50) NOT NULL,
  `gross_weight_quintals` DECIMAL(10,2) NOT NULL,
  `tare_weight_quintals` DECIMAL(10,2) NOT NULL,
  `net_weight_quintals` DECIMAL(10,2) NOT NULL,
  `weighbridge_id` VARCHAR(50) DEFAULT 'WB-01',
  `operator_name` VARCHAR(100) NOT NULL,
  `weighed_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`collection_id`) REFERENCES `collection_records` (`collection_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `procurement_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `procurement_id` VARCHAR(50) NOT NULL UNIQUE,
  `booking_id` INT NOT NULL,
  `collection_id` VARCHAR(50) NOT NULL,
  `farmer_id` VARCHAR(100) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `crop` VARCHAR(100) NOT NULL,
  `procured_quantity_quintals` DECIMAL(10,2) NOT NULL,
  `msp_rate_per_quintal` DECIMAL(10,2) NOT NULL,
  `total_procurement_value` DECIMAL(12,2) NOT NULL,
  `status` VARCHAR(50) DEFAULT 'CONFIRMED',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`collection_id`) REFERENCES `collection_records` (`collection_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `storage_lots` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `lot_id` VARCHAR(60) NOT NULL UNIQUE,
  `procurement_id` VARCHAR(50) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `crop` VARCHAR(100) NOT NULL,
  `quantity_quintals` DECIMAL(10,2) NOT NULL,
  `warehouse_name` VARCHAR(150) NOT NULL,
  `stack_number` VARCHAR(50) NOT NULL,
  `storage_date` DATE NOT NULL,
  `status` VARCHAR(50) DEFAULT 'STORED',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`procurement_id`) REFERENCES `procurement_records` (`procurement_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `payments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `payment_id` VARCHAR(50) NOT NULL UNIQUE,
  `procurement_id` VARCHAR(50) NOT NULL,
  `farmer_id` VARCHAR(100) NOT NULL,
  `amount` DECIMAL(12,2) NOT NULL,
  `msp_rate` DECIMAL(10,2) NOT NULL,
  `quantity_quintals` DECIMAL(10,2) NOT NULL,
  `payment_mode` VARCHAR(50) DEFAULT 'DBT_NEFT',
  `payment_status` ENUM('PENDING', 'INITIATED', 'PAID', 'FAILED') NOT NULL DEFAULT 'INITIATED',
  `transaction_ref` VARCHAR(100) NULL,
  `initiated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `paid_at` DATETIME NULL,
  `remarks` VARCHAR(255) NULL,
  FOREIGN KEY (`procurement_id`) REFERENCES `procurement_records` (`procurement_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 8. TRUCKS & LOGISTICS OPTIMIZATION
-- -------------------------------------------------------------
CREATE TABLE `trucks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `truck_number` VARCHAR(50) NOT NULL UNIQUE,
  `driver_name` VARCHAR(100) NOT NULL,
  `driver_phone` VARCHAR(20) NOT NULL,
  `capacity_quintals` DECIMAL(10,2) NOT NULL,
  `current_status` VARCHAR(50) DEFAULT 'AVAILABLE',
  `assigned_centre_id` VARCHAR(50) NOT NULL,
  `is_available` TINYINT(1) DEFAULT 1,
  INDEX `idx_truck_centre` (`assigned_centre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `truck_requests` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `request_code` VARCHAR(50) NOT NULL UNIQUE,
  `centre_id` VARCHAR(50) NOT NULL,
  `required_date` DATE NOT NULL,
  `required_capacity_quintals` DECIMAL(10,2) NOT NULL,
  `reason` VARCHAR(255) NOT NULL,
  `status` VARCHAR(50) DEFAULT 'PENDING',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `truck_allocations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `allocation_code` VARCHAR(50) NOT NULL UNIQUE,
  `request_id` INT NULL,
  `truck_id` INT NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `allocation_date` DATE NOT NULL,
  `assigned_quantity_quintals` DECIMAL(10,2) NOT NULL,
  `status` VARCHAR(50) DEFAULT 'ALLOCATED',
  `route_distance_km` DECIMAL(6,2) DEFAULT 25.50,
  `notes` VARCHAR(255) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`truck_id`) REFERENCES `trucks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `truck_collection_routes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `allocation_id` INT NOT NULL,
  `stop_sequence` INT NOT NULL,
  `farmer_id` VARCHAR(100) NOT NULL,
  `village_name` VARCHAR(100) NOT NULL,
  `estimated_quantity_quintals` DECIMAL(10,2) NOT NULL,
  `visited` TINYINT(1) DEFAULT 0,
  `visited_at` DATETIME NULL,
  FOREIGN KEY (`allocation_id`) REFERENCES `truck_allocations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 9. INVENTORY & BARDAN (GUNNY BAGS)
-- -------------------------------------------------------------
CREATE TABLE `inventory` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `item_type` VARCHAR(50) NOT NULL,
  `item_name` VARCHAR(100) NOT NULL,
  `current_stock` INT NOT NULL,
  `reserved_stock` INT NOT NULL DEFAULT 0,
  `unit` VARCHAR(20) NOT NULL DEFAULT 'Pieces',
  `reorder_level` INT NOT NULL DEFAULT 500,
  `last_restocked_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(`centre_id`, `item_type`, `item_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `inventory_transactions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `item_type` VARCHAR(50) NOT NULL,
  `transaction_type` ENUM('STOCK_IN', 'CONSUMED', 'DAMAGED', 'RETURNED') NOT NULL,
  `quantity` INT NOT NULL,
  `reference_id` VARCHAR(100) NULL,
  `reference_type` VARCHAR(50) NULL,
  `notes` TEXT NULL,
  `created_by` VARCHAR(100) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bardan_stock` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL UNIQUE,
  `total_bags` INT NOT NULL DEFAULT 25000,
  `bags_in_use` INT NOT NULL DEFAULT 6500,
  `bags_damaged` INT NOT NULL DEFAULT 200,
  `available_bags` INT NOT NULL DEFAULT 18300,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bardan_forecasts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `forecast_date` DATE NOT NULL,
  `current_stock` INT NOT NULL,
  `projected_consumption` INT NOT NULL,
  `projected_requirement` INT NOT NULL,
  `expected_shortage` INT NOT NULL DEFAULT 0,
  `status` ENUM('SAFE', 'LOW', 'WARNING', 'SHORTAGE') NOT NULL DEFAULT 'SAFE',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_bardan_centre` (`centre_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 10. COMPLAINTS & GRIEVANCE
-- -------------------------------------------------------------
CREATE TABLE `complaints` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `complaint_code` VARCHAR(50) NOT NULL UNIQUE,
  `user_id` VARCHAR(100) NOT NULL,
  `user_role` VARCHAR(50) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `priority` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
  `subject` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `status` ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED') NOT NULL DEFAULT 'OPEN',
  `resolution` TEXT NULL,
  `assigned_to` VARCHAR(100) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `resolved_at` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `complaint_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `complaint_id` INT NOT NULL,
  `sender_id` VARCHAR(100) NOT NULL,
  `sender_role` VARCHAR(50) NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `complaint_status_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `complaint_id` INT NOT NULL,
  `old_status` VARCHAR(50) NULL,
  `new_status` VARCHAR(50) NOT NULL,
  `changed_by` VARCHAR(100) NOT NULL,
  `notes` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 11. AI FORECASTING, CONGESTION & ANOMALIES
-- -------------------------------------------------------------
CREATE TABLE `supply_forecasts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `crop` VARCHAR(100) NOT NULL,
  `forecast_month` INT NOT NULL,
  `forecast_year` INT NOT NULL,
  `predicted_procurement_quantity` DECIMAL(12,2) NOT NULL,
  `predicted_arrivals` DECIMAL(12,2) NOT NULL,
  `predicted_collection` DECIMAL(12,2) NOT NULL,
  `confidence_score` DECIMAL(5,2) DEFAULT 0.92,
  `model_version` VARCHAR(50) DEFAULT 'xgboost_v1.0',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `centre_congestions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `centre_id` VARCHAR(50) NOT NULL,
  `calculation_date` DATE NOT NULL,
  `predicted_arrivals` DECIMAL(10,2) NOT NULL,
  `existing_bookings_qty` DECIMAL(10,2) NOT NULL,
  `expected_collection_qty` DECIMAL(10,2) NOT NULL,
  `daily_capacity` DECIMAL(10,2) NOT NULL,
  `utilization_percent` DECIMAL(5,2) NOT NULL,
  `congestion_level` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_cong_centre_date` (`centre_id`, `calculation_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `anomaly_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `anomaly_code` VARCHAR(50) NOT NULL UNIQUE,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` VARCHAR(100) NOT NULL,
  `centre_id` VARCHAR(50) NOT NULL,
  `anomaly_type` VARCHAR(100) NOT NULL,
  `anomaly_score` DECIMAL(6,4) NOT NULL,
  `risk_level` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
  `reason` TEXT NOT NULL,
  `status` ENUM('OPEN', 'UNDER REVIEW', 'RESOLVED', 'DISMISSED') NOT NULL DEFAULT 'OPEN',
  `resolved_by` VARCHAR(100) NULL,
  `resolution_notes` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_anom_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ai_model_metrics` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `model_name` VARCHAR(100) NOT NULL,
  `model_type` VARCHAR(50) NOT NULL,
  `mae` DECIMAL(8,4) NULL,
  `rmse` DECIMAL(8,4) NULL,
  `r2_score` DECIMAL(8,4) NULL,
  `precision_score` DECIMAL(8,4) NULL,
  `recall_score` DECIMAL(8,4) NULL,
  `f1_score` DECIMAL(8,4) NULL,
  `evaluation_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `dataset_info` VARCHAR(255) DEFAULT 'Synthetic demonstration dataset (Seed 42)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------
-- 12. AUDIT LOGS
-- -------------------------------------------------------------
CREATE TABLE `audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(100) NOT NULL,
  `action` VARCHAR(100) NOT NULL,
  `entity` VARCHAR(100) NOT NULL,
  `entity_id` VARCHAR(100) NULL,
  `old_value` TEXT NULL,
  `new_value` TEXT NULL,
  `ip_address` VARCHAR(50) DEFAULT '127.0.0.1',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_audit_user` (`user_id`),
  INDEX `idx_audit_entity` (`entity`, `entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

    print("Generating Geography and Procurement Centres...")
    # Insert States, Districts, Blocks
    emit("-- -------------------------------------------------------------")
    emit("-- INSERT GEOGRAPHY")
    emit("-- -------------------------------------------------------------")
    state_id_map = {}
    dist_id_map = {}
    s_idx = 1
    d_idx = 1
    b_idx = 1
    for st in GEOGRAPHY:
        emit(f"INSERT INTO `states` (`id`, `code`, `name`) VALUES ({s_idx}, '{st['state_code']}', '{st['state']}');")
        state_id_map[st["state"]] = s_idx
        for dst in st["districts"]:
            emit(f"INSERT INTO `districts` (`id`, `state_id`, `name`) VALUES ({d_idx}, {s_idx}, '{dst['name']}');")
            dist_id_map[dst["name"]] = d_idx
            for blk in dst["blocks"]:
                emit(f"INSERT INTO `blocks` (`id`, `district_id`, `name`) VALUES ({b_idx}, {d_idx}, '{blk}');")
                b_idx += 1
            d_idx += 1
        s_idx += 1

    # Insert 25+ Procurement Centres
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT PROCUREMENT CENTRES")
    emit("-- -------------------------------------------------------------")
    centres_data = [
        {"id": "CENTRE-GOA-01", "name": "Sanquelim Krishi Upaj Mandi", "loc": "Bicholim Road, Sanquelim", "state": "Goa", "dist": "North Goa", "cap": 800.0, "crops": "Paddy,Maize,Pulses"},
        {"id": "CENTRE-GOA-02", "name": "Mapusa Agricultural Yard", "loc": "Market Complex, Mapusa", "state": "Goa", "dist": "North Goa", "cap": 750.0, "crops": "Paddy,Pulses,Sugarcane"},
        {"id": "CENTRE-GOA-03", "name": "Margao APMC Yard", "loc": "Station Road, Margao", "state": "Goa", "dist": "South Goa", "cap": 1000.0, "crops": "Paddy,Maize,Sugarcane"},
        {"id": "CENTRE-GOA-04", "name": "Ponda Farmer Hub", "loc": "Curti, Ponda", "state": "Goa", "dist": "South Goa", "cap": 700.0, "crops": "Paddy,Pulses"},
        {"id": "CENTRE-GOA-05", "name": "Valpoi Agriculture Sub-Centre", "loc": "Municipal Market, Valpoi", "state": "Goa", "dist": "North Goa", "cap": 600.0, "crops": "Paddy,Maize"},
        {"id": "CENTRE-MH-01", "name": "Baramati APMC Centre", "loc": "MIDC Area, Baramati", "state": "Maharashtra", "dist": "Pune", "cap": 1500.0, "crops": "Wheat,Maize,Soybean,Sugarcane"},
        {"id": "CENTRE-MH-02", "name": "Shirur Grain Market Yard", "loc": "Pune-Nagar Road, Shirur", "state": "Maharashtra", "dist": "Pune", "cap": 1200.0, "crops": "Wheat,Bajra,Soybean"},
        {"id": "CENTRE-MH-03", "name": "Junnar Krishi Kendra", "loc": "Kalyan Highway, Junnar", "state": "Maharashtra", "dist": "Pune", "cap": 900.0, "crops": "Soybean,Wheat,Maize"},
        {"id": "CENTRE-MH-04", "name": "Niphad Grain Procurement Hub", "loc": "Station Yard, Niphad", "state": "Maharashtra", "dist": "Nashik", "cap": 1400.0, "crops": "Wheat,Maize,Soybean"},
        {"id": "CENTRE-MH-05", "name": "Malegaon Agri Mandi", "loc": "Agra Road, Malegaon", "state": "Maharashtra", "dist": "Nashik", "cap": 1300.0, "crops": "Cotton,Wheat,Bajra"},
        {"id": "CENTRE-MH-06", "name": "Dindori Farmer Yard", "loc": "Vani Road, Dindori", "state": "Maharashtra", "dist": "Nashik", "cap": 850.0, "crops": "Soybean,Wheat,Maize"},
        {"id": "CENTRE-MH-07", "name": "Katol Cotton & Grain Mandi", "loc": "Yard-1, Katol", "state": "Maharashtra", "dist": "Nagpur", "cap": 1100.0, "crops": "Cotton,Soybean,Wheat"},
        {"id": "CENTRE-MH-08", "name": "Saoner Agri Centre", "loc": "Chhindwara Road, Saoner", "state": "Maharashtra", "dist": "Nagpur", "cap": 950.0, "crops": "Cotton,Soybean,Wheat"},
        {"id": "CENTRE-MH-09", "name": "Karvir APMC Main Yard", "loc": "Shiroli, Kolhapur", "state": "Maharashtra", "dist": "Kolhapur", "cap": 1600.0, "crops": "Sugarcane,Paddy,Soybean"},
        {"id": "CENTRE-MH-10", "name": "Shirol Procurement Station", "loc": "Jaysingpur Road, Shirol", "state": "Maharashtra", "dist": "Kolhapur", "cap": 1050.0, "crops": "Sugarcane,Soybean,Maize"},
        {"id": "CENTRE-KA-01", "name": "Chikkodi Agriculture Mandi", "loc": "Main Market, Chikkodi", "state": "Karnataka", "dist": "Belagavi", "cap": 1250.0, "crops": "Paddy,Sugarcane,Maize"},
        {"id": "CENTRE-KA-02", "name": "Gokak Commodity Yard", "loc": "Falls Road, Gokak", "state": "Karnataka", "dist": "Belagavi", "cap": 1100.0, "crops": "Maize,Cotton,Wheat"},
        {"id": "CENTRE-KA-03", "name": "Athani Farmer Center", "loc": "Bijapur Highway, Athani", "state": "Karnataka", "dist": "Belagavi", "cap": 900.0, "crops": "Sugarcane,Wheat,Bajra"},
        {"id": "CENTRE-KA-04", "name": "Hubballi Amargol APMC Yard", "loc": "Amargol, Hubballi", "state": "Karnataka", "dist": "Dharwad", "cap": 1800.0, "crops": "Cotton,Wheat,Maize,Pulses"},
        {"id": "CENTRE-KA-05", "name": "Kundgol Grain Depot", "loc": "Station Road, Kundgol", "state": "Karnataka", "dist": "Dharwad", "cap": 850.0, "crops": "Cotton,Wheat,Pulses"},
        {"id": "CENTRE-MP-01", "name": "Sanwer Krishi Upaj Mandi", "loc": "Ujjain Road, Sanwer", "state": "Madhya Pradesh", "dist": "Indore", "cap": 1500.0, "crops": "Wheat,Soybean,Mustard"},
        {"id": "CENTRE-MP-02", "name": "Depalpur Grain Yard", "loc": "Betma Road, Depalpur", "state": "Madhya Pradesh", "dist": "Indore", "cap": 1000.0, "crops": "Wheat,Soybean,Mustard"},
        {"id": "CENTRE-MP-03", "name": "Mhow Procurement Hub", "loc": "Indore Road, Mhow", "state": "Madhya Pradesh", "dist": "Indore", "cap": 950.0, "crops": "Wheat,Soybean,Maize"},
        {"id": "CENTRE-MP-04", "name": "Khachrod APMC Mandi", "loc": "Station Road, Khachrod", "state": "Madhya Pradesh", "dist": "Ujjain", "cap": 1200.0, "crops": "Wheat,Soybean,Mustard"},
        {"id": "CENTRE-MP-05", "name": "Mahidpur Grain Yard", "loc": "Alote Road, Mahidpur", "state": "Madhya Pradesh", "dist": "Ujjain", "cap": 900.0, "crops": "Wheat,Mustard,Pulses"}
    ]

    for c in centres_data:
        emit(f"INSERT INTO `procurement_centres` (`centre_id`, `centre_name`, `location`, `state`, `district`, `contact_number`, `operating_days`, `opening_time`, `closing_time`, `supported_crops`, `max_daily_capacity_quintals`, `total_storage_capacity_quintals`, `current_storage_usage_quintals`, `status`) VALUES "
             f"('{c['id']}', '{c['name']}', '{c['loc']}', '{c['state']}', '{c['dist']}', '9822{random.randint(100000, 999999)}', 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday', '09:00 AM', '05:00 PM', '{c['crops']}', {c['cap']}, {c['cap']*25}, {c['cap']*6}, 'OPERATIONAL');")

    # 3. Create Demo Users & Core Roles
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT DEMO ACCOUNTS & INITIAL SYSTEM USERS")
    emit("-- -------------------------------------------------------------")
    demo_users = [
        # Required Demo Accounts
        ("admin@bharatagri.demo", "National Procurement Officer", "admin@bharatagri.demo", "9800000001", DEMO_BCRYPT_HASH, "government", "English"),
        ("centre@bharatagri.demo", "Sanquelim Centre Manager", "centre@bharatagri.demo", "9800000002", DEMO_BCRYPT_HASH, "centre", "English"),
        ("agent@bharatagri.demo", "Pernem CSC Operator", "agent@bharatagri.demo", "9800000003", DEMO_BCRYPT_HASH, "agent", "English"),
        ("farmer@bharatagri.demo", "Rameshwar Patil", "farmer@bharatagri.demo", "9800000004", DEMO_BCRYPT_HASH, "farmer", "English"),
        # Legacy Backward-Compatibility Users (from Iteration 1 tests)
        ("centre01", "Sanquelim Krishi Upaj Mandi", "centre01@bharatagri.org", "9876543210", LEGACY_BCRYPT_HASH, "centre", "English"),
        ("farmer01", "Rameshwar Patil", "farmer01@bharatagri.org", "9823456789", LEGACY_BCRYPT_HASH, "farmer", "English")
    ]
    # Add other centre users for each centre
    for c in centres_data:
        demo_users.append((c["id"], c["name"] + " Incharge", f"{c['id'].lower()}@bharatagri.demo", f"9822{random.randint(100000, 999999)}", DEMO_BCRYPT_HASH, "centre", "English"))

    for u in demo_users:
        emit(f"INSERT INTO `users` (`user_id`, `name`, `email`, `mobile`, `password_hash`, `role`, `preferred_language`, `status`) VALUES "
             f"('{u[0]}', '{u[1]}', '{u[2]}', '{u[3]}', '{u[4]}', '{u[5]}', '{u[6]}', 'ACTIVE');")

    # Add Demo Farmer Profile
    emit(f"INSERT INTO `farmers` (`farmer_code`, `user_id`, `name`, `mobile`, `email`, `dob`, `gender`, `address`, `state`, `district`, `taluka`, `village`, `land_area_hectares`, `ekyc_status`, `bank_name`, `bank_account_no`, `bank_ifsc`) VALUES "
         f"('FRM-DEMO-001', 'farmer@bharatagri.demo', 'Rameshwar Patil', '9800000004', 'farmer@bharatagri.demo', '1982-05-14', 'Male', 'Plot 12, Bicholim Road', 'Goa', 'North Goa', 'Bicholim', 'Bicholim Village-4', 3.50, 'VERIFIED', 'State Bank of India', '10293847561', 'SBIN0001234');")
    emit(f"INSERT INTO `farmer_crops` (`farmer_id`, `crop_name`, `season`, `sowing_date`, `expected_harvest_date`, `estimated_quantity_quintals`) VALUES "
         f"(1, 'Paddy', 'Kharif', '2026-06-15', '2026-10-20', 140.00), "
         f"(1, 'Maize', 'Kharif', '2026-06-25', '2026-10-30', 95.00);")

    # Add Demo Agent Profile
    emit(f"INSERT INTO `agents` (`agent_code`, `user_id`, `agency_type`, `organization_name`, `name`, `mobile`, `email`, `state`, `district`, `taluka`, `status`) VALUES "
         f"('AGT-DEMO-001', 'agent@bharatagri.demo', 'CSC Kendra', 'Pernem Digital Seva', 'Pernem CSC Operator', '9800000003', 'agent@bharatagri.demo', 'Goa', 'North Goa', 'Pernem', 'ACTIVE');")

    # 4. Generate 2,000+ Farmers with realistic crops and geography
    print("Generating 2,050 Realistic Farmers...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT 2,050 FARMERS")
    emit("-- -------------------------------------------------------------")
    farmer_values = []
    farmer_user_values = []
    farmer_crop_values = []

    farmer_records = [] # for in-memory booking generation

    for i in range(2, 2052):
        f_name = generate_full_name()
        f_mobile = f"98{random.randint(10000000, 99999999)}"
        f_uid = f"farmer_{i:04d}"
        f_code = f"FRM-2026-{i:05d}"
        f_email = f"farmer{i}@bharatagri.demo"
        st, st_code, dist, taluka, village = get_random_geo()
        land = round(random.uniform(1.0, 8.5), 2)
        dob_year = random.randint(1965, 2002)
        dob = f"{dob_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

        farmer_user_values.append(f"('{f_uid}', '{f_name}', '{f_email}', '{f_mobile}', '{DEMO_BCRYPT_HASH}', 'farmer', 'English', 'ACTIVE')")
        farmer_values.append(
            f"('{f_code}', '{f_uid}', '{f_name}', '{f_mobile}', '{f_email}', '{dob}', 'Male', 'Farm House #{random.randint(1, 200)}, {village}', "
            f"'{st}', '{dist}', '{taluka}', '{village}', {land}, 'VERIFIED', 'HDFC Bank', '{random.randint(10000000000, 99999999999)}', 'HDFC0002134')"
        )

        # 1 or 2 crops per farmer
        num_crops = random.choice([1, 2])
        chosen_crops = random.sample(CROPS, num_crops)
        for crp in chosen_crops:
            est_qty = round(land * random.uniform(crp["yield_range"][0], crp["yield_range"][1]) * 0.7, 2)
            farmer_crop_values.append(
                f"({i}, '{crp['name']}', '{crp['season']}', '2026-06-15', '2026-10-25', {est_qty})"
            )

        farmer_records.append({
            "id": i,
            "uid": f_uid,
            "name": f_name,
            "mobile": f_mobile,
            "state": st,
            "district": dist,
            "crops": [c["name"] for c in chosen_crops]
        })

    # Batch insert farmer users
    for chunk in [farmer_user_values[x:x+200] for x in range(0, len(farmer_user_values), 200)]:
        emit(f"INSERT INTO `users` (`user_id`, `name`, `email`, `mobile`, `password_hash`, `role`, `preferred_language`, `status`) VALUES\n" + ",\n".join(chunk) + ";")

    # Batch insert farmers
    for chunk in [farmer_values[x:x+200] for x in range(0, len(farmer_values), 200)]:
        emit(f"INSERT INTO `farmers` (`farmer_code`, `user_id`, `name`, `mobile`, `email`, `dob`, `gender`, `address`, `state`, `district`, `taluka`, `village`, `land_area_hectares`, `ekyc_status`, `bank_name`, `bank_account_no`, `bank_ifsc`) VALUES\n" + ",\n".join(chunk) + ";")

    # Batch insert farmer crops
    for chunk in [farmer_crop_values[x:x+200] for x in range(0, len(farmer_crop_values), 200)]:
        emit(f"INSERT INTO `farmer_crops` (`farmer_id`, `crop_name`, `season`, `sowing_date`, `expected_harvest_date`, `estimated_quantity_quintals`) VALUES\n" + ",\n".join(chunk) + ";")

    # 5. Agents & Farmer Assignments
    print("Generating 20 Agents & Regional Assignments...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT AGENTS & ASSIGNMENTS")
    emit("-- -------------------------------------------------------------")
    agent_records = []
    agent_user_vals = []
    agent_vals = []
    assign_vals = []

    for idx, c in enumerate(centres_data[:20], start=2):
        ag_uid = f"agent_{idx:02d}"
        ag_name = f"{c['dist']} CSC Assistant {idx}"
        ag_code = f"AGT-2026-{idx:04d}"
        ag_org = f"{c['dist']} Panchayat Gram Seva Kendra"
        ag_phone = f"97{random.randint(10000000, 99999999)}"
        ag_email = f"agent{idx}@bharatagri.demo"

        agent_user_vals.append(f"('{ag_uid}', '{ag_name}', '{ag_email}', '{ag_phone}', '{DEMO_BCRYPT_HASH}', 'agent', 'English', 'ACTIVE')")
        agent_vals.append(f"('{ag_code}', '{ag_uid}', 'CSC', '{ag_org}', '{ag_name}', '{ag_phone}', '{ag_email}', '{c['state']}', '{c['dist']}', '{c['loc']}', 'ACTIVE')")
        agent_records.append(idx)

    emit(f"INSERT INTO `users` (`user_id`, `name`, `email`, `mobile`, `password_hash`, `role`, `preferred_language`, `status`) VALUES\n" + ",\n".join(agent_user_vals) + ";")
    emit(f"INSERT INTO `agents` (`agent_code`, `user_id`, `agency_type`, `organization_name`, `name`, `mobile`, `email`, `state`, `district`, `taluka`, `status`) VALUES\n" + ",\n".join(agent_vals) + ";")

    # Assign demo agent (id 1) and other agents to farmers in their district
    for f in farmer_records[:400]:
        ag_id = (f["id"] % 20) + 1
        assign_vals.append(f"({ag_id}, {f['id']})")
    # ensure demo agent has farmers 1 to 50
    for fid in range(1, 51):
        assign_vals.append(f"(1, {fid})")

    # Deduplicate assignments
    unique_assigns = list(set(assign_vals))
    for chunk in [unique_assigns[x:x+200] for x in range(0, len(unique_assigns), 200)]:
        emit(f"INSERT IGNORE INTO `agent_farmer_assignments` (`agent_id`, `farmer_id`) VALUES\n" + ",\n".join(chunk) + ";")

    # 6. Generate Slots & Daily Capacities for Centres
    print("Generating Slots & Daily Capacities for 25 Centres across 60 days...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT SLOTS & DAILY CAPACITIES")
    emit("-- -------------------------------------------------------------")
    today = datetime.date(2026, 9, 30)
    start_date = today - datetime.timedelta(days=45)
    end_date = today + datetime.timedelta(days=15)

    slot_id_counter = 1
    slot_lookup = {} # (centre_id, date_str) -> list of slot_ids
    slot_inserts = []
    cap_inserts = []

    curr_dt = start_date
    while curr_dt <= end_date:
        d_str = curr_dt.strftime("%Y-%m-%d")
        is_sunday = curr_dt.weekday() == 6

        for c in centres_data:
            if is_sunday:
                continue
            cap_inserts.append(f"('{c['id']}', '{d_str}', {c['cap']})")
            
            # 4 slots per day
            times = [("09:00 AM", "11:00 AM"), ("11:00 AM", "01:00 PM"), ("01:30 PM", "03:30 PM"), ("03:30 PM", "05:00 PM")]
            slot_lookup[(c['id'], d_str)] = []
            for st_t, end_t in times:
                slot_inserts.append(f"({slot_id_counter}, '{c['id']}', '{d_str}', '{st_t}', '{end_t}', 25)")
                slot_lookup[(c['id'], d_str)].append(slot_id_counter)
                slot_id_counter += 1

        curr_dt += datetime.timedelta(days=1)

    for chunk in [cap_inserts[x:x+300] for x in range(0, len(cap_inserts), 300)]:
        emit(f"INSERT INTO `daily_capacity` (`centre_id`, `date`, `max_quintals_per_day`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [slot_inserts[x:x+300] for x in range(0, len(slot_inserts), 300)]:
        emit(f"INSERT INTO `slots` (`id`, `centre_id`, `date`, `start_time`, `end_time`, `max_capacity`) VALUES\n" + ",\n".join(chunk) + ";")

    # Add Non-operational / holiday dates
    emit("\n-- Non-operational dates")
    holidays = [
        ("CENTRE-GOA-01", "2026-10-02", "Gandhi Jayanti"),
        ("CENTRE-GOA-02", "2026-10-02", "Gandhi Jayanti"),
        ("CENTRE-MH-01", "2026-10-02", "Gandhi Jayanti"),
        ("CENTRE-MH-02", "2026-10-02", "Gandhi Jayanti"),
        ("CENTRE-GOA-01", "2026-09-15", "Centre Maintenance"),
        ("CENTRE-MH-04", "2026-09-18", "Weighbridge Calibration Day")
    ]
    for h in holidays:
        emit(f"INSERT INTO `non_operational_dates` (`centre_id`, `date`, `reason`) VALUES ('{h[0]}', '{h[1]}', '{h[2]}');")

    # 7. Generate 10,200 Bookings and End-to-End Traceability Lots
    print("Generating 10,200 Bookings, Collections, Weighments, Procurements & Storage Lots...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT 10,200 BOOKINGS & PROCUREMENT CHAIN")
    emit("-- -------------------------------------------------------------")

    booking_inserts = []
    status_history_inserts = []
    collection_inserts = []
    quality_inserts = []
    weighment_inserts = []
    procurement_inserts = []
    storage_inserts = []
    payment_inserts = []
    qr_inserts = []

    # Dataset for ML training
    ml_training_rows = []
    anomaly_training_rows = []

    # Create mapping of district -> centres
    dist_centre_map = {}
    for c in centres_data:
        dist_centre_map.setdefault(c["dist"], []).append(c)

    booking_id = 1
    col_id = 1
    proc_id = 1

    # Deterministic dates
    historical_dates = []
    upcoming_dates = []
    curr_dt = start_date
    while curr_dt <= end_date:
        if curr_dt.weekday() != 6:
            if curr_dt < today:
                historical_dates.append(curr_dt.strftime("%Y-%m-%d"))
            else:
                upcoming_dates.append(curr_dt.strftime("%Y-%m-%d"))
        curr_dt += datetime.timedelta(days=1)

    # First add a test booking for Demo Farmer at Sanquelim Centre
    demo_slot_id = slot_lookup[("CENTRE-GOA-01", today.strftime("%Y-%m-%d"))][0]
    booking_inserts.append(
        f"(1, 'PF-260930-101', 'PF-260930-101', 'farmer@bharatagri.demo', 'CENTRE-GOA-01', {demo_slot_id}, 'Paddy', 45.00, 'CONFIRMED', 'BA-QR-PF-260930-101', NULL, NULL, NULL, '2026-09-28 10:30:00')"
    )
    qr_inserts.append(f"('BOOKING', 'PF-260930-101', 'BA-QR-PF-260930-101', 0, NULL, '2026-10-05 23:59:59')")
    booking_id = 2

    # Loop to create realistic bookings
    num_total_bookings = 10200
    for b_idx in range(2, num_total_bookings + 1):
        f = farmer_records[(b_idx - 2) % len(farmer_records)]
        eligible_centres = dist_centre_map.get(f["district"], centres_data)
        centre = random.choice(eligible_centres)
        
        # 85% historical (processed), 15% upcoming/today (confirmed/pending)
        is_historical = (b_idx <= 8600)
        if is_historical:
            b_date = random.choice(historical_dates)
            status = random.choices(
                ['PAID', 'STORED', 'PROCURED', 'WEIGHED', 'COLLECTED', 'REJECTED'],
                weights=[70, 15, 6, 4, 3, 2]
            )[0]
        else:
            b_date = random.choice(upcoming_dates)
            status = 'CONFIRMED'

        slots_available = slot_lookup.get((centre["id"], b_date))
        if not slots_available:
            continue
        slot_id = random.choice(slots_available)

        crop = random.choice(f["crops"])
        qty = round(random.uniform(15.0, 95.0), 2)
        appt_id = f"PF-{b_date.replace('-','')[2:]}-{b_idx:04d}"
        qr_token = f"BA-QR-{appt_id}"

        verified_dt_sql = f"'{b_date} 09:15:00'" if status != 'CONFIRMED' else "NULL"
        is_used_val = 1 if status != 'CONFIRMED' else 0

        booking_inserts.append(
            f"({b_idx}, '{appt_id}', '{appt_id}', '{f['uid']}', '{centre['id']}', {slot_id}, '{crop}', {qty}, '{status}', '{qr_token}', NULL, NULL, {verified_dt_sql}, '{b_date} 08:30:00')"
        )
        qr_inserts.append(f"('BOOKING', '{appt_id}', '{qr_token}', {is_used_val}, {verified_dt_sql}, '2026-11-30 23:59:59')")

        # Traceability chain for processed records
        if status in ['PAID', 'STORED', 'PROCURED', 'WEIGHED', 'COLLECTED']:
            collection_code = f"COL-{centre['id']}-{col_id:05d}"
            collection_inserts.append(
                f"({col_id}, '{collection_code}', {b_idx}, '{f['uid']}', '{centre['id']}', '{crop}', {qty}, '{b_date}', 'DIRECT_CENTRE', 'GA-03-A-1284', 'Inspector Patil', 'COLLECTED', '{b_date} 09:30:00')"
            )

            # Quality Check
            crop_info = next((c for c in CROPS if c["name"] == crop), CROPS[0])
            moisture = round(random.gauss(crop_info["moisture_std"], 0.8), 2)
            foreign_matter = round(random.uniform(0.5, 2.8), 2)
            broken_grains = round(random.uniform(1.0, 4.0), 2)
            passed = 1
            grade = "GRADE_A" if moisture <= crop_info["moisture_std"] + 1.0 else "GRADE_B"
            qc_id = f"QC-{centre['id']}-{col_id:05d}"
            quality_inserts.append(
                f"({col_id}, '{qc_id}', '{collection_code}', {moisture}, {foreign_matter}, {broken_grains}, '{grade}', 'Quality Officer Deshmukh', {passed}, 'Standard FAQ verified', '{b_date} 09:45:00')"
            )

            # Weighment
            gross_wt = qty + round(random.uniform(18.0, 22.0), 2)
            tare_wt = round(gross_wt - qty, 2)
            weighment_code = f"WB-{centre['id']}-{col_id:05d}"
            weighment_inserts.append(
                f"({col_id}, '{weighment_code}', '{collection_code}', {gross_wt}, {tare_wt}, {qty}, 'WB-01', 'Operator Naik', '{b_date} 10:10:00')"
            )

            # Procurement Record
            if status in ['PAID', 'STORED', 'PROCURED']:
                proc_code = f"PRC-{centre['id']}-{proc_id:05d}"
                msp = crop_info["msp"]
                tot_val = round(qty * msp, 2)
                procurement_inserts.append(
                    f"({proc_id}, '{proc_code}', {b_idx}, '{collection_code}', '{f['uid']}', '{centre['id']}', '{crop}', {qty}, {msp}, {tot_val}, 'CONFIRMED', '{b_date} 10:30:00')"
                )

                # Storage Lot with standard Lot ID format
                state_code = next((s["state_code"] for s in GEOGRAPHY if s["state"] == centre["state"]), "IN")
                lot_code = f"LOT-2026-{state_code}-{centre['id']}-{proc_id:06d}"
                wh_name = f"{centre['name']} Warehouse Godown-{random.randint(1, 4)}"
                stack = f"Stack-A{random.randint(1, 12)}"
                storage_inserts.append(
                    f"({proc_id}, '{lot_code}', '{proc_code}', '{centre['id']}', '{crop}', {qty}, '{wh_name}', '{stack}', '{b_date}', 'STORED', '{b_date} 11:00:00')"
                )

                # Payment Record
                pay_status = 'PAID' if status == 'PAID' else 'INITIATED'
                pay_code = f"PAY-{centre['id']}-{proc_id:05d}"
                tx_ref = f"UTR2026{random.randint(100000000, 999999999)}" if pay_status == 'PAID' else None
                paid_dt = f"'{b_date} 16:30:00'" if pay_status == 'PAID' else "NULL"
                tx_ref_sql = f"'{tx_ref}'" if tx_ref else "NULL"
                payment_inserts.append(
                    f"({proc_id}, '{pay_code}', '{proc_code}', '{f['uid']}', {tot_val}, {msp}, {qty}, 'DBT_NEFT', '{pay_status}', {tx_ref_sql}, '{b_date} 14:00:00', {paid_dt}, 'Direct Benefit Transfer verified')"
                )

                # Collect ML training record
                d_obj = datetime.datetime.strptime(b_date, "%Y-%m-%d")
                ml_training_rows.append({
                    "centre_id": centre["id"],
                    "state": centre["state"],
                    "district": centre["dist"],
                    "crop": crop,
                    "month": d_obj.month,
                    "day_of_week": d_obj.weekday(),
                    "registered_farmers_count": 85 + (b_idx % 200),
                    "booked_quantity": qty,
                    "expected_harvest_quantity": qty * 1.05,
                    "daily_capacity": centre["cap"],
                    "historic_arrival_qty": qty * random.uniform(0.9, 1.02),
                    "trucks_demand": max(1, int(qty // 80) + 1),
                    "bardan_bags_consumed": int(qty * 2),
                    "procured_quantity": qty
                })

                proc_id += 1
            col_id += 1

    # Batch insert Bookings
    print("Writing SQL inserts for Bookings and Traceability...")
    for chunk in [booking_inserts[x:x+200] for x in range(0, len(booking_inserts), 200)]:
        emit(f"INSERT INTO `bookings` (`id`, `appointment_id`, `booking_id`, `farmer_id`, `centre_id`, `slot_id`, `crop`, `quantity`, `status`, `qr_token`, `redirected_from_centre_id`, `redirection_reason`, `verified_at`, `created_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [qr_inserts[x:x+250] for x in range(0, len(qr_inserts), 250)]:
        emit(f"INSERT INTO `qr_codes` (`entity_type`, `entity_id`, `qr_code_value`, `is_used`, `used_at`, `expires_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [collection_inserts[x:x+200] for x in range(0, len(collection_inserts), 200)]:
        emit(f"INSERT INTO `collection_records` (`id`, `collection_id`, `booking_id`, `farmer_id`, `centre_id`, `crop`, `collected_quantity`, `collection_date`, `collection_method`, `truck_number`, `collected_by`, `status`, `created_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [quality_inserts[x:x+200] for x in range(0, len(quality_inserts), 200)]:
        emit(f"INSERT INTO `quality_checks` (`id`, `check_id`, `collection_id`, `moisture_content_pct`, `foreign_matter_pct`, `broken_grains_pct`, `quality_grade`, `inspector_name`, `passed`, `remarks`, `checked_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [weighment_inserts[x:x+200] for x in range(0, len(weighment_inserts), 200)]:
        emit(f"INSERT INTO `weighments` (`id`, `weighment_id`, `collection_id`, `gross_weight_quintals`, `tare_weight_quintals`, `net_weight_quintals`, `weighbridge_id`, `operator_name`, `weighed_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [procurement_inserts[x:x+200] for x in range(0, len(procurement_inserts), 200)]:
        emit(f"INSERT INTO `procurement_records` (`id`, `procurement_id`, `booking_id`, `collection_id`, `farmer_id`, `centre_id`, `crop`, `procured_quantity_quintals`, `msp_rate_per_quintal`, `total_procurement_value`, `status`, `created_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [storage_inserts[x:x+200] for x in range(0, len(storage_inserts), 200)]:
        emit(f"INSERT INTO `storage_lots` (`id`, `lot_id`, `procurement_id`, `centre_id`, `crop`, `quantity_quintals`, `warehouse_name`, `stack_number`, `storage_date`, `status`, `created_at`) VALUES\n" + ",\n".join(chunk) + ";")

    for chunk in [payment_inserts[x:x+200] for x in range(0, len(payment_inserts), 200)]:
        emit(f"INSERT INTO `payments` (`id`, `payment_id`, `procurement_id`, `farmer_id`, `amount`, `msp_rate`, `quantity_quintals`, `payment_mode`, `payment_status`, `transaction_ref`, `initiated_at`, `paid_at`, `remarks`) VALUES\n" + ",\n".join(chunk) + ";")

    # 8. Trucks, Allocations, and Routes
    print("Generating Trucks and Smart Allocations...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT TRUCKS & ALLOCATIONS")
    emit("-- -------------------------------------------------------------")
    truck_inserts = []
    truck_alloc_inserts = []
    for t_idx in range(1, 55):
        centre = centres_data[t_idx % len(centres_data)]
        plate = f"{centre['state'][:2].upper()}-{(t_idx % 12) + 1:02d}-TR-{1000 + t_idx:04d}"
        driver = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = f"98{random.randint(10000000, 99999999)}"
        capacity = random.choice([100.0, 150.0, 200.0, 250.0])
        status = random.choice(['AVAILABLE', 'IN_TRANSIT', 'DISPATCHED', 'MAINTENANCE'])
        is_avail = 1 if status == 'AVAILABLE' else 0
        truck_inserts.append(f"({t_idx}, '{plate}', '{driver}', '{phone}', {capacity}, '{status}', '{centre['id']}', {is_avail})")

        # Allocations
        if t_idx <= 40:
            alloc_code = f"ALC-2026-{t_idx:04d}"
            alloc_date = (today - datetime.timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d")
            assigned_qty = round(capacity * random.uniform(0.75, 0.98), 2)
            truck_alloc_inserts.append(
                f"({t_idx}, '{alloc_code}', NULL, {t_idx}, '{centre['id']}', '{alloc_date}', {assigned_qty}, 'COMPLETED', {random.uniform(15.0, 48.0):.2f}, 'Optimized route dispatched via OR-Tools engine', '{alloc_date} 08:00:00')"
            )

    emit(f"INSERT INTO `trucks` (`id`, `truck_number`, `driver_name`, `driver_phone`, `capacity_quintals`, `current_status`, `assigned_centre_id`, `is_available`) VALUES\n" + ",\n".join(truck_inserts) + ";")
    emit(f"INSERT INTO `truck_allocations` (`id`, `allocation_code`, `request_id`, `truck_id`, `centre_id`, `allocation_date`, `assigned_quantity_quintals`, `status`, `route_distance_km`, `notes`, `created_at`) VALUES\n" + ",\n".join(truck_alloc_inserts) + ";")

    # 9. Inventory, Bardan Stock & Forecasts
    print("Generating Inventory & Bardan Stock & Forecasts...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT INVENTORY & BARDAN")
    emit("-- -------------------------------------------------------------")
    inv_inserts = []
    bardan_stock_inserts = []
    bardan_forecast_inserts = []

    for c in centres_data:
        total_b = random.randint(18000, 32000)
        in_use = random.randint(4000, 9000)
        damaged = random.randint(150, 450)
        avail = total_b - in_use - damaged
        bardan_stock_inserts.append(f"('{c['id']}', {total_b}, {in_use}, {damaged}, {avail})")

        # Standard Inventory items
        inv_inserts.append(f"('{c['id']}', 'BARDAN_BAGS', 'Standard 50kg Jute Gunny Bags', {avail}, 1200, 'Bags', 2000, '2026-09-25 10:00:00')")
        inv_inserts.append(f"('{c['id']}', 'TARPAULINS', 'Heavy Duty Waterproof Tarpaulins', {random.randint(45, 120)}, 5, 'Sheets', 20, '2026-09-20 11:00:00')")
        inv_inserts.append(f"('{c['id']}', 'MOISTURE_METERS', 'Digital Grain Moisture Meters', {random.randint(6, 15)}, 1, 'Units', 3, '2026-09-18 09:00:00')")
        inv_inserts.append(f"('{c['id']}', 'DIGITAL_SCALES', 'Electronic Weighbridge Calibration Weights', {random.randint(10, 25)}, 0, 'Pieces', 5, '2026-09-10 14:00:00')")

        # Bardan Forecast for next 14 days
        proj_consumption = int(c['cap'] * 14 * 2 * 0.8) # 2 bags per quintal
        proj_req = proj_consumption
        shortage = max(0, proj_req - avail)
        if shortage > 2500:
            b_status = 'SHORTAGE'
        elif shortage > 500:
            b_status = 'WARNING'
        elif avail < proj_req * 1.15:
            b_status = 'LOW'
        else:
            b_status = 'SAFE'

        bardan_forecast_inserts.append(
            f"('{c['id']}', '2026-10-15', {avail}, {proj_consumption}, {proj_req}, {shortage}, '{b_status}', '2026-09-30 06:00:00')"
        )

    emit(f"INSERT INTO `bardan_stock` (`centre_id`, `total_bags`, `bags_in_use`, `bags_damaged`, `available_bags`) VALUES\n" + ",\n".join(bardan_stock_inserts) + ";")
    emit(f"INSERT INTO `inventory` (`centre_id`, `item_type`, `item_name`, `current_stock`, `reserved_stock`, `unit`, `reorder_level`, `last_restocked_at`) VALUES\n" + ",\n".join(inv_inserts) + ";")
    emit(f"INSERT INTO `bardan_forecasts` (`centre_id`, `forecast_date`, `current_stock`, `projected_consumption`, `projected_requirement`, `expected_shortage`, `status`, `created_at`) VALUES\n" + ",\n".join(bardan_forecast_inserts) + ";")

    # 10. Realistic Anomalies & Isolation Forest training
    print("Generating Anomaly Records across Procurement Chain...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT ANOMALIES & AUDIT LOGS")
    emit("-- -------------------------------------------------------------")
    anomaly_types = [
        ("EXCESS_WEIGHT_MISMATCH", "Net weighed quantity is significantly higher than booked quantity (+45%)."),
        ("MOISTURE_THRESHOLD_OVERRIDE", "Grade A marked despite moisture content exceeding FAQ limit (16.8%)."),
        ("UNUSUAL_VOLUME_SPIKE", "Centre daily processed volume exceeded 185% of normal seasonal baseline."),
        ("RAPID_DUPLICATE_PAYMENT", "Multiple payment initiation events flagged within 10 minutes for single farmer lot."),
        ("TARE_WEIGHT_ANOMALY", "Truck tare weight logged 30% below vehicle registration standard weight."),
        ("AFTER_HOURS_WEIGHMENT", "Weighment transaction recorded outside centre operational working hours.")
    ]

    anomaly_inserts = []
    for anom_idx in range(1, 46):
        a_code = f"ANOM-2026-{anom_idx:04d}"
        c = centres_data[anom_idx % len(centres_data)]
        a_type, a_desc = random.choice(anomaly_types)
        score = round(random.uniform(-0.85, -0.45), 4)
        risk = random.choice(['HIGH', 'CRITICAL', 'MEDIUM'])
        status = random.choice(['OPEN', 'UNDER REVIEW', 'RESOLVED', 'DISMISSED'])
        resolved_by = "'Govt Auditor Sharma'" if status in ['RESOLVED', 'DISMISSED'] else "NULL"
        res_notes = "'Audit verified with physical ledger records.'" if status == 'RESOLVED' else ("'Dismissed after re-checking scale calibration.'" if status == 'DISMISSED' else "NULL")
        dt = (today - datetime.timedelta(days=random.randint(0, 15))).strftime("%Y-%m-%d %H:%M:%S")

        anomaly_inserts.append(
            f"({anom_idx}, '{a_code}', 'PROCUREMENT_TRANSACTION', 'PRC-{c['id']}-{anom_idx:04d}', '{c['id']}', '{a_type}', {score}, '{risk}', '{a_desc}', '{status}', {resolved_by}, {res_notes}, '{dt}')"
        )

        anomaly_training_rows.append({
            "booked_quantity": random.uniform(20, 80),
            "collected_quantity": random.uniform(20, 80),
            "weighed_quantity": random.uniform(20, 130),
            "procured_quantity": random.uniform(20, 130),
            "moisture_content": random.uniform(10, 19),
            "processing_time_mins": random.uniform(15, 240),
            "qty_difference": random.uniform(0, 45),
            "is_anomaly": 1 if anom_idx <= 25 else 0
        })

    emit(f"INSERT INTO `anomaly_records` (`id`, `anomaly_code`, `entity_type`, `entity_id`, `centre_id`, `anomaly_type`, `anomaly_score`, `risk_level`, `reason`, `status`, `resolved_by`, `resolution_notes`, `created_at`) VALUES\n" + ",\n".join(anomaly_inserts) + ";")

    # 11. Complaints
    print("Generating Complaints & Resolutions...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT COMPLAINTS")
    emit("-- -------------------------------------------------------------")
    complaint_cats = [
        ("Weighment Discrepancy", "Difference observed between farm-gate weight and centre weighbridge reading.", "HIGH"),
        ("Slot Booking Assistance", "Facing difficulty securing morning time-slot due to high seasonal rush.", "MEDIUM"),
        ("Payment Delay Notice", "DBT transfer pending beyond standard 48-hour procurement window.", "HIGH"),
        ("Quality Assessment Dispute", "Dispute on moisture deduction percentage applied during quality grading.", "MEDIUM"),
        ("Gunny Bag Shortage", "Shortage of Bardan bags delaying unloading at the arrival gate.", "CRITICAL")
    ]
    complaint_inserts = []
    for c_idx in range(1, 35):
        c_code = f"CMP-2026-{c_idx:04d}"
        c = centres_data[c_idx % len(centres_data)]
        cat, desc, prio = random.choice(complaint_cats)
        c_status = random.choice(['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'])
        if c_status in ['RESOLVED', 'CLOSED']:
            res_sql = "'Resolved by District Agriculture Officer. Amount adjusted / Slot rescheduled.'"
        else:
            res_sql = "NULL"
        c_date = (today - datetime.timedelta(days=random.randint(1, 20))).strftime("%Y-%m-%d %H:%M:%S")

        complaint_inserts.append(
            f"({c_idx}, '{c_code}', 'farmer_{c_idx:04d}', 'farmer', '{c['id']}', '{cat}', '{prio}', '{cat} at {c['name']}', '{desc}', '{c_status}', {res_sql}, 'District Grievance Officer', '{c_date}')"
        )

    emit(f"INSERT INTO `complaints` (`id`, `complaint_code`, `user_id`, `user_role`, `centre_id`, `category`, `priority`, `subject`, `description`, `status`, `resolution`, `assigned_to`, `created_at`) VALUES\n" + ",\n".join(complaint_inserts) + ";")

    # 12. Centre Congestions
    print("Generating Centre Congestion Data...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT CENTRE CONGESTION")
    emit("-- -------------------------------------------------------------")
    cong_inserts = []
    for c in centres_data:
        pred_arr = round(c['cap'] * random.uniform(0.4, 0.95), 2)
        exist_bk = round(c['cap'] * random.uniform(0.3, 0.8), 2)
        exp_col = round(c['cap'] * random.uniform(0.2, 0.5), 2)
        tot = exist_bk + (pred_arr * 0.4)
        util = round((tot / c['cap']) * 100, 2)
        if util > 90.0:
            c_lvl = 'CRITICAL'
        elif util > 75.0:
            c_lvl = 'HIGH'
        elif util > 50.0:
            c_lvl = 'MEDIUM'
        else:
            c_lvl = 'LOW'

        cong_inserts.append(
            f"('{c['id']}', '{today.strftime('%Y-%m-%d')}', {pred_arr}, {exist_bk}, {exp_col}, {c['cap']}, {util}, '{c_lvl}', '{today.strftime('%Y-%m-%d')} 07:00:00')"
        )

    emit(f"INSERT INTO `centre_congestions` (`centre_id`, `calculation_date`, `predicted_arrivals`, `existing_bookings_qty`, `expected_collection_qty`, `daily_capacity`, `utilization_percent`, `congestion_level`, `created_at`) VALUES\n" + ",\n".join(cong_inserts) + ";")

    # 13. Audit Logs
    print("Generating Audit Logs...")
    emit("\n-- -------------------------------------------------------------")
    emit("-- INSERT AUDIT LOGS")
    emit("-- -------------------------------------------------------------")
    audit_samples = [
        ("admin@bharatagri.demo", "LOGIN_SUCCESS", "USER", "admin@bharatagri.demo", "User authenticated into Government Admin Portal"),
        ("centre@bharatagri.demo", "QR_VERIFIED", "BOOKING", "PF-260930-101", "Farmer appointment QR code scanned and verified entry"),
        ("centre@bharatagri.demo", "QUALITY_CHECK_COMPLETED", "QUALITY_CHECK", "QC-CENTRE-GOA-01-00001", "Moisture 13.8% verified, Grade A assigned"),
        ("centre@bharatagri.demo", "WEIGHMENT_RECORDED", "WEIGHMENT", "WB-CENTRE-GOA-01-00001", "Gross: 65.2Q, Tare: 20.2Q, Net: 45.0Q"),
        ("admin@bharatagri.demo", "PAYMENT_BATCH_DISPATCHED", "PAYMENT", "BATCH-20260930", "DBT payment released for 150 procurement lots"),
        ("agent@bharatagri.demo", "FARMER_REGISTRATION_ASSIST", "FARMER", "FRM-2026-00042", "Assisted farmer e-KYC and land documentation update")
    ]
    audit_inserts = []
    for a_user, a_act, a_ent, a_eid, a_msg in audit_samples:
        audit_inserts.append(f"('{a_user}', '{a_act}', '{a_ent}', '{a_eid}', NULL, '{a_msg}', '127.0.0.1', '2026-09-30 08:30:00')")

    emit(f"INSERT INTO `audit_logs` (`user_id`, `action`, `entity`, `entity_id`, `old_value`, `new_value`, `ip_address`, `created_at`) VALUES\n" + ",\n".join(audit_inserts) + ";")

    # Footer
    emit("\nSET FOREIGN_KEY_CHECKS = 1;")
    emit("-- =================================================================")
    emit("-- END OF BHARATAGRI ITERATION 2 DATABASE DUMP")
    emit("-- =================================================================")

    # Write SQL File
    sql_file_path = os.path.join(db_dir, "bharatagri_iteration2.sql")
    with open(sql_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"Successfully generated complete SQL file at: {sql_file_path} (Size: {os.path.getsize(sql_file_path) / (1024*1024):.2f} MB)")

    # Save ML Training Datasets
    ml_df = pd.DataFrame(ml_training_rows)
    # Add more synthetic rows to reach 10,000 training points for XGBoost
    if len(ml_df) < 10000:
        extra_rows = []
        for _ in range(10000 - len(ml_df)):
            c = random.choice(centres_data)
            crp = random.choice(CROPS)
            bk_qty = round(random.uniform(20.0, 100.0), 2)
            m = random.randint(1, 12)
            extra_rows.append({
                "centre_id": c["id"],
                "state": c["state"],
                "district": c["dist"],
                "crop": crp["name"],
                "month": m,
                "day_of_week": random.randint(0, 5),
                "registered_farmers_count": random.randint(75, 300),
                "booked_quantity": bk_qty,
                "expected_harvest_quantity": bk_qty * random.uniform(0.95, 1.15),
                "daily_capacity": c["cap"],
                "historic_arrival_qty": bk_qty * random.uniform(0.85, 1.05),
                "trucks_demand": max(1, int(bk_qty // 80) + 1),
                "bardan_bags_consumed": int(bk_qty * 2),
                "procured_quantity": round(bk_qty * random.uniform(0.9, 1.02), 2)
            })
        ml_df = pd.concat([ml_df, pd.DataFrame(extra_rows)], ignore_index=True)

    ml_csv_path = os.path.join(ml_data_dir, "procurement_training_data.csv")
    ml_df.to_csv(ml_csv_path, index=False)
    print(f"Saved procurement ML dataset: {ml_csv_path} ({len(ml_df)} rows)")

    # Save Anomaly training data
    anom_extra = []
    for _ in range(5000):
        b_q = random.uniform(20, 80)
        is_anom = 1 if random.random() < 0.05 else 0
        diff = random.uniform(25, 75) if is_anom else random.uniform(0, 5)
        w_q = b_q + diff if is_anom else b_q + random.uniform(-2, 2)
        anom_extra.append({
            "booked_quantity": round(b_q, 2),
            "collected_quantity": round(b_q * random.uniform(0.98, 1.02), 2),
            "weighed_quantity": round(w_q, 2),
            "procured_quantity": round(w_q * 0.99, 2),
            "moisture_content": round(random.uniform(11, 18 if is_anom else 14.5), 2),
            "processing_time_mins": round(random.uniform(20, 220 if is_anom else 60), 2),
            "qty_difference": round(abs(w_q - b_q), 2),
            "is_anomaly": is_anom
        })
    anom_df = pd.concat([pd.DataFrame(anomaly_training_rows), pd.DataFrame(anom_extra)], ignore_index=True)
    anom_csv_path = os.path.join(ml_data_dir, "anomaly_training_data.csv")
    anom_df.to_csv(anom_csv_path, index=False)
    print(f"Saved anomaly ML dataset: {anom_csv_path} ({len(anom_df)} rows)")

    print("\nDataset generation finished successfully.")

if __name__ == "__main__":
    main()

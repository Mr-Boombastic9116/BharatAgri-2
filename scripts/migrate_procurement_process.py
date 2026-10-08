import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'bharatagri_iteration2')
    )
    with conn.cursor() as cur:
        # 1. procurement_process_steps
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `procurement_process_steps` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `booking_id` INT NOT NULL,
            `appointment_id` VARCHAR(50) NOT NULL,
            `step_number` INT NOT NULL,
            `step_type` VARCHAR(50) NOT NULL,
            `status` ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CORRECTED', 'SKIPPED') NOT NULL DEFAULT 'PENDING',
            `completed_by` VARCHAR(100) NULL,
            `employee_name` VARCHAR(150) NULL,
            `started_at` DATETIME NULL,
            `completed_at` DATETIME NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX `idx_proc_step_booking` (`booking_id`),
            INDEX `idx_proc_step_appt` (`appointment_id`),
            INDEX `idx_proc_step_num` (`step_number`),
            UNIQUE KEY `uq_booking_step` (`booking_id`, `step_number`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 2. ai_quality_inspections
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `ai_quality_inspections` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `inspection_code` VARCHAR(50) NOT NULL UNIQUE,
            `booking_id` INT NOT NULL,
            `appointment_id` VARCHAR(50) NOT NULL,
            `centre_id` VARCHAR(50) NOT NULL,
            `crop` VARCHAR(100) NOT NULL DEFAULT 'Mango',
            `image_path` VARCHAR(255) NOT NULL,
            `annotated_image_path` VARCHAR(255) NULL,
            `model_version` VARCHAR(50) NOT NULL DEFAULT 'mango-quality-v1',
            `model_type` VARCHAR(100) NOT NULL DEFAULT 'SVM+KNN Fusion CIELAB',
            `sample_count` INT NOT NULL DEFAULT 0,
            `healthy_count` INT NOT NULL DEFAULT 0,
            `defect_count` INT NOT NULL DEFAULT 0,
            `anthracnose_count` INT NOT NULL DEFAULT 0,
            `scab_count` INT NOT NULL DEFAULT 0,
            `bacterial_canker_count` INT NOT NULL DEFAULT 0,
            `stem_end_rot_count` INT NOT NULL DEFAULT 0,
            `other_count` INT NOT NULL DEFAULT 0,
            `affected_percentage` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
            `visual_grade` VARCHAR(50) NOT NULL DEFAULT 'Grade A',
            `confidence` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
            `status` ENUM('COMPLETED', 'NEEDS_REVIEW', 'MANUALLY_OVERRIDDEN') NOT NULL DEFAULT 'COMPLETED',
            `reviewed_by` VARCHAR(100) NULL,
            `reviewed_at` DATETIME NULL,
            `review_notes` TEXT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_ai_insp_booking` (`booking_id`),
            INDEX `idx_ai_insp_appt` (`appointment_id`),
            INDEX `idx_ai_insp_centre` (`centre_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 3. ai_inspection_detections
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `ai_inspection_detections` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `inspection_id` INT NOT NULL,
            `sample_index` INT NOT NULL,
            `predicted_class` VARCHAR(50) NOT NULL,
            `confidence` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
            `box_x` INT NOT NULL DEFAULT 0,
            `box_y` INT NOT NULL DEFAULT 0,
            `box_w` INT NOT NULL DEFAULT 0,
            `box_h` INT NOT NULL DEFAULT 0,
            `crop_image_path` VARCHAR(255) NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_ai_det_insp` (`inspection_id`),
            FOREIGN KEY (`inspection_id`) REFERENCES `ai_quality_inspections`(`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 4. process_step_corrections
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `process_step_corrections` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `booking_id` INT NOT NULL,
            `appointment_id` VARCHAR(50) NOT NULL,
            `step_number` INT NOT NULL,
            `field_name` VARCHAR(100) NOT NULL,
            `old_value` TEXT NULL,
            `new_value` TEXT NOT NULL,
            `correction_reason` TEXT NOT NULL,
            `corrected_by` VARCHAR(100) NOT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_step_corr_booking` (`booking_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 5. process_audit_logs
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `process_audit_logs` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `user_id` VARCHAR(100) NOT NULL,
            `centre_id` VARCHAR(50) NOT NULL,
            `appointment_id` VARCHAR(50) NOT NULL,
            `process_step` VARCHAR(50) NOT NULL,
            `action` VARCHAR(100) NOT NULL,
            `record_id` VARCHAR(100) NULL,
            `old_value` TEXT NULL,
            `new_value` TEXT NULL,
            `correction_reason` TEXT NULL,
            `ip_address` VARCHAR(50) DEFAULT '127.0.0.1',
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_proc_audit_appt` (`appointment_id`),
            INDEX `idx_proc_audit_user` (`user_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 6. Ensure states and crop metadata match exact specification
        # Goa -> Mango, Banana, Tomato
        # Maharashtra -> Sugarcane, Wheat, Cotton
        # Karnataka -> Paddy, Maize, Bajra
        # Clean up any bad spellings like 'Karnatake'
        cur.execute("UPDATE `states` SET `name` = 'Karnataka' WHERE `name` LIKE 'Karnatak%';")
        
        # Add Banana and Mango to crop_metadata if missing
        cur.execute("""
        INSERT INTO `crop_metadata` 
        (`crop_name`, `category`, `season`, `is_perishable`, `shelf_life_days`, `urgency_level`, `perishability_score`, `storage_requirements`, `demand_patterns`)
        VALUES 
        ('Mango', 'HORTICULTURE', 'Summer/Zaid', 1, 14, 'HIGH', 0.85, 'Ripening chambers / Cold transit (12-14°C) / Ambient ventilated', 'HIGH_PEAK_SUMMER'),
        ('Banana', 'HORTICULTURE', 'All-Season', 1, 10, 'HIGH', 0.80, 'Ethylene ripening rooms / Temperature 13-15°C', 'YEAR_ROUND_STABLE')
        ON DUPLICATE KEY UPDATE 
        category=VALUES(category), season=VALUES(season), is_perishable=VALUES(is_perishable),
        shelf_life_days=VALUES(shelf_life_days), urgency_level=VALUES(urgency_level);
        """)

    conn.commit()
    conn.close()
    print("Procurement process migration executed successfully!")

if __name__ == "__main__":
    run_migration()

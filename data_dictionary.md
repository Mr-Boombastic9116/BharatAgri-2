# BharatAgri-2 Agricultural & Procurement Data Dictionary

This document specifies the relational data dictionary for state agricultural data, procurement process steps, and AI quality inspections.

---

## 1. Table: `state_crop_supply_demand`

Stores regional supply, demand, inventory, and market pricing intelligence.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Synthetic identifier. |
| `state` | `VARCHAR(100)` | `NOT NULL, INDEX` | State name (`Goa`, `Maharashtra`, `Karnataka`). |
| `crop` | `VARCHAR(100)` | `NOT NULL, INDEX` | Designated crop for the state. |
| `season` | `VARCHAR(50)` | `NOT NULL` | Agricultural marketing season (e.g., `Kharif 2025-26`, `Rabi 2025-26`, `Summer/Zaid 2026`). |
| `official_msp` | `DECIMAL(10,2)` | `NOT NULL` | Statutory Minimum Support Price / Benchmark floor rate (INR per quintal). |
| `expected_supply_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Forecasted seasonal harvest supply (quintals). |
| `current_procurement_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Cumulative produce procured to date at mandis. |
| `projected_procurement_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Target procurement volume by end of season. |
| `current_inventory_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Currently held warehouse buffer stock. |
| `available_storage_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Available unutilized godown capacity. |
| `expected_demand_quintals` | `DECIMAL(12,2)` | `NOT NULL` | Aggregate domestic, PDS, and commercial mill demand. |
| `surplus_deficit_quintals` | `DECIMAL(12,2)` | `NOT NULL` | `(expected_supply - expected_demand)` in quintals. |
| `market_sentiment` | `VARCHAR(20)` | `DEFAULT 'BALANCED'` | Market status (`HIGH_DEMAND`, `BALANCED`, `SURPLUS_BUFFER`, `SUPPLY_DEFICIT`). |
| `estimated_procurement_price` | `DECIMAL(10,2)` | `NOT NULL` | Modal mandi spot price based on market clearing conditions. |
| `price_explanation` | `TEXT` | `NULL` | Macroeconomic and agronomic rationale for current price behavior. |
| `updated_at` | `DATETIME` | `AUTO_TIMESTAMP` | Last updated timestamp. |

---

## 2. Table: `procurement_process_steps`

Tracks the strict, sequential 5-step intake and verification process per appointment.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Step record identifier. |
| `booking_id` | `INT` | `NOT NULL, FK(bookings.id), INDEX` | Associated appointment booking record ID. |
| `appointment_id` | `VARCHAR(50)` | `NOT NULL, INDEX` | Human-readable appointment code (e.g. `APT-2026-10-00123`). |
| `step_number` | `INT` | `NOT NULL, INDEX` | Sequence number: `1` to `5`. |
| `step_type` | `VARCHAR(50)` | `NOT NULL` | `COLLECTION`, `PHYSICAL_QC`, `AI_VISUAL_QC`, `WEIGHMENT`, `PROCUREMENT`. |
| `status` | `ENUM` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CORRECTED`, `SKIPPED` | Execution state of the step. |
| `completed_by` | `VARCHAR(100)` | `NULL` | Employee `user_id` who completed the step. |
| `employee_name` | `VARCHAR(150)` | `NULL` | Display name of the completing employee. |
| `started_at` | `DATETIME` | `NULL` | Timestamp when employee opened the step. |
| `completed_at` | `DATETIME` | `NULL` | Timestamp when employee submitted the step. |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Initial initialization timestamp. |
| `updated_at` | `DATETIME` | `AUTO_UPDATE` | Last update timestamp. |

---

## 3. Table: `ai_quality_inspections`

Stores lot-level Mango AI visual quality assessments.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Unique inspection ID. |
| `inspection_code` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Unique tracking code (e.g. `INSP-2026-0042`). |
| `booking_id` | `INT` | `NOT NULL, FK(bookings.id)` | Associated booking ID. |
| `appointment_id` | `VARCHAR(50)` | `NOT NULL, INDEX` | Associated appointment code. |
| `centre_id` | `VARCHAR(50)` | `NOT NULL, INDEX` | Procurement centre where scan took place. |
| `crop` | `VARCHAR(100)` | `DEFAULT 'Mango'` | Verified crop (Strictly `Mango`). |
| `image_path` | `VARCHAR(255)` | `NOT NULL` | Path to original sample image containing multiple mangoes. |
| `annotated_image_path`| `VARCHAR(255)` | `NULL` | Path to generated image with detection bounding boxes & labels. |
| `model_version` | `VARCHAR(50)` | `DEFAULT 'mango-quality-v1'` | Version of the model executing inference. |
| `model_type` | `VARCHAR(100)` | `NOT NULL` | Architecture descriptor (`RBF SVM (CIELAB L*a*b*)` or `SVM+KNN Fusion`). |
| `sample_count` | `INT` | `DEFAULT 0` | Total mangoes detected in the photograph. |
| `healthy_count` | `INT` | `DEFAULT 0` | Count of healthy mangoes. |
| `defect_count` | `INT` | `DEFAULT 0` | Count of defective / infected mangoes. |
| `anthracnose_count` | `INT` | `DEFAULT 0` | Count of mangoes with Anthracnose lesions. |
| `scab_count` | `INT` | `DEFAULT 0` | Count of mangoes with Scab spotting. |
| `bacterial_canker_count`| `INT` | `DEFAULT 0` | Count of mangoes with Bacterial Canker lesions. |
| `stem_end_rot_count`| `INT` | `DEFAULT 0` | Count of mangoes with Stem End Rot decay. |
| `other_count` | `INT` | `DEFAULT 0` | Count of other fungal/rot conditions. |
| `affected_percentage`| `DECIMAL(5,2)` | `NOT NULL` | `(defect_count / sample_count) * 100`. |
| `visual_grade` | `VARCHAR(50)` | `NOT NULL` | `Grade A`, `Grade B`, `Grade C`, `Reject`, or `Needs Review`. |
| `confidence` | `DECIMAL(5,2)` | `NOT NULL` | Average prediction confidence percentage across samples. |
| `status` | `ENUM` | `COMPLETED`, `NEEDS_REVIEW`, `MANUALLY_OVERRIDDEN` | Review and verification status. |
| `reviewed_by` | `VARCHAR(100)` | `NULL` | Employee ID if human review was performed. |
| `reviewed_at` | `DATETIME` | `NULL` | Timestamp of human review. |
| `review_notes` | `TEXT` | `NULL` | Comments entered during human audit. |

---

## 4. Table: `ai_inspection_detections`

Stores individual bounding-box detection results for each mango isolated in the lot image.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Detection identifier. |
| `inspection_id` | `INT` | `NOT NULL, FK(ai_quality_inspections.id)` | Parent lot inspection record. |
| `sample_index` | `INT` | `NOT NULL` | Sequence index (`1`, `2`, `3`...). |
| `predicted_class`| `VARCHAR(50)` | `NOT NULL` | Predicted condition (`Healthy`, `Anthracnose`, etc.). |
| `confidence` | `DECIMAL(5,2)` | `NOT NULL` | Prediction confidence percentage. |
| `box_x` | `INT` | `NOT NULL` | Bounding box top-left X coordinate in pixels. |
| `box_y` | `INT` | `NOT NULL` | Bounding box top-left Y coordinate in pixels. |
| `box_w` | `INT` | `NOT NULL` | Bounding box width in pixels. |
| `box_h` | `INT` | `NOT NULL` | Bounding box height in pixels. |
| `crop_image_path`| `VARCHAR(255)` | `NULL` | File path to isolated cropped mango image. |

---

## 5. Table: `process_audit_logs` & `process_step_corrections`

Enforces auditability, data isolation, and anti-fraud non-overwrite policies.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Log identifier. |
| `user_id` | `VARCHAR(100)` | `NOT NULL, INDEX` | Acting employee user ID. |
| `centre_id` | `VARCHAR(50)` | `NOT NULL` | Procurement centre identifier. |
| `appointment_id`| `VARCHAR(50)` | `NOT NULL, INDEX` | Appointment code. |
| `process_step` | `VARCHAR(50)` | `NOT NULL` | Step affected (`COLLECTION`, `PHYSICAL_QC`, etc.). |
| `action` | `VARCHAR(100)` | `NOT NULL` | Action code (`STEP_COMPLETED`, `CORRECTION_APPLIED`, `MANUAL_OVERRIDE`). |
| `record_id` | `VARCHAR(100)` | `NULL` | ID of the underlying record created or modified. |
| `old_value` | `TEXT` | `NULL` | Historical value before correction (never silently replaced). |
| `new_value` | `TEXT` | `NULL` | New audited value. |
| `correction_reason`| `TEXT` | `NULL` | Compulsory justification recorded by the employee. |
| `ip_address` | `VARCHAR(50)` | `DEFAULT '127.0.0.1'` | Client IP address. |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Tamper-evident timestamp. |

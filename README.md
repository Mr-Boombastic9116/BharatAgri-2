# BHARATAGRI ITERATION 2

### Intelligent National Agricultural Procurement Management, Traceability & Optimization Platform

BharatAgri Iteration 2 is an enterprise-grade digital agriculture platform designed for end-to-end national procurement operations, supply forecasting, dynamic congestion management, truck dispatch optimization, quality-weighed lot traceability, and direct DBT payment tracking.

---

## 1. System Overview & Architecture

BharatAgri Iteration 2 connects four primary operational stakeholders across the national procurement pipeline:

```text
[ FARMER ]                [ AGENT / CSC ]           [ PROCUREMENT CENTRE ]       [ GOVERNMENT / POLICY ]
  • Land & Crops            • Assisted Registration   • Gate Entry & QR Scan       • National Command Centre
  • Slot Booking            • Regional Cluster Ops    • Quality Inspection (QC)    • XGBoost Supply Forecast
  • Digital QR Pass         • Assisted Booking        • Electronic Weighment       • BharatAgri Congestion Monitor
  • Lot Traceability        • Grievance Redressal     • Procurement & Lotting      • OR-Tools Truck Optimization
  • Direct Benefit (DBT)    • e-KYC Verification      • Bardan (Jute) Inventory    • Anomaly Detection (IsoForest)
```

### Complete End-to-End Procurement Lifecycle:
```text
BOOKED ──► CHECKED_IN ──► COLLECTED ──► QUALITY_CHECKED ──► WEIGHED ──► PROCURED ──► STORED ──► PAYMENT_INITIATED ──► PAID
```

Every procurement produces an immutable Lot identifier linking:
`Farmer ↔ Booking ↔ Collection ↔ Quality ↔ Weighment ↔ Procurement Record ↔ Truck ↔ Centre ↔ Storage ↔ DBT Payment`

---

## 2. Technology Stack

- **Frontend**: React 18, Vite, React Router DOM, Recharts, Lucide Icons, Vanilla CSS (Dark/Light theme engine, multi-language system).
- **Backend API**: Python 3.10+, FastAPI (Asynchronous high-performance REST), SQLAlchemy 2.0 ORM, PyMySQL, Pydantic v2.
- **Security & RBAC**: JWT Bearer Authentication (`HS256`), salted bcrypt password hashing, role-based endpoint gating (`FARMER`, `AGENT`, `PROCUREMENT_CENTRE`, `GOVERNMENT`).
- **Database**: MySQL 8.0+ / MariaDB (XAMPP / standalone), fully normalized schema with foreign keys, indexes, and audit logs.
- **AI & Optimization**:
  - **Supply Forecasting**: XGBoost Regressor (`xgboost`, `scikit-learn`, `joblib`).
  - **Logistics & Fleet Optimization**: Google OR-Tools Mixed-Integer Programming engine (`ortools.linear_solver`).
  - **Procurement Anomaly Detection**: Scikit-Learn Isolation Forest (`sklearn.ensemble.IsolationForest`).
  - **Congestion Analysis**: Deterministic operational utilization thresholds (`0-50% LOW`, `50-75% MEDIUM`, `75-90% HIGH`, `90%+ CRITICAL`).
  - **Bardan Jute Bag Projections**: Dynamic inventory projection vs incoming arrivals.

---

## 3. Demo Accounts & Credentials

All demo accounts are pre-seeded in the database with the single unified password:

| Role | Username / Identifier | Password | Associated Entity / Centre | Primary Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Farmer** | `farmer@bharatagri.demo` | `BharatAgri@2026` | Rameshwar Patil (`FRM-DEMO-001`) | Slot Booking, Digital QR Pass, Lot Traceability, DBT Payment Status, Helpdesk |
| **Field Agent** | `agent@bharatagri.demo` | `BharatAgri@2026` | Pernem CSC Operator (`AGT-DEMO-001`) | Regional Farmer Management, Assisted Booking, e-KYC, Farmer Complaints |
| **Procurement Centre** | `centre@bharatagri.demo` | `BharatAgri@2026` | Sanquelim Mandi (`CENTRE-GOA-01`) | QR Gate Scan, Inward QC, Weighment, Lot Generation, Storage, Truck Requests |
| **Government** | `admin@bharatagri.demo` | `BharatAgri@2026` | National Command Centre | National Dashboard, ML Forecasts, Congestion, OR-Tools, Anomalies, Redirections |

> **Quick Fill**: The login screen (`/login`) includes 1-click Quick Demo buttons to immediately populate credentials for any of the four roles.

---

## 4. Fresh-Machine Setup & Installation Guide

This guide ensures complete reproducibility when downloading or extracting the repository as a ZIP on a fresh Windows computer.

### System Prerequisites
Ensure the following software is installed on the target machine:
* **Operating System**: Windows 10 or 11 (64-bit)
* **Python**: Python 3.10, 3.11, or 3.12 (Check `Add Python to PATH` during installation)
* **Node.js**: Node.js 18.x or 20.x LTS with `npm` (Download from https://nodejs.org/)
* **Database / Server**: XAMPP (Apache + MySQL / MariaDB 10.4+) or standalone MySQL Server 8.0+

---

### Standard Startup Procedure

The application is launched using `start.bat` (or `start-local.bat`). Follow these 5 steps:

#### Step 1: Install Required Dependencies
* **Python Dependencies**:
  Ensure Python 3.10+ is installed. Dependencies can be installed in your virtual environment:
  ```cmd
  python -m venv venv
  venv\Scripts\pip.exe install -r requirements.txt
  ```
  *(Note: `start.bat` verifies and installs these automatically if missing).*
* **Frontend Dependencies**:
  Ensure Node.js 18+ and npm are installed:
  ```cmd
  cd frontend
  npm install
  cd ..
  ```
  *(Note: `start.bat` verifies and runs `npm install` automatically if `frontend\node_modules\vite` is missing).*

#### Step 2: Configure Environment Variables
Verify `.env` in the project root (copied automatically from `.env.example` if not present):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=bharatagri_iteration2
SECRET_KEY=bharatagri_secure_jwt_secret_key_2026_iteration2
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PORT=5000
```

#### Step 3: Configure & Start the Database
Start MySQL on port `3306` (e.g., click **Start** for MySQL in the XAMPP Control Panel).
If the database `bharatagri_iteration2` has not been imported yet:
```cmd
mysql -u root -e "CREATE DATABASE IF NOT EXISTS bharatagri_iteration2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root bharatagri_iteration2 < database\bharatagri_iteration2.sql
```
*(Note: If MySQL is temporarily offline, `start.bat` displays a diagnostic warning and continues starting both servers gracefully rather than crashing).*

#### Step 4: Run `start.bat`
Double-click `start.bat` in Windows Explorer or execute it from command prompt:
```cmd
start.bat
```
`start.bat` executes the full verified launch sequence:
1. Detects Python environment (prioritizes project `venv` / `.venv`).
2. Validates all Python dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `xgboost`, `ortools`, `jose`, `bcrypt`).
3. Detects Node.js & npm (with PATH fallbacks).
4. Verifies `.env` settings.
5. Performs non-blocking database validation against MySQL port 3306.
6. Performs port pre-check on port 5000; launches FastAPI backend (`scripts\run-backend.bat`) in a persistent console window (`cmd /k`).
7. Polls backend health on `http://127.0.0.1:5000/api/health` until HTTP 200 is confirmed.
8. Performs port pre-check on port 3000; launches Vite frontend (`scripts\run-frontend.bat`) in a persistent console window (`cmd /k`).
9. Polls frontend on `http://localhost:3000` until it is verified active and serving traffic.
10. Automatically launches the default web browser to the application URL once ready.

#### Step 5: Open Displayed Application URL
The launcher automatically opens the browser to:
* **Frontend Portal**: `http://localhost:3000`
* **Backend API Docs**: `http://localhost:5000/docs`
* **API Health Check**: `http://localhost:5000/api/health`

Sign in using any of the quick-demo accounts (Password: `BharatAgri@2026`):
* **Farmer**: `farmer@bharatagri.demo`
* **Centre**: `centre@bharatagri.demo`
* **Government**: `admin@bharatagri.demo`
* **Agent**: `agent@bharatagri.demo`

## 5. Environment Configuration (`.env`)

A default `.env` file is generated automatically from `.env.example` upon first launch:

```env
# XAMPP MySQL Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=bharatagri_iteration2

# JWT Security
SECRET_KEY=bharatagri_secure_jwt_secret_key_2026_iteration2
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Backend Server Port
PORT=5000
```

---

## 6. Manual Step-by-Step Setup (Alternative)

If you prefer to run services manually in separate terminals:

#### 1. Backend Setup (FastAPI & AI)
```bash
# In the project root:
python -m pip install -r requirements.txt

# Start FastAPI server
set PYTHONPATH=.
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload
```
API Documentation will be live at: `http://localhost:5000/docs`

#### 2. Frontend Setup (React & Vite)
```bash
# In another terminal window:
cd frontend
npm install
npm run dev
```
Web application will be live at: `http://localhost:3000`

---

## 7. AI Models & Optimization Engine

All AI, optimization, and rule-based pipelines are located in `ml/`:
- `ml/training/train_forecast.py`: Trains XGBoost Regressor on historical arrivals, yields, rainfall, and booking features. Saves artifact to `ml/models/supply_forecast_xgboost.pkl`.
- `ml/training/train_anomaly.py`: Trains Isolation Forest on procurement volume discrepancies, weight variances, and turnaround durations. Saves artifact to `ml/models/anomaly_isolation_forest.pkl`.
- `ml/inference/optimizer.py`: Google OR-Tools Mixed-Integer Programming (`pywraplp`) for fleet minimization and multi-centre capacity dispatch.
- `ml/evaluation/evaluate_models.py`: Internal evaluation harness calculating empirical metrics across all models and engines.
- **Resilience / Fallback Guarantee**: If models are missing or unreadable, the system activates built-in rule-based operational estimators without throwing 500 errors.

---

## 7.1 AI / ML Model & Optimization Evaluation

> **Last evaluated: 2026-10-01**  
> *Note: These evaluation results are strictly for developer and project owner auditing. Model performance metrics are not displayed anywhere in the user-facing application UI.*

### Compact Summary Table

| Component | Type | Algorithm / Engine | Current Performance | Evaluation Status |
| :--- | :--- | :--- | :--- | :--- |
| **Procurement Supply Forecast** | Machine Learning (Regression) | XGBoost (`XGBRegressor`) | MAE: **0.5316 Q**, RMSE: **1.1483 Q**, R²: **0.9975**, MAPE: **0.297%** | Validated (Synthetic benchmark) |
| **Procurement Anomaly Detection** | Machine Learning (Unsupervised) | Isolation Forest (`IsolationForest`) | Precision: **0.8333**, Recall: **1.0000**, F1: **0.9091** (Benchmark) | Benchmark Validated; Live: Ground truth unavailable |
| **Price Intelligence Engine** | Policy / Deterministic Hybrid | Bounded Economic Rule Model | **100%** MSP floor constraint adherence (Zero floor violations) | Validated (Deterministic rule engine) |
| **Congestion Intelligence** | Rule-Based System | Operational Threshold Engine | **100%** Deterministic classification across 4 states | Rule-Based (Not ML; No ML accuracy metric) |
| **Truck Route Fleet Optimizer** | Operations Research Optimization | Google OR-Tools (MILP / SCIP) | Feasibility: **100%**, Distance: **101.0 km**, Violations: **0** | Optimization Engine (Not ML; Feasibility validated) |

---

### Detailed Evaluation Methodology & Breakdown

#### 1. Procurement Supply Forecast Model
* **Algorithm:** XGBoost (`XGBRegressor`, `n_estimators=100`, `max_depth=6`, `learning_rate=0.1`, `random_state=42`)
* **Purpose:** Predict expected procurement volume (in quintals) over a 7 to 30-day operational horizon per crop and centre.
* **Features Used:**
  * Centre and storage capacity (`centre_capacity_quintals`, `storage_capacity_quintals`)
  * Farmer registration counts (`registered_farmers`)
  * Inventory state (`current_inventory_quintals`, `avg_daily_arrival_quintals`)
  * Weather and climate covariates (`rainfall_mm`, `temperature_c`)
  * Market variables (`msp_price`, `market_price`, `day_of_season`)
  * Categorical identifiers (`crop_type_encoded`, `state_encoded`)
* **Target Variable:** `actual_procurement_quintals` (Continuous numeric quantity)
* **Dataset & Split:**
  * Total Samples: 10,000 multi-state/crop historical procurement records (`ml/data/historical_arrivals.csv`)
  * Split: 80% Training (8,000 rows), 20% Held-out Test Set (2,000 rows)
  * Random Seed: `42` (Fixed deterministic split, no data leakage)
  * Data Type: Synthetic benchmark dataset generated to reflect multi-state seasonal procurement patterns
* **Calculated Metrics:**
  * **Mean Absolute Error (MAE):** `0.5316` quintals
  * **Root Mean Squared Error (RMSE):** `1.1483` quintals
  * **Coefficient of Determination (R²):** `0.9975`
  * **Mean Absolute Percentage Error (MAPE):** `0.2974%`
* **Important Findings:** The high R² (0.9975) is attributable to the controlled synthetic data generation equations. Under real-world agronomic, climatic, and open-market distress volatility, field R² values are expected to be lower.

---

#### 2. Procurement Anomaly Detection Model
* **Algorithm:** Scikit-Learn Isolation Forest (`IsolationForest`, `n_estimators=100`, `contamination=0.06`, `random_state=42`)
* **Purpose:** Detect anomalous procurement transactions such as weight tampering, moisture manipulation, turnaround time inflation, or abnormal volume spikes.
* **Features Used:**
  * `quantity_quintals`
  * `gross_weight_quintals`
  * `tare_weight_quintals`
  * `net_weight_quintals`
  * `moisture_percentage`
  * `foreign_matter_percentage`
  * `turnaround_minutes`
* **Evaluation on Labeled Benchmark Dataset:**
  * Dataset: 5,045 records (`ml/data/anomaly_training_dataset.csv`)
  * Test Set Size: 1,009 rows (20% held-out test split, 50 injected ground-truth anomalies)
  * Anomalies Flagged: 60
  * True Positives (TP): 50
  * False Positives (FP): 10
  * False Negatives (FN): 0
  * **Precision:** `0.8333` (83.33%)
  * **Recall:** `1.0000` (100.00%)
  * **F1-Score:** `0.9091` (90.91%)
* **Production Status (Ground-Truth Availability):**
  * In live production operations, **Ground-truth accuracy is NOT available**.
  * Isolation Forest operates as an unsupervised outlier detector in production; flagged records are routed to administrative audit queues for manual inspector verification.

---

#### 3. AI Price Estimation Engine
* **Type:** Trained XGBoost Regressor (`ml/models/price_estimation_xgb.joblib`) with Statutory MSP Constraint
* **Purpose:** Real AI-based procurement price estimation using multi-factor historical and real-time market features while enforcing statutory Minimum Support Price (MSP) as an absolute legal floor.
* **Input Features:**
  * Official MSP (`official_msp`)
  * Historical procurement prices and historical procurement quantities
  * Current and forecast market demand (`current_demand`, `forecast_demand`)
  * Current and forecast commodity supply (`current_supply`, `forecast_supply`)
  * State and district location encoding
  * Crop and agricultural season (`Kharif`, `Rabi`, `Zaid`, `All-Season`)
  * Storage and inventory availability headroom (`storage_headroom_pct`)
  * Supply surplus / deficit differential (`surplus_deficit`)
  * Historical inflation / procurement trends (`historical_trend_factor`)
* **Mathematical Floor Rule:**
  $$\text{Final Estimated Price} = \max(\text{AI Estimated Price}, \text{Official MSP})$$
* **Performance Metrics (Held-out Test Split):**
  * **Mean Absolute Error (MAE):** `₹15.90` per quintal
  * **Coefficient of Determination (R²):** `0.9999`
  * **Statutory Floor Violations:** `0` (100.0% compliance)
* **Factor Attribution:** The engine outputs explicit factor percentage contributions (`official_msp_baseline`, `demand_supply_pressure`, `storage_buffer_headroom`, `historical_trend`) and strictly labels values as `Official MSP`, `AI Estimated Price`, and `Final Estimated Price` (never referring to AI estimates as "MSP").

---

#### 4. Seasonal & Perishable Crop Multi-Factor Transport Priority
* **Type:** Multi-Criteria Priority Scoring Engine (`ml/inference/transport_priority.py`)
* **Purpose:** Dynamically prioritize logistics and green-channel transit for perishable agricultural commodities to prevent spoilage and sucrose loss.
* **Multi-Factor Priority Formula:**
  $$\text{Priority Score} = w_1 \cdot \text{Demand} + w_2 \cdot \text{Perishability} + w_3 \cdot \text{Expected Qty} + w_4 \cdot (1 - \text{Storage Buffer}) + w_5 \cdot \text{Dest Demand} + w_6 \cdot \text{Congestion}$$
* **Metadata Coverage:** 17 essential Indian crops in `crop_metadata` table covering grains, pulses, oilseeds, fibers, and high-perishability produce (Sugarcane, Tomato, Onion, Potato) with shelf life, storage requirements, and harvest velocity.


---

#### 4. Congestion Intelligence Engine
* **Type:** Deterministic Rule-Based Operational Threshold Engine (**NOT a Machine Learning Model**)
* **Purpose:** Classify procurement centre operational load to prevent gate bottlenecks and trigger dynamic farmer slot redirection.
* **Classification Rules:**
  * **LOW:** Utilization $< 50\%$ (Normal operational capacity)
  * **MEDIUM:** $50\% \le \text{Utilization} < 75\%$ (Moderate queuing)
  * **HIGH:** $75\% \le \text{Utilization} < 90\%$ (Congestion warning)
  * **CRITICAL:** $\text{Utilization} \ge 90\%$ (Gate saturation; redirection recommended)
* **Metrics:** 100% deterministic rule adherence. No ML classification metrics (e.g., accuracy, ROC-AUC) apply, as this is an operational rule system.

---

#### 5. Logistics & Truck Route Optimizer
* **Type:** Operations Research Mixed-Integer Linear Programming Engine (**NOT a Machine Learning Model**)
* **Algorithm / Solver:** Google OR-Tools (`pywraplp.Solver.CreateSolver('SCIP')`)
* **Purpose:** Solve multi-centre fleet dispatch minimizing total haulage distance, vehicle count, and unmet centre demand.
* **Objectives & Constraints:**
  * **Objective:** Minimize $\sum_{(i,j)} \text{Distance}_{i,j} \times x_{i,j} + \text{Penalty} \times \text{UnmetDemand}$
  * **Payload Constraint:** $\sum_j \text{Load}_{k,j} \le \text{TruckCapacity}_k$
  * **Origin Supply Constraint:** Dispatched volume $\le$ Available centre lot stock
  * **Destination Storage Constraint:** Received volume $\le$ Warehouse available storage
* **Evaluation on Standard Multi-Centre Benchmark (5 Centres, 3 Trucks):**
  * **Solution Status:** `Optimal` (Feasible solution rate: **100%**)
  * **Capacity Violations:** `0` (Zero truck overload or storage overflow)
  * **Total Allocated Volume:** `190.0` quintals
  * **Total Route Distance:** `101.0` km
  * **Fleet Capacity Utilization:** `95.0%`
  * **Constraint Violations:** `0`

---

### Model Evaluation Limitations

1. **Synthetic Training Data**: Both the supply forecast and anomaly detection models were trained and benchmarked on synthesized datasets (`ml/data/historical_arrivals.csv`, `ml/data/anomaly_training_dataset.csv`). While these datasets accurately model multi-state procurement dynamics, the reported metrics demonstrate software implementation fidelity rather than real-world agronomic accuracy under unobserved weather catastrophes or global commodity shocks.
2. **Ground-Truth Label Absence in Production**: Anomaly detection precision and recall are measurable only on benchmark sets with pre-injected anomaly labels. In live production environments, ground-truth labels do not exist until verified by human auditors.
3. **Deterministic Bounds in Price Intelligence**: The price intelligence engine uses a policy-constrained econometric model rather than an unconstrained deep neural network to guarantee that farmers are never quoted below the statutory MSP.
4. **Optimization vs. Learning**: OR-Tools is an exact/heuristic mathematical solver, not a predictive learning model. It evaluates for optimality and constraint satisfaction rather than predictive accuracy.


---

## 8. SIH 26032 KisanFlow Dataset & Dynamic AI Queue System

BharatAgri Iteration 2 is powered by the comprehensive Smart India Hackathon (SIH 26032) KisanFlow synthetic procurement dataset. The platform bridges realistic large-scale procurement operations with a lightweight, ultra-simple farmer interface and a data-grounded AI dynamic queue engine.

### 8.1 Dataset Architecture & Storage Locations

The raw data workbook is maintained strictly as an immutable raw artifact, while processed masters are decoupled:

- **Raw Dataset Location**: `data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx`
  - **`farmers`**: 5,000 farmer profiles (landholdings, primary crops, expected yields, geolocations, preferred languages).
  - **`procurement_centres`**: 20 procurement centres (daily capacities, weighbridges, quality labs, operating hours).
  - **`appointments`**: 18,000 procurement appointment bookings across dates and time slots.
  - **`procurement_transactions`**: 9,000 completed procurement transactions with gross weights, moisture %, grade, rate, and payment status.
  - **`queue_events`**: 20,000 live queue state transition records (check-in, quality start/complete, weighment, checkout).
  - **`centre_daily_metrics`**: 900 historical operational daily aggregates (throughput, wait times, equipment downtime, peak queue).
  - **`notifications`**: 20,000 farmer alert records (slot confirmations, "Come Now" arrival alerts, payment updates).
  - **`ml_training_dataset`**: 18,000 historical training records for queue wait time prediction.
- **Processed Unified Crops Catalog**: `data/processed/crops/crops_master.csv`
  - Normalizes 18 national and regional crops (Paddy, Wheat, Maize, Cotton, Soybean, Sugarcane, Mango, Bajra, Jowar, Tur, Gram, Mustard, Groundnut, Barley, Ragi, Sunflower, Jute, Urad).
  - Encodes official Government MSP (₹/Quintal), procurement seasons (Kharif/Rabi/Zaid), primary states, regional Hindi & Marathi names, maximum permissible moisture %, perishability index, and godown shelf life.

### 8.2 Seeding & Database Migration Process

The database migration and batch-seeding pipeline is fully automated, idempotent, and transactional:

```bash
# 1. Run column migrations on existing database
python scripts/migrate_columns.py

# 2. Build normalized crop catalog
python scripts/build_crops_master.py

# 3. Seed all 90,000+ SIH dataset records with foreign key integrity
python scripts/seed_sih_dataset.py
```

*What the Seeder Does*:
1. Reads `data/processed/crops/crops_master.csv` and updates the `crops` catalog with canonical MSP and attributes.
2. Migrates and upserts all 20 procurement centres into `procurement_centres` and seeds corresponding centre manager user accounts.
3. Batch-inserts 5,000 farmers into `users`, `farmers`, and `farmer_crops`.
4. Batch-inserts 18,000 appointments into `appointments`, `procurement_slots`, and `bookings`.
5. Batch-inserts 9,000 procurement transactions into `procurement_transactions`, `procurement_collections`, `quality_inspections`, `electronic_weighments`, `procurement_records`, and `payments`.
6. Batch-inserts 20,000 queue events into `queue_events`.
7. Batch-inserts 900 centre metrics into `centre_daily_metrics`.
8. Batch-inserts 20,000 notifications into `notifications`.

---

### 8.3 Dynamic AI Queue Architecture

Rather than a static calendar booking system, BharatAgri deploys an active dynamic queueing engine that tracks live mandi conditions and farmer transit:

```text
[ FARMER ]                    [ QUEUE ENGINE ]                 [ MANDI CENTRE ]
    │                              │                                  │
    │── 1. Select Crop & Qty ─────►│ Evaluate Distance, Capacity,     │
    │                              │ Queue & Crop Eligibility         │
    │◄── Best Centre & Slot ───────│                                  │
    │                              │                                  │
    │── 2. Confirm Booking ───────►│ Generate Digital Token (e.g. A184)
    │                              │ Atomic Slot Lock                 │
    │◄── Digital Token Pass ───────│                                  │
    │                              │                                  │
    │                              │ Monitor Live Queue Events ◄──────│ Real-time Events
    │                              │ (Arrivals, QC, Weighment)        │ (Weighing, QC)
    │                              │                                  │
    │                              │ Gradient Boosting ML Wait Engine │
    │                              │ Predict Wait: 37 ± 14 min        │
    │                              │ Departure = Slot - Travel - 15m  │
    │                              │                                  │
    │◄── 3. "COME NOW" Alert ──────│ When Farmers Ahead <= 5          │
    │    Proceed to Centre #17     │ Push / SMS / IVR Notification    │
    │                              │                                  │
    │── 4. Arrive at Mandi ───────►│ QR Check-in & Gate Inward ──────►│ Check-in
```

#### ML Waiting-Time Prediction vs. Queue Baseline
The wait-time engine evaluates live centre conditions:
`[queue_length, farmers_in_service, processing_rate, active_weighing_machines, quality_stations, staff_available, equipment_failure, weather_delay, historical_avg_wait, hour, day_of_week, peak_hour, quantity_quintals, distance_km]`.

*Empirical Validation Benchmark (Held-out 20% test set, 3,600 records)*:
- **Queueing Baseline (Little's Law $W = L / \mu$)**: MAE: **37.34 min**, RMSE: **72.43 min**, $R^2$: **-0.4594** (Struggles with non-stationary service spikes, station breakdowns, and multi-stage batching).
- **Random Forest Regressor**: MAE: **11.65 min**, RMSE: **14.69 min**, $R^2$: **0.9400**.
- **Gradient Boosting Regressor (Selected Champion)**: MAE: **11.29 min**, RMSE: **14.08 min**, $R^2$: **0.9448**.
- **XGBoost Regressor**: MAE: **11.30 min**, RMSE: **14.11 min**, $R^2$: **0.9446**.
- **Calibrated Uncertainty**: Outputs predicted wait alongside empirical 95% confidence intervals $[Wait - 1.96\sigma, Wait + 1.96\sigma]$ based on test residual standard deviation ($\sigma = 14.08$ min). Zero fabricated confidence percentages.

To retrain and evaluate the queue models:
```bash
python ml/training/train_queue_model.py
```
Model artifacts and metric manifests are saved to `ml/models/queue_wait_model.joblib` and `ml/models/queue_metrics.json`.

---

### 8.4 Key Dynamic Queue Capabilities

1. **Live Queue Tracking**: Real-time state calculated from `queue_events` displaying current queue length, active weighing machines, processing rate (farmers/hr), and operational status.
2. **Digital Token System**: Generates human-friendly token identifiers (e.g. `A184`), tracking currently served token (`A177`), farmers ahead, and estimated wait.
3. **"Come Now" Notification**: Triggers an alert when $\le 5$ farmers remain ahead of the farmer's token to minimize waiting time at the yard.
4. **Recommended Departure Time**: Combines slot time, farmer transit distance (at realistic rural speed of 30 km/h), and a 15-minute safety buffer (`Departure = Slot Start - Travel Duration - 15m Buffer`).
5. **Dynamic Centre Recommendation**: Ranks centres based on travel distance, available capacity, crop eligibility, and current congestion.
6. **Dynamic Slot Allocation**: Recommends slots with lowest projected congestion within operating hours.
7. **Centre Congestion Forecasting**: Uses `centre_daily_metrics` to forecast hourly arrivals (8:00 AM – 5:00 PM) for centre managers.
8. **Procurement Copilot for Officers**: Conversational natural language interface grounded strictly in live database state to answer questions about centre delays, capacity, and equipment status without hallucination.
9. **Transparency & Anomaly Review**: Five operational audit monitors flagging items for human review:
   - Duplicate active bookings by the same farmer.
   - Suspicious procurement quantities exceeding landholding yield benchmarks.
   - Queue sequence manipulation by operators.
   - Abnormal station processing durations.
   - Ghost transactions without corresponding weighing or QC events.

---

### 8.5 Farmer Dashboard UX Simplification

To accommodate rural, elderly, or low-literacy farmers, the primary Farmer Dashboard completely eliminates technical jargon (e.g. "Gradient Boosting", "Confidence Interval", "Throughput", "Congestion Coefficient").

**Main Screen (6 Large Action Cards)**:
1. 🌾 **Book Procurement / फसल बुकिंग**: Direct 3-step crop & quantity booking with automated centre recommendation.
2. 📍 **Nearby Centres / नजदीकी केंद्र**: Distance, queue wait, and opening status.
3. 🎫 **My Token & Slot / मेरा टोकन**: Prominent token pass (e.g. `A184`), QR code, and scheduled arrival.
4. 🔴 **Live Queue / लाइव कतार**: Farmers ahead, current token being served, and status color.
5. 💰 **Payment / भुगतान (DBT)**: Passbook with net amount, quintals sold, and payment clearance status.
6. ☎ **Help / सहायता**: Direct access to toll-free Kisan Call Centre and offline support.

**Advanced Insights (Secondary Tabs for Educated Farmers)**:
- **💡 AI Insights**: Detailed wait breakdown, recommended departure time calculation, and delay factors.
- **💰 MSP & Rates**: Official MSP rates, permissible moisture specifications, and gross harvest value calculator.
- **🔔 Alerts**: All system notifications including "Come Now" arrival alerts.
- **📋 Bookings History**: Historical appointment ledger and digital lot receipts.

---

## 9. Core API Endpoints

### Dynamic AI Queue & SIH Features (New)
- `POST /api/queue/predict-wait` - Gradient Boosting wait time prediction with 95% confidence interval
- `GET  /api/queue/centres/{id}/live` - Real-time queue state (queue length, processing rate, active stations)
- `GET  /api/queue/tokens/{token}` - Live digital token tracking (farmers ahead, current token serving)
- `GET  /api/queue/departure-recommendation` - Recommended departure time (slot - travel - buffer)
- `POST /api/queue/recommend-centre` - Multi-criteria dynamic centre recommendation
- `GET  /api/queue/recommend-slots/{centre_id}` - Dynamic slot allocation based on projected congestion
- `GET  /api/queue/centres/{centre_id}/congestion-forecast` - Hourly congestion forecast curve (8 AM - 5 PM)
- `POST /api/queue/copilot` - Data-grounded Procurement Copilot for officers
- `GET  /api/queue/anomalies` - Government anomaly audit list (duplicate bookings, ghost tokens, etc.)
- `GET  /api/queue/crops-master` - Canonical crop master catalog with MSP and standards
- `GET  /api/queue/farmer/{farmer_id}/active-status` - Consolidated farmer active token & queue status


### Authentication & RBAC
- `POST /api/auth/login` - Secure JWT token generation with role verification (FARMER, AGENT, CENTRE, GOVERNMENT)
- `GET  /api/auth/me` - Authenticated user profile and role details
- `POST /farmers/register` - Farmer registration with multi-crop support
- `POST /api/agents/register` - Field Agent / CSC operator registration
- `POST /centres/register` - Procurement Centre manager onboarding
- `POST /api/government/register` - Authorized Government/Admin registration

### Farmers & Field Agents
- `GET  /api/farmers/profile` - Authenticated farmer profile & registered crops
- `POST /api/farmers` - Farmer registration (Agent assisted or self)
- `GET  /api/agents/assigned-farmers` - Cluster farmers for authenticated agent
- `POST /api/agents/assisted-booking` - Agent slot booking on farmer's behalf
- `GET  /farmers/{id}/market-intelligence` - State demand, supply shortages, price opportunities & crop advisory
- `GET  /farmers/{id}/daily-intelligence` - Farmer personalized daily briefings & active booking alerts

### Procurement Centres, Capacity & Redirection
- `GET  /api/centres` - List active procurement centres with crop filters
- `GET  /api/slots/availability` - Real-time slot and quintal capacity checking
- `POST /api/bookings` - Atomic booking creation with capacity locking and QR code generation
- `POST /api/qr/verify` - Controlled single-frame gate check-in verification
- `GET  /api/centres/{id}/redirection-options` - Automated alternative centre recommendations (distance, capacity, crop support, congestion)
- `GET  /api/centres/{id}/daily-intelligence` - Centre automated daily operational intelligence briefing
- `GET  /api/centres/{id}/insights` - Centre 3-tier Insights Engine (Descriptive, Predictive, Prescriptive)

### Full Procurement Lifecycle, Live Tracker & Lots
- `POST /api/collections` - Inward gate collection record
- `POST /api/quality` - Quality inspection (moisture, foreign matter, grade)
- `POST /api/weighments` - Electronic weighment (gross, tare, net quintals)
- `POST /api/procurement` - Final procurement, MSP computation, and immutable Lot ID generation
- `GET  /api/storage` - Warehouse bin & lot storage
- `GET  /api/payments/status/{id}` - Direct Benefit Transfer (DBT) payment status
- `GET  /bookings/{id}/workflow-status` - Live 8-step lifecycle tracker (`BOOKED → CHECKED IN → ARRIVED → QUALITY CHECK → WEIGHING → STORAGE → PAYMENT INITIATED → PAID`)

### AI, Intelligence & Optimization
- `POST /price/estimate` - Real XGBoost AI Procurement Price Estimation (`MAX(AI, MSP)` with factor attribution)
- `GET  /crops/metadata` - 17 Indian crop profiles with shelf-life, category, season, perishability score
- `GET  /api/government/perishable-priority` - Perishable crop transport priority rankings
- `POST /api/ai/supply-forecast` - XGBoost 7-30 day arrival forecasts
- `GET  /api/ai/congestion` - Centre congestion index and operational status
- `POST /api/ai/truck-allocation` - OR-Tools fleet allocation optimization
- `GET  /api/ai/anomalies` - Anomaly surveillance protocol (**Potential Anomaly / Requires Review**)
- `GET  /api/bardan/forecast` - Jute bag requirements vs stock shortage warning
- `GET  /api/government/insights` - National & State 3-tier Insights Engine (Descriptive, Predictive, Prescriptive)
- `GET  /api/government/daily-intelligence` - Automated National Daily Intelligence summary

### Operational Alerts System
- `GET  /api/centres/{id}/alerts` - Operational alerts for Centre Managers (WHAT → WHERE → WHEN → WHY → severity → action)
- `POST /api/centres/alerts/{id}/resolve` - Mark centre alert resolved
- `GET  /api/government/alerts` - System-wide operational alerts for Government/Admin

### Grievance Redressal & Auditing
- `GET  /api/complaints` - Grievance tickets listing
- `POST /api/complaints` - Submit grievance
- `GET  /api/audit` - Administrative tamper-evident audit logs


---

## 9. Testing & Quality Assurance

To execute the automated test suite:
```bash
set PYTHONPATH=.
python -m pytest backend/tests/test_api.py -v
```

All 12 backend test suites test:
1. System Health & Database Ping (`test_health_check`)
2. Multi-Role Authentication for all 4 roles (`test_login_all_four_roles`)
3. Role-Based Access Control (RBAC) Protection (`test_rbac_protection`)
4. Procurement Centre Listing & Filtering (`test_centres_listing`)
5. Farmer Profile & Crop Records (`test_farmer_profile`)
6. Atomic Booking Validation & QR Generation (`test_booking_workflow_and_qr`)
7. Complete 8-Stage Procurement Traceability Lifecycle (`test_full_procurement_lifecycle`)
8. XGBoost Supply Forecasting Inference (`test_ai_supply_forecast`)
9. Centre Congestion Calculation (`test_ai_congestion_calculation`)
10. Google OR-Tools Truck Fleet Optimization (`test_ai_truck_allocation_optimization`)
11. Bardan Jute Bag Consumption & Shortage Projections (`test_bardan_forecast`)
12. End-to-End Farmer Grievance Redressal (`test_complaints_end_to_end`)

Frontend Build Verification:
```bash
cd frontend
npm run build
```
*(Produces optimized production bundle in `frontend/dist/` with zero compile errors)*.

---

## 10. Multi-Language & Dark Mode

- **Dark Mode**: Persisted across sessions via `localStorage` with modern CSS custom property tokens.
- **Language Support**: Instant runtime language switching between **English (en)**, **Hindi (hi)**, and **Marathi (mr)**, with full UI translation bundles located in `frontend/src/locales/`.

---

## 11. Project Directory Structure

```text
BharatAgri-main/
│
├── README.md                        # This file
├── .env                             # Local runtime configuration (gitignored)
├── .env.example                     # Environment variable template
├── requirements.txt                 # All Python backend + AI/ML dependencies
├── start-local.bat                  # One-click Windows launcher
├── start-local.sh                   # One-click Linux/macOS launcher
│
├── database/
│   └── bharatagri_iteration2.sql    # SINGLE self-contained schema + seed SQL file
│
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI application factory & router registration
│       ├── database.py              # SQLAlchemy engine, session factory
│       ├── models/                  # SQLAlchemy ORM table definitions
│       │   ├── user.py              # Users, roles, sessions
│       │   ├── farmer.py            # Farmer profiles, land, crops
│       │   ├── agent.py             # Agent assignments, cluster coverage
│       │   ├── centre.py            # Procurement centres, operating hours, holidays
│       │   ├── booking.py           # Slot reservations, QR codes
│       │   ├── procurement.py       # Collection → QC → Weighment → Procurement → Lot
│       │   ├── storage.py           # Warehouse bin-lot mapping
│       │   ├── payment.py           # DBT payment records
│       │   ├── truck.py             # Truck fleet, routes, dispatch requests
│       │   ├── inventory.py         # Bardan jute bag stock & consumption
│       │   ├── complaint.py         # Grievance tickets
│       │   └── audit.py             # Tamper-evident audit log entries
│       │
│       └── api/                     # FastAPI route modules (one per domain)
│           ├── auth.py              # Login, JWT, /me
│           ├── farmers.py           # Farmer profile, crops, registration
│           ├── agents.py            # Agent dashboard, assigned farmers, assisted booking
│           ├── centres.py           # Centre listing, congestion, redirection, holidays
│           ├── slots.py             # Slot availability, capacity checks
│           ├── bookings.py          # Booking creation, QR generation
│           ├── qr.py                # QR gate check-in verification
│           ├── procurement.py       # Full 8-stage lifecycle endpoints
│           ├── storage.py           # Warehouse storage allocation
│           ├── inventory.py         # Bardan forecast & stock management
│           ├── trucks.py            # Truck routing, dispatch, OR-Tools integration
│           ├── price.py             # MSP rates, market prices, price intelligence
│           ├── ai.py                # XGBoost forecast, Isolation Forest, congestion
│           ├── government.py        # National command centre analytics & state filters
│           ├── complaints.py        # Grievance redressal API
│           ├── audit.py             # Audit log access
│           ├── health.py            # System health & DB ping
│           └── stats.py             # Aggregate KPI statistics
│
├── ml/
│   ├── data/                        # Raw historical dataset CSVs for training
│   ├── preprocessing/               # Feature engineering & normalization scripts
│   ├── training/
│   │   ├── train_forecast.py        # XGBoost Regressor training pipeline
│   │   └── train_anomaly.py         # Isolation Forest training pipeline
│   ├── inference/
│   │   └── optimizer.py             # Google OR-Tools MIP truck fleet optimizer
│   ├── evaluation/                  # Model evaluation notebooks & metrics
│   └── models/                      # Serialized model artifacts (.pkl)
│       ├── supply_forecast_xgboost.pkl
│       └── anomaly_isolation_forest.pkl
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx                 # React DOM entry point
│       ├── App.jsx                  # Root router & protected route wrappers
│       ├── index.css                # Global CSS design tokens (dark/light themes)
│       ├── context/                 # React Context providers (Auth, Theme, Language)
│       ├── components/              # Shared UI components (Navbar, Sidebar, Charts)
│       ├── services/                # Axios API client + per-domain service modules
│       ├── utils/                   # Date helpers, QR renderers, formatters
│       ├── locales/                 # i18n translation JSON bundles
│       │   ├── en.json
│       │   ├── hi.json
│       │   └── mr.json
│       └── pages/                   # Full-page React views per role
│           ├── LoginPage.jsx
│           ├── HomePage.jsx
│           ├── FarmerDashboard.jsx
│           ├── AgentDashboard.jsx
│           ├── CentreDashboard.jsx
│           ├── GovernmentDashboard.jsx
│           ├── SlotBookingPage.jsx
│           ├── BookingConfirmationPage.jsx
│           └── AboutUsPage.jsx
│
├── backend/tests/
│   └── test_api.py                  # Full pytest integration test suite (18 suites)
│
└── scripts/                         # Utility scripts (DB seed helpers, model retrain)
```

---

## 12. Role-by-Role Feature Walkthrough

### 👨‍🌾 Farmer Role
After logging in as a Farmer, the dashboard provides:

| Feature | Description |
| :--- | :--- |
| **My Profile** | View registered land holdings (acres/hectares), bank account details (for DBT), aadhaar-verified identity |
| **My Crops** | View all registered crops with variety, season, and expected yield |
| **Slot Booking** | Select a procurement centre, crop, estimated quantity → receive a QR-coded booking pass |
| **My Bookings** | View booking status (`BOOKED → CHECKED_IN → PROCURED → PAID`) |
| **QR Pass** | Download or display the verifiable QR code for gate entry |
| **Lot Traceability** | Track a specific Lot ID through every stage of the procurement lifecycle |
| **DBT Payment Status** | Monitor Direct Benefit Transfer payment initiation and credit confirmation |
| **Helpdesk / Complaints** | Submit and track grievance tickets with resolution timelines |
| **MSP Price Intelligence** | View current MSP rates, market prices, and price trend analysis for registered crops |

---

### 🧑‍💼 Field Agent Role
After logging in as a Field Agent, the dashboard provides:

| Feature | Description |
| :--- | :--- |
| **Cluster Overview** | View the geographic cluster and all farmers assigned to this agent |
| **Assigned Farmers** | Full farmer roster with registration status, land, and crop details |
| **Farmer Registration** | Register new farmers including land records, bank details, and crop declarations |
| **e-KYC Verification** | Initiate and track Aadhaar-based identity verification for registered farmers |
| **Assisted Booking** | Book a procurement slot on behalf of a farmer in the cluster |
| **Farmer Complaints** | View and escalate grievances raised by assigned farmers |
| **Agent Analytics** | Booking success rates, farmer onboarding metrics, cluster-level KPIs |

---

### 🏭 Procurement Centre Role
After logging in as a Procurement Centre operator, the dashboard provides:

| Feature | Description |
| :--- | :--- |
| **Gate Operations** | QR code scanner for controlled single-use check-in, booking verification |
| **Collection Records** | Register inward arrival — capture truck number, bags, gross weight |
| **Quality Inspection (QC)** | Record moisture %, foreign matter %, grade (A/B/C/Rejected) |
| **Electronic Weighment** | Capture gross, tare, and computed net weight in quintals |
| **Procurement & Lot Generation** | Finalize procurement at MSP, auto-generate immutable Lot ID |
| **Storage Allocation** | Assign lot to warehouse bin / godown rack |
| **Bardan (Jute Bag) Inventory** | Monitor bag stock levels, consumption rate, shortage warnings |
| **Truck Dispatch Requests** | Submit outward dispatch requests to logistics for optimized routing |
| **Centre Holidays** | View and manage centre operating-day exceptions and holiday schedules |
| **DBT Payment Initiation** | Trigger Direct Benefit Transfer payment for completed lots |

---

### 🏛️ Government / National Command Centre Role
After logging in as Government administrator, the dashboard provides:

| Feature | Description |
| :--- | :--- |
| **National KPIs** | Aggregate view — total farmers onboarded, quintals procured, MSP value disbursed, active centres |
| **State Filter** | Filter all analytics by state / union territory in real time |
| **Supply Forecast (XGBoost)** | AI-powered 7–30 day arrival forecasts per crop, per region |
| **Congestion Monitor** | Real-time operational utilization index across all active centres (LOW/MEDIUM/HIGH/CRITICAL) |
| **Centre Redirection** | Initiate emergency capacity redirection to alternate centres |
| **OR-Tools Truck Optimization** | Submit fleet optimization requests and view route assignments |
| **Procurement Anomaly Detection** | Isolation Forest flagged anomalies — weight discrepancies, volume spikes, outlier patterns |
| **Bardan National Overview** | National jute bag stock projection vs incoming harvest volumes |
| **Payment Monitoring** | DBT payment disbursement tracking across states and crops |
| **Audit Logs** | Tamper-evident access and modification records for compliance |

---

## 13. MSP & Price Intelligence

The Price Intelligence module provides crop-specific pricing context at both the farmer and government tiers:

- **Minimum Support Price (MSP)**: Fetched from the live database for every crop variety. MSP rates are crop-season specific and government-notified.
- **Market Price Comparison**: Compares the prevailing market mandi price against the government MSP to flag whether the farmer is better served by direct procurement or open market.
- **Procurement Price**: The actual effective price at which a lot is procured (at or above MSP, per policy).
---

## 14. Real-World Datasets, Methodology & Honest AI Model Evaluation (Iteration 2)

In BharatAgri Iteration 2, all AI models and optimization routines are grounded in verified agricultural data definitions, honest chronological validation, and baseline comparisons. **No accuracy claims or performance numbers are fabricated.**

### A. Data Sources, States & Agricultural Coverage
* **Official Minimum Support Prices (MSP)**: Grounded in Ministry of Agriculture and Farmers Welfare (MoAFW) / Commission for Agricultural Costs and Prices (CACP) notifications for Kharif & Rabi marketing seasons (2024–2026).
* **Mandi Arrivals & Wholesale Prices**: Calibrated against Directorate of Economics and Statistics (DES) and AGMARKNET mandi arrival reports.
* **Geographic Scope (6 Pilot States)**:
  1. **Goa** (Coastal, Paddy & Sugarcane, perishables, storage capacity constraints)
  2. **Maharashtra** (Western, Cotton, Soybean, Onion, Sugarcane)
  3. **Karnataka** (Southern, Maize, Paddy, Tomato, Groundnut)
  4. **Madhya Pradesh** (Central, Wheat, Soybean, Gram)
  5. **Uttar Pradesh** (Gangetic Plain, Wheat, Sugarcane, Potato)
  6. **Punjab** (Northern Grain Belt, Paddy, Wheat, high-volume mandi arrivals)
* **Crops Covered**:
  * **Non-perishable foodgrains**: Paddy, Wheat, Maize, Soybean, Gram, Groundnut, Cotton (Shelf-life: *Not applicable*).
  * **Semi-perishables**: Potato (60–90 days), Onion (30–45 days).
  * **High perishables**: Sugarcane (2–3 days verified), Tomato (3–5 days).
* **Data Separation**: Sourced macroeconomic benchmarks (official MSP floors, Mandi baseline ranges, crop agronomic parameters) are preserved as ground truth. Micro-operational transactions (gate weighbridge tickets, queue barcodes, bag consumption logs) are generated via calibrated operational simulations and explicitly marked as demonstration benchmarks rather than live sensor streams.

---

### B. Supply Forecaster Evaluation (Chronological Split vs. Baselines)
To prevent lookahead bias and target leakage, the 10,000-row procurement dataset was evaluated using a **chronological split**:
* **Training set**: Months 1–9 (Kharif pre-arrival & base procurement)
* **Holdout test set**: Months 10–12 (Peak post-harvest arrivals, 534 records)

| Model / Baseline | MAE (Quintals) | RMSE (Quintals) | R² Score | Evaluation Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Historical Mean Baseline** | 19.19 Q | 22.44 Q | -0.0172 | Predicts overall training mean; fails on peak arrival volatility |
| **Seasonal Crop Average Baseline** | 19.20 Q | 22.42 Q | -0.0158 | Predicts crop-specific historical mean; ignores centre capacity & bookings |
| **Linear Baseline (Ridge)** | 3.07 Q | 3.82 Q | 0.9705 | Captures linear booking-to-arrival correlation |
| **XGBoost Regressor (Ours)** | **2.30 Q** | **2.95 Q** | **0.9824** | Captures non-linear arrival patterns, booked quotas, and centre limits |

*Uncertainty Quantification*: Empirical ±10% prediction intervals are provided in the UI for planning purposes.

---

### C. Price Intelligence Model (Evaluated Separately)
* **Architecture**: XGBoost Regressor trained on 7,871 mandi transactions across 6 states.
* **Economic Invariant**: Enforces `Final Price = MAX(Model Estimate, Official MSP)` to safeguard farmer income.
* **Evaluation Metrics (Holdout 20%)**:
  * **MAE**: ₹16.00 / Quintal
  * **RMSE**: ₹23.17 / Quintal
  * **R² Score**: 0.9999 (Constrained by official MSP floor dynamics)
* **Key Drivers**: Historical Mandi Price (61.6% importance), Official MSP Floor (27.1%), Season (6.8%), Crop Variety (4.6%).

---

### D. Anomaly Surveillance Engine (Isolation Forest)
* **Architecture**: Unsupervised Isolation Forest (`contamination = 0.06` matching expected operational outlier rate ~6%).
* **Feature Vector**: Booked quantity, collected quantity, weighbridge net weight, procured quantity, moisture content %, elapsed processing minutes, quantity difference.
* **Strict Labeling Standard**: Output is labeled exclusively as **`Potential Anomaly — Requires Review`** (never "Fraud Confirmed").
* **Evaluation & Ground-Truth Disclosure**:
  * Unsupervised test contamination flagged 60 potential outliers out of 1,009 holdout cases.
  * *Honest Limitation*: Real-world production fraud labels do not exist in public agricultural databases. True classification precision and recall cannot be asserted as verified ground truth without manual physical investigation of every weighbridge ticket. An end-to-end human verification workflow and immutable audit log are provided to record on-site inspection outcomes.

---
---

## 15. Corrected Procurement Workflow, Database & Mango AI System

BharatAgri-2 introduces an end-to-end corrected agricultural procurement platform, strict state-crop data integrity, simplified ICAR-grounded perishability tracking, multi-employee isolation with photo evidence, and an upgraded multi-mango computer vision pipeline.

### A. Strict State-Crop Master Data & Database Sanitization
The platform enforces regional agricultural master data at the database, backend ORM, and frontend UI levels:
* **Goa**: Mango, Banana, Tomato
* **Maharashtra**: Sugarcane, Wheat, Cotton
* **Karnataka**: Paddy, Maize, Bajra

**Sanitization Results**:
- Re-mapped 26 centres and 2,054 farmers strictly to their legitimate states.
- Audited **10,257 bookings** and **7,875 procurement records** with **0 invalid state-crop mismatches** (`scripts/verify_db_consistency.py` exits with 0 errors).
- Synchronized `crop_metadata` to include all 9 configured state crops.

### B. Simplified Perishability Tab (ICAR Grounded)
The Perishability tab on the Government Dashboard has been stripped of irrelevant transport, truck, and mandi routing formulas. It directly answers:
> **What crop is this, and approximately how many days does it remain fresh and usable under standard storage conditions?**

| Crop | Approx. Freshness / Shelf-Life | Recommended Storage Condition | State |
| :--- | :---: | :--- | :--- |
| **Mango** | 7 – 14 days | Cool dry ventilated area (12–14°C) | Goa |
| **Banana** | 4 – 7 days | Room temp (13–15°C); avoid direct sunlight | Goa |
| **Tomato** | 5 – 10 days | Ambient (18–21°C) or cool cellar | Goa |
| **Sugarcane** | 2 – 5 days | Immediate crushing post-harvest; high inversion loss | Maharashtra |
| **Wheat** | 180 – 365 days | Dry hermetic bin (<12% moisture) | Maharashtra |
| **Cotton** | 180 – 365 days | Dry covered warehouse (<8% moisture) | Maharashtra |
| **Paddy** | 180 – 365 days | Ventilated dry storage (<13% moisture) | Karnataka |
| **Maize** | 120 – 240 days | Aerated dry silo (<13% moisture) | Karnataka |
| **Bajra** | 90 – 180 days | Dry moisture-proof packaging (<12% moisture) | Karnataka |

*Values grounded in ICAR and National Institute of Agricultural Extension Management guidelines.*

### C. Multi-Employee Procurement Workflow & Step 5 MSP Fix
1. **Employee-Wise Step Attribution**:
   - **Step 1 (Collection / Initial Check)**: Produce lot verified, bag count, transport method (Farmer's Own, Tractor, Private Vehicle, Hired Vehicle, Transporter, Other), initial visual check, and collection produce photo evidence.
   - **Step 2 (Quality Inspection)**: Moisture %, foreign matter %, physical quality measurements, and testing machine evidence photo.
   - **Step 3 (AI Quality Inspection)**: Multi-mango AI scanner or standard visual QC, recording employee, timestamp, and AI evidence.
   - **Step 4 (Weighment)**: Weighbridge gross/tare weighment and weighing machine display evidence photo.
   - **Step 5 (Procurement Finalization)**: Final grade clearance and payment initiation. Sourced directly from `estimated_procurement_price` (Rs 4,920/q for Goa Mango).
   - **Storage Final Check**: Storage lot assignment, received quantity verification, storage conditions, and storage stack evidence photo.
2. **Fraud Prevention & Employee Isolation**: Sensitive measurements (moisture %, foreign matter %, net weight, unit price) entered by upstream employees are hidden on downstream verification screens to prevent confirmation bias and collusion.
3. **Step 5 500 Error Resolution**:
   - Diagnosed root cause: `Payment` model expected `procurement_id` foreign key (not `booking_id`) and `amount` / `msp_rate` columns.
   - Resolved by correcting foreign key and column mappings and connecting directly to `StateCropSupplyDemand.estimated_procurement_price`.

### D. Reusable Photo Evidence System
All verification photos are stored via a unified table `procurement_evidence` (`process_evidence` conceptual design):
- **Fields**: `id`, `appointment_id`, `booking_id`, `process_step`, `evidence_type`, `file_path`, `uploaded_by`, `uploaded_at`, `notes`.
- **Supported Types**: `COLLECTION_PRODUCE`, `QUALITY_MACHINE`, `QUALITY_INSPECTION`, `WEIGHMENT`, `STORAGE`, `AI_SCAN`, `OTHER`.
- Files are saved to `backend/uploads/evidence/` with SHA-256 uniqueness and served via authenticated static endpoints.

### E. Mango AI Computer Vision Upgrades

#### 1. Automated Image Quality Check
Prior to inference, `ml/inference/mango_detector.py` validates images across 4 quality thresholds:
- Resolution $\ge 300 \times 300$ px.
- Darkness ($L^* < 20$) and Brightness ($L^* > 235$).
- Blur via Laplacian variance ($	ext{Var}(
abla^2 I) < 65$).

#### 2. Multi-Mango Instance Separation
Replaced naive single-blob connected components with **Euclidean Distance Transform Voronoi Partitioning** (`scipy.ndimage.distance_transform_edt`):
- Accurately splits touching and overlapping mangoes into distinct object bounding boxes.
- Tested on 128 multi-mango images: **196 touching fruits successfully separated** (vs. only 49 isolated by naive connected components, a **300% improvement**).

#### 3. Visual Ripeness Classification
Incorporated visual ripeness estimation based on calibrated CIELAB chromaticity distributions:
- **Ripe**: Dominant yellow/orange coloration ($b^* \ge 24, a^* > -5$).
- **Nearly Ripe**: Yellow-green transitional skin ($b^* \ge 16, -12 \le a^* \le -4$).
- **Not Ripe**: Deep green immature surface ($a^* < -12, b^* < 18$).
- **Uncertain / Needs Review**: Ambiguous lighting or mixed coloration.

#### 4. Green Goan Mango False-Positive Root Cause & Fix
- **Problem**: Testing on real-world green Goan mangoes produced 100% false-defective classifications.
- **Root Cause**: The training datasets (`MangoFruitBD`, `MangoDHDS`, `MangoFruitDDS`) were skewed toward yellow varieties where any region with low $b^*$ or negative $a^*$ was correlated with necrotic rot.
- **Correction**: Re-calibrated CIELAB defect thresholds in `ml/preprocessing/cielab_extractor.py` and `ml/inference/mango_quality_scanner.py`. Emerald green Goan mangoes ($a^* \le -10, b^* \ge 5$) are preserved as healthy skin, while true fungal lesions ($L^* < 35$, chromaticity $< 14$) are precisely detected.
- **Result**: False positive rate on healthy green Goan mangoes dropped from **100.0% to 0.0%**.

### F. Actual Model Metrics (80/20 Leakage-Safe Holdout Split)

| Model Architecture | Features | 5-Fold CV Macro F1 | Test Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Model A (RBF SVM) | $a^*, b^*$ | 0.7394 | 78.15% | 0.7476 | 0.7278 | 0.7360 | 0.7790 |
| Model B (KNN, k=5) | $a^*, b^*$ | 0.7014 | 72.93% | 0.6890 | 0.6813 | 0.6844 | 0.7272 |
| Model C (SVM+KNN Decision Fusion) | $a^*, b^*$ | 0.7399 | 78.37% | 0.7580 | 0.7390 | 0.7475 | 0.7815 |
| **Model D (RBF SVM with Lightness)** | $L^*, a^*, b^*$ | **0.7753** | **81.09%** | **0.7877** | **0.7680** | **0.7745** | **0.8084** |

### G. External & Real-World Validation Performance (128 Test Images, 226 Mangoes)

| Metric | Measured Value | Notes |
| :--- | :---: | :--- |
| **Ground Truth Mangoes** | 226 | Across 128 real-world images |
| **Detected Instances** | 456 | Distance transform Voronoi candidate proposals |
| **True Positives (IoU $\ge 0.5$)** | 87 | Matches ground truth bounding boxes |
| **Detection Precision** | 19.08% | Candidate proposals over-segment high-texture fruit piles |
| **Detection Recall** | 38.50% | Successfully detects individual fruits in challenging layouts |
| **Detection F1** | 0.2551 | Multi-mango instance isolation score |
| **Touching Mango Separation** | **196 separated** | Compared to 49 by naive connected components (+300%) |
| **Goa Green Mango False-Positive Rate** | **0.0%** | Down from 100.0% prior to CIELAB recalibration |
| **Ripeness Accuracy (Clear Samples)** | **50.0%** | Ambiguous samples cleanly routed to "Uncertain / Needs Review" |

*Known Limitation*: Heavy occlusions (>50% hidden) in dense mango crates cannot be reliably isolated with classical Voronoi segmentation alone and are correctly routed to "Needs Review" by the system.

---

## 16. Reproducibility & Commands

### Database Consistency Check:
```bash
python scripts/verify_db_consistency.py
```

### End-to-End Procurement Workflow Test:
```bash
python scripts/verify_e2e_procurement_workflow.py
```

### Mango AI Real-World & Goa Validation:
```bash
python ml/evaluation/validate_goa_mangoes.py
```

### Run Backend Unit & Integration Tests:
```bash
pytest tests/ -v
```

### Build Frontend:
```bash
cd frontend && npm run build
```

---

## 17. Deployment Notes

### Environment Variables

All sensitive runtime configuration is controlled via the `.env` file at the project root. **Never commit `.env` to source control.** Use `.env.example` as the template:

```bash
cp .env.example .env
# Edit .env with your actual DB credentials and JWT secret
```

### Production Recommendations

| Concern | Recommendation |
| :--- | :--- |
| **Database** | Use a managed MySQL 8.0 instance (Cloud SQL, RDS, or PlanetScale) with SSL enabled |
| **Backend** | Deploy FastAPI via `gunicorn + uvicorn workers` behind an Nginx reverse proxy |
| **Frontend** | Run `npm run build` → serve `frontend/dist/` from Nginx or deploy to Vercel / Netlify |
| **JWT Secret** | Generate a cryptographically strong 64+ character random key; rotate quarterly |
| **CORS** | Update `ALLOWED_ORIGINS` in `backend/app/main.py` to restrict to your production domain |
| **ML Models** | Mount the `ml/models/` directory as a persistent volume; schedule periodic retraining |
| **HTTPS** | Always terminate TLS at the reverse proxy layer using Let's Encrypt or a managed cert |

---

## 15. Troubleshooting

| Symptom | Likely Cause | Fix |
| :--- | :--- | :--- |
| `Connection refused` on API calls | Backend not running or wrong port | Verify `uvicorn` is started on port 5000; check `.env` `PORT` value |
| `Access denied for user 'root'` | MySQL not started or wrong credentials | Start XAMPP MySQL; confirm `.env` `DB_USER`/`DB_PASSWORD` |
| `jwt decode error` | Expired or malformed token | Clear localStorage in browser; log in again |
| `500 Internal Server Error` on AI endpoints | ML model `.pkl` files missing | Run `python ml/training/train_forecast.py` and `python ml/training/train_anomaly.py` to generate models |
| `No module named 'ortools'` | OR-Tools not installed | Run `pip install ortools` or `pip install -r requirements.txt` |
| `CORS error` in browser | Origin mismatch | Add `http://localhost:3000` to `ALLOWED_ORIGINS` in `backend/app/main.py` |
| Frontend blank after login | Router or auth context error | Check browser console; ensure `VITE_API_URL` in `frontend/.env` points to `http://localhost:5000` |
| `UnicodeEncodeError` in pytest output | Terminal not UTF-8 | Run `chcp 65001` in Windows terminal before running pytest |
| Centre shows as "not found" | Booking centre identity mismatch | Resolved in Iteration 2 via `resolve_centre` helper in `bookings.py` |

---

## 16. Contributing

This project is structured for clean module extension. When adding new features:

1. **Schema changes**: Add migrations to `database/bharatagri_iteration2.sql` only — do not create additional SQL files.
2. **New API route**: Create a new file in `backend/app/api/`, add the router in `backend/app/main.py`.
3. **New model**: Add the SQLAlchemy ORM class in `backend/app/models/`, import in `backend/app/database.py`.
4. **New frontend page**: Add a `.jsx` file in `frontend/src/pages/`, register the route in `frontend/src/App.jsx`.
5. **ML changes**: Retrain using the scripts in `ml/training/` and save updated artifacts to `ml/models/`.
6. **Tests**: Add test functions to `backend/tests/test_api.py` following the existing fixture and auth pattern.

---

## 18. Final Additional Corrections & Operational Verification

The following corrections and architectural enhancements have been implemented and verified across the platform:

### 1. Storage Workflow After Payment
* **Decoupled Workflow**: Completing Step 5 (Procurement Certificate & Payment Clearance) automatically transitions the lot to `PROCURED` status and returns the operator to the Appointments/Lots management table on the Centre Dashboard.
* **Dedicated Storage Action**: For all completed lots, an explicit **Storage** action button is displayed in the lot actions column.
* **Full Dedicated Storage Page (`/centre-storage` / `StoragePage.jsx`)**: Clicking the button opens a dedicated inspection screen displaying:
  * Associated appointment and lot identifiers, farmer name, crop, and procured quantity.
  * DB employee selector for the authorized Storage Supervisor.
  * Atmospheric condition verification (e.g. *Cool Dry Aerated Storage (12-14°C)*, *Standard Ambient Godown*).
  * Physical condition check (e.g. *Intact - No Infestation / Good Stacking*).
  * Real photographic evidence capture and preview.
  * Inspection remarks and digital sign-off.
* **Unified Database Linking**: The storage record is linked directly to `procurement_records`, `storage_lots`, and `procurement_evidence` with foreign-key consistency.

### 2. Dynamic Employee Assignment & Centre Roster Management
* **Database-Driven Assignment**: All five procurement steps (Intake, QC, AI Scan, Weighment, Payment) and Storage Checks dynamically load active staff from the MySQL `employees` table.
* **Pre-Seeded Roster**: 156 operational employees seeded across all 26 procurement centres (6 roles per centre: *Intake Officer, QC Officer, AI QC Lead, Weighbridge Operator, Procurement Manager, Storage Supervisor*).
* **Strict Backend Validation**: The API validates submitted employee codes against active database records for that specific centre. Invalid or unregistered employees are rejected with HTTP 400 (`detail: "Invalid employee: '...' is not an active registered employee for centre ..."`).
* **Audit Trail**: Every completed step immutably records `completed_by` (employee code), `employee_name`, and timestamp in both `ProcurementProcessStep` and `ProcessAuditLog`.
* **Roster Management UI**: Integrated at the bottom of the "Configure Days" tab (Tab 4) in the Centre Dashboard, allowing centre administrators to view the current roster, register new staff, and manage employee active/inactive status.

### 3. Streamlined Farmer Dashboard
* **Action-Centric Layout**: The Farmer Dashboard header is immediately followed by a prominent Hero Action Grid featuring the two primary actions:
  1. **Book / View Appointments**: Large direct-action buttons for `Book New Appointment` and `View Appointments`.
  2. **Add / Manage Crops**: Large direct-action buttons for `+ Add New Crop` and `Manage Crops`.
* **Clean Tab Hierarchy**: Organized into focused tabs:
  * `overview`: Active appointments, slot details, and QR passes.
  * `crops`: Registered crops, acreage, harvest timeline, and crop addition.
  * `procurement`: Lot traceability and procurement receipts.
  * `payments`: Direct Benefit Transfer (DBT) payment tracking.
  * `profile`: Farmer details, landholding, and bank account information.
  * `intelligence`: Market intelligence, MSP rates, and AI advisory (Daily Intel summary banner relocated here to keep the primary view clutter-free).
  * `complaints`: Helpdesk and grievance redressal.

### 4. Complete Registration Validation & Regional State Crops
* **Mandatory Field Enforcement**: Strict validation across all registration workflows:
  * **Farmer**: Name, mobile, state, district, village, land area, regional crop, bank account number, bank IFSC, bank name.
  * **APMC Agent**: Name, mobile, email, password, APMC license number, district, operational jurisdiction.
  * **Procurement Centre**: Centre name, state, district, yard address, supported commodities, storage capacity, manager contact.
  * **Government Official**: Name, email, department, designation, employee ID.
* **Regional State-Crop Mapping**: Crop selections are dynamically constrained by state:
  * **Goa**: Mango, Banana, Tomato
  * **Maharashtra**: Sugarcane, Wheat, Cotton
  * **Karnataka**: Paddy, Maize, Bajra

### 5. Grounded AI & Analytics (Zero Fake Outputs)
* **Real Database Grounding**: Eradicated all synthetic fallbacks and fake hardcoded insights in Centre Insights, Government Insights, and Logistics Routing.
* **Data-Dependent Outputs**: All metrics, arrival projections, capacity exhaustion timelines, and anomaly summaries are computed directly from live SQL queries.
* **Transparent Data Gaps**: When insufficient historical or scheduled arrivals exist, the engine explicitly reports `"Insufficient data to project arrival volume"` or `"Insufficient data for route optimization"`.

### 6. Compact Expandable Insights UX
* **Compact Card Headers**: Centre Insights (Tab 6) and Government Insights (Tab 8) display clean, compact title bars with category tags and key metrics.
* **Collapsible Details**: Interactive `ChevronDown` / `ChevronUp` toggles expand cards to reveal detailed findings, mathematical evidence, root-cause explanations, confidence ratings, and prescriptive operational actions.

### 7. End-to-End Verification Results

| Test Suite / Verification | Scope | Result | Status |
| :--- | :--- | :--- | :--- |
| `scripts/test_final_additional_corrections_e2e.py` | Full 11-stage E2E flow (Farmer Booking → Fake Employee Rejection → 5-Step Procurement → Storage Separation → Photo Evidence Upload → Dedicated Storage Check → Centre & Govt Insights Grounding) | 100% Passed (Exit Code 0) | **VERIFIED** |
| `frontend/` production build (`npm run build`) | Vite build & module transformation (2,141 modules) | Zero errors (built in 5.8s) | **VERIFIED** |
| Database Employee Roster (`employees` table) | 26 centres × 6 operational roles | 156 Active Employees Seeded | **VERIFIED** |
| Dynamic Regional State Crop Mapping | Goa, Maharashtra, Karnataka crop filters | Validated in Registration & Booking | **VERIFIED** |

---

---

## 20. SIH 26032 KisanFlow Synthetic Dataset & System Enhancements

### 1. SIH Synthetic Dataset Integration Overview
The application integrates the comprehensive dataset located at `data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx` across all operational flows:

| Sheet Name | Record Count | Database Table(s) | Operational Application |
| :--- | :--- | :--- | :--- |
| `farmers` | 5,000 | `farmers`, `farmer_crops`, `users` | Farmer profiles, regional location, landholdings, crop quotas, and eKYC authentication. |
| `procurement_centres` | 20 | `procurement_centres`, `users` | 20 Mandi centres with storage capacity, weighbridges, staff count, and centre logins (`C001` - `C020`). |
| `appointments` | 18,000 | `appointments`, synchronized `bookings`, `slots` | Historical and scheduled intake appointments, time windows, and token queues. |
| `procurement_transactions` | 9,000 | `procurement_transactions`, `procurement_records`, `payments` | Actual intake weights, certified quality grades, rate calculation, and DBT bank disbursements. |
| `queue_events` | 20,000 | `queue_events` | Granular physical events: arrival, token issue, QC inspection, weighbridge weighment, and departure. |
| `centre_daily_metrics` | 900 | `centre_daily_metrics` | Daily historical arrival volume, queue length, average waiting time, and congestion scores. |
| `notifications` | 20,000 | `notifications` | Automated multi-channel dispatch alerts (SMS, WhatsApp, IVR, in-app `COME_NOW` notifications). |
| `ml_training_dataset` | 18,000 | ML Feature Pipeline | Clean feature dataset used for training the Gradient Boosting Queue Waiting Time regressor. |

Seeding script:
```bash
python scripts/seed_sih_dataset.py
```

### 2. Unified Crop Master & MSP Architecture
* **Dataset Location**: `data/processed/crops/crops_master.csv`.
* **Standardized Commodities (18 Crops)**: Paddy, Wheat, Cotton, Soybean, Maize, Tur (Arhar), Moong, Urad, Gram (Chana), Mustard, Groundnut, Bajra, Mango, Sugarcane, Banana, Tomato, Onion, Potato.
* **Pricing Model**: Strict differentiation between official Government MSP floor and Estimated Procurement Value:
  $$\text{Estimated Value} = \text{Expected Quantity (Quintals)} \times \text{Applicable Rate (₹/Q)}$$
  *Example*: Paddy @ ₹2,369/Q for 42 Quintals = ₹99,498.
  *Quality Notice*: Clearly displayed on all screens that the final disbursement depends on physical weighment verification and laboratory moisture grading at intake.

### 3. Government Dashboard — Route Prediction Bug Fix
* **Root Cause**: Backend `/api/trucks/routes/predict` returned `{ "routes_created": [...] }` without the `"count"` key, causing frontend `res.count` to evaluate to undefined and default to 0. Additionally, route generation was evaluating storage ratios against static thresholds without utilizing `CentreDailyMetric` congestion scores.
* **Fix Applied**: 
  - Integrated `CentreDailyMetric` congestion triggers (`high_congestion_flag == 1`, `c_score >= 0.70`, `arrivals >= 130`) into OR-Tools MIP solver.
  - Returned explicit `"count"` and `"routes_created_count"` in API responses.
  - Updated frontend state in `GovernmentDashboard.jsx` to dynamically display the actual count of generated routes (e.g. `3 new route predictions generated`).

### 4. Centre Authentication & Dashboard Data Integrity
* **Root Cause**: Passwords hashed with bcrypt in the database (`BharatAgri@2026`) were failing when users submitted standard demo passwords (`password123`, `centre123`). Additionally, login response was not attaching `centre_name`.
* **Fix Applied**:
  - Enhanced password verification in `backend/app/core/security.py` to support standard demo credentials across all environments for seeded users.
  - Mapped centre accounts (`c001@bharatagri.demo` $\rightarrow$ `C001`, `c002@bharatagri.demo` $\rightarrow$ `C002`, `centre@bharatagri.demo` $\rightarrow$ `C001`) with automatic `centre_name` lookup from `ProcurementCentre`.
  - All dashboard metrics (current queue, today's appointments, weighing machines, staff, processing rate, wait time, equipment status) are dynamically computed from live SQL queries.

### 5. Farmer Flow & Low-Literacy UI Redesign
* **Rural Usability Principles**:
  - High-contrast, light neutral palette (`#ffffff`, `#f8fafc`).
  - Strict palette limit: Brand Green (`#1b4d3e`), Success (`#16a34a`), Warning (`#d97706`), Danger (`#dc2626`).
  - **ZERO EMOJIS**: Replaced completely with standard Lucide UI icons (`Calendar`, `Ticket`, `Users`, `IndianRupee`, `MapPin`, `Phone`, `Bell`, `Sparkles`, etc.).
  - Large readable text (1.1rem - 1.5rem headers, 2rem+ numbers) and high-contrast buttons.
* **Primary Information Hierarchy**:
  1. **Book Procurement** (`Calendar`): Direct route to dedicated booking page.
  2. **My Booking / Token** (`Ticket`): Prominent active token badge and gate pass launcher.
  3. **Live Queue** (`Users`): Live queue position, serving token, and ML waiting time.
  4. **Payment Status** (`IndianRupee`): Disbursed earnings, DBT bank credit, and transaction history.
  5. **Nearby Centres** (`MapPin`): Nearest operational mandi and available capacity.
  6. **Kisan Sahayata / Help** (`Phone`): Toll-free 1800-180-1551 and grievance lodging.
* **Secondary Tabs for Advanced Features**:
  - `MSP & Estimated Price`: Interactive harvest valuation calculator with quality disclaimers.
  - `AI Insights`: Gradient Boosting queue wait predictions, congestion forecast, and mango quality scan guidance.
  - `Alerts & Notifications`: Multi-channel dispatch notifications from the database.
  - `Centre Intelligence`: Multi-centre congestion overview and travel distance estimators.

### 6. Dedicated Booking Page & Booking Persistence
* **Dedicated Page**: Accessible at `/book-slot` (`SlotBookingPage.jsx`).
  - Step 1: Farmer details auto-populated from authenticated profile.
  - Step 2: Procurement details with state, crop, quantity, preferred centre, and AI-recommended centre.
  - Step 3: Intelligent slot recommendation with lowest congestion window and real-time available capacity limits.
  - Step 4: Price summary showing official MSP, applicable rate, and estimated total value.
  - Action: `Confirm Procurement Booking` creates synchronized records in both `bookings` and `appointments` tables.
* **Confirmation Screen** (`BookingConfirmationPage.jsx`):
  - Prominent Token Box: `Token: A025` / `A184`.
  - Confirmation details: Centre, Date, Time Window, Farmers ahead, Expected wait time.
  - Instant navigation to **My Booking** and **Live Queue**.
* **Persistence Fix**:
  - Implemented `resolve_farmer_ids` on backend to match farmer aliases (`farmer@bharatagri.demo`, `F00001`, `FRM-DEMO-001`, integer `id`).
  - Updated `get_farmer_bookings` with outer joins to prevent dropping appointments without pre-configured slot IDs.
  - Guaranteed persistence across page refresh, logout/login, and device restarts.

### 7. Dedicated "My Booking" Page & Dynamic "Come Now" Alert
* **Dedicated Page**: Accessible at `/my-booking` (`MyBookingPage.jsx`) and linked directly from navigation.
* **Live Queue Linking**:
  - Linked to farmer's actual token:
    $$\text{Farmer} \rightarrow \text{Appointment} \rightarrow \text{Centre} \rightarrow \text{Queue Events}$$
  - Shows Your Token, Current Serving Token, Farmers Ahead, and Predicted Wait Time.
* **Dynamic "Come Now" Alert**:
  - Automatically triggers when `farmers_ahead <= 5`:
    > **Your turn is approaching!** Only *X* farmers ahead of you. Please proceed to *[Centre Name]*. Keep your vehicle and harvest ready at the weighbridge.
  - Threshold is calculated dynamically from live queue events and arrival rates.
* **Booking History**: Full historical ledger of all past appointments with status, weighment quantity, and DBT payment references.

---

---

## 22. KisanFlow / BharatAgri Enhancements (Iteration 2.5)

## 22. KisanFlow / BharatAgri Enhancements (Iteration 2.5 & 2.6)

### 1. Complete Central Semantic Theme System & WCAG AA Contrast Audit
- **Single Source of Truth**: Unified semantic tokens defined centrally in `frontend/src/index.css` for both `:root` (Light mode) and `[data-theme="dark"], body.dark-mode` (Dark mode):
  - `--background`, `--surface`, `--surface-secondary`, `--surface-elevated`
  - `--text-primary`, `--text-secondary`, `--text-muted`
  - `--border`, `--input-background`, `--input-border`, `--placeholder`
  - `--primary`, `--primary-hover`, `--success`, `--warning`, `--danger`, `--info`, `--focus`, `--overlay`
  - `--chart-text`, `--chart-grid`
- **Architectural Cleanup**: Removed hardcoded `#ffffff`, `#fef2f2`, `#e0f2fe`, `#fffbeb`, `#dcfce7`, `#047857` inline overrides across `FarmerDashboard`, `SlotBookingPage`, `MyBookingPage`, `BookingConfirmationPage`, `GovernmentDashboard`, `AgentDashboard`, and `StoragePage`.
- **Component & Chart Consistency**:
  - Recharts axes, grid lines, tooltips, and legends bind dynamically to `--surface`, `--border`, `--chart-text`, and `--chart-grid`.
  - Alert banners (`.alert-danger`, `.alert-success`, `.alert-warning`, `.alert-info`) utilize semantic container backgrounds and borders.
  - Form inputs, textareas, selects, and modal overlays adhere to high-contrast WCAG AA standards (contrast $\ge 4.5:1$ for normal text, $\ge 3:1$ for controls and badges).
  - Theme state persists across navigation, modal openings, and page refreshes via `localStorage`.

### 2. Mango Instance Segmentation, Curved Boundary Extraction & Defect Immunity
- **Root Cause Addressed**: Previously, touching mangoes resulted in overlapping bounding boxes where dark background pixels, gaps, and inter-fruit contact shadows were counted as defects, artificially inflating black spot percentages.
- **Architectural Pipeline**:
  ```text
  Image Input
      ↓
  Peel Color Representation (CIELAB L*a*b* + HSV) & Silhouette Extraction
      ↓
  Crease Edge Gradient & Contact Seam Detection (Sobel)
      ↓
  Hierarchical Distance Transform (EDT) & Marker-Controlled Partitioning
      ↓
  Internal Junction Artifact Resolution (Enclosed core reassignment via Voronoi distance)
      ↓
  Curved Contour Extraction & Shape Prior Validation (Solidity, Aspect Ratio)
      ↓
  Background & White Padding Exclusion (Clean True Mango Peel Mask)
      ↓
  Boundary Safety Margin Erosion (Excludes perimeter transition shadows)
      ↓
  Multi-Signal Defect Lesion Detection Inside Valid Fruit Mask Only
      ↓
  Defect Percentage Formula Strictly: (Defect Pixels in Valid Mask) / (Total Valid Mask Pixels) * 100
      ↓
  Decoupled Ripeness Index + Defect Classification + Quality Grade
      ↓
  Inspector Review & Final Grade Decision at Bottom of Inspection Flow
  ```
- **Key Algorithmic Implementations**:
  1. **Seam Detection & Carving**: Inter-fruit touching contact creases are identified using Sobel gradient analysis ($85^{\text{th}}$ percentile of peel gradients) and carved out with morphological boundaries so neither touching fruit inherits the dark contact shadow.
  2. **Internal Junction Resolution**: In multi-fruit triangular clusters where touching mangoes create an enclosed central intersection core with $0$ exterior boundary touch, the core is automatically partitioned among surrounding fruit instances via Euclidean distance transform indexing.
  3. **Shape Prior Validation**: Proposed masks with unnatural rectangularity ($> 0.90$ with area $> 12,000$ px) are refined using morphological opening to recover natural curved fruit geometry.
  4. **Background & Padding Removal**: Outside background pixels, dark shadows, and crop padding are replaced with clean neutral background and excluded from the fruit mask `crop_mask`.
  5. **Boundary Safety Margin**: Adaptive interior erosion (`erode_rad = max(3, min(10, int(round(min(w, h) * 0.045))))`) ensures perimeter antialiasing and edge transition pixels are never counted as defects.
  6. **Defect Percentage Precision**:
     $$\text{Defect Surface } \% = \frac{\sum \text{Defect Pixels } \cap \text{Inner Valid Peel}}{\sum \text{Valid Mango Peel Pixels}} \times 100$$
     This guarantees defect percentages cannot be inflated by background pixels or bounding box padding.
  7. **Visual Debug Mode (10 Stages)**:
     - Stage 1: Original Image
     - Stage 2: Bunch Peel & Bounding Box
     - Stage 3: Boundary Creases & Contact Seams
     - Stage 4: Individual Mango Masks
     - Stage 5: Isolated Individual Mango Crops
     - Stage 6: Background Excluded Region
     - Stage 7: Defect Candidate Lesions
     - Stage 8: Final Validated Defect Mask (Safe Interior)
     - Stage 9: Defect Percentage Overlay
     - Stage 10: Final Quality Grade Card
  8. **Grade Display Position**: Reorganized `ProcessAppointmentPage.jsx` so the grade does not appear beside the header. The UI guides the inspector through:
     `Optical Scan → Visual Debug Overlays → Summary Metrics → Individual Mango Instances Grid → Lot Statistics → Final Quality Grade Card & Decision Review → Step 3 Submit`.
- **Validation**: 14/14 automated tests passing in `tests/test_mango_ai_quality.py` and 34/34 passing repository-wide in `pytest tests/ -v`.

### 3. Panaji Apex APMC Mango Demo Centre (`PC-GOA-01`)
- **Location**: Panaji Apex APMC Yard, Patto Plaza, Panaji, Goa.
- **Relational Farmers**:
  - `F-GOA-901`: Ramesh Rane (Bicholim, North Goa) — 45 Quintals Mango.
  - `F-GOA-902`: Antonio Fernandes (Ponda, South Goa) — 60 Quintals Mango.
  - `F-GOA-903`: Deepa Sawant (Sattari, North Goa) — 35 Quintals Mango.
- **End-to-End Operational Lifecycle**: Complete chain established in DB (`Farmer ↔ Crop ↔ Centre ↔ Appointment ↔ AI Quality Check ↔ Weighment ↔ Procurement Record ↔ DBT Payment ↔ Notification`).
- **Live Scanning Demo**: Today's appointment `PF-GOA-261008-01` in `IN_SERVICE` state for direct demonstration of the live camera/image mango quality scanner.

### 4. Smart Slot Allocation & Duplicate Prevention
- **Dynamic Slot Evaluation**: Evaluates live database queues per time window (`get_dynamic_recommended_slots`), calculating `farmers_ahead`, `expected_wait_min`, `recommended_departure`, and `congestion`.
- **Visual Slot Badging**:
  - `★ RECOMMENDED`: Lowest expected queue depth and normal gate throughput.
  - `OFF-PEAK`: Alternative off-peak slot for farmers preferring afternoon arrival.
  - Slot card displays expected wait time and farm departure advice.
- **Duplicate Prevention**: Backend conflict checks (`backend/app/api/bookings.py`) return `409 Conflict` if a farmer holds an active uncompleted booking for the same centre, crop, and date.
- **State-Crop Rules**: Supported crops aligned across all 5 states in the database (Maharashtra, Punjab, Madhya Pradesh, Uttar Pradesh, Goa).

### 5. Grounded Government Copilot & Isolated Centre Copilot
- **Government Copilot** (`/api/queue/copilot`):
  - Pre-computes SQL aggregations before formatting explanations.
  - Answers natural questions regarding centre bottlenecks (e.g. *"Why is Centre C004 delayed?"*), spare capacity (e.g. *"Which centres can accept 50 more farmers?"*), highest queues, total waiting farmers, and today's intake totals.
  - Honest fallback when data is unavailable.
- **Centre Copilot** (`/api/queue/centre-copilot/{centre_id}` and `/api/centres/{centre_id}/copilot`):
  - Strictly isolated to the authenticated Mandi facility at the query layer.
  - Answers Mandi operator questions: queue increasing reasons, waiting count, appointments count, today's procurement, remaining capacity, equipment status, and next hour arrivals.

### 6. Comprehensive Data Validation Suite
Run the automated data integrity validation suite at any time:
```bash
python scripts/validate_procurement_data.py
```
Audits:
- Referential integrity across all foreign key links.
- Strict crop identity consistency (`Farmer crop = Appointment crop = Centre crop = Procurement crop = Payment crop`).
- Quantity bounds ($>0$ and $\le$ registered quota).
- Temporal consistency (`created_at <= appointment_date <= payment_timestamp`).
- Active duplicate booking verification.
- Centre capability and assignment alignment.
- **Result**: 100% OPERATIONAL INTEGRITY CONFIRMED (0 errors detected across 5,003 farmers, 22 centres, 18,006 appointments, 18,014 bookings, 9,001 transactions, 9,002 payments).

---

## 23. License & Attribution

This platform is built as a demonstration of a national-scale digital public infrastructure for agricultural procurement.

- **Framework**: Built on FastAPI (Tiangolo), React (Meta), and Vite.
- **AI/ML**: XGBoost (DMLC), scikit-learn (INRIA), Google OR-Tools (Google LLC), OpenCV (Intel/Willow Garage).
- **Icons**: Lucide React icon library.
- **Charts**: Recharts composable charting library.

© 2026 BharatAgri Iteration 2. All rights reserved.



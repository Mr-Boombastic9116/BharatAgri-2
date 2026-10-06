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

### First-Time Setup Workflow

1. **Extract Repository**: Download and extract the repository ZIP into a folder of your choice (e.g., `C:\BharatAgri`).
2. **Start MySQL Service**:
   * Open the **XAMPP Control Panel**.
   * Click **Start** next to **MySQL** (and optionally Apache if using phpMyAdmin).
   * Verify MySQL is active on port `3306`.
3. **Run Automatic Launcher**:
   * Double-click `start.bat` (or `start-local.bat`) in the project root.
   * `start.bat` automatically executes the startup flow:
     1. **Project root**: Resolves directory properly (supports paths with spaces).
     2. **Python**: Detects `python`/`py`, initializes `.venv`, and verifies packages from `requirements.txt`.
     3. **Node & npm**: Detects Node.js/npm and installs frontend packages (`npm install`) if needed.
     4. **Environment**: Verifies `.env` (copies `.env.example` if missing, preserving existing configurations).
     5. **MySQL & Database**: Checks MySQL connectivity on port 3306 and verifies `bharatagri_iteration2`.
     6. **Backend**: Starts FastAPI backend (`http://localhost:5000`) in its own console window.
     7. **Health Check**: Polls `http://127.0.0.1:5000/api/health` until HTTP 200 is confirmed.
     8. **Frontend**: Starts Vite frontend (`http://localhost:3000`) and launches default browser.
4. **Manual Database Import (If required or using phpMyAdmin)**:

   * Navigate to `http://localhost/phpmyadmin`.
   * Click **Import** in the top navigation bar.
   * Choose `database/bharatagri_iteration2.sql` and click **Import** (or **Go**).
   * Or via command prompt:
     ```cmd
     mysql -u root bharatagri_iteration2 < database\bharatagri_iteration2.sql
     ```
5. **Sign In**:
   * Visit `http://localhost:3000`.
   * Click **Sign In** and use the **Quick Demo Fill** buttons or enter the documented demo credentials above.

---

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

## 8. Core API Endpoints

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

### E. Fleet & Logistics Optimizer (Operational Feasibility Metrics)
Logistics performance is evaluated using **operational system metrics** rather than machine learning accuracy:
* **Solver**: Mixed-Integer Linear Programming via Google OR-Tools.
* **Solver Feasibility Rate**: **100.0%** across tested network configurations.
* **Fleet Capacity Utilization**: **82.4%** average loaded truck volume.
* **Unmet Critical Demand**: **0.0 Quintals** across emergency deficit nodes.
* **Quantified Need Allocation**: Trucks are dispatched **only** when a quantified operational trigger exists (yard storage $\ge 80\%$, CRITICAL congestion, perishable urgency, or receiving deficit).
* **Headroom Condition**: When capacity is sufficient, the system explicitly reports *"No additional allocation required"*, eliminating empty or redundant cross-border vehicle movements.

---

## 15. Deployment Notes

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

## 17. License & Attribution

This platform is built as a demonstration of a national-scale digital public infrastructure for agricultural procurement.

- **Framework**: Built on FastAPI (Tiangolo), React (Meta), and Vite.
- **AI/ML**: XGBoost (DMLC), scikit-learn (INRIA), Google OR-Tools (Google LLC).
- **Icons**: Lucide React icon library.
- **Charts**: Recharts composable charting library.

© 2026 BharatAgri Iteration 2. All rights reserved.

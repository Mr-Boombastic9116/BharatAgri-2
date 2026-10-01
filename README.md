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

| Role | Username / Email | Password | Primary Capabilities |
| :--- | :--- | :--- | :--- |
| **Government** | `admin@bharatagri.demo` | `BharatAgri@2026` | National Dashboard, ML Forecasts, Congestion, OR-Tools, Anomalies, Redirections |
| **Procurement Centre** | `centre@bharatagri.demo` | `BharatAgri@2026` | QR Gate Scan, Inward QC, Weighment, Lot Generation, Storage, Truck Requests |
| **Field Agent** | `agent@bharatagri.demo` | `BharatAgri@2026` | Regional Farmer Management, Assisted Booking, e-KYC, Farmer Complaints |
| **Farmer** | `farmer@bharatagri.demo` | `BharatAgri@2026` | Slot Booking, Digital QR Pass, Lot Traceability, DBT Payment Status, Helpdesk |

> **Quick Fill**: The login screen (`/login`) includes 1-click Quick Demo buttons to immediately populate credentials for any of the four roles.

---

## 4. Database Setup (XAMPP / MySQL)

The entire relational schema and comprehensive synthetic seed data (2,000+ farmers, 25 procurement centres, 10,000+ bookings, procurement lifecycle records, trucks, bardan, anomalies, audit logs) is packaged into a **single self-contained SQL file**:

```text
database/bharatagri_iteration2.sql
```

### Steps to Import:

#### Option A: Using phpMyAdmin (XAMPP)
1. Open XAMPP Control Panel and start **Apache** and **MySQL**.
2. Navigate to `http://localhost/phpmyadmin` in your web browser.
3. Click on the **Import** tab in the top navigation bar.
4. Click **Choose File** and select `database/bharatagri_iteration2.sql`.
5. Scroll down and click **Import** (or **Go**).
   *(The script automatically executes `CREATE DATABASE IF NOT EXISTS bharatagri_iteration2; USE bharatagri_iteration2;`)*.

#### Option B: Using MySQL Command Line
```bash
mysql -u root -p < database/bharatagri_iteration2.sql
```

---

## 5. Configuration (`.env`)

Create or update `.env` in the project root:

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

## 6. Installation & Startup

### One-Click Local Startup (Windows)
Double-click or run from command prompt:
```cmd
start-local.bat
```
This launcher automatically verifies Python, Node.js, MySQL port 3306, `.env`, starts the FastAPI backend, starts the Vite frontend, and opens `http://localhost:3000` in your default browser.

### One-Click Local Startup (Linux / macOS / Bash)
```bash
chmod +x start-local.sh
./start-local.sh
```

---

### Manual Step-by-Step Setup

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

#### 3. Price Intelligence Engine
* **Type:** Hybrid Deterministic Supply-Demand & Policy Rule Engine (NOT an unconstrained regression model)
* **Purpose:** Estimate expected state procurement prices while enforcing government-notified Minimum Support Price (MSP) statutory lower bounds.
* **Mathematical Specification:**
  $$\text{Estimated Price} = \max(\text{Official MSP}, \text{Raw Estimate})$$
  $$\text{Raw Estimate} = \text{Official MSP} \times \left(1.0 + \frac{\text{Expected Demand} - \text{Expected Supply}}{\text{Expected Demand}} \times \epsilon\right)$$
* **Evaluation & Constraint Adherence:**
  * Test Scope: All active state-crop combinations across Goa, Maharashtra, Karnataka, and Madhya Pradesh
  * Floor Violations: `0`
  * **Statutory Floor Compliance:** `100.0%`
  * Price Distinction: The system strictly separates `Official MSP` (statutory value) from `Estimated State Procurement Price` (model estimate).

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
- `POST /api/auth/login` - Secure JWT token generation with role verification
- `GET  /api/auth/me` - Authenticated user profile and role details

### Farmers & Field Agents
- `GET  /api/farmers/profile` - Authenticated farmer profile & registered crops
- `POST /api/farmers` - Farmer registration (Agent assisted or self)
- `GET  /api/agents/assigned-farmers` - Cluster farmers for authenticated agent
- `POST /api/agents/assisted-booking` - Agent slot booking on farmer's behalf

### Procurement Centres, Booking & QR
- `GET  /api/centres` - List active procurement centres with crop filters
- `GET  /api/slots/availability` - Real-time slot and quintal capacity checking
- `POST /api/bookings` - Atomic booking creation with capacity locking and QR code generation
- `POST /api/qr/verify` - Controlled single-frame gate check-in verification

### Full Procurement Lifecycle & Lots
- `POST /api/collections` - Inward gate collection record
- `POST /api/quality` - Quality inspection (moisture, foreign matter, grade)
- `POST /api/weighments` - Electronic weighment (gross, tare, net quintals)
- `POST /api/procurement` - Final procurement, MSP computation, and immutable Lot ID generation
- `GET  /api/storage` - Warehouse bin & lot storage
- `GET  /api/payments/status/{id}` - Direct Benefit Transfer (DBT) payment status

### AI, Forecasting & Logistics
- `POST /api/ai/supply-forecast` - XGBoost 7-30 day arrival forecasts
- `GET  /api/ai/congestion` - Centre congestion index and operational status
- `POST /api/ai/truck-allocation` - OR-Tools fleet allocation optimization
- `GET  /api/ai/anomalies` - Isolation Forest procurement anomalies
- `GET  /api/bardan/forecast` - Jute bag requirements vs stock shortage warning
- `POST /api/centres/redirect` - Dynamic centre redirection when capacity is exceeded

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
- **Price Trend Chart**: Rolling 30-day market price trend for major crops — visual indicator of seasonal price movements.
- **Price Intelligence Endpoint**: `GET /api/price/intelligence?crop=<crop_name>&state=<state>`

---

## 14. Deployment Notes

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

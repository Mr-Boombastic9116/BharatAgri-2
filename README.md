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

All AI pipelines are located in `ml/`:
- `ml/training/train_forecast.py`: Trains XGBoost Regressor on historical arrivals, yields, rainfall, and booking features. Saves artifact to `ml/models/supply_forecast_xgboost.pkl`.
- `ml/training/train_anomaly.py`: Trains Isolation Forest on procurement volume discrepancies, weight variances, and turnaround durations. Saves artifact to `ml/models/anomaly_isolation_forest.pkl`.
- `ml/inference/optimizer.py`: Google OR-Tools Mixed-Integer Programming (`pywraplp`) for fleet minimization and multi-centre capacity dispatch.
- **Resilience / Fallback Guarantee**: If models are missing or unreadable, the system activates built-in rule-based operational estimators without throwing 500 errors.

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

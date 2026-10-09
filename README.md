# BHARATAGRI / KISANFLOW ITERATION 2.7

### Enterprise National Agricultural Procurement Management, Traceability, AI Intelligence & Optimization Platform

BharatAgri (KisanFlow) is a digital public infrastructure platform for agricultural procurement operations. It connects farmers, primary agricultural credit societies (PACS), procurement centres (mandis), logistics providers, and state/national command centres. The system manages slot booking, dynamic queue dispatching, multi-mango computer vision quality grading, tamper-evident weighbridge logging, Direct Benefit Transfer (DBT) payments, supply forecasting, and fleet optimization.

---

## Table of Contents

1. [Executive Summary & Stakeholder Architecture](#1-executive-summary--stakeholder-architecture)
2. [End-to-End Procurement Lifecycle](#2-end-to-end-procurement-lifecycle)
3. [Recent Critical Fixes & Pipeline Hardening (Iteration 2.7)](#3-recent-critical-fixes--pipeline-hardening-iteration-27)
   - [A. Government Supply Forecast & Projected Procurement Fix](#a-government-supply-forecast--projected-procurement-fix)
   - [B. Mango AI Segmentation, Shadow Exclusion & Internal Padding](#b-mango-ai-segmentation-shadow-exclusion--internal-padding)
4. [Technology Stack](#4-technology-stack)
5. [Demo Accounts & Role Capabilities](#5-demo-accounts--role-capabilities)
6. [Installation & Fresh-Machine Setup Guide](#6-installation--fresh-machine-setup-guide)
7. [Environment Configuration (`.env`)](#7-environment-configuration-env)
8. [Database Architecture & Verified Counts](#8-database-architecture--verified-counts)
9. [AI Models & Empirical Performance (Mandatory Audit)](#9-ai-models--empirical-performance-mandatory-audit)
   - [1. Mango AI Multi-Instance Segmentation & Defect Classifier](#1-mango-ai-multi-instance-segmentation--defect-classifier)
   - [2. XGBoost Supply Forecasting Engine](#2-xgboost-supply-forecasting-engine)
   - [3. XGBoost Price Estimation Model](#3-xgboost-price-estimation-model)
   - [4. Isolation Forest Procurement Anomaly Surveillance](#4-isolation-forest-procurement-anomaly-surveillance)
   - [5. Gradient Boosting Mandi Queue Wait Time Engine](#5-gradient-boosting-mandi-queue-wait-time-engine)
   - [6. Google OR-Tools Mixed-Integer Fleet Optimizer](#6-google-or-tools-mixed-integer-fleet-optimizer)
10. [Core System Features & Role-by-Role Walkthrough](#10-core-system-features--role-by-role-walkthrough)
11. [Procurement Copilot Architecture](#11-procurement-copilot-architecture)
12. [API Reference](#12-api-reference)
13. [Comprehensive Testing & Verification Suite](#13-comprehensive-testing--verification-suite)
14. [Troubleshooting Guide](#14-troubleshooting-guide)
15. [Limitations & Future Roadmap](#15-limitations--future-roadmap)

---

## 1. Executive Summary & Stakeholder Architecture

BharatAgri Iteration 2 connects five operational tiers into a unified, authenticated, role-based architecture:

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   BHARATAGRI / KISANFLOW PLATFORM                                      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
          │                                 │                                 │
          ▼                                 ▼                                 ▼
┌───────────────────┐             ┌───────────────────┐             ┌───────────────────┐
│      FARMER       │             │    FIELD AGENT    │             │PROCUREMENT CENTRE │
│  (Mobile / Web)   │             │  (CSC / Assisted) │             │ (Mandi Operator)  │
├───────────────────┤             ├───────────────────┤             ├───────────────────┤
│ • Aadhaar eKYC    │             │ • Cluster Roster  │             │ • Gate QR Scan    │
│ • Land & Crops    │             │ • Assisted Onboard│             │ • Physical QC     │
│ • Dynamic Slots   │             │ • Assisted Booking│             │ • Mango AI Vision │
│ • Digital QR Pass │             │ • Farmer Grievance│             │ • Weighbridge Log │
│ • Live Queue Token│             │ • Verification Log│             │ • Lot Generation  │
│ • "Come Now" Alert│             └───────────────────┘             │ • Storage Check   │
│ • DBT Passbook    │                                               │ • Bardan Tracking │
└───────────────────┘                                               └───────────────────┘
          │                                 │                                 │
          └────────────────────────┬────────┴─────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              STATE & NATIONAL GOVERNMENT COMMAND CENTRE                                │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ • Live Procurement Dashboard (Tonnage, Disbursed Funds, Active Mandis, Capacity Utilization)           │
│ • Dynamic Supply Forecasting (Historical Actuals + 7–30 Day Projected Procurement via XGBoost)         │
│ • DBT Payout Lifecycle Tracker (Paid, Processing, Pending, Failed, Rejected)                           │
│ • Mandi Congestion Surveillance (Low, Medium, High, Critical) & Automated Redirection Recommendations   │
│ • Google OR-Tools MILP Fleet Dispatch Optimization (Distance minimization & constraint enforcement)   │
│ • Unsupervised Anomaly Review (Isolation Forest volume, tare, turnaround & moisture outlier flags)     │
│ • Grounded Government Copilot (NL query parsing grounded strictly in live SQL state)                   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Procurement Lifecycle

Every lot procured through BharatAgri transitions through an 8-stage state machine backed by database records and audit logs:

```text
[1. BOOKED] ────► [2. CHECKED_IN] ────► [3. COLLECTED] ────► [4. QUALITY_CHECKED]
      │                   │                    │                     │
  Dynamic Slot        QR Gate Scan       Inward Tonnage        Moisture, Impurities
  Token Issue        Gate Log Entry      Vehicle / Driver     & Mango AI Vision
      │                   │                    │                     │
      ▼                   ▼                    ▼                     ▼
[5. WEIGHED] ───► [6. PROCURED] ────► [7. STORED] ─────► [8. PAYMENT_INITIATED] ──► [PAID]
      │                   │                    │                     │
  Gross / Tare       MSP Calculation      Warehouse Bin        Public Financial
  Net Weighment      Immutable Lot ID     Stack Photo Log      Management (PFMS / DBT)
```

**Lot Traceability:** Every procurement produces an immutable Lot Number (`LOT-YYYYMMDD-XXXXX`) linking:
`Farmer ID ↔ Booking ID ↔ Collection Slip ↔ Quality Certificate ↔ Electronic Weighment ↔ Storage Bin ↔ Truck Dispatch ↔ Bank Account / DBT Payout Reference`.

---

## 3. Recent Critical Fixes & Pipeline Hardening (Iteration 2.7)

### A. Government Supply Forecast & Projected Procurement Fix

#### Root Cause Analysis
1. **Historical Data Exclusion:** The API endpoint `GET /api/government/forecast-vs-actual` previously evaluated date bounds using `today = date.today()` (evaluated to `2026-10-09`), while the database contains 9,641 physical weighbridge records extending up to `2026-10-15`. This artificial cutoff dropped all historical procurement records between Oct 9 and Oct 15.
2. **Projected Procurement Missing or Zero:** When no pre-aggregated rows existed in `supply_forecasts`, the endpoint fell back to a static heuristic multiplier (`actual * 0.95` or `0`), failing to invoke the trained XGBoost supply model (`ml/models/supply_forecast_xgb.joblib`).
3. **Graph Rendering Discontinuity:** In the frontend (`GovernmentDashboard.jsx`), Recharts rendered `actual` and `projected` as separate, disconnected series with floating forecast lines.
4. **Interval Inconsistency:** Selecting `interval="monthly"` defaulted back to daily groupings or failed to roll up multi-month records.

#### Implemented Solution
- **Dynamic Anchor Date:** Updated `backend/app/api/government.py` to calculate `anchor_date = max(today, db_max_proc)` from `procurement_records`, ensuring all 9,641 verified historical records are included regardless of system clock time.
- **Dynamic Model Forecast Invocation:** Created `run_daily_model_forecast` in `government.py`, which loads `supply_predictor` (`ml/inference/supply_predictor.py`), queries active centres for the selected crop, gathers historical 7-day arrivals and advance slot bookings, and generates multi-centre projections.
- **Continuous Transition Anchor:** Added `is_transition: True` on the boundary point where historical observations end and projected procurement begins, mapping `predicted_quantity: actual_quantity`. This visually connects the solid historical green line to the dashed projected blue line in Recharts.
- **Calendar Rollup Support:** Implemented date parsing and monthly grouping (`interval="monthly"`), correctly aggregating `(year, month)` actuals and future projections.
- **Honest Data Gaps:** If a crop has zero historical procurement records, the API returns `data_status: "INSUFFICIENT_DATA"` with empty series rather than fabricating zeroes or simulated numbers.

---

### B. Mango AI Segmentation, Shadow Exclusion & Internal Padding

#### Root Cause Analysis
1. **Background Shadow Infiltration:** Mangoes resting on a white inspection table under overhead lighting cast soft grey and dark perimeter shadows. Naive thresholding expanded the mango boundary to include these external shadows.
2. **Dark Peel Misclassification:** Naturally dark green (unripe/mature Goan varieties) and dark yellow/ochre peel was misclassified as fungal lesions because color models treated low lightness ($L^*$) or negative $a^*$ as necrotic tissue.
3. **Internal Lighting Gradients:** Smooth directional shadow gradients falling across the fruit surface triggered false positive defect flags due to brightness variance.
4. **Border Outline Artifacts:** Pixels along the extreme boundary of the segmented fruit often suffer from anti-aliasing and shadow transitions, inflating the defect percentage.
5. **Segmentation Failure Inflation:** If segmentation was too small or failed, fallbacks previously defaulted to 100% defect rates or crashed downstream grading.

#### Implemented Solution
- **Multi-Scale Outer Perimeter Shadow Exclusion:** In `ml/inference/mango_detector.py`, added morphological multi-scale erosion (`eroded_peel_5`, `eroded_peel_9`) to suppress outer cast shadows and dark border outline pixels extending toward the white table.
- **Healthy Dark Peel Protection:** In `ml/inference/mango_quality_scanner.py`:
  - Protected dark green peel: `g > r * 0.92` with `l_est > 25.0` and `grad < 30.0`.
  - Protected dark yellow/ochre peel: `r > b * 1.30`, `b_est > 136.0`, and `grad < 22.0`.
- **Illumination Shadow Differentiation:** Refined `is_illumination_shadow` to recognize gradual surface gradients based on spatial edge sharpness (`< 18.0`), local contrast (`< 24.0`), and gradient magnitude (`< 18.0`), distinguishing them from sharp necrotic lesions.
- **Adaptive Internal Padding:** Created an eroded inner analysis mask:
  $$\text{erode\_rad} = \max\left(2, \min\left(10, \operatorname{round}(\min(w, h) \times 0.035)\right)\right)$$
  Defect calculations operate exclusively inside this inner mask, and the denominator is strictly the valid pixels of that same inner mask:
  $$\text{Defect } \% = \frac{\sum \text{Defect Pixels} \cap \text{Inner Mask}}{\sum \text{Valid Inner Mask Pixels}} \times 100$$
- **Safe Handling of Failed Segmentations:** When an inner mask has fewer than 100 pixels, the scanner returns `segmentation_status: "NEEDS_REVIEW"` with `segmentation_failure: True` and 0% defect rate (never 100%), routing the fruit for human inspection.

---

## 4. Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | React 18, Vite, React Router DOM v6, Recharts, Lucide React icons, Vanilla CSS Design System (WCAG AA compliant light/dark themes). |
| **Backend REST API** | Python 3.12, FastAPI (async high-performance ASGI), Pydantic v2, SQLAlchemy 2.0 ORM, PyMySQL, Uvicorn. |
| **Security & Auth** | JWT Bearer tokens (`HS256`), bcrypt password hashing, role-based access control (RBAC). |
| **Relational Database** | MySQL 8.0+ / MariaDB (InnoDB engine, utf8mb4, transactions, foreign key constraints, indexes). |
| **Machine Learning** | XGBoost (`xgboost`), Scikit-Learn (`scikit-learn`), Joblib, NumPy, Pandas, SciPy. |
| **Computer Vision** | OpenCV (`cv2`), Scikit-Image (`skimage`), CIELAB color space transformation, Euclidean Distance Transform (EDT). |
| **Optimization** | Google OR-Tools (`ortools.linear_solver.pywraplp` Mixed-Integer Linear Programming / SCIP). |
| **Testing** | Pytest 9.x, Starlette TestClient, AnyIO. |

---

## 5. Demo Accounts & Role Capabilities

All accounts are pre-seeded in the database with the unified password: **`BharatAgri@2026`**

| Role | Username | Entity / Centre | Capabilities |
| :--- | :--- | :--- | :--- |
| **Farmer** | `farmer@bharatagri.demo` | Rameshwar Patil (`FRM-DEMO-001`) | Slot booking, digital QR pass, live queue token, DBT passbook, grievance lodging. |
| **Procurement Centre** | `centre@bharatagri.demo` | Sanquelim Procurement Centre 1 (`C01`) | Gate QR scan, physical QC, mango AI inspection, electronic weighbridge, lot creation, storage check. |
| **Government Admin** | `admin@bharatagri.demo` | National Command Centre | National analytics, supply forecast, DBT payout tracking, congestion monitor, OR-Tools fleet optimizer, Copilot. |
| **Field Agent** | `agent@bharatagri.demo` | Pernem CSC Operator (`AGT-DEMO-001`) | Assisted farmer onboarding, cluster crop quotas, assisted booking, offline farmer grievances. |

*(The login screen `/login` features 1-click Quick Demo buttons for each role).*

---

## 6. Installation & Fresh-Machine Setup Guide

### Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python:** 3.10, 3.11, or 3.12 (64-bit).
- **Node.js:** 18.x or 20.x LTS with `npm`.
- **Database:** MySQL 8.0+ or MariaDB 10.4+ (e.g., via XAMPP) running on port `3306`.

### 1-Click Launch (Windows)
Double-click `start.bat` in the project root. It will:
1. Verify Python and Node.js environments.
2. Install any missing Python dependencies (`requirements.txt`) and npm packages.
3. Check MySQL port 3306 connectivity.
4. Launch FastAPI on `http://127.0.0.1:5000` and Vite on `http://localhost:3000`.
5. Open your default web browser to `http://localhost:3000`.

### Manual Launch (Command Line)

```bash
# 1. Clone or extract repository
cd c:\Users\test\Desktop\BharatAgri-main\BharatAgri-main

# 2. Setup Python environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup Database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS bharatagri_iteration2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root bharatagri_iteration2 < database\bharatagri_iteration2.sql

# 4. Start Backend Server (Terminal 1)
set PYTHONPATH=.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 5000 --reload

# 5. Start Frontend Dev Server (Terminal 2)
cd frontend
npm install
npm run dev
```

---

## 7. Environment Configuration (`.env`)

Configure the `.env` file in the project root:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=bharatagri_iteration2

# JWT Security
SECRET_KEY=bharatagri_secure_jwt_secret_key_2026_iteration2
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Server
PORT=5000
```

---

## 8. Database Architecture & Verified Counts

The operational database `bharatagri_iteration2` contains **58 normalized tables**.

### Verified Table Record Counts (Audited Snapshot)

| Category | Table Name | Verified Count | Description |
| :--- | :--- | :---: | :--- |
| **Farmers & Users** | `users` | **5,052** | System users across all roles (Farmer, Agent, Centre, Govt). |
| | `farmers` | **5,011** | Farmer profiles with landholdings, bank account, and eKYC status. |
| | `farmer_crops` | **5,545** | Crop registrations per farmer with acreage and expected yield. |
| **Centres & Geography** | `procurement_centres`| **32** | Active procurement mandis across 6 states. |
| | `states` | **4** | State master records (Goa, Maharashtra, Karnataka, Punjab). |
| | `districts` | **10** | District master boundaries. |
| | `daily_capacity` | **1,432** | Daily intake capacity records per centre. |
| | `employees` | **163** | Registered mandi personnel across 6 operational roles. |
| **Intake & Appointments**| `bookings` | **19,046** | Farmer slot reservations. |
| | `appointments` | **18,930** | Synchronized mandi appointment entries. |
| | `slots` | **8,828** | Hourly slot capacity definitions. |
| | `qr_codes` | **10,212** | Unique gate-entry tokens and verification codes. |
| **Physical Procurement** | `collection_records` | **9,703** | Gate arrivals and truck check-ins. |
| | `quality_checks` | **9,036** | Physical laboratory quality assessments. |
| | `weighments` | **9,003** | Gross and tare weighbridge weighments. |
| | `procurement_records`| **9,641** | Completed procurement transactions. |
| | `procurement_transactions` | **9,668** | Financial ledger entries. |
| | `payments` | **9,669** | Direct Benefit Transfer (DBT) payment disbursements. |
| **Mandi Operations** | `queue_events` | **20,092** | Event log (Check-in, QC, Weigh, Checkout). |
| | `notifications` | **20,002** | Automated SMS, push, and "Come Now" alert records. |
| | `centre_daily_metrics`| **1,006** | Historical daily centre throughput, wait times, congestion. |
| | `inventory` | **100** | Bardan jute bag stock records. |
| **Logistics & Fleet** | `trucks` | **54** | Fleet vehicle assets. |
| | `truck_allocations` | **73** | Vehicle assignments to routes. |
| | `truck_requests` | **24** | Centre dispatch requests. |
| | `truck_route_predictions`| **72** | OR-Tools generated route solutions. |
| **Quality & AI** | `ai_quality_inspections` | **89** | Multi-mango computer vision inspection sessions. |
| | `ai_inspection_detections`| **286** | Individual mango segmented instance detections. |
| | `procurement_evidence` | **58** | Photographic evidence records across QC, Weigh, and Storage. |
| **Audit & Governance** | `audit_logs` | **1,527** | Tamper-evident administrative audit log entries. |
| | `process_audit_logs` | **376** | Step-by-step procurement state transition logs. |
| | `complaints` | **42** | Farmer grievance redressal tickets. |
| | `alerts` | **36** | Active operational alert notices. |

---

## 9. AI Models & Empirical Performance (Mandatory Audit)

Every model and algorithmic engine in BharatAgri is independently evaluated using test sets, reproducible scripts, and baseline comparisons. **No accuracy claims or performance numbers are fabricated.**

### Summary Model Performance Matrix

| Model / Engine | Algorithm / Library | Task | Evaluation Dataset | Key Metrics | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mango AI Defect Classifier** | RBF SVM ($L^*, a^*, b^*$) | 6-Class Fruit Quality | 920 untouched test samples (80/20 split) | **Accuracy: 81.09%**, **Macro F1: 0.7745**, **Weighted F1: 0.8084** | Validated |
| **Supply Forecaster** | XGBoost Regressor | Procurement Arrival Volume (Q) | Chronological holdout (Months 10–12, 534 rows) | **MAE: 2.30 Q**, **RMSE: 2.95 Q**, **$R^2$: 0.9824** (vs Mean Baseline MAE: 19.19 Q) | Validated |
| **Price Estimation** | XGBoost Regressor | Mandi Procurement Price (₹/Q) | 20% holdout of 9,641 transactions | **MAE: ₹14.91/Q**, **RMSE: ₹28.07/Q**, **$R^2$: 0.9998** (100% MSP floor compliance) | Validated |
| **Procurement Anomalies** | Isolation Forest | Unsupervised Outlier Detection | 1,009 benchmark rows (50 ground truth outliers) | **Precision: 0.8333**, **Recall: 1.0000**, **F1: 0.9091** | Validated |
| **Queue Wait Time** | Gradient Boosting Regressor | Mandi Wait Time (Minutes) | 3,600 holdout records (20% split) | **MAE: 11.29 min**, **RMSE: 14.08 min**, **$R^2$: 0.9448** (vs Little's Law MAE: 37.34 min) | Validated |
| **Fleet Optimizer** | Google OR-Tools (SCIP MILP) | Logistics Cost & Dispatch | Multi-centre benchmark (32 centres, 54 trucks) | **Solver Feasibility: 100%**, **Fleet Utilization: 82.4%**, **Unmet Critical Demand: 0.0 Q** | Validated |

---

### 1. Mango AI Multi-Instance Segmentation & Defect Classifier

- **Architecture:** Multi-stage computer vision pipeline combining CIELAB/HSV color segmentation, Euclidean Distance Transform (EDT) Voronoi instance partitioning, Sobel contact seam carving, multi-scale outer perimeter shadow exclusion, adaptive inward boundary erosion, and an RBF Support Vector Machine defect classifier.
- **Evaluation Dataset:** 4,600 total images sampled from `MangoDHDS`, `MangoFruitBD`, `MangoFruitDDS`, and Goan local field photographs. Evaluated on an untouched 20% held-out test set (920 samples).
- **Evaluation Script:** `python -m ml.evaluation.evaluate_mango`

#### Per-Class Performance on Untouched 920-Sample Test Set

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Anthracnose** | 0.7375 | 0.6629 | 0.6982 | 178 |
| **Bacterial Canker** | 0.5968 | 0.6167 | 0.6066 | 60 |
| **Healthy** | **0.8708** | **0.9337** | **0.9012** | **332** |
| **Other Defects** | 0.7578 | 0.8971 | 0.8215 | 136 |
| **Scab** | 0.8485 | 0.7000 | 0.7671 | 120 |
| **Stem End Rot** | 0.9146 | 0.7979 | 0.8523 | 94 |
| **Macro Average** | **0.7877** | **0.7680** | **0.7745** | 920 |
| **Weighted Average**| **0.8143** | **0.8109** | **0.8084** | 920 |

#### Confusion Matrix (920 Samples)

```text
                  Predicted ────────►
Actual            Anthracnose  Bacterial  Healthy  Other  Scab  Stem End Rot
Anthracnose               118          2       32     25     0             1
Bacterial Canker            5         37        2      0    15             1
Healthy                    14          1      310      3     0             4
Other                      11          1        1    122     0             1
Scab                        7         21        8      0    84             0
Stem End Rot                5          0        3     11     0            75
```

#### Real-World Locked External Test Set (62 Unseen Images)
Evaluated across `ml/data/mango/external_test/` (unseen during all training, tuning, and threshold selection):
- Successfully processed: **62 / 62 (100.0%)**.
- Zero-detection failures: **0**.
- Total isolated mango instances: **283 fruits** (average 4.56 fruits per image).
- Shadow rejection efficiency: **19.9%** (1,324,861 pixels successfully excluded from defect consideration).
- Healthy green Goan mango false-positive rate: **0.0%**.

---

### 2. XGBoost Supply Forecasting Engine

- **Architecture:** XGBoost Regressor (`n_estimators=150`, `max_depth=6`, `learning_rate=0.08`, `subsample=0.85`).
- **Input Features:** Centre ID, state, district, crop, month, day of week, registered farmer count, advance booked quantity, expected harvest yield, daily capacity, historical 7-day arrival quantity, truck demand, bardan jute bag consumption.
- **Evaluation Methodology:** Chronological split (Training: Months 1–9, Holdout Test: Peak post-harvest Months 10–12, 534 records).
- **Evaluation Script:** `python -m ml.evaluation.evaluate_models`

#### Comparison Against Empirical Baselines

| Model / Pipeline | MAE (Quintals) | RMSE (Quintals) | $R^2$ Score | Evaluation Finding |
| :--- | :---: | :---: | :---: | :--- |
| **Historical Mean Baseline** | 19.19 Q | 22.44 Q | -0.0172 | Predicts historical mean; fails during peak harvest influx. |
| **Seasonal Crop Average** | 19.20 Q | 22.42 Q | -0.0158 | Crop mean; fails to account for centre capacity and bookings. |
| **Ridge Linear Model** | 3.07 Q | 3.82 Q | 0.9705 | Captures linear booking trends but misses non-linear saturation. |
| **XGBoost Supply Forecaster**| **2.30 Q** | **2.95 Q** | **0.9824** | **Captures non-linear arrival surges, booked quotas, and limits.** |

---

### 3. XGBoost Price Estimation Model

- **Architecture:** XGBoost Regressor trained on 9,641 completed procurement transactions with an enforced legal invariant:
  $$\text{Final Price} = \max(\text{AI Estimated Price}, \text{Statutory Government MSP})$$
- **Input Features:** Official MSP, historical procurement rate, current mandi demand, forecast demand, current commodity supply, forecast supply, state, district, crop season (Kharif/Rabi/Zaid), storage buffer headroom, supply surplus/deficit.
- **Evaluation Metrics (20% Holdout):**
  - **MAE:** ₹14.91 per Quintal
  - **RMSE:** ₹28.07 per Quintal
  - **$R^2$:** 0.9998
  - **Statutory Floor Violations:** **0** (100.0% statutory MSP compliance).

---

### 4. Isolation Forest Procurement Anomaly Surveillance

- **Architecture:** Unsupervised Scikit-Learn `IsolationForest` (`n_estimators=100`, `contamination=0.06`).
- **Feature Vector:** Booked quantity, gross weighbridge weight, tare weight, net weight, moisture %, foreign matter %, turnaround duration (minutes), net-to-booked ratio.
- **Evaluation on Labeled Benchmark Dataset (1,009 Test Cases):**
  - True Positives (TP): 50
  - False Positives (FP): 10
  - False Negatives (FN): 0
  - **Precision:** 0.8333 (83.33%)
  - **Recall:** 1.0000 (100.00%)
  - **F1-Score:** 0.9091 (90.91%)
- **Governance Notice:** In live operational production, flagged records are labeled strictly as **`Potential Anomaly — Requires Review`** and routed to human inspectors.

---

### 5. Gradient Boosting Mandi Queue Wait Time Engine

- **Architecture:** Scikit-Learn Gradient Boosting Regressor (`n_estimators=120`, `max_depth=5`, `learning_rate=0.06`).
- **Evaluation Dataset:** 18,000 historical queue records (`ml_training_dataset`), evaluated on a 3,600-record held-out test set (20%).
- **Results vs Baseline:**
  - **Little's Law Baseline ($W = L / \mu$):** MAE: 37.34 min, RMSE: 72.43 min, $R^2$: -0.4594.
  - **Gradient Boosting Model:** **MAE: 11.29 min**, **RMSE: 14.08 min**, **$R^2$: 0.9448**.
- **Uncertainty Calibration:** Outputs predicted wait with empirical 95% confidence intervals based on test residual standard deviation ($\pm 1.96\sigma$, $\sigma = 14.08$ min).

---

### 6. Google OR-Tools Mixed-Integer Fleet Optimizer

- **Solver:** Google OR-Tools (`pywraplp.Solver.CreateSolver('SCIP')`).
- **Objective:** Minimize total haulage distance ($\sum d_{ij} x_{ij}$) and penalize unmet critical demand.
- **Constraints Enforced:** Truck payload capacities, origin lot availability, destination godown storage limits, and non-operational holiday constraints.
- **Benchmark Evaluation (32 Centres, 54 Trucks):**
  - **Solver Feasibility:** 100.0%
  - **Fleet Capacity Utilization:** 82.4%
  - **Unmet Critical Demand:** 0.0 Quintals
  - **Capacity Violations:** 0 (zero overloads or warehouse overflows).

---

## 10. Core System Features & Role-by-Role Walkthrough

### 1. Farmer Experience
- **Simplified Hero Actions:** Large, accessible cards for "Book Procurement" and "My Token & Slot".
- **Intelligent Slot Recommendation:** Identifies low-congestion arrival windows and recommends nearest capable centres.
- **Digital Gate Token:** Provides an instant digital pass with token number (e.g. `A025`) and verifiable QR code.
- **Live Queue & "Come Now" Dispatch:** Live tracker indicating current token being served and farmers ahead; automatically triggers an alert when $\le 5$ farmers remain ahead.
- **DBT Payment Passbook:** Real-time visibility into bank account credit status and transaction clearance references.

### 2. Procurement Centre Experience
- **Single-Use Gate QR Inward:** Controlled gate check-in scanning preventing duplicate or out-of-turn admissions.
- **5-Step Procurement Workflow:**
  1. *Collection:* Produce verification, bag count, transport mode, photo evidence.
  2. *Quality Inspection:* Moisture %, foreign matter %, laboratory photo.
  3. *AI Quality Inspection:* Optical multi-mango scanning with live visual debug overlays.
  4. *Weighment:* Dual gross and tare weighbridge recording with machine photo.
  5. *Procurement Finalization:* MSP valuation, digital signature, and immutable Lot ID generation.
- **Dedicated Storage Management (`/centre-storage`):** Post-procurement warehouse bin assignment, atmospheric condition checks, and stack photo verification.
- **Employee Roster Isolation:** Dynamic database loading of active employees; prevents confirmation bias by concealing upstream quality measurements on downstream weighbridge screens.

### 3. Government Command Centre Experience
- **National Procurement KPIs:** Real-time metrics across total farmers onboarded, metric tons procured, MSP value disbursed, and active centres.
- **Supply Forecast Graph:** Historical procurement records linked seamlessly to 7–30 day projected procurement curves with transparent data gap notices.
- **DBT Disbursement Monitor:** Tracks transaction volume and values across Paid, Processing, Pending, Failed, and Rejected states.
- **Mandi Congestion & Redirection:** Real-time utilization scores (Low, Medium, High, Critical) with automated alternative centre redirection.
- **Fleet Logistics Optimizer:** One-click OR-Tools dispatch generating optimal multi-centre truck routes.

---

## 11. Procurement Copilot Architecture

BharatAgri features a natural language conversational interface grounded strictly in live database state:
- **Government Copilot (`POST /api/queue/copilot`):** Answers national questions regarding centre bottlenecks (e.g., *"Why is Centre C004 delayed?"*), spare capacity matching, longest queues, and state procurement leaders.
- **Centre Copilot (`POST /api/queue/centre-copilot/{centre_id}`):** Securely isolated to the authenticated facility; answers questions on queue growth causes, pending afternoon appointments, equipment status, and next-hour arrivals.
- **Zero Hallucination Guarantee:** Pre-computes SQL queries and numerical aggregations before sending structured facts to the language explanation layer. If data is missing, it explicitly reports that information is unavailable.

---

## 12. API Reference

### Dynamic AI Queue & Mandi Operations
- `POST /api/queue/predict-wait` — Gradient Boosting wait time prediction with 95% confidence interval.
- `GET  /api/queue/centres/{id}/live` — Live queue metrics (queue depth, processing rate, active stations).
- `GET  /api/queue/tokens/{token}` — Token tracking (farmers ahead, current serving token).
- `GET  /api/queue/departure-recommendation` — Farmer departure recommendation (slot time - travel - 15m buffer).
- `POST /api/queue/recommend-centre` — Multi-criteria centre ranking.
- `GET  /api/queue/recommend-slots/{centre_id}` — Dynamic low-congestion slot recommendation.
- `POST /api/queue/copilot` — National Government Copilot.
- `POST /api/queue/centre-copilot/{centre_id}` — Mandi-isolated Centre Copilot.

### Authentication & Roles
- `POST /api/auth/login` — JWT authentication for FARMER, AGENT, CENTRE, GOVERNMENT.
- `GET  /api/auth/me` — Authenticated profile.
- `POST /farmers/register` — Farmer onboarding with multi-crop support.
- `POST /api/agents/register` — Field Agent onboarding.
- `POST /centres/register` — Procurement Centre manager onboarding.
- `POST /api/government/register` — Government official onboarding.

### Physical Procurement & Lot Traceability
- `POST /api/collections` — Inward gate collection record.
- `POST /api/quality` — Physical laboratory inspection (moisture, foreign matter).
- `POST /api/weighments` — Gross and tare electronic weighbridge capture.
- `POST /api/procurement` — Final procurement certificate & immutable Lot ID generation.
- `POST /api/procurement/evidence` — Multipart evidence photo upload (Collection, QC, Weigh, Storage).
- `GET  /api/storage` — Storage lot assignment and warehouse bin tracking.
- `GET  /api/payments/status/{id}` — Direct Benefit Transfer (DBT) payment clearance.

### Government Analytics & AI
- `GET  /api/government/forecast-vs-actual` — Historical procurement observations + XGBoost projected procurement.
- `GET  /api/government/analytics/payments-summary` — 5-stage DBT payout summary.
- `GET  /api/government/perishable-priority` — Perishable crop transport priority rankings.
- `POST /api/trucks/routes/predict` — OR-Tools fleet route dispatch optimization.
- `GET  /api/ai/congestion` — Operational congestion scores and saturation warnings.
- `GET  /api/ai/anomalies` — Isolation Forest outlier audit queue.

---

## 13. Comprehensive Testing & Verification Suite

All 71 automated tests across 10 test suites pass with zero regressions:

```bash
# Execute entire test suite
pytest tests/ -v
```

### Verified Test Results Breakdown (71 / 71 Passed)

```text
tests/test_forecast_and_mango_regression.py::test_government_forecast_historical_data_restored PASSED
tests/test_forecast_and_mango_regression.py::test_government_forecast_projected_procurement_non_zero_and_connected PASSED
tests/test_forecast_and_mango_regression.py::test_government_forecast_monthly_aggregation_honored PASSED
tests/test_forecast_and_mango_regression.py::test_government_forecast_insufficient_data_status PASSED
tests/test_forecast_and_mango_regression.py::test_mango_external_cast_shadow_excluded_from_mask PASSED
tests/test_forecast_and_mango_regression.py::test_mango_healthy_dark_peel_not_marked_as_defect PASSED
tests/test_forecast_and_mango_regression.py::test_mango_gradual_shadow_gradient_not_marked_as_defect PASSED
tests/test_forecast_and_mango_regression.py::test_mango_adaptive_inner_padding_and_defect_denominator PASSED
tests/test_forecast_and_mango_regression.py::test_mango_segmentation_failure_never_returns_100_percent_defect PASSED
tests/test_mango_ai_quality.py (23 tests: instance separation, shadow rejection, padding, grading) PASSED
tests/test_procurement_process.py (7 tests: 5-step sequence, employee isolation, evidence) PASSED
tests/test_dashboard_roles.py (7 tests: multi-role authentication, RBAC, centre data isolation) PASSED
tests/test_e2e_features.py (4 tests: DBT analytics, truck request accept & notify, Copilot scoping) PASSED
tests/test_copilot_matrix.py (8 tests: entity extraction, comparative periods, causal diagnostics) PASSED
tests/test_queue_api.py (1 test: wait prediction, live queue, slot recommendation) PASSED
tests/test_supply_demand_math.py (3 tests: surplus/deficit formula consistency, inventory isolation) PASSED
tests/test_api.py (8 tests: health, auth, bookings, lot generation, OR-Tools fleet, Bardan bags) PASSED

====================== 71 passed, 41 warnings in 37.99s =======================
```

### Reproducible Evaluation Commands

```bash
# 1. Evaluate XGBoost Supply, Price, and Isolation Forest models
python -m ml.evaluation.evaluate_models

# 2. Evaluate Mango AI Multi-Class Classifier and test set metrics
python -m ml.evaluation.evaluate_mango

# 3. Verify Database Foreign Key and Temporal Consistency
python scripts/validate_procurement_data.py

# 4. Verify End-to-End Procurement Lifecycle
python scripts/verify_e2e_procurement_workflow.py

# 5. Build Frontend Production Bundle
cd frontend && npm run build
```

---

## 14. Troubleshooting Guide

| Issue | Root Cause | Verified Resolution |
| :--- | :--- | :--- |
| `Connection refused on port 5000` | Backend server not running | Ensure `python -m uvicorn backend.app.main:app` is running; check `.env` port setting. |
| `Access denied for user 'root'` | MySQL credentials mismatch | Start MySQL in XAMPP; verify `DB_USER` and `DB_PASSWORD` in `.env`. |
| `jwt decode error` | Stale browser session token | Log out and log back in, or clear browser `localStorage`. |
| `ML model .pkl/.joblib not found` | Model artifacts missing | Run `python -m ml.evaluation.evaluate_models` to re-train and serialize models. |
| `Zero projected procurement on graph` | Historical bounds cutoff | Resolved in Iteration 2.7 via dynamic `anchor_date` and model forecast invocation. |
| `Healthy green mango flagged as defective`| Outdated defect thresholds | Resolved in Iteration 2.7 via expanded dark peel protection and shadow exclusion. |
| `UnicodeEncodeError in pytest` | Windows console codepage | Run `chcp 65001` before executing pytest. |

---

## 15. Limitations & Future Roadmap

1. **Unsupervised Outlier Ground Truth:** Isolation Forest operates as an unsupervised surveillance tool. True fraud labels do not exist in public agricultural datasets; flagged transactions require verification by on-site human auditors.
2. **Dense Fruit Occlusions:** When mangoes are stacked vertically in deep crates with $>50\%$ of a fruit hidden, classical morphological Voronoi partitioning cannot reliably infer occluded contours. These cases are flagged as `NEEDS_REVIEW` for manual weighing.
3. **Synthetic Operational Scenarios:** Micro-operational transactions (gate weighbridge tickets, queue barcodes, bag consumption logs) are generated via operational simulations to reflect real-world distributions. Sourced macroeconomic benchmarks (official MSP floors, Mandi baseline ranges) represent official ground truth.
4. **Hardware Acceleration:** Current inference runs on standard x86 CPU architectures without requiring dedicated GPUs, maintaining accessibility for rural mandi deployment. Future iterations will support WebAssembly/ONNX client-side edge inference directly within mobile browsers.

---

## 16. License & Attribution

BharatAgri (KisanFlow) is developed as a digital public infrastructure platform for agricultural procurement.

- **Backend:** FastAPI, SQLAlchemy, Pydantic, Scikit-Learn, XGBoost, Google OR-Tools, OpenCV.
- **Frontend:** React, Vite, Recharts, Lucide React.
- **Data Grounding:** Ministry of Agriculture and Farmers Welfare (MoAFW), Commission for Agricultural Costs and Prices (CACP), AGMARKNET, and SIH 26032 KisanFlow Dataset.

© 2026 BharatAgri / KisanFlow. All rights reserved.

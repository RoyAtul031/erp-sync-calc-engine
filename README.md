# Enterprise ERP Data Sync & Deterministic ESG Calculation Engine

> **The Integration Solution**: Automated ERP Ingestion, Multi-Framework Emission Factor Libraries, and Cryptographically Verifiable Deterministic Calculations.

An enterprise-grade integration and analytics platform built with **Python, Django REST Framework, Celery, Redis, and PostgreSQL**. 

This system emulates the exact integration challenges of modern sustainability software platforms like **Breathe ESG** and **SAP Sustainability Control Tower**: pulling operational consumption and HR metrics directly from enterprise systems (like SAP S/4HANA and Workday HCM), snapshotting immutable raw data for financial audits (SOX/GHG Protocol), and deterministically computing Greenhouse Gas (GHG) Scope 1 & 2 carbon footprints alongside Social KPIs.

---

## 🌟 Key Architecture & Capabilities

```
  +-------------------------------------------------------------------------+
  |              ENTERPRISE DATA SOURCES (SAP S/4HANA & Workday)            |
  |  - SAP Plant Maintenance (Meter Readings & Utility Invoices)             |
  |  - Workday HCM (EHS Incident Reporting, Worker Demographics & Hours)    |
  +-------------------------------------------------------------------------+
                                       │
                                       ▼ (REST / Scheduled Celery Beat)
  +-------------------------------------------------------------------------+
  |                    INGESTION & DELTA SYNC PIPELINE                     |
  |  - ERP Client with retry, bearer tokens, & delta watermarks             |
  |  - SHA-256 payload hashing for deduplication & SOX audit proof          |
  |  - Facility auto-provisioning & unit normalization                      |
  +-------------------------------------------------------------------------+
                                       │
                                       ▼
  +-------------------------------------------------------------------------+
  |                          ESG DATA WAREHOUSE                             |
  |  - Facility (Operational Plant / Headquarters / R&D Hubs)               |
  |  - FacilityUtilityRecord (Diesel, Natural Gas, Electricity, Water)     |
  |  - WorkforceMetricRecord (Headcount, Diversity, LTI, Exposure Hours)    |
  +-------------------------------------------------------------------------+
                                       │
                                       ▼
  +-------------------------------------------------------------------------+
  |               DETERMINISTIC ESG CALCULATION ENGINE                     |
  |  - Safe AST Mathematical Evaluator (No unsafe eval(); handles math AST) |
  |  - Scope 1 Direct Combustion (Diesel Liters, Natural Gas m3)            |
  |  - Scope 2 Location-Based Grid (EPA eGRID, DEFRA, CEA India, Germany)   |
  |  - Scope 2 Market-Based (Contractual Instruments, REC / PPA Zero-Factor)|
  |  - Social KPIs (Gender Diversity %, Lost Time Injury Frequency Rate)   |
  +-------------------------------------------------------------------------+
                                       │
                                       ▼
  +-------------------------------------------------------------------------+
  |                  EXECUTIVE & ANALYST DASHBOARD + APIs                   |
  |  - Interactive Glassmorphism Dark-Mode Portal                           |
  |  - Real-time ERP Connector Hub & Sync Monitor                           |
  |  - Live Formula Sandbox & Custom Methodology Editor                     |
  |  - Audit Lineage & Proof Inspector Modal                                |
  |  - OpenAPI 3.0 & Interactive Swagger Documentation                      |
  +-------------------------------------------------------------------------+
```

---

## 🚀 Core Features

### 1. Simulated ERP Sync Pipeline
* **High-Fidelity Simulators**: Realistic SAP S/4HANA OData and Workday HCM REST endpoints providing plant maintenance material documents, invoices, smart meter IDs, and employee safety records.
* **Idempotent Ingestion**: Raw payloads are hashed using SHA-256. Subsequent syncs skip duplicates and maintain an audit log of batch checksums.
* **Incremental Delta Sync**: Uses delta watermarks (`?since=...`) to fetch only newly posted records since the last sync.

### 2. Deterministic Calculation Engine
* **Safe AST Formula Evaluation**: Uses Python's Abstract Syntax Tree (`ast`) to safely evaluate custom math equations without vulnerability to code injection.
* **Multi-Framework Standards**:
  * **GHG Protocol Corporate Standard** (Global benchmark)
  * **US EPA Mandatory Reporting (GHGRP & eGRID 2024)**
  * **UK DEFRA / DESNZ 2024 GHG Conversion Factors**
  * **India SEBI BRSR Core Disclosures**
* **Traceability Proof Generation**: Every calculated metric records its exact lineage:
  * Raw input measurement & unit normalization steps
  * Certified emission factor value, units, and citation
  * Fully resolved algebraic equation
  * Final audited output with timestamp

### 3. Customizable Calculation Methodologies
* Analysts and compliance officers can customize formulas (e.g. `(consumption * emission_factor) / 1000.0`) in the UI without modifying Python source code.
* Built-in **Formula Sandbox** allows live testing of equations against variables with immediate AST syntax validation.

### 4. Background Scheduled Tasks (Celery & Redis)
* Hourly Celery Beat tasks to poll active ERP connections.
* Daily automated recalculations when new utility meter readings are ingested.
* Full asynchronous job queuing for heavy batch jobs.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.14 / Django 6.1 |
| **API Framework** | Django REST Framework (DRF) |
| **API Documentation** | drf-spectacular (OpenAPI 3.0 / Swagger UI / ReDoc) |
| **Task Queue & Scheduler** | Celery 5.6 + Celery Beat + Redis |
| **Database** | PostgreSQL ready with seamless zero-dependency SQLite fallback |
| **Formula Engine** | Python AST (`ast.parse`) Deterministic Safe Math Parser |
| **Frontend UI** | HTML5, Vanilla CSS (Glassmorphism & dark theme), Modern JS |

---

## 📦 Quickstart Guide

### 1. Local Setup (Zero-Configuration with SQLite)

```bash
# Navigate to the project directory
cd c:\code\erp-sync-calc-engine

# Activate the virtual environment
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate (Linux/Mac)

# Run database migrations
python manage.py migrate

# Seed enterprise compliance reference data
python manage.py seed_enterprise_data

# Start the development server
python manage.py runserver
```

Now open your browser:
* **Landing & Enterprise Login Portal**: [http://127.0.0.1:8050/](http://127.0.0.1:8050/)
* **Executive ESG Dashboard Console**: [http://127.0.0.1:8050/dashboard/](http://127.0.0.1:8050/dashboard/)
* **Interactive Swagger API Docs**: [http://127.0.0.1:8050/api/docs/](http://127.0.0.1:8050/api/docs/)
* **OpenAPI 3.0 JSON Schema**: [http://127.0.0.1:8050/api/schema/](http://127.0.0.1:8050/api/schema/)
* **ReDoc Documentation**: [http://127.0.0.1:8050/api/redoc/](http://127.0.0.1:8050/api/redoc/)

#### Pre-Configured Demo Accounts:
* **Chief Sustainability Officer (CSO)**: `cso@enterprise.com` / `Enterprise2026!`
* **Lead ESG Compliance Analyst**: `analyst@enterprise.com` / `Enterprise2026!`
* **External Statutory Auditor**: `auditor@deloitte-audit.com` / `Enterprise2026!`
*(Or click any one-click demo role button on the landing page for instant login!)*

---

### 2. Running with Docker Compose (PostgreSQL + Redis + Celery)

```bash
docker-compose up --build
```
This spins up:
* `erp_esg_postgres` (PostgreSQL 16)
* `erp_esg_redis` (Redis 7)
* `erp_esg_web` (Django Application)
* `erp_esg_celery_worker` (Celery Worker)
* `erp_esg_celery_beat` (Celery Periodic Task Scheduler)

---

### 3. Running Background Celery Tasks Locally

If running Redis locally:
```bash
# Terminal 1: Celery Worker
celery -A core worker --loglevel=info

# Terminal 2: Celery Beat Periodic Scheduler
celery -A core beat --loglevel=info
```

---

## 🧪 Running the Test Suite

```bash
python manage.py test tests
```

Tests include:
* ✅ `test_sap_sync_and_facility_provisioning`
* ✅ `test_sync_idempotency` (Deduplication validation)
* ✅ `test_workday_workforce_sync`
* ✅ `test_standard_math_evaluation` & division by zero handling
* ✅ `test_rejects_unsafe_code` (AST security checks)
* ✅ `test_scope_1_calculation`
* ✅ `test_scope_2_market_based_zero_for_renewables`
* ✅ `test_social_workforce_kpi_calculation`
* ✅ `test_formula_customization_reflects_in_calculation`
* ✅ `test_formula_simulator_api`

---

## 📂 Project Structure

```
erp-sync-calc-engine/
├── core/                       # Django core configuration & settings
│   ├── celery.py               # Celery application & beat schedule
│   ├── settings.py             # DRF, PostgreSQL, Celery, CORS & Spectacular config
│   ├── urls.py                 # API routing & Swagger endpoints
│   └── wsgi.py
├── apps/
│   ├── erp_connector/          # Simulated ERP endpoints & sync pipeline
│   │   ├── models.py           # ERPConnection, SyncBatch, RawIngestedPayload
│   │   ├── client.py           # Resilient ERP HTTP client
│   │   ├── mock_erp_api.py     # Simulated SAP S/4HANA & Workday REST APIs
│   │   ├── services.py         # ERPSyncService with SHA-256 snapshotting
│   │   ├── tasks.py            # Celery sync jobs (scheduled & on-demand)
│   │   └── views.py / urls.py
│   ├── data_warehouse/         # Normalized ESG warehouse storage
│   │   ├── models.py           # Facility, FacilityUtilityRecord, WorkforceMetricRecord
│   │   └── views.py / urls.py
│   ├── calculation_engine/     # Deterministic Calculation Engine
│   │   ├── models.py           # ComplianceFramework, EmissionFactor, FormulaRule, CalculationRun
│   │   ├── engine.py           # SafeMathEvaluator (AST) & DeterministicCalculationEngine
│   │   ├── seed_data.py        # EPA eGRID, DEFRA, BRSR factor seed data
│   │   ├── tasks.py            # Celery calculation tasks
│   │   └── views.py / urls.py
│   └── dashboard/              # Interactive UI
│       ├── templates/dashboard/index.html
│       └── static/css/ & static/js/
├── tests/                      # Full test suite
├── docker-compose.yml          # Production-ready PostgreSQL/Redis container stack
├── Dockerfile
├── requirements.txt
└── manage.py
```

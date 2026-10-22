# 🌍 OmniSync ESG
### Global Enterprise ERP Data Sync & Deterministic ESG Calculation Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/Django_REST_Framework-3.18-red?style=for-the-badge)](https://www.django-rest-framework.org)
[![Celery](https://img.shields.io/badge/Celery-5.6-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Swagger](https://img.shields.io/badge/OpenAPI-3.0_Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](http://127.0.0.1:8050/api/docs/)

> **The Enterprise Integration Solution**: Automated ERP Ingestion (SAP S/4HANA & Workday HCM), Multi-Framework Certified Emission Factor Libraries, and Cryptographically Verifiable Deterministic Calculations.

---

## 💡 What is OmniSync ESG?

In large enterprises (such as Fortune 500 corporations and multinational manufacturers), utility meter readings, fuel invoices, and workforce metrics are scattered across legacy corporate systems like **SAP S/4HANA**, **Oracle Cloud**, and **Workday HCM**.

Calculating greenhouse gas (GHG) carbon footprints and social ESG disclosures manually using spreadsheets is slow, prone to errors, and **fails modern statutory audits** (such as the EU CSRD mandate and US SEC climate rules).

**OmniSync ESG** solves this by providing:
1. **Automated ERP Delta Ingestion**: Regularly polls enterprise systems (simulating SAP OData and Workday REST APIs) using resilient HTTP clients with timestamp watermarks.
2. **Cryptographic Lineage (SHA-256)**: Stores immutable raw snapshots of every invoice and meter reading for SOX and financial audit compliance.
3. **Deterministic AST Calculation Engine**: Replaces dangerous `eval()` calls with a safe, tokenized Abstract Syntax Tree (AST) parser to execute customizable compliance formulas.
4. **Multi-Jurisdiction Standards**: Built-in certified factors for **EU CSRD (ESRS E1)**, **US EPA eGRID 2024**, **UK DEFRA**, **India SEBI BRSR**, and the **GHG Protocol**.
5. **Full Audit Traceability**: Any reported emissions number can be inspected down to its raw SAP material document, unit conversion step, certified factor citation, and evaluated algebraic equation.

---

## 🏗️ System Architecture

```
+-----------------------------------------------------------------------------------+
|                           ENTERPRISE ERP & HR DATA SOURCES                        |
|   - SAP S/4HANA: Plant Maintenance (PM) & Utility Invoicing (MM Material Docs)    |
|   - Workday HCM: Worker Headcounts, Gender Diversity, Safety Incidents (EHS)      |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ (REST / Celery Beat Scheduled Tasks)
+-----------------------------------------------------------------------------------+
|                          INGESTION & DELTA SYNC PIPELINE                          |
|   - Resilient ERP Client with retry policies & delta watermarks (?since=...)      |
|   - SHA-256 Cryptographic Checksum generation for tamper detection                |
|   - Idempotent deduplication: raw payload preservation (RawIngestedPayload)       |
|   - Automated Facility Provisioning & Unit Normalization (Liters, kWh, m³)        |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                                ESG DATA WAREHOUSE                                 |
|   - Facility: Global operational sites (Austin, Munich, Bangalore, London)        |
|   - FacilityUtilityRecord: Normalized energy consumption, fuel & tariffs          |
|   - WorkforceMetricRecord: Operational headcounts, exposure hours, LTI cases      |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        DETERMINISTIC CALCULATION ENGINE                           |
|   - Safe AST Mathematical Evaluator: Zero arbitrary code execution                |
|   - Scope 1 Direct Combustion: Diesel Generators, Fleet & Natural Gas Heating     |
|   - Scope 2 Location-Based Grid: Regional grid emission factors (ERCOT, CAMX, etc)|
|   - Scope 2 Market-Based: Zero emission factor for Renewable Energy Contracts(REC)|
|   - Social KPIs: Gender Diversity (%) & Lost Time Injury Frequency Rate (LTIFR)   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        PRESENTATION & EXPORT INTERFACES                           |
|   - Executive ESG Portal: Glassmorphic dark-theme analytics & operational status  |
|   - Live Formula Sandbox: Real-time equation preview with AST token validation    |
|   - Audit Proof Inspector Modal: Step-by-step mathematical proof for each number  |
|   - SOX/CSRD Audit Export: One-click CSV and JSON compliance spreadsheets         |
|   - Interactive OpenAPI 3.0: Full Swagger UI & ReDoc developer documentation      |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Key Features

* **🛡️ Safe AST Math Engine**: Allows compliance officers to customize formulas in the UI (e.g. `(consumption * emission_factor) / 1000.0` or LTIFR equations). Python's `ast` parser checks syntax, prevents arbitrary code injection, and handles edge cases like division-by-zero deterministically.
* **⚡ One-Click Audit Lineage**: Clicking *"Inspect Proof"* on any calculated metric reveals:
  * Raw ERP document reference (e.g. `SAP-MATDOC-2024-00101`)
  * SHA-256 batch checksum and ingestion timestamp
  * Raw consumption measurement & unit conversion step
  * Certified factor citation (e.g. *EPA eGRID2024 Subregion ERCT*)
  * Evaluated algebraic formula and verified final value.
* **🌐 Multi-Jurisdiction Compliance**:
  * **EU CSRD / ESRS E1** (European Sustainability Reporting Standards)
  * **US EPA GHGRP & eGRID 2024** (Subregions: ERCOT, CAMX, etc.)
  * **UK DEFRA / DESNZ 2024** Government GHG Conversion Factors
  * **India SEBI BRSR Core** ESG Disclosure Standard
  * **GHG Protocol Corporate Standard** (Global WRI/WBCSD baseline)
* **🔄 Asynchronous & Scheduled Task Queue**: Configured with Celery & Redis to run scheduled hourly ERP syncs and nightly batch recalculations.
* **📊 Downloadable Audit Reports**: Built-in CSV export generates complete audit-ready spreadsheets containing all formulas, source citations, and raw document IDs.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Backend Framework** | Python 3.11+ / Django 6.1 | Enterprise application framework |
| **API Framework** | Django REST Framework (DRF) | Clean RESTful endpoints & pagination |
| **API Specification** | drf-spectacular | OpenAPI 3.0, Swagger UI, and ReDoc |
| **Formula Engine** | Python AST (`ast.parse`) | Safe mathematical expression evaluation |
| **Task Queue & Scheduler** | Celery 5.6 + Redis | Distributed worker queue & Celery Beat crons |
| **Database** | PostgreSQL / SQLite | Production PostgreSQL with local SQLite fallback |
| **Frontend UI** | HTML5 / Vanilla CSS & JS | Glassmorphic, dark-mode, responsive web interface |
| **Deployment** | Docker Compose / Render / Railway | Containerized multi-service deployment |

---

## 🔑 Pre-Configured Demo Accounts

When visiting the login portal, you can use these enterprise accounts or click the **One-Click Demo Role** buttons:

| Role | Username / Email | Password | Access Level |
|---|---|---|---|
| **Chief Sustainability Officer (CSO)** | `cso@enterprise.com` | `Enterprise2026!` | Full Executive & Strategy Overview |
| **Lead ESG Compliance Analyst** | `analyst@enterprise.com` | `Enterprise2026!` | Formula Studio & Custom Rule Editing |
| **External Statutory Auditor** | `auditor@deloitte-audit.com` | `Enterprise2026!` | Cryptographic Lineage & CSV Export |

*(Guest access is also available via the "Explore Console as Guest" link with no login required!)*

---

## 📦 Quickstart Guide (Local Development)

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/RoyAtul031/erp-sync-calc-engine.git
cd erp-sync-calc-engine

# Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database & Reference Data

```bash
# Apply database migrations
python manage.py migrate

# Seed global compliance frameworks, emission factors, and ERP connectors
python manage.py seed_enterprise_data
```

### 3. Start the Server

```bash
python manage.py runserver 127.0.0.1:8050
```

Open your browser:
* 🚀 **Landing & Login Gateway**: [http://127.0.0.1:8050/](http://127.0.0.1:8050/)
* 📊 **Executive ESG Dashboard**: [http://127.0.0.1:8050/dashboard/](http://127.0.0.1:8050/dashboard/)
* 📚 **Interactive Swagger API Docs**: [http://127.0.0.1:8050/api/docs/](http://127.0.0.1:8050/api/docs/)
* 📄 **OpenAPI 3.0 Schema**: [http://127.0.0.1:8050/api/schema/](http://127.0.0.1:8050/api/schema/)
* 📖 **ReDoc Specification**: [http://127.0.0.1:8050/api/redoc/](http://127.0.0.1:8050/api/redoc/)

---

## 🧪 Automated Testing & Verification

Run the full automated test suite:

```bash
python manage.py test tests
```

Run the live end-to-end integration verification script:

```bash
python tests/verify_e2e.py
```

```
======================================================================
        OMNISYNC ESG - GLOBAL ENTERPRISE PLATFORM VERIFICATION        
======================================================================
[PASS] 1. Dashboard HTML Interface            | Status 200 (52202 bytes)
[PASS] 2. Interactive Swagger UI              | Status 200
[PASS] 3. OpenAPI 3.0 Specification           | Status 200 (98129 bytes)
[PASS] 4. ERP Connections Registry            | 3 active connectors
[PASS] 5. SAP S/4HANA Delta Ingestion         | Ingestion pipeline verified
[PASS] 6. SHA-256 Cryptographic Snapshots     | Verified hash: 1e77f8060e2ec424...
[PASS] 7. Facility Auto-Provisioning          | 4 global plants registered
[PASS] 8. Multi-Jurisdiction Compliance       | EU_CSRD, GHG_PROTOCOL, INDIA_BRSR, UK_DEFRA, US_EPA
[PASS] 9. AST Safe Math Parser                | Evaluated: 53.74 tCO2e
[PASS] 10. Calculation Methodology Registry   | Active methodology v1.0
[PASS] 11. Deterministic Calculation Run      | Scope 1=199.16 tCO2e | Scope 2=473.54 tCO2e
[PASS] 12. SOX/CSRD CSV Audit Report Export   | Exported 6203 bytes
[PASS] 13. Granular Lineage Proof Trace       | Evaluated math proof verified
======================================================================
FINAL STATUS: 100% PRODUCTION READY & VERIFIED
======================================================================
```

---

## ☁️ 1-Click Cloud Deployment (Render Blueprint)

The repository includes a ready-to-use [`render.yaml`](render.yaml) specification:

1. Push your repository to GitHub.
2. Log in to [render.com](https://render.com/) and click **"New +"** ➔ **"Blueprint"**.
3. Select your repository `RoyAtul031/erp-sync-calc-engine`.
4. Render automatically configures:
   * **Free Managed PostgreSQL Database** (`omnisync-esg-db`)
   * **Django Web Service** (`omnisync-esg-web` running Gunicorn)
   * **Celery Background Worker** (`omnisync-esg-celery-worker`)
5. Click **Apply** — Render automatically builds, migrates, seeds, and serves your app over HTTPS!

---

## 🐳 Docker Deployment

To spin up the complete multi-container stack locally (PostgreSQL + Redis + Celery Worker + Celery Beat + Web):

```bash
docker-compose up --build
```

---

## 📂 Repository Structure

```
erp-sync-calc-engine/
├── core/                       # Django project configuration
│   ├── celery.py               # Celery app & periodic task schedule
│   ├── settings.py             # DRF, PostgreSQL, Celery/Redis, CORS & Spectacular config
│   ├── urls.py                 # Application routing & Swagger documentation
│   └── wsgi.py                 # WSGI entrypoint with Vercel/Render compatibility
├── apps/
│   ├── erp_connector/          # Simulated ERP endpoints & sync pipeline
│   │   ├── models.py           # ERPConnection, SyncBatch, RawIngestedPayload (SHA-256)
│   │   ├── client.py           # Resilient ERP HTTP client
│   │   ├── mock_erp_api.py     # Simulated SAP S/4HANA & Workday REST APIs
│   │   ├── services.py         # ERPSyncService with deduplication & warehouse mapping
│   │   ├── tasks.py            # Celery sync jobs (scheduled & on-demand)
│   │   └── views.py / urls.py
│   ├── data_warehouse/         # Normalized ESG warehouse storage
│   │   ├── models.py           # Facility, FacilityUtilityRecord, WorkforceMetricRecord
│   │   └── views.py / urls.py
│   ├── calculation_engine/     # Deterministic Calculation Engine
│   │   ├── models.py           # ComplianceFramework, EmissionFactor, FormulaRule, CalculationRun
│   │   ├── engine.py           # SafeMathEvaluator (AST) & DeterministicCalculationEngine
│   │   ├── seed_data.py        # EU CSRD, EPA eGRID, DEFRA, BRSR factor seed data
│   │   ├── tasks.py            # Celery calculation tasks
│   │   └── views.py / urls.py
│   └── dashboard/              # Interactive UI
│       ├── templates/dashboard/landing.html  # Landing & Enterprise SSO/Login
│       ├── templates/dashboard/index.html    # Executive ESG Dashboard Console
│       └── static/css/ & static/js/          # Glassmorphic styling & client logic
├── tests/                      # Automated test suite & verification scripts
├── render.yaml                 # 1-click Render cloud deployment blueprint
├── docker-compose.yml          # Production-ready PostgreSQL/Redis container stack
├── Dockerfile
├── requirements.txt
└── manage.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

# Cell Division Timer — Biotechnology & Life-Sciences Platform

A production-grade, asynchronous RESTful backend platform engineered for biotechnology research, high-throughput live-cell microscopy analysis, and computational cell-cycle kinetics profiling. Built with **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 ORM**, **Pydantic V2**, **Alembic**, and **PostgreSQL / SQLite**.

---

## Table of Contents
1. [Domain Background & Problem Statement](#domain-background--problem-statement)
2. [Architectural Overview](#architectural-overview)
3. [Data Models & Schema Design](#data-models--schema-design)
4. [Biological Calculations & Kinetic Formulas](#biological-calculations--kinetic-formulas)
5. [Synthetic Benchmark Dataset](#synthetic-benchmark-dataset)
6. [API Specification & Endpoints](#api-specification--endpoints)
7. [Installation & Local Setup](#installation--local-setup)
8. [Database Migrations (Alembic)](#database-migrations-alembic)
9. [Database Seeding](#database-seeding)
10. [Automated Testing](#automated-testing)
11. [Containerization & Docker Deployment](#containerization--docker-deployment)
12. [Production Readiness & Life-Sciences Extensibility](#production-readiness--life-sciences-extensibility)

---

## Domain Background & Problem Statement

In cellular biology, cancer therapeutics, and bioprocess fermentation engineering, quantifying mitotic progression and cell cycle dynamics is fundamental:
* **Mitosis / Active Division Duration ($T_{div}$)**: Time interval from nuclear envelope breakdown / prophase through telophase and cytokinesis (typically minutes to hours).
* **Interdivision Generation Time / Doubling Time ($T_d$)**: Full cycle interval between consecutive cytokinesis events across sequential generations (hours to days).
* **Specific Growth Rate ($\mu$)**: Fundamental kinetic constant describing cellular population expansion under substrate and thermal constraints ($\text{hr}^{-1}$).

Microscopy time-lapse experiments produce dense streams of morphological division measurements. Without automated data validation, quality control (e.g. metaphase arrest, thermal stress outliers), and structured relational storage, laboratory workflows suffer from manual transcription errors and lack of reproducibility.

**Cell Division Timer** bridges laboratory instrument tracking and quantitative bioinformatics by providing:
- Structured hierarchical lineage: `Cell` samples $\rightarrow$ `CellDivisionRecord` observation events.
- Real-time kinetics derivation: automatic computation of division duration, specific growth rate, and generation doubling times.
- Automated biological outlier screening against organism-specific reference ranges (*S. cerevisiae*, *E. coli*, *H. sapiens* HeLa, *M. musculus* NIH/3T3).
- Batch quality control, multi-attribute filtering, and statistical kinetic aggregations.

---

## Architectural Overview

The application strictly implements clean, layered domain-driven separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│               Client / Laboratory Instrument           │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON / CSV
┌───────────────────────────▼────────────────────────────┐
│                    API Layer (FastAPI)                 │
│  - Routes: /health, /cells, /divisions, /analytics,    │
│            /data (CSV import/export)                   │
│  - Dependency Injection (FastAPI Depends)              │
│  - Exception Handlers & Request Validation (Pydantic)  │
└───────────────────────────┬────────────────────────────┘
                            │ Service Method Calls
┌───────────────────────────▼────────────────────────────┐
│                    Service Layer                       │
│  - CellService, DivisionService, AnalyticsService,     │
│    CSVService                                          │
│  - Business logic, validation orchestration,           │
│    kinetics computations (app.utils.biology)           │
└───────────────────────────┬────────────────────────────┘
                            │ Repository Method Calls
┌───────────────────────────▼────────────────────────────┐
│                   Repository Layer                     │
│  - BaseRepository[T], CellRepository,                  │
│    DivisionRepository                                  │
│  - Raw query generation, eager loading (joinedload),   │
│    filtering, multi-column sorting, pagination         │
└───────────────────────────┬────────────────────────────┘
                            │ SQLAlchemy 2.0 ORM
┌───────────────────────────▼────────────────────────────┐
│                 Database Engine Layer                  │
│  - PostgreSQL 16 (Production) / SQLite (Development)   │
│  - Alembic Versioned Migrations                        │
│  - Foreign Keys, Cascade Deletion, Check Constraints   │
└────────────────────────────────────────────────────────┘
```

### Directory Structure
```
cell_division_timer_fastapi/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py    # Baseline migration
│   ├── env.py                       # Migration runner
│   └── script.py.mako               # Template
├── alembic.ini                      # Alembic configuration
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── analytics.py         # Statistical & kinetics endpoints
│   │   │   ├── cells.py             # Biological cell sample CRUD
│   │   │   ├── data_transfer.py     # CSV streaming import/export
│   │   │   ├── divisions.py         # Observation records CRUD & filters
│   │   │   └── health.py            # System & DB connectivity probe
│   │   ├── deps.py                  # Service dependencies
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py                # Pydantic Settings & environment vars
│   │   ├── database.py              # Engine, SessionLocal, Base
│   │   └── logging.py               # Loguru structured logging
│   ├── models/
│   │   ├── base.py                  # TimestampedBase model
│   │   ├── cell.py                  # Cell SQLAlchemy entity
│   │   └── division.py              # CellDivisionRecord SQLAlchemy entity
│   ├── repositories/
│   │   ├── base.py                  # Generic BaseRepository[ModelType]
│   │   ├── cell_repository.py       # Cell data access & lineage counts
│   │   └── division_repository.py   # Division queries, filters, eager loads
│   ├── schemas/
│   │   ├── analytics.py             # MetricStatistics, summaries, aggregations
│   │   ├── cell.py                  # CellCreate, CellUpdate, CellResponse
│   │   ├── common.py                # HealthResponse, ErrorResponse
│   │   └── division.py              # CellDivisionCreate, CellDivisionResponse
│   ├── services/
│   │   ├── analytics_service.py     # Statistical distributions & batch QC
│   │   ├── cell_service.py          # Cell business operations
│   │   ├── csv_service.py           # Bulk CSV parser & exporter
│   │   └── division_service.py      # Division kinetics & biological validation
│   ├── utils/
│   │   ├── biology.py               # Kinetic formulas, outlier thresholds
│   │   └── pagination.py            # PaginationParams & PaginatedResponse
│   ├── main.py                      # FastAPI application bootstrap
│   └── seed.py                      # Deterministic 100-record synthetic seeder
├── data/
│   ├── synthetic_cell_divisions_100.csv
│   └── synthetic_cell_divisions_100.json
├── output/
│   └── cell_division_export.csv
├── scripts/
│   ├── export_data.py               # CLI tool to export database to CSV
│   └── seed.py                      # CLI tool to populate database
├── tests/
│   ├── conftest.py                  # In-memory SQLite fixtures & TestClient
│   ├── test_analytics.py            # Analytics routes test suite
│   ├── test_biology.py              # Biology mathematical formulas tests
│   ├── test_cells.py                # Cell sample CRUD tests
│   ├── test_csv.py                  # CSV import/export tests
│   ├── test_divisions.py            # Division CRUD, filters, sorting tests
│   ├── test_health.py               # Health probe tests
│   ├── test_seed.py                 # Seeding verification tests
│   └── test_validation.py           # Pydantic validation failure tests
├── .env.example                     # Environment configuration template
├── .gitignore                       # Clean Git rules
├── docker-compose.yml               # Multi-container Compose (App + PostgreSQL)
├── Dockerfile                       # Multi-stage production container build
├── requirements.txt                 # Pinned dependencies
└── README.md                        # Comprehensive system documentation
```

---

## Data Models & Schema Design

### 1. `cells` Table
Represents the parent biological specimen or immortalized cell line.
- `id` (VARCHAR(64), Primary Key): Unique laboratory identifier (e.g. `CELL-SC-001`).
- `name` (VARCHAR(128), Indexed): Descriptive line name.
- `organism` (VARCHAR(128), Indexed): Taxonomic species name (*Saccharomyces cerevisiae*, *Escherichia coli*, *Homo sapiens*, etc.).
- `cell_type` (VARCHAR(128), Indexed): Morphological or tissue class (e.g. `Budding yeast`, `Epithelial adenocarcinoma`).
- `passage_number` (INTEGER, Optional): Culture passage generation.
- `source_line` (VARCHAR(128), Optional): Repository accession (e.g. ATCC / DSMZ identifier).
- `description` (TEXT, Optional): Protocol or genotype context.
- `created_at` / `updated_at` (TIMESTAMPTZ): Audit trail.

### 2. `cell_division_records` Table
Individual time-lapse mitosis / cytokinesis observation events.
- `id` (INTEGER, Primary Key, Autoincrement): Synthetic observation surrogate key.
- `cell_id` (VARCHAR(64), Foreign Key $\rightarrow$ `cells.id` ON DELETE CASCADE, Indexed).
- `experimental_batch` (VARCHAR(64), Indexed): Experimental cohort ID (e.g. `BATCH-2024-Q1`).
- `replicate` (INTEGER): Biological or technical replicate index (1, 2, 3...).
- `experimental_condition` (VARCHAR(128), Indexed): Treatment parameter (e.g. `Control`, `Thermal Stress (+5°C)`).
- `medium` (VARCHAR(128)): Culture media substrate (e.g. `YPD Broth`, `DMEM + 10% FBS`).
- `temperature_celsius` (FLOAT, Indexed): Incubator temperature.
- `generation` (INTEGER, Indexed): Lineage generational index.
- `division_start_time` (TIMESTAMPTZ, Indexed): Onset of mitosis.
- `division_end_time` (TIMESTAMPTZ, Indexed): Completion of cytokinesis.
- `division_duration_minutes` (FLOAT, Indexed): Calculated duration ($T_{end} - T_{start}$).
- `cell_cycle_duration_hours` (FLOAT, Indexed): Complete doubling cycle time.
- `growth_rate` (FLOAT, Indexed): Specific growth rate $\mu = \frac{\ln(2)}{T_d}$.
- `is_outlier` (BOOLEAN, Indexed): Outlier classification flag.
- `quality_flag` (VARCHAR(32), Indexed): Status (`PASS`, `OUTLIER_DURATION_EXCESSIVE`, `OUTLIER_TEMPERATURE_EXTREME`, `SUSPECT_DIVISION_EXCEEDS_CYCLE`).
- `notes` (TEXT, Optional): Microscopist observation notes.
- `metadata_json` (TEXT, Optional): Instrument telemetry (imaging channels, magnification, microscope model).
- `created_at` / `updated_at` (TIMESTAMPTZ): Audit trail.

#### Database Integrity & Constraints
- `ck_division_end_after_start`: `division_end_time >= division_start_time`
- `ck_positive_division_duration`: `division_duration_minutes >= 0`
- `ck_positive_cell_cycle_duration`: `cell_cycle_duration_hours > 0`
- `ck_plausible_temperature`: `temperature_celsius >= -10.0 AND temperature_celsius <= 100.0`
- Composite Index: `ix_divisions_batch_condition (experimental_batch, experimental_condition)`
- Composite Index: `ix_divisions_cell_gen (cell_id, generation)`

---

## Biological Calculations & Kinetic Formulas

All kinetic derivations are implemented in `app.utils.biology`:

### 1. Active Division Duration ($T_{div}$)
$$T_{div} = \frac{t_{end} - t_{start}}{60} \quad [\text{minutes}]$$
Validated to ensure $t_{end} \ge t_{start}$.

### 2. Specific Growth Rate ($\mu$)
For exponentially expanding populations where doubling time $T_d = \text{cell\_cycle\_duration\_hours}$:
$$N(t) = N_0 \cdot 2^{t / T_d} = N_0 \cdot e^{\mu t}$$
$$\mu = \frac{\ln(2)}{T_d} \approx \frac{0.693147}{T_d} \quad [\text{hr}^{-1}]$$

### 3. Biological Reference Ranges & Outlier Detection
The system compares observed kinetic parameters against established biological baselines:
* *Saccharomyces cerevisiae*: Division duration 15–45 min; Cell cycle 1.2–4.5 hr; Normal temperature 22–37°C.
* *Escherichia coli*: Division duration 8–35 min; Cell cycle 0.3–2.0 hr; Normal temperature 25–42°C.
* *Homo sapiens* (Mammalian): Division duration 40–150 min; Cell cycle 14.0–36.0 hr; Normal temperature 35–39°C.
* *Mus musculus* (Murine): Division duration 45–160 min; Cell cycle 12.0–32.0 hr; Normal temperature 35–39°C.

Flagging logic tags measurements as outliers if:
1. Active cytokinesis duration exceeds the entire generation cell cycle ($T_{div} \ge 60 \cdot T_d$).
2. Incubation temperature falls outside physiological limits ($T < 10^\circ\text{C}$ or $T > 50^\circ\text{C}$).
3. Observed division duration exceeds $3.0\times$ typical baseline (indicative of metaphase arrest or mitotic checkpoint failure).

### 4. Descriptive Statistics & Dispersion
For any parameter vector $X = [x_1, \dots, x_n]$:
* **Mean**: $\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i$
* **Median**: 50th percentile (robust to extreme outliers)
* **Sample Standard Deviation**: $s = \sqrt{\frac{1}{n-1}\sum_{i=1}^n (x_i - \bar{x})^2}$
* **Coefficient of Variation**: $CV = \frac{s}{\bar{x}} \times 100\%$

---

## Synthetic Benchmark Dataset

Because wet-lab microscopy datasets are proprietary, the application includes a deterministic generator (`app.seed`) that synthesizes **100 realistic development records**:
* **4 Cell Models**:
  - `CELL-SC-001`: *S. cerevisiae* BY4741 (25 observations)
  - `CELL-EC-001`: *E. coli* K-12 MG1655 (25 observations)
  - `CELL-HELA-001`: HeLa CCL-2 (25 observations)
  - `CELL-NIH3T3-001`: NIH/3T3 Fibroblast (25 observations)
* **5 Experimental Conditions**: Control, Nutrient Depletion (0.1% Glucose), Thermal Stress (+5°C), Rapamycin Inhibition (10 nM), Osmotic Stress (0.4M Sorbitol).
* **4 Batches**: `BATCH-2024-Q1` through `BATCH-2024-Q4`.
* **Replicates & Generations**: Replicates 1–3, Generations 1–5.
* **Deliberate Outliers**: Injects 4 biologically characterized outlier records (e.g. mitotic spindle arrest, thermal heat shock, rapid fragmentation) to validate outlier detection and QC alerts.

All synthetic data is exported into:
- `data/synthetic_cell_divisions_100.csv`
- `data/synthetic_cell_divisions_100.json`

---

## API Versioning & Header-Based Routing

The platform employs a hybrid **Path + Header-Based Versioning Architecture** managed by an ASGI `APIVersioningMiddleware` (`app.core.middleware`):

### Supported Routing Mechanisms
1. **Explicit Path Prefix**:
   - Production Stable: `/api/v1/...`
   - Future Beta: `/api/v2/...`
2. **Header-Based Routing for Unversioned Paths**:
   Clients issuing requests to unversioned `/api/...` endpoints (e.g. `GET /api/divisions`) are dynamically routed based on headers or query parameters:
   - Header: `X-API-Version: 1` (routes to v1) or `X-API-Version: 2` / `X-API-Version: 2-beta` (routes to v2 beta).
   - Vendor Accept Header: `Accept: application/vnd.celldivision.v2+json`.
   - Query Parameter: `?api-version=2`.
   - Fallback Default: Defaults to `v1` (Stable Production) if unversioned and no version header is present.
3. **Response Lifecycle Headers**:
   Every response includes lifecycle transparency metadata:
   - `X-API-Version`: `v1` or `v2-beta`
   - `X-API-Lifecycle`: `stable` (for v1) or `beta` (for v2)
   - `X-API-Warning`: Injected on v2 requests alerting consumers of experimental preview status.
   - `Vary: X-API-Version, Accept` for caching proxies.
4. **Unsupported Version Protection**:
   Explicit requests for unsupported versions (e.g. `X-API-Version: 99`) are rejected with `400 Bad Request` containing supported versions list and default fallback instructions.

---

## API Specification & Endpoints

Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.  
Alternative ReDoc documentation is available at `http://localhost:8000/redoc`.

### Route Structure: v1 (Stable Production) vs. v2 (Beta Preview)

| Method | Endpoint | Version | Description |
|---|---|---|---|
| `GET` | `/health` | Core | System and DB connectivity probe (returns latency) |
| `GET` | `/` | Core | Root service metadata and version directory |
| **v2 Beta Lifecycle** | | | |
| `GET` | `/api/v2/beta/status` | `v2-beta` | Roadmap, active features, changelog, backward compatibility |
| **Cells & Lineages** | | | |
| `POST` | `/api/v1/cells` | `v1` | Register new cell sample or lineage |
| `GET` | `/api/v1/cells` | `v1` | List cell samples with pagination and filters |
| `GET` | `/api/v1/cells/{id}` | `v1` | Get cell sample and division observation count |
| `PUT` | `/api/v1/cells/{id}` | `v1` | Update cell metadata |
| `DELETE` | `/api/v1/cells/{id}` | `v1` | Delete cell sample (cascades to divisions) |
| **Divisions & Kinetics** | | | |
| `POST` | `/api/v1/divisions` | `v1` | Record observation (auto-computes duration and μ) |
| `GET` | `/api/v1/divisions` | `v1` | Multi-attribute search, filters, pagination, sort |
| `GET` | `/api/v1/divisions/{id}` | `v1` | Get single division observation record |
| `PUT` | `/api/v1/divisions/{id}` | `v1` | Update record (recalculates affected kinetics) |
| `DELETE` | `/api/v1/divisions/{id}` | `v1` | Delete observation record |
| `GET` | `/api/v2/divisions` | `v2-beta` | Enhanced with subphase timing & SAC arrest scoring |
| `POST` | `/api/v2/divisions/batch-analyze`| `v2-beta` | Bulk kinetic profiler with population distributions |
| **Analytics & Modeling** | | | |
| `GET` | `/api/v1/analytics/summary` | `v1` | Overarching statistical kinetics summary |
| `GET` | `/api/v1/analytics/by-cell-type` | `v1` | Kinetics stratified by morphological cell type |
| `GET` | `/api/v1/analytics/by-condition` | `v1` | Kinetics stratified by media/chemical condition |
| `GET` | `/api/v1/analytics/by-temperature`| `v1` | Kinetics stratified by incubation temperature |
| `GET` | `/api/v1/analytics/by-generation` | `v1` | Replicative timing shifts across generations |
| `GET` | `/api/v1/analytics/batches` | `v1` | Batch QC, replicate distribution, outlier rates |
| `GET` | `/api/v2/analytics/predictive-kinetics`| `v2-beta` | Arrhenius Q10 temperature coefficient modeling |
| `GET` | `/api/v2/analytics/mitotic-phases` | `v2-beta` | Mitotic subphase global breakdown (pro/meta/ana/telo) |
| **Data Transfer** | | | |
| `GET` | `/api/v1/data/export/csv` | `v1` | Download complete dataset as CSV |
| `POST` | `/api/v1/data/import/csv` | `v1` | Batch upload CSV records (auto-creates cells) |

### Header-Based Routing Examples

```bash
# 1. Access v2 Beta using standard unversioned URL with header
curl -X GET http://localhost:8000/api/divisions \
  -H "X-API-Version: 2"

# 2. Access v2 Beta using content negotiation (vendor MIME)
curl -X GET http://localhost:8000/api/divisions \
  -H "Accept: application/vnd.celldivision.v2+json"

# 3. Access v1 Stable with explicit header
curl -X GET http://localhost:8000/api/divisions \
  -H "X-API-Version: 1"

# 4. Attempting an unsupported version returns 400 Bad Request
curl -i -X GET http://localhost:8000/api/divisions \
  -H "X-API-Version: 99"
# Response: HTTP/1.1 400 Bad Request
# {"detail": "Unsupported API version '99'. Supported versions: v1, v2-beta.", ...}
```

---

## Installation & Local Setup

### Prerequisites
- Python 3.11+
- Virtualenv
- SQLite (built-in) or PostgreSQL 14+

### Quickstart
```bash
# 1. Clone repository and navigate to root
cd cell_division_timer_fastapi

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env

# 5. Apply database migrations
alembic upgrade head

# 6. Seed 100 synthetic benchmark records
python3 scripts/seed.py

# 7. Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Database Migrations (Alembic)

```bash
# Apply all pending migrations to database
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate a new migration script from SQLAlchemy models
alembic revision --autogenerate -m "add_custom_microscopy_fields"

# View current migration state
alembic current
```

---

## Database Seeding

To idempotently seed or reset the database with the 100 benchmark records:
```bash
# Safe idempotent seed (skips if already populated)
python3 scripts/seed.py

# Force reset and reseed
python3 scripts/seed.py --force
```

---

## Automated Testing

The project maintains a comprehensive `pytest` test suite configured with an isolated in-memory SQLite database (`sqlite:///:memory:`) using `StaticPool`.

```bash
# Run all tests with verbose output
pytest -v

# Run specific test module
pytest tests/test_divisions.py -v

# Run with test coverage report
pytest --cov=app tests/
```

### Test Coverage Highlights
- **Health & DB**: Database connection latency and service discovery.
- **Lineage Integrity**: Sample creation, 409 conflict handling, cascaded deletion.
- **Kinetics Calculations**: Automated division duration, growth rate $\mu = \ln(2)/T_d$.
- **Validation**: Negative duration rejection, end before start timestamps, extreme thermal bounds.
- **Analytical Engines**: Distributions, CV calculations, batch outlier rate tracking.
- **Data Exchange**: CSV streaming export and batch parser import.
- **Seeding Verification**: 100-record dataset generation, biological plausibility, idempotency.

---

## Containerization & Docker Deployment

### Run with Docker Compose (FastAPI + PostgreSQL)
```bash
# Launch PostgreSQL 16 and FastAPI application
docker compose up --build -d

# View live logs
docker compose logs -f api

# Execute migrations inside container
docker compose exec api alembic upgrade head

# Seed synthetic dataset
docker compose exec api python3 scripts/seed.py

# Shutdown stack
docker compose down
```

### Standalone Docker Container
```bash
docker build -t cell-division-timer:latest .
docker run -p 8000:8000 --env DATABASE_URL=sqlite:///./cell_division.db cell-division-timer:latest
```

---

## Production Readiness & Life-Sciences Extensibility

### Industry Readiness Checklist
- [x] **Layered Architecture**: Absolute separation between API routers, Service domain managers, Repositories, and Database entities.
- [x] **Validation & Integrity**: Pydantic V2 schemas with custom model validators and relational database Check Constraints.
- [x] **Automated Biological Derivation**: Division duration and exponential growth kinetics computed automatically from raw timestamps and doubling times.
- [x] **Auditing & Traceability**: Automated `created_at` and `updated_at` timestamps on all entities.
- [x] **Quality Control & Outliers**: Automated flagging of spindle arrests and thermal stress conditions.
- [x] **Multi-Database Support**: Tested seamlessly with SQLite for development and PostgreSQL for enterprise production.
- [x] **Modern Asynchronous Stack**: Built on FastAPI with asynchronous lifespan lifecycle handlers and connection pool optimization.

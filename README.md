# Sheets to PostgreSQL Migration

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-30%2B%20passing-brightgreen.svg)](#running-tests)

Production ETL pipeline for migrating business data from Google Sheets to PostgreSQL with data cleaning, validation, and reconciliation.

---

## Pipeline Architecture

```mermaid
flowchart LR
    A[Google Sheets] -->|Extract| B[Raw Data]
    B -->|Clean| C[Cleaned Data]
    C -->|Validate| D{Pass?}
    D -->|Yes| E[PostgreSQL]
    D -->|No| F[Error Report]
    E -->|Reconcile| G[Verification Report]

    style A fill:#4285F4,color:#fff
    style E fill:#336791,color:#fff
    style D fill:#FFA500,color:#fff
    style G fill:#34A853,color:#fff
```

### Phases

| Phase | Description | Key Feature |
|-------|-------------|-------------|
| **Extract** | Read from Google Sheets API v4 | Auto-pagination for 1000+ rows, rate limiting |
| **Clean** | Normalize data types and encoding | Multi-format price/date parsing, unicode normalization |
| **Validate** | Apply business rules per row | 7 rule types, cross-row uniqueness checks |
| **Load** | Batch insert/upsert into PostgreSQL | Configurable batch size, ON CONFLICT support |
| **Reconcile** | Verify migration integrity | Count checks, row checksums, numeric sum comparison |

## Design Decisions

- **Configurable column mappings** via JSON — no code changes needed for new sheets
- **Fail threshold** — pipeline tolerates a configurable percentage of validation failures before aborting
- **Dry-run mode** — runs Extract → Clean → Validate without touching the database
- **Resume support** — restart from any failed phase without re-processing earlier ones
- **Batch processing** — memory-efficient loading with configurable batch sizes

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Google credentials and PostgreSQL connection
```

### 3. Set up Google Sheets API credentials

Place your `credentials.json` service account key in the project root.

### 4. Configure column mappings

Edit `config/column_mappings.json` to map your sheet columns to database columns:

```json
{
  "mappings": [
    {
      "source": "Nombre del Producto",
      "target": "product_name",
      "operation": "rename",
      "db_type": "text"
    }
  ]
}
```

### 5. Run the pipeline

```python
from src.pipeline.orchestrator import MigrationPipeline, PipelineConfig

config = PipelineConfig(
    spreadsheet_id="your-sheet-id",
    sheet_name="Sheet1",
    table_name="products",
    column_mappings_path="config/column_mappings.json",
    pg_dsn="postgresql://user:pass@localhost/db",
)

pipeline = MigrationPipeline()
results = pipeline.run(config)

for r in results:
    print(f"{r.phase.value}: {'OK' if r.success else 'FAIL'} ({r.duration_secs}s)")
```

### Dry-Run Mode

```python
config.dry_run = True
results = pipeline.run(config)  # skips LOAD phase
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All tests use `unittest.mock` — no Google API credentials or PostgreSQL connection required.

## Project Structure

```
sheets-to-postgres-migration/
├── src/
│   ├── extract/          # Google Sheets API reader
│   ├── transform/        # Cleaners, validators, column mappers
│   ├── load/             # PostgreSQL batch loader
│   ├── reconcile/        # Post-migration verification
│   └── pipeline/         # 5-phase orchestrator
├── tests/                # 30+ unit tests with mocks
├── config/               # Column mappings & validation rules
├── .env.example
├── requirements.txt
└── README.md
```

## Related Projects

- [manifest-csv-importer](https://github.com/AspiranteD/manifest-csv-importer) — CSV manifest processing pipeline
- [reusalia-backend](https://github.com/AspiranteD/reusalia-backend) — FastAPI backend for product management

## License

MIT

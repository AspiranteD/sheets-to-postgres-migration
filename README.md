# Sheets to PostgreSQL Migration
> **Portfolio context:** Extracted from founder-led production systems — multi-marketplace inventory, orders, and warehouse execution. **[Full portfolio](https://github.com/AspiranteD/AspiranteD)** · [aspiranted.github.io](https://aspiranted.github.io)

Production migration pipeline that transferred 10,000+ inventory items, sales, cash transactions, and incidents from a Google Sheets-based ERP to PostgreSQL with full data validation and reporting.

## Architecture

```
src/
+-- config/
¦   +-- mappings.py      # Value maps, column mappings, null sets, migration order
¦   +-- settings.py      # Sheet names and defaults
+-- transform/
¦   +-- cleaners.py      # Data cleaning, type conversion, status mapping
¦   +-- resolvers.py     # FK resolution with alias support
+-- validate/
¦   +-- row_validators.py  # Per-table validation rules
+-- report/
    +-- markdown_report.py  # 3-phase report generation
```

## Key Technical Features

### Data Cleaning (`src/transform/cleaners.py`)

Handles real-world messy spreadsheet data:

- **Price normalization**: detects European (1.234,56) vs American (1,234.56) format, strips €/EUR/$, handles comma-as-decimal
- **Weight parsing**: extracts numeric values from "1.5kg", "500g"
- **Null detection**: configurable set of null-equivalent values ("", "-", "n/a", "null", "sin datos", etc.)
- **Date parsing**: 8 format variants (YYYY-MM-DD, DD/MM/YYYY, DD/MM/YY, etc.) with sanity check (year 2020-2030)
- **Condition mapping**: free-text ("perfecto", "con tara", "para piezas") to FK integers
- **Available logic**: inverted boolean (VENDIDO?=TRUE means available=FALSE)
- **Do-not-list detection**: accent-insensitive, whitespace-insensitive comparison for "No se anuncia"
- **Incident action parsing**: dual mode - numeric values become discount amounts, text values map to incident types
- **Resolution inference**: keyword matching on solution text to categorize resolution types

### FK Resolvers (`src/transform/resolvers.py`)

Map free-text values to database foreign keys:

- **Employee resolver**: direct lookup + alias chain (e.g., "liu" -> "jose" -> employee_id). Handles accent variants ("jose"/"josé")
- **Truckload resolver**: text A2Z ID to numeric FK with alias support (e.g., "reg-paolita" -> "REG")
- **Payment method**: text ("wallapop") -> code ("PLATAFORMA") -> method_id
- **Payment status**: text with default fallback ("PAGADO")
- **Platform account**: supports both numeric IDs and text names

### Row Validators (`src/validate/row_validators.py`)

Per-table validation rules matching PostgreSQL CHECK constraints:

- **physical_item**: PK uniqueness (against existing DB), NOT NULL (LPN, ASIN), condition_id range (1-5), numeric type checks, FK resolution verification
- **listing**: FK existence, title presence, price type check
- **sale**: FK existence, final_price NOT NULL + type check
- **cash_transaction**: transaction_type enum, amount NOT NULL, all FK resolutions verified
- **incident**: sale_id FK, incident_type and status against valid enum sets, description NOT NULL

### Report Generation (`src/report/markdown_report.py`)

Structured Markdown reports for each migration phase:

- **Phase 1 (Analysis)**: sheet structure, column types, null percentages, detected problems (truncated at 50)
- **Phase 2 (Validation)**: valid/transformed/critical/skipped counts per table, error details with row+LPN reference
- **Phase 3 (Migration)**: inserted/skipped/errors per table, dry-run vs live mode, target environment tagging

### Column Mappings (`src/config/mappings.py`)

Per-sheet column name mappings (Sheet header -> DB field):
- **Inventario**: 26 columns including special prefixed columns (`_pvp`, `_precio_revisado`) for derived fields
- **Caja**: 8 columns for cash transactions
- **Incidencias**: 8 columns for post-sale incidents
- **Migration order**: respects FK dependencies (physical_item -> listing -> sale -> cash_transaction -> incident)

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

**164 tests** covering:
- Cleaners (null handling, price formats, weights, conditions, dates, incidents, resolutions)
- Resolvers (employees with aliases, truckloads, payment methods/statuses, platform accounts)
- Validators (all 5 table validators, valid/invalid scenarios, FK verification)
- Reports (all 3 phases, truncation, multi-table, dry-run/live modes)

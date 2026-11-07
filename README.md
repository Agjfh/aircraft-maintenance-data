# Aircraft Maintenance Data – Airbus A320

Dataset repository for an aircraft-maintenance graduation project. It includes a SQLite database, synthetic A320 fleet records, NASA C-MAPSS turbofan data, FAA Service Difficulty Reports, processed ML datasets, and baseline ML scripts.

## Repository structure

- `db/`: SQLite database, SQL schema, seed script, and example queries.
- `data/raw/`: source datasets. The A320 fleet sample is synthetic; NASA C-MAPSS is a generic turbofan simulation and is not specific to an A320 engine; FAA SDR reports are historical safety reports.
- `data/processed/`: prepared C-MAPSS and SDR datasets for model training and evaluation.
- `ml/`: baseline remaining-useful-life (RUL) and SDR classification scripts.
- `DATA_SOURCES.md`: dataset sources, licensing notes, and important caveats.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the example SQL queries with SQLite:

```bash
sqlite3 db/a320_maintenance.db < db/queries.sql
```

Rebuild the database from the CSV files:

```bash
python db/seed.py
```

Run baseline models:

```bash
python ml/rul_baseline.py FD001
python ml/sdr_classifier.py hazard_binary
```

Read `DATA_SOURCES.md` before citing or presenting the datasets. In particular, do not describe synthetic A320 records as real operational data, and do not describe NASA C-MAPSS as A320-specific.

## Using raw GitHub files in code

Raw file URL pattern:

```text
https://raw.githubusercontent.com/Agjfh/aircraft-maintenance-data/main/<path>
```

Example (Python) — currently uploaded A320 CSV files:

```python
import pandas as pd

BASE = "https://raw.githubusercontent.com/Agjfh/aircraft-maintenance-data/main"

aircraft = pd.read_csv(f"{BASE}/data/raw/a320_synthetic/aircraft.csv")
engines = pd.read_csv(f"{BASE}/data/raw/a320_synthetic/engines.csv")
parts = pd.read_csv(f"{BASE}/data/raw/a320_synthetic/parts_inventory.csv")
technicians = pd.read_csv(f"{BASE}/data/raw/a320_synthetic/technicians.csv")
```

## Current upload status

The repository currently contains the project documentation, SQL scripts, ML baseline scripts, and the four A320 CSV files listed above. The original ZIP also contains larger datasets and binary files (including sensor readings, FAA/NASA datasets, and the SQLite database) that are not yet uploaded. Do not use a Raw URL for a file until that file appears in the repository.

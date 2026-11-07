# Aircraft Maintenance Data – Airbus A320 Graduation Project

Public data repository for an aircraft-maintenance graduation project. The repository currently contains a usable subset of the original ZIP archive. Some large source files are still not present; see **Upload status and limitations** below.

## Repository contents

### Synthetic A320 maintenance data

Folder: `data/raw/a320_synthetic/`

| File | Description |
|---|---|
| `aircraft.csv` | Aircraft / fleet records |
| `engines.csv` | Engine assignments and health indicators |
| `parts_inventory.csv` | Spare-parts inventory |
| `technicians.csv` | Technician records |
| `maintenance_schedule.csv` | Maintenance schedule |
| `defect_reports_part1.csv` to `defect_reports_part3.csv` | 500 defect-report rows, split into three files |
| `work_orders_part1.csv` to `work_orders_part4.csv` | 500 work-order rows, split into four files |

The synthetic A320 records are generated for this project and are **not real airline operational records**. Maintenance intervals are illustrative and are not official Airbus MPD data.

### NASA C-MAPSS labels

Folder: `data/raw/nasa_cmapss/`

The repository includes the NASA source readme and the RUL label files for FD001–FD004 as regular CSV files. The full train/test sensor trajectory archives are **not uploaded yet**. C-MAPSS is a turbofan simulation and is not specific to an A320 engine.

### SQL and machine-learning code

- `db/schema.sql`, `db/queries.sql`, `db/seed.py`: SQL schema, example queries and database seeding script.
- `ml/rul_baseline.py`, `ml/sdr_classifier.py`: baseline model scripts.
- `data/load_remote_data.py`: Python helper for downloading and combining the currently published A320 CSV files.

## Load the published data from Python

Install the dependency:

```bash
pip install pandas
```

Then run:

```python
from data.load_remote_data import load_project_data

tables = load_project_data()

aircraft = tables["aircraft"]
engines = tables["engines"]
defects = tables["defects"]
work_orders = tables["work_orders"]
maintenance_schedule = tables["maintenance_schedule"]

print(len(aircraft), len(defects), len(work_orders))
```

You can also read an individual file using its Raw URL:

```python
import pandas as pd

url = (
    "https://raw.githubusercontent.com/Agjfh/"
    "aircraft-maintenance-data/main/"
    "data/raw/a320_synthetic/aircraft.csv"
)
aircraft = pd.read_csv(url)
```

## Upload status and limitations

Uploaded and verified: the seven A320 data groups listed above (aircraft, engines, inventory, technicians, schedule, defects, and work orders), the four NASA RUL label CSVs, the C-MAPSS metadata file, project documentation, SQL scripts, and ML baseline scripts.

Still not uploaded from the original ZIP: the complete engine sensor readings CSV, the full FAA SDR report CSV, the full NASA C-MAPSS train/test trajectory archives, the processed SDR and C-MAPSS training datasets, the extra unverified flight-operations CSV, and the SQLite database file. Their larger sizes or binary format could not be transferred through the currently available GitHub file-writing interface. **Do not assume these missing files are available through Raw URLs.**

## Data source and academic-use notes

Read `DATA_SOURCES.md` before using or citing the data. In particular:
- A320 fleet / maintenance / defects / work orders are synthetic.
- NASA C-MAPSS represents simulated turbofan degradation, not A320-specific engine data.
- The extra flight-operations CSV is marked unverified in the original dataset.
- Do not use this dataset or the example models as a substitute for approved aircraft maintenance data or procedures.

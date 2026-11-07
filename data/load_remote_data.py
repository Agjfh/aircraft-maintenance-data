"""Load the A320 project CSV files that are currently published in this repository.

The synthetic defect-report table is split into three CSV chunks so that each
file remains manageable through the GitHub upload interface. This loader
combines those chunks into one DataFrame.
"""
from __future__ import annotations

import pandas as pd

BASE_URL = (
    "https://raw.githubusercontent.com/Agjfh/"
    "aircraft-maintenance-data/main"
)


def read_remote_csv(relative_path: str) -> pd.DataFrame:
    """Download one published CSV from GitHub Raw."""
    url = f"{BASE_URL}/{relative_path}"
    return pd.read_csv(url)


def load_project_data() -> dict[str, pd.DataFrame]:
    root = "data/raw/a320_synthetic"

    aircraft = read_remote_csv(f"{root}/aircraft.csv")
    engines = read_remote_csv(f"{root}/engines.csv")
    parts = read_remote_csv(f"{root}/parts_inventory.csv")
    technicians = read_remote_csv(f"{root}/technicians.csv")
    maintenance_schedule = read_remote_csv(f"{root}/maintenance_schedule.csv")

    defect_files = [
        f"{root}/defect_reports_part1.csv",
        f"{root}/defect_reports_part2.csv",
        f"{root}/defect_reports_part3.csv",
    ]
    defects = pd.concat(
        [read_remote_csv(path) for path in defect_files],
        ignore_index=True,
    )

    return {
        "aircraft": aircraft,
        "engines": engines,
        "parts": parts,
        "technicians": technicians,
        "maintenance_schedule": maintenance_schedule,
        "defects": defects,
    }


if __name__ == "__main__":
    tables = load_project_data()
    for table_name, frame in tables.items():
        print(f"{table_name}: {len(frame):,} rows")

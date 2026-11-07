"""Load the A320 project CSV files published in this repository.

Large tables are split into numbered CSV parts. Each part repeats its header;
this module concatenates the parts into one pandas DataFrame.
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


def read_csv_parts(root: str, stem: str, count: int) -> pd.DataFrame:
    """Read numbered CSV chunks and combine them into one DataFrame."""
    frames = [
        read_remote_csv(f"{root}/{stem}_part{part}.csv")
        for part in range(1, count + 1)
    ]
    return pd.concat(frames, ignore_index=True)


def load_project_data() -> dict[str, pd.DataFrame]:
    root = "data/raw/a320_synthetic"

    return {
        "aircraft": read_remote_csv(f"{root}/aircraft.csv"),
        "engines": read_remote_csv(f"{root}/engines.csv"),
        "parts": read_remote_csv(f"{root}/parts_inventory.csv"),
        "technicians": read_remote_csv(f"{root}/technicians.csv"),
        "maintenance_schedule": read_remote_csv(
            f"{root}/maintenance_schedule.csv"
        ),
        "defects": read_csv_parts(root, "defect_reports", 3),
        "work_orders": read_csv_parts(root, "work_orders", 4),
    }


if __name__ == "__main__":
    for name, frame in load_project_data().items():
        print(f"{name}: {len(frame):,} rows")

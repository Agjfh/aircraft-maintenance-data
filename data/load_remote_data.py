"""Download the published project datasets from GitHub Raw."""
from __future__ import annotations
import pandas as pd

BASE = "https://raw.githubusercontent.com/Agjfh/aircraft-maintenance-data/main"


def read_csv(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(f"{BASE}/{path}", **kwargs)


def load_a320_data() -> dict[str, pd.DataFrame]:
    root = "data/raw/a320_synthetic"
    return {
        "aircraft": read_csv(f"{root}/aircraft.csv"),
        "engines": read_csv(f"{root}/engines.csv"),
        "defects": read_csv(f"{root}/defect_reports.csv"),
        "work_orders": read_csv(f"{root}/work_orders.csv"),
        "parts": read_csv(f"{root}/parts_inventory.csv"),
        "technicians": read_csv(f"{root}/technicians.csv"),
        "maintenance_schedule": read_csv(f"{root}/maintenance_schedule.csv"),
        "engine_sensor_data": read_csv(f"{root}/engine_sensor_data.csv"),
        "symptoms": read_csv(f"{root}/symptoms.csv"),
        "fault_catalog": read_csv(f"{root}/fault_catalog.csv"),
        "fault_symptoms": read_csv(f"{root}/fault_symptoms.csv"),
        "defect_symptoms": read_csv(f"{root}/defect_symptoms.csv"),
        "component_status": read_csv(f"{root}/component_status.csv"),
    }


def load_nasa_cmapss(split: str, subset: str) -> pd.DataFrame:
    """Load a gzipped NASA C-MAPSS CSV; e.g. split='train', subset='FD001'."""
    if split not in {"train", "test", "RUL"} or subset not in {"FD001", "FD002", "FD003", "FD004"}:
        raise ValueError("Use split train/test/RUL and subset FD001/FD002/FD003/FD004")
    suffix = f"{split}_{subset}.csv.gz" if split != "RUL" else f"RUL_{subset}.csv.gz"
    return read_csv(f"data/raw/nasa_cmapss/{suffix}", compression="gzip", header=None)


if __name__ == "__main__":
    for name, frame in load_a320_data().items():
        print(f"{name}: {len(frame):,} rows")

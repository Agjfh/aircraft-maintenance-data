"""Rebuild the SQLite database from schema.sql + CSV files. Usage: python db/seed.py"""
import sqlite3
import os
import pandas as pd

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
out = "db/a320_maintenance.db"
if os.path.exists(out):
    os.remove(out)

con = sqlite3.connect(out)
con.executescript(open("db/schema.sql").read())
for table in ["aircraft", "engines", "technicians", "parts_inventory", "maintenance_schedule", "defect_reports", "work_orders", "engine_sensor_data"]:
    pd.read_csv(f"data/raw/a320_synthetic/{table}.csv").to_sql(table, con, if_exists="append", index=False)

sdr = pd.read_csv("data/raw/faa_sdr/faa_sdr_all_reports.csv")
sdr["source_id"] = pd.to_numeric(sdr["source_id"], errors="coerce")
cols = ["sdr_id", "source_id", "hazard_category", "is_hazard", "report_text", "part_name", "part_condition", "nature_of_condition", "is_a320", "ata_chapter", "ata_system"]
sdr[cols].to_sql("faa_sdr_reports", con, if_exists="append", index=False)
con.commit()
con.close()
print("done ->", out)

"""Baseline: predict Remaining Useful Life (RUL) of turbofan engines from NASA C-MAPSS.
Usage: python ml/rul_baseline.py FD001
Train on every cycle (target = rul_clipped, capped at 125), evaluate on the LAST cycle of each test engine
against the true RUL provided by NASA (standard C-MAPSS evaluation)."""
import sys
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

fd = sys.argv[1] if len(sys.argv) > 1 else "FD001"
directory = "data/processed/cmapss/"
feats = json.load(open(directory + "meta.json"))[fd]["kept_sensors"]

def add_rolling(df, window=10):
    df = df.sort_values(["engine_id", "cycle"]).copy()
    for col in feats:
        df[col + "_mean"] = df.groupby("engine_id")[col].transform(lambda s: s.rolling(window, min_periods=1).mean())
    return df

train = add_rolling(pd.read_csv(directory + f"{fd}_train.csv.gz"))
test_full = add_rolling(pd.read_csv(directory + f"{fd}_test.csv.gz"))
last = pd.read_csv(directory + f"{fd}_test_last_cycle_with_true_rul.csv.gz")[["engine_id", "true_rul_at_last_cycle"]]
test = test_full.groupby("engine_id").tail(1).merge(last, on="engine_id")
features = [c for c in train.columns if c in feats or c.endswith("_mean")] + ["cycle"]
model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0).fit(train[features], train["rul_clipped"])
pred = np.clip(model.predict(test[features]), 0, 125)
actual = test["true_rul_at_last_cycle"].clip(upper=125)
print(f"{fd} RMSE={mean_squared_error(actual, pred) ** 0.5:.2f} MAE={mean_absolute_error(actual, pred):.2f} (test engines: {len(test)})")

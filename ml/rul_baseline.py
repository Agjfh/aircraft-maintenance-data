"""Baseline: predict Remaining Useful Life (RUL) of turbofan engines from NASA C-MAPSS.
Usage: python ml/rul_baseline.py FD001
Train on every cycle (target = rul_clipped, capped at 125), evaluate on the LAST cycle of each test engine
against the true RUL provided by NASA (standard C-MAPSS evaluation)."""
import sys, json, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
fd = sys.argv[1] if len(sys.argv) > 1 else "FD001"
D = "data/processed/cmapss/"
feats = json.load(open(D + "meta.json"))[fd]["kept_sensors"]

def add_rolling(df, w=10):
    df = df.sort_values(["engine_id", "cycle"]).copy()
    for c in feats:
        df[c + "_mean"] = df.groupby("engine_id")[c].transform(lambda s: s.rolling(w, min_periods=1).mean())
    return df

tr = add_rolling(pd.read_csv(D + f"{fd}_train.csv.gz"))
te_full = add_rolling(pd.read_csv(D + f"{fd}_test.csv.gz"))
last = pd.read_csv(D + f"{fd}_test_last_cycle_with_true_rul.csv.gz")[["engine_id", "true_rul_at_last_cycle"]]
te = te_full.groupby("engine_id").tail(1).merge(last, on="engine_id")
X = [c for c in tr.columns if c in feats or c.endswith("_mean")] + ["cycle"]
m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0).fit(tr[X], tr["rul_clipped"])
pred = np.clip(m.predict(te[X]), 0, 125)
y = te["true_rul_at_last_cycle"].clip(upper=125)
print(f"{fd}  RMSE={mean_squared_error(y, pred) ** 0.5:.2f}  MAE={mean_absolute_error(y, pred):.2f}  (test engines: {len(te)})")

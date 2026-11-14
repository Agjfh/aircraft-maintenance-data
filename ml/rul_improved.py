"""Improved RUL model for NASA C-MAPSS turbofan engines (scikit-learn only, no deep-learning framework).

Compared with ml/rul_baseline.py it adds:
  - per-operating-condition normalisation of each kept sensor (FD002/FD004 have 6 operating
    conditions; a sensor reading only means something relative to its own condition).
    The mean/std per condition come from the TRAINING set only and are applied to test rows.
  - per kept sensor: rolling mean (10 and 30 cycles), rolling std (10), change over the last
    5 and 20 cycles (degradation trend)
  - the cycle index
(An earlier version also added each engine's first-cycle reading. It helped FD001/FD003 but hurt
FD002/FD004, so it was removed: it lets the model memorise each engine's identity.)
Evaluation is the same as the baseline: train on every cycle (target = rul_clipped, capped at 125),
test on the LAST cycle of each test engine against NASA's true RUL (capped at 125).

Usage: python ml/rul_improved.py FD001
"""
import sys, json
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

fd = sys.argv[1] if len(sys.argv) > 1 else "FD001"
D = "data/processed/cmapss/"
feats = json.load(open(D + "meta.json"))[fd]["kept_sensors"]

tr_raw = pd.read_csv(D + f"{fd}_train.csv.gz")
te_raw = pd.read_csv(D + f"{fd}_test.csv.gz")
last = pd.read_csv(D + f"{fd}_test_last_cycle_with_true_rul.csv.gz")[["engine_id", "true_rul_at_last_cycle"]]

# Per-operating-condition standardisation, statistics from training data only.
if "cond" in tr_raw.columns:
    stats = tr_raw.groupby("cond")[feats].agg(["mean", "std"])
    for df in (tr_raw, te_raw):
        for c in feats:
            mu = df["cond"].map(stats[(c, "mean")])
            sd = df["cond"].map(stats[(c, "std")]).replace(0, 1.0).fillna(1.0)
            df[c] = (df[c] - mu) / sd


def add_features(df):
    df = df.sort_values(["engine_id", "cycle"]).reset_index(drop=True)
    g = df.groupby("engine_id")
    cols = {}
    for c in feats:
        s = g[c]
        cols[f"{c}_m10"] = s.transform(lambda x: x.rolling(10, min_periods=1).mean())
        cols[f"{c}_m30"] = s.transform(lambda x: x.rolling(30, min_periods=1).mean())
        cols[f"{c}_sd10"] = s.transform(lambda x: x.rolling(10, min_periods=2).std().fillna(0.0))
        cols[f"{c}_d5"] = df[c] - s.shift(5).fillna(df[c])
        cols[f"{c}_d20"] = df[c] - s.shift(20).fillna(df[c])
    df = pd.concat([df, pd.DataFrame(cols)], axis=1)
    return df, list(cols.keys())


tr, fcols = add_features(tr_raw)
te_full, _ = add_features(te_raw)
te = te_full.groupby("engine_id").tail(1).merge(last, on="engine_id")

X = fcols + ["cycle"]
m = HistGradientBoostingRegressor(max_iter=500, learning_rate=0.03, max_leaf_nodes=31,
                                  l2_regularization=1.0, random_state=0)
m.fit(tr[X], tr["rul_clipped"])
pred = np.clip(m.predict(te[X]), 0, 125)
y = te["true_rul_at_last_cycle"].clip(upper=125)
print(f"{fd} improved  RMSE={mean_squared_error(y, pred) ** 0.5:.2f}  "
      f"MAE={mean_absolute_error(y, pred):.2f}  (test engines: {len(te)}, features: {len(X)})")

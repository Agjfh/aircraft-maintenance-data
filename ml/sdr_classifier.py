"""Baseline: classify FAA SDR maintenance reports from their free text (TF-IDF + Logistic Regression).
Usage: python ml/sdr_classifier.py [hazard_binary|hazard_category]"""
import sys, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report
target = sys.argv[1] if len(sys.argv) > 1 else "hazard_binary"
D = "data/processed/sdr/"
tr, va, te = (pd.read_csv(D + f"sdr_{s}.csv") for s in ("train", "val", "test"))
if target == "hazard_binary":      # 1 = safety hazard, 0 = not a hazard (corrosion rows have no label -> dropped)
    tr, va, te = (d.dropna(subset=["hazard_binary"]) for d in (tr, va, te))
model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                      LogisticRegression(max_iter=2000, class_weight="balanced"))
model.fit(tr["text"], tr[target])
print("VALIDATION\n", classification_report(va[target], model.predict(va["text"]), digits=3, zero_division=0))
print("TEST\n", classification_report(te[target], model.predict(te["text"]), digits=3, zero_division=0))

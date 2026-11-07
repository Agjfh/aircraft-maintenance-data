"""Baseline: classify FAA SDR reports from free text (TF-IDF + Logistic Regression).
Usage: python ml/sdr_classifier.py [hazard_binary|hazard_category]"""
import sys
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

target = sys.argv[1] if len(sys.argv) > 1 else "hazard_binary"
directory = "data/processed/sdr/"
train, validation, test = (pd.read_csv(directory + f"sdr_{split}.csv") for split in ("train", "val", "test"))
if target == "hazard_binary":
    train, validation, test = (frame.dropna(subset=["hazard_binary"]) for frame in (train, validation, test))

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
    LogisticRegression(max_iter=2000, class_weight="balanced")
)
model.fit(train["text"], train[target])
print("VALIDATION\n", classification_report(validation[target], model.predict(validation["text"]), digits=3, zero_division=0))
print("TEST\n", classification_report(test[target], model.predict(test["text"]), digits=3, zero_division=0))

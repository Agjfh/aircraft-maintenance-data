"""Symptom-based fault diagnosis (the app's Diagnose screen).
Usage: python ml/diagnosis_classifier.py

Input : the symptoms a technician ticks (one-hot S01..S40)
Output: ranked probable faults with a confidence score -> fault_catalog gives ATA code + recommended checks.

Model : Bernoulli Naive Bayes. It is small, explainable, and its parameters are exported to
        ml/diagnosis_model.json so a backend (e.g. Laravel/PHP) can score symptoms without Python:
            score(f) = class_log_prior[f] + sum_s ( x_s ? log_p[f][s] : log_1mp[f][s] )
            confidence = softmax(score)
"""
import json, os, numpy as np, pandas as pd
from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
D = "data/processed/diagnosis/"
tr, va, te = (pd.read_csv(D + f"diagnosis_{s}.csv") for s in ("train", "val", "test"))
S = [c for c in tr.columns if c.startswith("S")]

def report(name, m):
    for split, d in (("val", va), ("test", te)):
        p = m.predict_proba(d[S])
        pred = m.classes_[p.argmax(1)]
        print(f"{name:8s} {split}: acc={accuracy_score(d.fault_id, pred):.3f}  macroF1={f1_score(d.fault_id, pred, average='macro'):.3f}"
              f"  top3={top_k_accuracy_score(d.fault_id, p, k=3, labels=m.classes_):.3f}")

nb = BernoulliNB(alpha=1.0).fit(tr[S], tr.fault_id); report("NB", nb)
lr = LogisticRegression(max_iter=3000).fit(tr[S], tr.fault_id); report("LogReg", lr)

# final model: refit NB on train+val and export
full = pd.concat([tr, va])
nb = BernoulliNB(alpha=1.0).fit(full[S], full.fault_id)
logp = nb.feature_log_prob_
json.dump({"model": "BernoulliNB", "symptoms": S, "faults": nb.classes_.tolist(),
           "class_log_prior": nb.class_log_prior_.round(6).tolist(),
           "log_p": logp.round(6).tolist(), "log_1mp": np.log1p(-np.exp(logp)).round(6).tolist()},
          open("ml/diagnosis_model.json", "w"))

# example: what the app would show
fc = pd.read_csv("data/raw/a320_synthetic/fault_catalog.csv").set_index("fault_id")
x = pd.DataFrame([[1 if s in ("S03", "S02") else 0 for s in S]], columns=S)
p = nb.predict_proba(x)[0]
print("\nExample  symptoms = S03 (hydraulic leak) + S02 (reservoir low level)")
for i in p.argsort()[::-1][:3]:
    f = nb.classes_[i]
    print(f"  {p[i]*100:5.1f}%  {f}  {fc.loc[f, 'fault_name']}  (ATA {fc.loc[f, 'ata_code']})")
print("  checks:", fc.loc[nb.classes_[p.argmax()], "recommended_checks"].replace("|", " -> "))

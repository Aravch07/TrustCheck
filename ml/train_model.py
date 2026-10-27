"""Reproducible labeled simulation -> grouped split -> logistic regression."""
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if not (ROOT / "ml_model.py").exists():
    ROOT = ROOT.parent
OUTPUT = ROOT / "ml" if (ROOT / "ml").is_dir() else ROOT
sys.path.insert(0, str(ROOT))
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, average_precision_score, confusion_matrix)
from sklearn.dummy import DummyClassifier
from ml_model import FEATURES, LOG_FEATURES, feature_rows, transform, predict

SEED = 271026


def make_dataset():
    rng = random.Random(SEED)
    reviews, accounts = [], []
    labels, groups = {}, {}
    openings = ["I tried this", "My experience was", "On my visit it felt", "The result seemed",
                "After using it I found", "Overall I thought", "This time it was", "For the price it felt"]
    qualities = ["pleasant", "disappointing", "quite good", "average", "excellent", "inconsistent",
                 "reasonable", "comfortable", "slow", "surprisingly helpful", "worthwhile", "ordinary"]
    topics = ["service", "quality", "comfort", "value", "delivery", "staff", "packaging", "details"]
    endings = ["I may return.", "There is room to improve.", "My friends agreed.", "It met my needs.",
               "The timing mattered.", "I visited on Tuesday.", "I compared several options.", "I kept the receipt."]
    for business in range(1, 181):
        start = datetime(2026, 1, 1) + timedelta(days=rng.randrange(120))
        campaign = rng.random() < .75
        stealth = rng.random() < .3
        promotion = rng.random() < .45
        baseline = rng.uniform(2.2, 4.3)
        account_ids = [business*100+i for i in range(70)]
        for i, uid in enumerate(account_ids):
            age = rng.randint(1, 35) if (i>=60 and rng.random()<.65) else rng.randint(30, 900)
            accounts.append({"id": uid, "name": "Synthetic account "+str(uid),
                             "joined": start-timedelta(days=age)})
        shared = "Amazing quality and excellent service. Highly recommend this choice to everyone."
        for i in range(85):
            injected = i >= 55
            label = int(injected and campaign)
            day = rng.uniform(25, 30) if stealth else 28
            posted = (start+timedelta(days=day, minutes=rng.uniform(0,65))) if injected else start+timedelta(days=rng.uniform(0,24))
            if label:
                uid = rng.choice(account_ids[60:67] if not stealth else account_ids[35:70])
                rating = rng.choices([1,2,3,4,5], [2,1,2,18,77])[0]
                copied = rng.random() < (.45 if stealth else .8)
            else:
                uid = rng.choice(account_ids[:65])
                rating = min(5,max(1,round(rng.gauss(baseline+(.7 if injected else 0),1.1))))
                copied = injected and promotion and rng.random()<.45
            text = shared if copied else " ".join([rng.choice(openings), rng.choice(qualities),
                  "and the", rng.choice(topics), "was", rng.choice(qualities)+".", rng.choice(endings)])
            rid = len(reviews)+1
            reviews.append({"id":rid,"business_id":business,"reviewer_id":uid,
                            "rating":rating,"body":text,"posted":posted})
            labels[rid], groups[rid] = label, business
    features = feature_rows(reviews, accounts)
    ordered = sorted(features)
    X = np.array([features[rid] for rid in ordered], dtype=float)
    return X, np.array([labels[rid] for rid in ordered]), np.array([groups[rid] for rid in ordered])


def metrics(y, probability, threshold):
    predicted = probability >= threshold
    return {"accuracy": accuracy_score(y,predicted),
            "precision": precision_score(y,predicted,zero_division=0),
            "recall": recall_score(y,predicted,zero_division=0),
            "f1": f1_score(y,predicted,zero_division=0),
            "roc_auc": roc_auc_score(y,probability),
            "average_precision": average_precision_score(y,probability),
            "confusion_matrix": confusion_matrix(y,predicted,labels=[0,1]).tolist()}


def main():
    X, y, groups = make_dataset()
    rng = np.random.default_rng(SEED)
    businesses = rng.permutation(np.unique(groups))
    train_groups, validation_groups, test_groups = businesses[:108], businesses[108:144], businesses[144:]
    train = np.isin(groups,train_groups)
    validation = np.isin(groups,validation_groups)
    test = np.isin(groups,test_groups)
    Z = np.array([transform(row) for row in X])
    scaler = StandardScaler().fit(Z[train])
    classifier = LogisticRegression(max_iter=2000,random_state=SEED)
    classifier.fit(scaler.transform(Z[train]),y[train])
    val_probability = classifier.predict_proba(scaler.transform(Z[validation]))[:,1]
    thresholds = np.arange(.1,.91,.025)
    threshold = float(max(thresholds,key=lambda t:f1_score(y[validation],val_probability>=t)))
    model = {"model_type":"StandardScaler + LogisticRegression","version":1,"seed":SEED,
             "features":FEATURES,"log_features":LOG_FEATURES,
             "mean":scaler.mean_.tolist(),"scale":scaler.scale_.tolist(),
             "weights":classifier.coef_[0].tolist(),"intercept":float(classifier.intercept_[0]),
             "threshold":round(threshold,6),
             "training_scope":"Synthetic simulation only. No real-world fraud validation."}
    probability = classifier.predict_proba(scaler.transform(Z[test]))[:,1]
    exported_probability = np.array([predict(row,model)["probability"] for row in X[test]])
    assert np.allclose(exported_probability,probability,atol=1e-12)
    dummy = DummyClassifier(strategy="prior").fit(Z[train],y[train])
    report = {"scope":"Held-out synthetic businesses only; not real-world fraud accuracy.",
              "labels":"Known simulated campaign membership, not thresholded rule scores.",
              "seed":SEED,"rows":len(y),"positive_rows":int(y.sum()),"threshold":model["threshold"],
              "split":"60% train / 20% validation / 20% test by business; no business or account crosses splits.",
              "train_groups":train_groups.tolist(),"validation_groups":validation_groups.tolist(),
              "test_groups":test_groups.tolist(),
              "counts":{name:{"rows":int(mask.sum()),"positive":int(y[mask].sum())}
                        for name,mask in [("train",train),("validation",validation),("test",test)]},
              "test":metrics(y[test],probability,threshold),
              "majority_baseline":metrics(y[test],dummy.predict_proba(Z[test])[:,1],.5),
              "limitations":["Synthetic labels represent the simulator, not independently verified real review fraud.",
                "Related templates can appear across splits; the holdout tests new businesses, not new language sources.",
                "Numeric outputs are uncalibrated model estimates, not verified fraud probabilities.",
                "Causal features use only preceding timestamps/IDs; very early campaign reviews may be missed.",
                "Desktop seeded dataset differs from the training simulator and has no complete verified labels."]}
    (ROOT/"model.json").write_text(json.dumps(model,indent=2))
    (OUTPUT/"metrics.json").write_text(json.dumps(report,indent=2))
    with (OUTPUT/"training_data.csv").open("w",newline="") as file:
        writer=csv.writer(file);writer.writerow(["business_group","split",*FEATURES,"label"])
        for row,label,group in zip(X,y,groups):
            split="train" if group in train_groups else "validation" if group in validation_groups else "test"
            writer.writerow([int(group),split,*row,int(label)])
    print(json.dumps({"rows":len(y),"test":report["test"],"threshold":threshold},indent=2))


if __name__ == "__main__":
    main()

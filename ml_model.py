"""Shared feature extraction and the trained logistic regression predictor."""
import json
import math
import re
from collections import defaultdict
from datetime import datetime, date, time, timedelta
from pathlib import Path

FEATURES = ["Reviews in previous hour", "Highest wording similarity",
            "Previous reviews by this account of this business", "Account age in days",
            "Rating deviation from previous mean", "Recent rating rise"]
LOG_FEATURES = [0, 2, 3]
MODEL_PATH = Path(__file__).with_name("model.json")


def as_datetime(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, date):
        return datetime.combine(value, time())
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def feature_rows(reviews, reviewers):
    """Uses only earlier records, ordered by timestamp and ID. Never reads labels."""
    joined = {u["id"]: as_datetime(u["joined"]) for u in reviewers}
    history = defaultdict(list)
    output = {}
    for review in sorted(reviews, key=lambda r: (as_datetime(r["posted"]), r["id"])):
        now = as_datetime(review["posted"])
        previous = history[review["business_id"]]
        recent = [r for r in previous if now - as_datetime(r["posted"]) <= timedelta(days=7)]
        words = set(re.findall(r"[a-z]{3,}", review["body"].lower()))
        overlaps = []
        for other in recent:
            other_words = set(re.findall(r"[a-z]{3,}", other["body"].lower()))
            overlaps.append(len(words & other_words) / max(1, len(words | other_words)))
        last_day = [r["rating"] for r in previous if now-as_datetime(r["posted"]) <= timedelta(days=1)]
        older = [r["rating"] for r in previous if now-as_datetime(r["posted"]) > timedelta(days=1)]
        average = sum(r["rating"] for r in previous) / len(previous) if previous else review["rating"]
        rise = sum(last_day)/len(last_day)-sum(older)/len(older) if len(last_day)>=2 and len(older)>=5 else 0
        output[review["id"]] = [
            sum(now-as_datetime(r["posted"]) <= timedelta(hours=1) for r in previous),
            max(overlaps, default=0),
            sum(r["reviewer_id"] == review["reviewer_id"] for r in previous),
            max(0, (now-joined[review["reviewer_id"]]).total_seconds()/86400),
            abs(review["rating"]-average), rise]
        history[review["business_id"]].append(review)
    return output


def transform(values):
    return [math.log1p(max(0, v)) if i in LOG_FEATURES else v for i, v in enumerate(values)]


def predict(values, model=None):
    model = model or json.loads(MODEL_PATH.read_text())
    if len(values) != len(FEATURES) or not all(math.isfinite(float(v)) for v in values):
        raise ValueError("Provide six finite feature values.")
    transformed = transform(values)
    effects = [((x-m)/s)*w for x,m,s,w in zip(
        transformed, model["mean"], model["scale"], model["weights"])]
    log_odds = model["intercept"] + sum(effects)
    probability = 1 / (1 + math.exp(-max(-700, min(700, log_odds))))
    reasons = [{"feature": name, "value": round(value, 3), "effect": round(effect, 3)}
               for name,value,effect in zip(FEATURES, values, effects)]
    return {"probability": probability, "suspicious": probability >= model["threshold"],
            "reasons": sorted(reasons, key=lambda x: abs(x["effect"]), reverse=True)}


def apply_model(reviews, reviewers):
    model = json.loads(MODEL_PATH.read_text())
    values = feature_rows(reviews, reviewers)
    for review in reviews:
        result = predict(values[review["id"]], model)
        review["ml_score"] = round(result["probability"]*100, 1)
        review["ml_suspicious"] = result["suspicious"]
        review["ml_reasons"] = result["reasons"][:3]

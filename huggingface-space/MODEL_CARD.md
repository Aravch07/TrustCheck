---
language:
- en
tags:
- tabular-classification
- logistic-regression
- synthetic-data
- review-detection
library_name: sklearn
---

# TrustCheck - synthetic review behavior classifier

## Intended use
A small, explainable academic demonstration of supervised classification, combined with a local Flask/MySQL review management project. The labels indicate simulated campaign membership, not proven fraud. Do not use for automatic review removal, sanctions or public accusations.

This is a real fitted logistic regression classifier. It is not an LLM or a rules engine labeled as ML. The earlier weighted rule score is retained separately in the website and is not used as a training feature or target.

## Training data
Seed 271026 generates 180 independent synthetic businesses with 85 reviews each (15,300 rows). Each business has its own reviewer-account IDs. Each has 55 baseline reviews and 30 later event reviews. Some events are coordinated campaigns; others are legitimate activity/promotions. Campaigns can be concentrated or spread across several days. Account ages, ratings, language and timing distributions overlap between classes.

Labels are assigned by the simulator before feature extraction: 1 for a review injected as part of a simulated campaign; 0 for baseline/legitimate event reviews. No label is computed from the five rule scores.

The simulator supplies hypothetical ground truth. Repeated phrase templates can occur in all splits. This is not a benchmark of independently collected real reviews.

## Features
Features use only records preceding the current review by timestamp, breaking equal-timestamp ties with record ID. No future records, row IDs, business IDs, labels or rule scores enter the classifier.

1. Count of other reviews of the business in the previous hour.
2. Maximum Jaccard similarity to earlier review text from that business in the previous seven days. Text is lowercased and tokenized into distinct ASCII letter words of length ≥3.
3. Count of earlier reviews of this business by this account.
4. Account age at review time in days, using the account joined date; negative values are clamped to zero.
5. Absolute star-rating deviation from all previous reviews of the business. Zero when no prior reviews exist.
6. Mean rating of reviews in the preceding day minus the mean of older reviews, requiring at least 2 recent and 5 older reviews; otherwise zero.

Counts and account age are transformed with log(1+x). StandardScaler means/scales are fitted on training rows only. Logistic regression learns six coefficients plus an intercept. Inference uses sigmoid(intercept + sum(coefficient × standardized feature)).

## Split and evaluation
Businesses are shuffled reproducibly and assigned 60% to train (108), 20% to validation (36), 20% to test (36). No business or reviewer account crosses splits. Feature extraction uses a business's preceding events as context, which may include earlier test events at test time; their labels are never inputs.

The model fits on train only. Threshold maximizes F1 over a predefined grid on validation only. The final untouched synthetic test set is used once for reporting.

- Test examples: 3,060 (750 campaign, 2,310 non-campaign).
- Threshold: 0.50.
- Precision: 0.8864.
- Recall: 0.8840.
- F1: 0.8852.
- ROC-AUC: 0.9687.
- Average precision: 0.9479.
- Accuracy: 0.9438.
- Confusion matrix: [[2225,85],[87,663]] (rows actual 0/1; columns predicted 0/1).

metrics.json is the authoritative machine-readable report and includes majority-class baseline, split IDs, row counts, seed and limitations.

## Inference and explanation
model.json contains plain JSON coefficients, scaling statistics, log-transform indexes and the threshold. No untrusted pickle is loaded. ml_model.py reproduces Python/scikit-learn predictions; the browser uses the same formula in space.js.

Feature contributions are coefficient × standardized value in log-odds units, relative to the training mean. They explain the model's calculation, not causal evidence. A 90% output is an uncalibrated model estimate under this simulator, not an established 90% chance of real fraud.

## Limitations
- No real-world generalization claim; real-world precision/recall are unknown.
- The local 516-review seeded dataset differs from this training generator and lacks complete independent labels. We do not report its prediction agreement as real validation.
- Synthetic language/templates and injected behaviors are simplified; different campaigns may be missed.
- Early campaign reviews have little prior history. Genuine launch events or loyal repeat customers can be falsely flagged.
- English/ASCII tokenization loses other scripts, accents and punctuation.
- A grouped business holdout does not establish generalization to unseen language templates.
- Scores are not probability-calibrated against a real deployment population.

## Reproduce
Install requirements-ml.txt in the main project, then run python train_model.py. This creates model.json, metrics.json and training_data.csv. The last file includes explicit split labels. Keep the held-out test split out of model fitting and threshold selection.

The local website uses MySQL. The Hugging Face static Space uses a read-only export restricted to the original synthetic seed review IDs; it has no access to laptop MySQL or its password.

## Versions
Python 3.13, scikit-learn 1.9.0. See requirements-ml.txt for dependency constraints. Standard logistic regression, CPU only.

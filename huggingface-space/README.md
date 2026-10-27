---
title: TrustCheck ML
emoji: 🔎
colorFrom: green
colorTo: yellow
sdk: static
app_file: index.html
pinned: false
---

# TrustCheck ML

A static, browser-based demonstration of a Python-trained logistic regression model for suspicious review behavior.

The weights were learned with scikit-learn from independently labeled simulated review campaigns. This is not a hand-coded score presented as machine learning. All evaluation numbers describe synthetic test data only.

The complete local Flask/MySQL project is at https://github.com/Aravch07/TrustCheck.

This Space runs the exported learned coefficients in browser JavaScript. Its model transform is numerically checked against Python/scikit-learn. It requires no Python server, GPU, MySQL password, or public database connection.

The review explorer is a read-only synthetic snapshot exported from local MySQL. It is not a live database connection and changes made on the laptop do not appear until the snapshot is exported and deployed again.

Read MODEL_CARD.md for feature definitions, data provenance, split methodology, metrics and limitations.

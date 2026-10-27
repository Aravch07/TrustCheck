# TrustCheck

Review management with Python, MySQL, and an explainable machine learning model.

[Live demo](https://huggingface.co/spaces/Uniworld7/TrustCheck) · [Trained model](https://huggingface.co/Uniworld7/TrustCheck-Model) · [Product specification](docs/prd.md) · [Hosting guide](docs/HOSTING.md)

## What it does

- View reviews and compare business totals, average ratings, and suspicious activity.
- Search by business, reviewer, or review text.
- Add, mark reviewed, and delete records in local MySQL.
- Compare explicit rule scores with learned ML estimates and see contributing factors.
- Try the model online using a read-only synthetic-data snapshot.

## Run on your laptop

    python -m pip install -r requirements.txt
    python app.py

Open http://127.0.0.1:3000. MySQL must be running. Keep the terminal open; Ctrl+C stops the server. You can also double-click START-TRUSTCHECK.cmd.

For a fresh setup, copy .env.example to .env, enter your own MySQL credentials, and import database.sql in MySQL Workbench. Never commit .env. No npm or frontend build is required for the local application.

## Repository map

    app.py                  Flask routes and MySQL operations
    index.html              Local webpage and styles
    ml_model.py             Features and trained-model inference
    model.json              Learned weights used by the website
    database.sql            Schema and original synthetic seed data
    requirements.txt        Local app dependencies
    ml/                     Training code, evaluation and tests
    deployment/             Hosting tools and static website source
    docs/                   Model card, PRD and hosting instructions

Generated training CSVs and assembled deployment packages stay on your laptop and are ignored by Git. The published model, dataset and demo remain available on Hugging Face. The backup before this cleanup is separate from the repository.

## Model

Logistic regression uses six features: previous-hour volume, wording similarity, repeated account activity, account age, rating deviation, and recent rating rise.

Training uses 15,300 simulated reviews, with businesses/accounts separated across train, validation and test. Synthetic test precision is 88.64%, recall 88.40%, and F1 0.8852. These numbers do not establish real-world fraud performance. Estimates are uncalibrated and recommend human investigation, not automatic removal.

Read [the model card](docs/MODEL_CARD.md) and [evaluation report](ml/metrics.json) for definitions and limitations. The separate weighted rules are not the ML model and are not its training labels.

## Retrain and test

    python -m pip install -r ml/requirements.txt
    python ml/train_model.py
    python -m unittest discover -s ml -p test_model.py -v

Training writes model.json, ml/metrics.json, and the locally ignored ml/training_data.csv. Review evaluation before deploying a replacement. Browser-parity tests use Node.js if installed; running the local website does not require Node.js.

## Host online

**Hugging Face:** already deployed at the live-demo link above. It runs the learned formula in the browser, without accessing laptop MySQL.

**Vercel:** the repository includes vercel.json for the same read-only static demo. Import Aravch07/TrustCheck, select Other as the framework, keep the repository root, and deploy. The configuration builds .space-build using Python standard-library tools and a pinned published snapshot. No database secrets are needed for this mode.

The current Vercel configuration deliberately hosts the model demo, not the Flask/MySQL editor. A full online database app needs hosted MySQL and server-side credentials. See [hosting options](docs/HOSTING.md).

## Refresh Hugging Face

Sign in locally using deployment/HF-LOGIN.cmd, then:

    python deployment/prepare_space.py
    python deployment/deploy_huggingface.py

Export uses local MySQL and restricts records to original synthetic seed IDs. Review data before publication. If you only need to rebuild the existing public demo, run python deployment/build_demo.py; that path needs no MySQL connection.

After retraining, prepare and publish a matching snapshot, then update the pinned REVISION in deployment/build_demo.py to the new Hugging Face Space commit before a Vercel build. This prevents mixing stale snapshot predictions with new weights.

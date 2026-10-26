# TrustCheck

A basic Python, HTML and MySQL review management website.

## Run

    python -m pip install -r requirements.txt
    python app.py

Open http://127.0.0.1:3000. Or double-click START-TRUSTCHECK.cmd after installation. Keep the terminal open. Press Ctrl+C to stop.

The existing MySQL database is reused. Settings are in the private .env file. For a fresh setup, copy .env.example to .env, enter your MySQL credentials, and import database.sql using MySQL Workbench.

## Two code files
- app.py: MySQL connection, SELECT/INSERT/UPDATE/DELETE, and five scoring checks.
- index.html: the webpage with a small amount of CSS inside it. Flask fills {{ ... }} with data and repeats HTML using {% for ... %}.

requirements.txt lists Flask and MySQL Connector/Python. database.sql is an optional installation script, not needed during normal use. No npm, node_modules, React, build command, browser JSON API, or separate JavaScript/CSS files are required.

## Basic features
- List reviews, 25 per page.
- See each business's total reviews, average rating, high-risk count, unique reviewer count and reviewed count.
- Select a business to filter the review list; selection stays active across pages.
- Add a review for an existing business and account.
- Search reviews and filter high-risk scores.
- Mark a review as reviewed.
- Delete a review with confirmation.
- View each score's triggered reasons.

## Scoring
The program compares a review only with other reviews of the same business:
- At least 5 other reviews within ±1 hour: 25 points.
- At least 2 other reviews with the same text after lowercasing and trimming: 25 points.
- Daily-window mean exceeds earlier mean by >1 star (at least 5 in both groups): 20 points.
- At least 3 reviews of the business by one account, including this review: 20 points.
- Rating differs from earlier mean by ≥2 stars (at least 5 earlier reviews): 10 points.

Earlier means more than one day before the review; the daily window is ±1 day. High risk means ≥60 points. The current review is excluded from comparison groups. These are basic rules, not a machine learning model. Scores recompute when loading a page and are not saved as fixed database columns. Mark reviewed changes workflow status only.

Wording matching is deliberately simplified from word-overlap similarity to exact matching. Synthetic templates may produce false positives. Timing windows can include later reviews in the dataset. Suspicion is not proof.

Writes use parameterized %s placeholders. Each change and its audit entry are committed together. Foreign keys and rating constraints remain in MySQL.

This is a local learning project served by Flask's development server on this laptop only.

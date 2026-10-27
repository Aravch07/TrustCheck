# TrustCheck - Product Requirements and Current Product Specification

**Product status: 27 October 2026**  
**Release stage: Local Flask/MySQL application with a public Hugging Face ML demonstration**

This document describes the current product rather than the original aspirational build plan. It records implemented behavior, architecture, evaluation, limitations, and remaining work. Source code, model artifacts, and evaluation reports remain the implementation authority if this document becomes outdated.

## 1. Product summary

TrustCheck is a review management and suspicious-activity detection project. Users can explore businesses and their reviews, manage local records, and investigate patterns in review timing, wording, ratings, and account history.

The interface distinguishes three different numbers:

- **Star rating:** the reviewer's submitted rating, from 1 to 5.
- **Rule score:** manually weighted suspiciousness conditions, totaling 0 to 100.
- **ML estimate:** output of a trained logistic regression model, displayed as a percentage and compared with a decision threshold.

These measures are not interchangeable. Five stars does not automatically mean suspicious. A rule score is not a trained prediction. An ML estimate is not a verified probability of real-world fraud.

| Environment | Purpose | Data source | Record changes |
| --- | --- | --- | --- |
| Local Python website | Review management and database demonstration | Live local MySQL | Add, mark reviewed, delete |
| Public Hugging Face Space | Model demonstration and review exploration | Synthetic-data snapshot | Read-only |

The online demonstration does not connect to the laptop's MySQL server.

## 2. Product status and scope

### Implemented local application

- Single-page Python/Flask website with an HTML/Jinja template.
- Global review, business, account, and high-risk rule counts.
- Per-business total reviews, average rating, high-risk rule count, ML-flag count, unique reviewers, and reviewed count.
- Business selection by linked name or dropdown.
- Search across business names, reviewer names, and review bodies.
- Rule-based high-risk filter and 25-row pagination.
- Add-review form using existing businesses and accounts.
- Mark-reviewed action and confirmed deletion.
- Audit entries committed with successful database mutations.
- Separate rule and ML explanations.
- MySQL foreign keys, indexes, and rating constraints.

### Implemented public demonstration

- Public Hugging Face Static Space.
- Six-input prediction form with ordinary/campaign examples.
- Browser-based inference using the exported learned weights.
- Estimate, classification, threshold, intercept, and feature-contribution display.
- Business summaries and review explorer with text search, business selection, ML-flag filtering, and 20-row pagination.
- Read-only synthetic seed-data snapshot.
- Evaluation report and downloadable training code, dataset, and model.
- Separate Hugging Face model repository.

### Deferred

- Real-world labeled-data collection and validation.
- Scraping or automatic ingestion from review platforms.
- Public cloud MySQL, hosted editing, and automatic laptop synchronization.
- Authentication, roles, moderator accounts, and administration.
- Business/account creation and general text/rating editing.
- Scheduled retraining, live monitoring, and continuous dataset refresh.
- Multilingual semantic text modeling or transformers.
- Automatic review removal or guarantees that flagged reviews are fake.

## 3. Audience and core user tasks

The current product supports users who want to:

1. Inspect reviews and compare business activity.
2. Add a local review linked to existing database records.
3. Understand why a rule or model flags a review.
4. Mark a review as inspected without changing its score.
5. Demonstrate supervised ML training and evaluation.
6. Share a working online model without publishing database credentials.

The local form uses existing businesses/accounts. The public prediction form accepts hypothetical numeric features but does not create or save a review.

## 4. Pages and user-facing behavior

### Local / - Main page

Address: http://127.0.0.1:3000

- Shows the TrustCheck heading without the previous technical subtitle.
- Global summary cards remain global when filters change.
- Business summaries describe all reviews belonging to each business.
- Clicking a business name selects its review list.
- Add-review form requires a business, account, 1-5 rating, and text.
- Review rows show business/text, account, stars, rule score, ML estimate, status, and actions.
- Expandable rule reasons list triggered conditions and points.
- Expandable ML factors show the three largest absolute contributions.
- Mark reviewed updates workflow status; it does not establish fraud or alter model weights.
- Delete removes the selected review after browser confirmation and logs the operation.

### Local filters and pagination

- business_id selects one business; 0 means all.
- search matches business name, account name, or body, case-insensitively.
- flagged=yes keeps rule scores of at least 60.
- page selects a 25-row page.

Filters combine and persist across pagination. Summary rows do not shrink to the filtered page. Successful POST actions redirect to /, resetting filters and preventing duplicate submission on refresh.

### Public Space - Manual prediction

URL: https://huggingface.co/spaces/Uniworld7/TrustCheck

- Loads model.json, metrics.json, and demo_data.json.
- Accepts six raw feature values, not a pasted review sentence.
- Offers ordinary and campaign example buttons.
- Shows the estimate, flagged/not-flagged result, threshold, intercept, and all six contributions sorted by absolute magnitude.
- Runs prediction in the visitor's browser. The app does not send prediction-form values to an inference server.

### Public Space - Business and review explorer

- Displays snapshot review count, business count, ML flags, and training-example count.
- Business rows show total reviews, average rating, and ML flags.
- Business selection restricts the review explorer.
- Search matches review bodies, unlike the broader local search.
- The hosted high-risk checkbox filters ML flags; the local checkbox filters rule scores.
- Results use 20-row pagination.
- Review rows show exported rule scores and ML estimates.
- The public explorer has no add, update, or delete controls.

### Other paths

The local app has no separate REST JSON API, profile routes, or account pages. GET and POST / handle the current workflows. The static Space serves files without a server-side mutation API.

## 5. Design system and interaction

- **Visual direction:** simple, readable review analytics.
- **Palette:** pale green background, white cards, dark green text/buttons, muted secondary text, and brown/orange risk accents.
- **Local colors:** background #f4f7f3, primary text #29452f, buttons #396444, risk/error #b15f38.
- **Typography:** Arial/system sans-serif; no external font download.
- **Layout:** summary cards, business table, add form, and paginated review table.
- **Explanations:** native expandable details blocks.
- **Responsive behavior:** wrapping controls/cards and horizontally scrollable tables where implemented.
- **Accessibility:** labeled controls, accessible filter names, native buttons, and an alert role for local errors.
- **Hosted feedback:** loading/error status, prediction disabled until assets load, and live result updates.

Accessibility and small-screen support are basic; no formal conformance claim is made. The local page uses inline CSS and Jinja, without React, Vite, or a frontend build step.

## 6. Data and provenance

### Original local dataset

- 8 synthetic businesses.
- 96 synthetic reviewer accounts.
- 516 synthetic reviews: 480 baseline records and 36 planted five-star campaign reviews.

Baseline text uses repeated templates, so ordinary seeded records can also trigger wording signals. The planted campaign does not provide complete independently verified fraud labels for all local reviews.

Counts can change through local additions/deletions. Original seed data, current MySQL state, and hosted snapshot are separate concepts.

### ML training dataset

The separate reproducible simulator uses seed 271026:

- 180 businesses with 85 reviews each: 15,300 examples.
- Each business has 55 baseline reviews and 30 later event reviews.
- Some events are coordinated campaigns; others represent ordinary activity or legitimate promotions.
- Campaigns can be concentrated or spread across several days.
- Business-specific account IDs prevent reviewer overlap across business partitions.
- Timing, language, rating, and account-age distributions overlap between classes.

Labels are assigned from known simulated campaign membership before feature extraction. They are not obtained by thresholding the rule score.

### Public snapshot

prepare_space.py exports original seed review IDs 1-516, businesses 1-8, and reviewer accounts 1-96 from MySQL. It calculates scores and writes a dated demo_data.json.

The export omits the audit table and credentials. New review IDs outside the original range are excluded. The ID restriction is not a general privacy filter: if original seed content were replaced with private material, the export would need review before publication.

Explorer predictions stay fixed to the uploaded snapshot until export/deployment repeats. The manual form computes a fresh prediction from its numeric inputs.

### Database tables

| Table | Main fields | Responsibility |
| --- | --- | --- |
| businesses | id, name, category, city | Business records |
| reviewers | id, name, joined | Accounts and joining dates |
| reviews | id, business_id, reviewer_id, rating, body, posted, status | Review records and relationships |
| audit | id, action, created | Recorded mutations |

One business has many reviews; one account can write many reviews. Foreign keys prevent nonexistent parent references. Rating is constrained to 1-5. Indexes cover business_id/posted and reviewer_id. Tables use InnoDB and utf8mb4.

## 7. Prediction behavior and limitations

### Rule score

The rule engine compares a review with other reviews of its business, excluding itself:

| Rule | Trigger | Points |
| --- | --- | ---: |
| Review burst | At least 5 others within ±1 hour | 25 |
| Repeated wording | At least 2 others have the same lowercased, edge-trimmed text | 25 |
| Rating surge | Mean within ±1 day exceeds earlier mean by more than 1 star; at least 5 reviews in each group | 20 |
| Repeat account | At least 2 other reviews by the same account, making 3 including the current review | 20 |
| Rating mismatch | Rating differs from earlier mean by at least 2 stars; at least 5 earlier reviews | 10 |

For these rules, earlier means more than one day before the review. Maximum score is 100; at least 60 is high risk. Centered rule windows can include later records and differ from the earlier-only ML features.

### Current ML definition

The active model.json artifact is version 1: StandardScaler + LogisticRegression, with six coefficients, an intercept, and threshold 0.5.

The target is simulated campaign membership. Its percentage output is not calibrated against a real fraud population.

### Six input features

Comparison reviews belong to the same business and precede the current review by timestamp, breaking ties with ID.

| Feature | Calculation |
| --- | --- |
| Prior-hour volume | Count of preceding business reviews within 60 minutes |
| Highest wording similarity | Maximum unique-word Jaccard overlap against preceding business reviews within 7 days |
| Prior account/business reviews | Count of preceding reviews by this account of this business |
| Account age | Review time minus joining time in days; negative values become zero |
| Rating deviation | Absolute difference from the mean of all preceding business ratings; zero without history |
| Recent rating rise | Previous-day rating mean minus older rating mean; requires at least 2 recent and 5 older reviews, otherwise zero |

Wording uses lowercase distinct ASCII-letter words of length at least three. Jaccard similarity is shared unique words divided by all unique words across both texts. Missing similarity history gives zero.

### Inference formula

Features 1, 3, and 4 first receive log(1 + max(0, value)). Other features retain their raw values. Each transformed value is standardized with its training mean and scale.

    contribution[i] = weight[i] * (transformed_value[i] - mean[i]) / scale[i]
    z = intercept + sum(contribution[i])
    estimate = 1 / (1 + exp(-z))
    flag = estimate >= 0.5

The current intercept is approximately -1.8173. Positive contributions raise the estimate; negative contributions lower it. Contributions are in log-odds units relative to the transformed training mean, not percentage-point additions or causal evidence.

### Training and evaluation

Businesses are shuffled into non-overlapping partitions. No business or reviewer account crosses partitions.

| Partition | Businesses | Reviews | Campaign examples |
| --- | ---: | ---: | ---: |
| Train | 108 | 9,180 | 2,580 |
| Validation | 36 | 3,060 | 780 |
| Test | 36 | 3,060 | 750 |

Scaling and classifier fitting use train only. The decision threshold maximizes validation F1 over a predefined grid. The untouched test set supplies the reported evaluation.

| Synthetic test metric | Result |
| --- | ---: |
| Accuracy | 94.38% |
| Precision | 88.64% |
| Recall | 88.40% |
| F1 | 0.8852 |
| ROC-AUC | 0.9687 |
| Average precision | 0.9479 |

The confusion matrix is [[2225, 85], [87, 663]], with rows actual non-campaign/campaign and columns predicted non-campaign/campaign.

The majority-class baseline predicts every review as non-campaign: 75.49% accuracy, campaign precision/recall/F1 zero, and ROC-AUC 0.5. The trained model outperforms this baseline on the synthetic holdout.

### Interpretation limits

- The holdout evaluates new simulated businesses, not independently collected real fraud.
- Phrase templates can occur across partitions; business holdout is not language-template holdout.
- Local seed data differs from the training simulator.
- Sparse history can hide early campaign reviews.
- Genuine promotions, new accounts, loyal customers, and shared wording can cause false flags.
- ASCII overlap is not multilingual semantic understanding.
- Zero can represent unavailable history rather than measured absence.
- Manually entered values may be outside the training distribution.
- Real-world detection performance and probability calibration remain unknown.

## 8. Technical architecture and runtime

### Local environment

- Frontend: HTML/Jinja with inline CSS.
- Web framework: Flask.
- Database: local MySQL through mysql-connector-python.
- Inference: Python standard-library code using model.json.
- Training: scikit-learn and NumPy.
- Startup: python app.py, defaulting to 127.0.0.1:3000.

The Flask development server is a local runtime, not a hardened public backend.

### Hosted environment

- Host: Hugging Face Static Space.
- Frontend: HTML/CSS and space.js.
- Inference: browser JavaScript reproducing the learned formula.
- Data: exported demo_data.json, model.json, and metrics.json.
- Live MySQL and backend mutations: none.

Public destinations:

- Space: https://huggingface.co/spaces/Uniworld7/TrustCheck
- Model: https://huggingface.co/Uniworld7/TrustCheck-Model
- Source: https://github.com/Aravch07/TrustCheck

### Local request contracts

| Request | Submitted values | Behavior |
| --- | --- | --- |
| GET / | Optional business/search/risk/page parameters | Load MySQL, score reviews, calculate summaries, render HTML |
| POST /, action=add | business, reviewer, rating, body | Validate, insert review and audit, commit, redirect |
| POST /, action=reviewed | id | Update status, write audit, commit, redirect |
| POST /, action=delete | id | Delete review, write audit, commit, redirect |

Database writes use %s placeholders with separate parameters. Review changes and audit entries commit together; handled failures roll back. Invalid rating/text produces a visible error. Outer MySQL failures return a readable 503 response.

### Secrets

.env stores local credentials and is ignored by Git. .env.example remains an empty-password template. Hugging Face authentication uses its token cache outside the repository.

Deployment uses explicit file allowlists. MySQL passwords and Hugging Face tokens must not appear in frontend code, model artifacts, datasets, or Git history.

## 9. Current repository responsibilities

The repository separates the everyday app from supporting training, deployment and documentation files:

- app.py: local routing, MySQL, rules, model integration, business summaries and review management.
- index.html: local webpage, inline styles, forms, tables and explanations.
- ml_model.py: chronological feature extraction and JSON model inference.
- model.json: learned parameters required by local inference.
- database.sql: schema and synthetic seed records.
- ml/train_model.py: reproducible simulation, grouped splits, training and evaluation.
- ml/metrics.json: committed evaluation report.
- ml/test_model.py: model invariants and browser parity checks.
- ml/requirements.txt: offline training/deployment dependencies.
- ml/training_data.csv: generated dataset, kept locally and ignored by Git; published separately on Hugging Face.
- deployment/build_demo.py: assembles a static demo without MySQL using a pinned public snapshot.
- deployment/prepare_space.py: refreshes the seed snapshot from local MySQL and assembles the package.
- deployment/deploy_huggingface.py: uploads the package and model artifacts using allowlists.
- deployment/HF-LOGIN.cmd: local Hugging Face authentication.
- deployment/space/: canonical HTML, JavaScript and configuration for the hosted demo.
- .space-build/: generated complete static package, ignored by Git.
- docs/MODEL_CARD.md: intended use, methodology, results and limitations.
- docs/HOSTING.md: Vercel/Hugging Face options and live-database requirements.
- docs/prd.md: this product specification.
- vercel.json: read-only static-demo build configuration, not a hosted Flask/MySQL backend.
- requirements.txt: local Flask/MySQL runtime dependencies.
- START-TRUSTCHECK.cmd: local launcher.
- README.md: concise entry point and commands.
- .gitignore: excludes credentials, generated packages/datasets, caches, environment and logs.

## 10. Operations and maintenance

### Run locally

    python -m pip install -r requirements.txt
    python app.py

MySQL, valid .env settings, the database, and model artifact must be available. For fresh setup, import database.sql with MySQL Workbench.

The import uses CREATE IF NOT EXISTS and INSERT IGNORE. It does not reset edits, is not a schema-migration framework, and is not a live database backup.

### Train and test

    python -m pip install -r ml/requirements.txt
    python ml/train_model.py
    python -m unittest discover -s ml -p test_model.py -v

Training overwrites model.json, metrics.json, and training_data.csv. Review artifacts before publication. Website startup and review submission do not retrain weights.

### Prepare and publish

    python deployment/prepare_space.py
    python deployment/deploy_huggingface.py

Authenticate with deployment/HF-LOGIN.cmd first. The configured account is Uniworld7. Export requires local MySQL; deployment uploads prepared files. Training alone does not refresh hosted scores.

GitHub source synchronization is separate from Hugging Face deployment. A GitHub push alone does not run the configured Space-upload script.

### Release verification

- Confirm MySQL reads and intended record mutations.
- Reconcile business totals with the full review dataset.
- Run model tests and check cross-runtime predictions.
- Confirm the Space and its model/data/report assets load.
- Exercise example inputs, explanations, business filters, and pagination.
- Review snapshot contents before public upload.
- Confirm code, model, metrics, and snapshot match the intended release.

## 11. Known issues and next priorities

1. **Real-data validation:** obtain independently labeled, legally usable reviews before claiming real-world detection quality.
2. **Missing history:** distinguish unavailable measurements from observed zero values.
3. **Language generalization:** test new templates/sources and multilingual text.
4. **Calibration and thresholding:** evaluate probability calibration and false-positive costs against a relevant population.
5. **Evaluation breadth:** add forward-time and unseen-template holdouts.
6. **Rule/ML distinctions:** maintain clear labels because windows, wording rules, and thresholds differ.
7. **Hosted synchronization:** a live cloud database would need a separate architecture; current export is manual and read-only.
8. **Model readiness:** missing/malformed artifacts do not have complete graceful degradation in every path.
9. **Production security:** authentication, authorization, rate limiting, CSRF defenses, and hosted write controls are not a completed production design.
10. **Performance:** pairwise comparisons prioritize readable code over large-dataset scale.
11. **Documentation freshness:** earlier code-explanation PDFs describe earlier snapshots and need regeneration after source changes.
12. **Accessibility/input polish:** extend keyboard, mobile, missing-data, and manual-input checks.

## 12. Acceptance criteria for the current release

The local product is operational when:

- MySQL records and global totals display correctly.
- Business total/average/risk/account/status summaries are consistent.
- Business, search, rule-risk filters, and pagination combine correctly.
- Add, mark reviewed, and delete change the intended record and audit entry.
- Invalid input does not commit a partial mutation.
- Rule scores and ML estimates remain separately labeled.
- Model explanations do not claim causal proof.

The hosted demonstration is operational when:

- Model, metrics, and snapshot assets load.
- The six-input form returns an estimate and classification.
- Tested Python/browser predictions agree.
- Examples, contributions, business selection, body search, ML filtering, and pagination work.
- Hosted data is disclosed as a read-only synthetic snapshot.
- Training code, dataset, metrics, and model files are available.
- No credential is shipped in assets.
- Synthetic-only evaluation and real-world limitations are disclosed.

Reported metrics must name their evaluation set. The product must not equate 94.38% synthetic accuracy with proven real-world fraud detection.

## 13. Product decisions recorded

- Keep local development based on Python, Flask, HTML, and MySQL Connector.
- Retain review management and business-level summaries.
- Keep explicit rules and trained ML as separate assessments.
- Use explainable logistic regression rather than an unnecessarily complex model.
- Train from simulator-assigned labels, not existing rule scores.
- Use earlier-only ML features and document their differences from centered rules.
- Export learned parameters as JSON and verify browser/Python parity.
- Deploy a static Hugging Face model demonstration.
- Keep MySQL local and publish only a reviewed, credential-free synthetic snapshot.
- Treat flags as recommendations for investigation, not automatic punishment or proof.

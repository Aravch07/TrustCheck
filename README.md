# TrustCheck

A review management system that combines review timing, wording, ratings, and account activity to identify suspicious patterns.

## Run
After configuring MySQL, double-click START-TRUSTCHECK.cmd, keep the window open, and visit http://127.0.0.1:3000.

Or open a terminal in this folder:

    npm start

No build is required. After editing a browser file, refresh the browser. After editing server.js or analysis.js, stop with Ctrl+C and run npm start again.

## Project files

| File | What it does |
| --- | --- |
| index.html | The page layout, buttons, tables, and review form |
| style.css | Colors, spacing, charts, and mobile layout |
| app.js | Button actions; fetches JSON; updates the HTML |
| server.js | Connects to MySQL and runs SELECT, INSERT, UPDATE, DELETE |
| analysis.js | Five rules that calculate each review's score |
| database.sql | Creates all four tables and inserts the synthetic data |
| example-queries.sql | SQL joins, grouping, and transaction examples |
| .env | Your private local MySQL connection settings |
| package.json | Start command and names of the two libraries |
| package-lock.json | Automatically records installed library versions |
| START-TRUSTCHECK.cmd | Double-click launcher |

Project files are stored in the root folder. npm installs dependencies automatically in node_modules.

Express handles browser requests, and mysql2 connects JavaScript to MySQL. The frontend uses HTML, CSS, and JavaScript.

## How it works
1. The browser opens index.html, style.css, and app.js.
2. app.js asks server.js for /api/data.
3. server.js uses SELECT with JOIN to read linked records from MySQL.
4. analysis.js scores the reviews and returns ordinary JavaScript objects.
5. The server sends JSON; app.js fills in the page's tables and charts.
6. Adding, updating, or deleting a review sends JSON to /api/reviews.
7. The server validates it, executes parameterized SQL and writes an audit entry in one transaction.

## Tables
- businesses: id, name, category, city.
- reviewers: id, name, joined.
- reviews: id, business_id, reviewer_id, rating, body, posted, status.
- audit: id, action, created.

One business has many reviews; one reviewer has many reviews. Foreign keys prevent orphan records. Ratings must be between 1 and 5. Indexes support business/time and reviewer searches.

## Full MySQL import commands
Open MySQL Workbench and run database.sql, or use this at the mysql> prompt from the project folder:

    SOURCE database.sql;
    USE trustcheck_local;
    SHOW TABLES;
    SELECT COUNT(*) FROM reviews;

Original dataset: 516 reviews, 96 reviewers, 8 businesses. SQL creates the tables if absent and skips duplicate seed IDs; reimport does not reset existing edits.

On another laptop: install Node.js 22.13+ and MySQL 8.0.16+, run npm install, copy .env.example to .env, enter your own connection settings, import database.sql, then npm start. The password is never sent to the browser. Do not share .env.

## Scoring
Review burst (25), similar wording (25), rating surge (20), repeat reviewer (20), and rating mismatch (10). High risk ≥60, watchlist 30–59, low risk <30.

The rules are commented in analysis.js. Similarity uses shared unique words divided by all unique words. Scores recompute after database changes. Dismissing a flag changes its workflow status, not the rule score.

Data is synthetic and contains a planted campaign plus repeated baseline templates. Flags are for investigation, not proof of fraud. Similar templates can cause false positives. Windows are centered on the review timestamp, so scores can use later reviews in the dataset. The activity chart shows October 2026; new reviews use the current timestamp.


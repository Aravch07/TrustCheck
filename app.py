from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime, timedelta, timezone
from statistics import mean
from pathlib import Path

# Read the existing private MySQL settings.
folder = Path(__file__).parent
settings = {}
for line in (folder / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        settings[key] = value

app = Flask(__name__, template_folder=str(folder), static_folder=None)


# Five basic rules. A high score means suspicious, not proven fake.
def check_reviews(reviews):
    for review in reviews:
        others = [r for r in reviews if r["business_id"] == review["business_id"] and r["id"] != review["id"]]
        nearby = [r for r in others if abs(r["posted"] - review["posted"]) <= timedelta(hours=1)]
        same_text = [r for r in others if r["body"].strip().lower() == review["body"].strip().lower()]
        repeats = [r for r in others if r["reviewer_id"] == review["reviewer_id"]]
        earlier = [r for r in others if r["posted"] < review["posted"] - timedelta(days=1)]
        daily = [r for r in others if abs(r["posted"] - review["posted"]) <= timedelta(days=1)]
        signals = []
        if len(nearby) >= 5:
            signals.append(("Review burst", 25))
        if len(same_text) >= 2:
            signals.append(("Repeated wording", 25))
        if len(earlier) >= 5 and len(daily) >= 5 and mean(r["rating"] for r in daily) > mean(r["rating"] for r in earlier) + 1:
            signals.append(("Rating surge", 20))
        if len(repeats) >= 2:
            signals.append(("Repeat account", 20))
        if len(earlier) >= 5 and abs(review["rating"] - mean(r["rating"] for r in earlier)) >= 2:
            signals.append(("Rating mismatch", 10))
        review["score"] = sum(points for name, points in signals)
        review["signals"] = signals


@app.route("/", methods=["GET", "POST"])
def home():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=settings.get("MYSQL_HOST", "127.0.0.1"),
            port=int(settings.get("MYSQL_PORT", 3306)),
            user=settings.get("MYSQL_USER", "root"),
            password=settings.get("MYSQL_PASSWORD", ""),
            database=settings.get("MYSQL_DATABASE", "trustcheck_local")
        )
        cursor = connection.cursor(dictionary=True, buffered=True)
        error = ""
        if request.method == "POST":
            try:
                action = request.form["action"]
                if action == "add":
                    business = int(request.form["business"])
                    reviewer = int(request.form["reviewer"])
                    rating = int(request.form["rating"])
                    body = request.form["body"].strip()
                    if not 1 <= rating <= 5 or not 10 <= len(body) <= 2000:
                        raise ValueError("Use a rating of 1–5 and review text of 10–2000 characters.")
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    cursor.execute("INSERT INTO reviews(business_id,reviewer_id,rating,body,posted,status) VALUES(%s,%s,%s,%s,%s,'Pending')",
                                   (business, reviewer, rating, body, now))
                    message = "Added review #" + str(cursor.lastrowid)
                elif action in ("delete", "reviewed"):
                    review_id = int(request.form["id"])
                    if action == "delete":
                        cursor.execute("DELETE FROM reviews WHERE id=%s", (review_id,))
                    else:
                        cursor.execute("UPDATE reviews SET status='Reviewed' WHERE id=%s", (review_id,))
                    if cursor.rowcount == 0:
                        raise ValueError("Review not found or already updated.")
                    message = action + " review #" + str(review_id)
                else:
                    raise ValueError("Unknown action.")
                cursor.execute("INSERT INTO audit(action,created) VALUES(%s,UTC_TIMESTAMP(3))", (message,))
                connection.commit()
                return redirect("/")
            except (ValueError, mysql.connector.Error) as problem:
                connection.rollback()
                error = str(problem) if isinstance(problem, ValueError) else "Database rejected the change. Check the selected records."

        cursor.execute("SELECT r.*, b.name business, u.name reviewer FROM reviews r JOIN businesses b ON r.business_id=b.id JOIN reviewers u ON r.reviewer_id=u.id ORDER BY r.posted DESC,r.id DESC")
        reviews = cursor.fetchall()
        check_reviews(reviews)
        cursor.execute("SELECT id,name FROM businesses")
        businesses = cursor.fetchall()
        cursor.execute("SELECT id,name FROM reviewers")
        reviewers = cursor.fetchall()
        flagged = sum(r["score"] >= 60 for r in reviews)
        search = request.args.get("search", "").lower()
        rows = [r for r in reviews if search in (r["business"] + r["reviewer"] + r["body"]).lower()]
        if request.args.get("flagged") == "yes":
            rows = [r for r in rows if r["score"] >= 60]
        page = max(1, request.args.get("page", 1, type=int))
        pages = max(1, (len(rows) + 24) // 25)
        page = min(page, pages)
        return render_template("index.html", reviews=rows[(page-1)*25:page*25],
                               businesses=businesses, reviewers=reviewers, total=len(reviews),
                               flagged=flagged, error=error, page=page, pages=pages)
    except mysql.connector.Error:
        return "Cannot connect to MySQL. Check that MySQL is running and .env has the correct settings.", 503
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(settings.get("PORT", 3000)))

"""Exports only the original synthetic review IDs; never exports credentials."""
import json
from datetime import datetime, timezone, date
from pathlib import Path
import mysql.connector
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import settings, check_reviews
from ml_model import apply_model
from build_demo import build

SPACE = ROOT/".space-build"


def prepare():
    build(fetch_snapshot=False)
    connection = mysql.connector.connect(
        host=settings.get("MYSQL_HOST","127.0.0.1"),port=int(settings.get("MYSQL_PORT",3306)),
        user=settings.get("MYSQL_USER","root"),password=settings.get("MYSQL_PASSWORD",""),
        database=settings.get("MYSQL_DATABASE","trustcheck_local"))
    try:
        cursor = connection.cursor(dictionary=True,buffered=True)
        cursor.execute("SELECT r.*,b.name business,u.name reviewer FROM reviews r JOIN businesses b ON r.business_id=b.id JOIN reviewers u ON r.reviewer_id=u.id WHERE r.id BETWEEN 1 AND 516 ORDER BY r.posted DESC,r.id DESC")
        reviews = cursor.fetchall()
        cursor.execute("SELECT id,name,category,city FROM businesses WHERE id BETWEEN 1 AND 8")
        businesses = cursor.fetchall()
        cursor.execute("SELECT id,name,joined FROM reviewers WHERE id BETWEEN 1 AND 96")
        reviewers = cursor.fetchall()
        check_reviews(reviews)
        apply_model(reviews,reviewers)
        snapshot={"reviews":reviews,"businesses":businesses,
                  "exported_at":datetime.now(timezone.utc).isoformat(),
                  "provenance":"Original synthetic seed IDs 1–516 only. Read-only snapshot, not a live MySQL connection."}
        def encode(value):
            if isinstance(value,(date,datetime)):return value.isoformat()
            raise TypeError(type(value).__name__)
        (SPACE/"demo_data.json").write_text(json.dumps(snapshot,default=encode),encoding="utf-8")
    finally:
        connection.close()
    print("Prepared Space:",len(reviews),"synthetic reviews. No .env or database credentials copied.")


if __name__ == "__main__":
    prepare()

// 1. Load the two libraries: Express handles HTTP; mysql2 talks to MySQL.
import express from "express";
import mysql from "mysql2/promise";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { analyze } from "./analysis.js";

const folder = path.dirname(fileURLToPath(import.meta.url));
process.loadEnvFile(path.join(folder, ".env"));
const app = express();
app.use(express.json({ limit: "16kb" }));

// 2. Open a connection pool. Password stays on the server in .env.
const db = mysql.createPool({
  host: process.env.MYSQL_HOST || "127.0.0.1",
  port: Number(process.env.MYSQL_PORT || 3306),
  user: process.env.MYSQL_USER || "root",
  password: process.env.MYSQL_PASSWORD || "",
  database: process.env.MYSQL_DATABASE || "trustcheck_local",
  charset: "utf8mb4",
  timezone: "Z",
  dateStrings: true,
  connectionLimit: 5
});

function sqlTime() {
  return new Date().toISOString().slice(0, 23).replace("T", " ");
}
function isoTime(time) {
  return time.replace(" ", "T") + "Z";
}

// 3. Send just the three public website files. Do not expose .env.
app.get("/", (request, response) => response.sendFile(path.join(folder, "index.html")));
app.get("/style.css", (request, response) => response.sendFile(path.join(folder, "style.css")));
app.get("/app.js", (request, response) => response.sendFile(path.join(folder, "app.js")));

// 4. READ: join reviews with businesses and reviewers; calculate scores.
app.get("/api/data", async (request, response) => {
  try {
    const [reviews] = await db.query(
      "SELECT r.*, b.name business, b.category, u.name reviewer " +
      "FROM reviews r JOIN businesses b ON r.business_id=b.id " +
      "JOIN reviewers u ON r.reviewer_id=u.id ORDER BY r.posted DESC, r.id DESC"
    );
    const [businesses] = await db.query("SELECT * FROM businesses");
    const [reviewers] = await db.query("SELECT * FROM reviewers");
    const [audit] = await db.query("SELECT * FROM audit ORDER BY id DESC LIMIT 30");
    for (const review of reviews) review.posted = isoTime(review.posted);
    for (const entry of audit) entry.created = isoTime(entry.created);
    response.json({ reviews: analyze(reviews), businesses, reviewers, audit });
  } catch (error) {
    console.error(error.code || error.message);
    response.status(503).json({
      error: "Cannot read MySQL. Check .env, start MySQL, and import database.sql."
    });
  }
});

// 5. CREATE / UPDATE / DELETE: ? placeholders keep values separate from SQL.
// Each change and its audit entry commit together in one transaction.
app.post("/api/reviews", async (request, response) => {
  let connection;
  try {
    const data = request.body;
    if (!["add", "status", "delete"].includes(data.action)) {
      throw new Error("Choose add, status, or delete.");
    }
    connection = await db.getConnection();
    await connection.beginTransaction();
    let description;

    if (data.action === "add") {
      const business = Number(data.businessId);
      const reviewer = Number(data.reviewerId);
      const rating = Number(data.rating);
      if (!Number.isInteger(business) || !Number.isInteger(reviewer) ||
          !Number.isInteger(rating) || rating < 1 || rating > 5 ||
          typeof data.body !== "string" || data.body.trim().length < 10 ||
          data.body.length > 2000) {
        throw new Error("Choose a business, reviewer, rating 1–5, and text of 10–2000 characters.");
      }
      const [result] = await connection.execute(
        "INSERT INTO reviews(business_id,reviewer_id,rating,body,posted,status) VALUES (?,?,?,?,?,?)",
        [business, reviewer, rating, data.body.trim(), sqlTime(), "Pending"]
      );
      description = "Added review #" + result.insertId;
    } else {
      const id = Number(data.id);
      if (!Number.isInteger(id) || id < 1) throw new Error("Invalid review ID.");
      const [exists] = await connection.execute(
        "SELECT id FROM reviews WHERE id=? FOR UPDATE", [id]
      );
      if (exists.length === 0) throw new Error("Review not found.");
      if (data.action === "delete") {
        await connection.execute("DELETE FROM reviews WHERE id=?", [id]);
        description = "Deleted review #" + id;
      } else {
        if (!["Pending", "Reviewed", "Dismissed"].includes(data.status)) {
          throw new Error("Invalid status.");
        }
        await connection.execute("UPDATE reviews SET status=? WHERE id=?", [data.status, id]);
        description = "Review #" + id + " marked " + data.status;
      }
    }
    await connection.execute(
      "INSERT INTO audit(action,created) VALUES (?,?)", [description, sqlTime()]
    );
    await connection.commit();
    response.json({ ok: true });
  } catch (error) {
    if (connection) await connection.rollback();
    console.error(error.code || error.message);
    response.status(400).json({
      error: error.code ? "MySQL rejected the change. Check the connection and linked records." : error.message
    });
  } finally {
    if (connection) connection.release();
  }
});

// 6. Start on this laptop only.
const port = Number(process.env.PORT || 3000);
app.listen(port, "127.0.0.1", () => {
  console.log("TrustCheck: http://127.0.0.1:" + port);
  console.log("Keep this window open. Press Ctrl+C to stop.");
});

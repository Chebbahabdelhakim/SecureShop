const path = require("path");
const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const _ = require("lodash");

const PORT = 8004;
const DB_PATH = path.join(__dirname, "payments.db");

const app = express();
app.use(express.json());

function getDb() {
  return new sqlite3.Database(DB_PATH);
}

function initDb() {
  const db = getDb();
  db.serialize(() => {
    db.run(
      `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        amount_cents INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
      )`,
      (err) => {
        if (err) {
          console.error(err);
          return;
        }
        db.get("SELECT COUNT(*) AS c FROM payments", (e, row) => {
          if (e || !row || row.c > 0) {
            db.close();
            return;
          }
          db.run(
            "INSERT INTO payments (order_id, amount_cents, status) VALUES (?, ?, ?)",
            [1, 1998, "captured"],
            () => db.close()
          );
        });
      }
    );
  });
}

initDb();

app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", service: "payment-service" });
});

app.get("/payments", (req, res) => {
  const db = getDb();
  db.all("SELECT id, order_id, amount_cents, status FROM payments", [], (err, rows) => {
    db.close();
    if (err) {
      return res.status(500).json({ error: "database error" });
    }
    res.status(200).json(rows || []);
  });
});

app.get("/payments/:id", (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (Number.isNaN(id)) {
    return res.status(400).json({ error: "invalid id" });
  }
  const db = getDb();
  db.get(
    "SELECT id, order_id, amount_cents, status FROM payments WHERE id = ?",
    [id],
    (err, row) => {
      db.close();
      if (err) {
        return res.status(500).json({ error: "database error" });
      }
      if (!row) {
        return res.status(404).json({ error: "not found" });
      }
      res.status(200).json(row);
    }
  );
});

app.post("/payments", (req, res) => {
  const { order_id, amount_cents, metadata } = req.body || {};
  if (order_id == null || amount_cents == null) {
    return res.status(400).json({ error: "order_id and amount_cents required" });
  }
  const base = { order_id, amount_cents, status: "pending" };
  // VULNERABILITY: lodash@4.17.19 in package.json has known CVEs; merge with untrusted input is unsafe on vulnerable builds.
  const payload = _.merge({}, base, metadata || {});
  const db = getDb();
  db.run(
    "INSERT INTO payments (order_id, amount_cents, status) VALUES (?, ?, ?)",
    [payload.order_id, payload.amount_cents, payload.status || "pending"],
    function onRun(err) {
      db.close();
      if (err) {
        return res.status(500).json({ error: "database error" });
      }
      res.status(201).json({ id: this.lastID, status: "created" });
    }
  );
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`payment-service listening on ${PORT}`);
});

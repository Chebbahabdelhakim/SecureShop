const path = require("path");
const fs = require("fs");
const express = require("express");
const sqlite3 = require("sqlite3").verbose();

const PORT = 8005;
const DB_PATH = path.join(__dirname, "notifications.db");

const app = express();
app.use(express.json());

function getDb() {
  return new sqlite3.Database(DB_PATH);
}

function initDb() {
  const db = getDb();
  db.serialize(() => {
    db.run(
      `CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      )`,
      (err) => {
        if (err) {
          console.error(err);
          return;
        }
        db.get("SELECT COUNT(*) AS c FROM notifications", (e, row) => {
          if (e || !row || row.c > 0) {
            db.close();
            return;
          }
          db.run(
            "INSERT INTO notifications (channel, message) VALUES (?, ?)",
            ["email", "Welcome to SecureShop"],
            () => db.close()
          );
        });
      }
    );
  });
}

initDb();

app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", service: "notification-service" });
});

app.get("/notifications", (req, res) => {
  const db = getDb();
  db.all(
    "SELECT id, channel, message, created_at FROM notifications ORDER BY id DESC",
    [],
    (err, rows) => {
      db.close();
      if (err) {
        return res.status(500).json({ error: "database error" });
      }
      res.status(200).json(rows || []);
    }
  );
});

app.post("/notifications", (req, res) => {
  const { channel, message } = req.body || {};
  if (!channel || !message) {
    return res.status(400).json({ error: "channel and message required" });
  }
  const db = getDb();
  db.run(
    "INSERT INTO notifications (channel, message) VALUES (?, ?)",
    [String(channel), String(message)],
    function onRun(err) {
      db.close();
      if (err) {
        return res.status(500).json({ error: "database error" });
      }
      res.status(201).json({ id: this.lastID, status: "created" });
    }
  );
});

app.get("/notifications/:id", (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (Number.isNaN(id)) {
    return res.status(400).json({ error: "invalid id" });
  }
  const db = getDb();
  db.get(
    "SELECT id, channel, message, created_at FROM notifications WHERE id = ?",
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

app.listen(PORT, "0.0.0.0", () => {
  console.log(`notification-service listening on ${PORT}`);
});

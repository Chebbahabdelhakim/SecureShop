import os
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from flask import Flask, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

# VULNERABILITY: Hardcoded JWT signing secret committed to source; rotate and use env/secret manager in production.
JWT_SECRET = "insecure_workshop_jwt_secret_do_not_use_in_prod"
JWT_ALGORITHM = "HS256"

DATABASE = os.path.join(os.path.dirname(__file__), "users.db")

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )
    cur = db.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()[0] == 0:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("demo", generate_password_hash("demo123")),
        )
        db.commit()
    db.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "user-service"}), 200


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(row["id"]),
        "username": row["username"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return jsonify({"access_token": token, "token_type": "Bearer"}), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db = get_db()
    row = db.execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row["id"], "username": row["username"]}), 200


with app.app_context():
    init_db()

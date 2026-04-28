import os
import sqlite3

from flask import Flask, g, jsonify, request

DATABASE = os.path.join(os.path.dirname(__file__), "orders.db")

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
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    cur = db.execute("SELECT COUNT(*) AS c FROM orders")
    if cur.fetchone()[0] == 0:
        db.execute(
            "INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (1, 1, 2),
        )
        db.commit()
    db.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "order-service"}), 200


@app.route("/orders", methods=["GET"])
def list_orders():
    db = get_db()
    rows = db.execute(
        "SELECT id, user_id, product_id, quantity FROM orders"
    ).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if user_id is None or product_id is None:
        return jsonify({"error": "user_id and product_id required"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)",
        (int(user_id), int(product_id), int(quantity)),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "status": "created"}), 201


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    db = get_db()
    row = db.execute(
        "SELECT id, user_id, product_id, quantity FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row)), 200


with app.app_context():
    init_db()

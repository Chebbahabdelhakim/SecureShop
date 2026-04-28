import os
import sqlite3

from flask import Flask, g, jsonify, request

DATABASE = os.path.join(os.path.dirname(__file__), "inventory.db")

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
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INTEGER PRIMARY KEY,
            quantity INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur = db.execute("SELECT COUNT(*) AS c FROM inventory")
    if cur.fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO inventory (product_id, quantity) VALUES (?, ?)",
            [(1, 100), (2, 50)],
        )
        db.commit()
    db.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "inventory-service"}), 200


@app.route("/inventory", methods=["GET"])
def list_inventory():
    db = get_db()
    rows = db.execute("SELECT product_id, quantity FROM inventory").fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/inventory/<int:product_id>", methods=["GET"])
def get_stock(product_id):
    db = get_db()
    row = db.execute(
        "SELECT product_id, quantity FROM inventory WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row)), 200


@app.route("/inventory/<int:product_id>", methods=["PATCH"])
def update_stock(product_id):
    data = request.get_json(silent=True) or {}
    delta = data.get("quantity_delta")
    if delta is None:
        return jsonify({"error": "quantity_delta required"}), 400
    db = get_db()
    row = db.execute(
        "SELECT quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    new_qty = row["quantity"] + int(delta)
    db.execute(
        "UPDATE inventory SET quantity = ? WHERE product_id = ?",
        (new_qty, product_id),
    )
    db.commit()
    return jsonify({"product_id": product_id, "quantity": new_qty}), 200


with app.app_context():
    init_db()

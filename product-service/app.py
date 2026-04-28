import os
import sqlite3

from flask import Flask, g, jsonify, request

DATABASE = os.path.join(os.path.dirname(__file__), "products.db")

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
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL
        )
        """
    )
    cur = db.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO products (name, price_cents) VALUES (?, ?)",
            [("Widget", 999), ("Gadget", 1499)],
        )
        db.commit()
    db.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "product-service"}), 200


@app.route("/products", methods=["GET"])
def list_products():
    db = get_db()
    rows = db.execute("SELECT id, name, price_cents FROM products").fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/products/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "")
    db = get_db()
    # VULNERABILITY: User-controlled value concatenated into SQL enables SQL injection; use parameterized queries.
    sql = "SELECT id, name, price_cents FROM products WHERE name LIKE '%" + q + "%'"
    rows = db.execute(sql).fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    db = get_db()
    row = db.execute(
        "SELECT id, name, price_cents FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row)), 200


with app.app_context():
    init_db()

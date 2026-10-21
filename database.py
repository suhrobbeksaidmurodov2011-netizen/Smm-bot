import sqlite3
from contextlib import closing
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(get_conn()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                price INTEGER NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                payment_method TEXT,
                total INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'kutilmoqda',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)


# ---------- Categories ----------

def add_category(name):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        return cur.lastrowid


def get_categories():
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()


# ---------- Products ----------

def add_product(category_id, name, description, price, stock):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO products (category_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)",
            (category_id, name, description, price, stock),
        )
        return cur.lastrowid


def get_products(category_id=None, active_only=True):
    with closing(get_conn()) as conn:
        q = "SELECT * FROM products"
        conds, params = [], []
        if category_id is not None:
            conds.append("category_id = ?")
            params.append(category_id)
        if active_only:
            conds.append("active = 1")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY name"
        return conn.execute(q, params).fetchall()


def get_product(product_id):
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def update_product_stock(product_id, delta):
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (delta, product_id))


def set_product_active(product_id, active):
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE products SET active = ? WHERE id = ?", (1 if active else 0, product_id))


def delete_product(product_id):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


# ---------- Cart ----------

def add_to_cart(user_id, product_id, quantity=1):
    with closing(get_conn()) as conn, conn:
        existing = conn.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
                (quantity, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity),
            )


def get_cart(user_id):
    with closing(get_conn()) as conn:
        return conn.execute("""
            SELECT ci.id as cart_id, ci.quantity, p.id as product_id, p.name, p.price
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.id
        """, (user_id,)).fetchall()


def remove_from_cart(cart_id):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM cart_items WHERE id = ?", (cart_id,))


def clear_cart(user_id):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))


def cart_total(user_id):
    items = get_cart(user_id)
    return sum(i["price"] * i["quantity"] for i in items)


# ---------- Orders ----------

def create_order(user_id, username, full_name, phone, address, payment_method, items, total):
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("""
            INSERT INTO orders (user_id, username, full_name, phone, address, payment_method, total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, phone, address, payment_method, total))
        order_id = cur.lastrowid
        for item in items:
            conn.execute("""
                INSERT INTO order_items (order_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?)
            """, (order_id, item["name"], item["price"], item["quantity"]))
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                         (item["quantity"], item["product_id"]))
        return order_id


def get_order(order_id):
    with closing(get_conn()) as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        return order, items


def get_orders(status=None, user_id=None):
    with closing(get_conn()) as conn:
        q = "SELECT * FROM orders"
        conds, params = [], []
        if status:
            conds.append("status = ?")
            params.append(status)
        if user_id:
            conds.append("user_id = ?")
            params.append(user_id)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY created_at DESC"
        return conn.execute(q, params).fetchall()


def update_order_status(order_id, status):
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

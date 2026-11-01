"""SQLite data layer: users, products, cart and orders."""

import hashlib
import os
import sqlite3
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shop.db")

SAMPLE_PRODUCTS = [
    ("Wireless Headphones", "Electronics", 2499.00, 25, "Over-ear Bluetooth headphones with 30h battery."),
    ("Smart Watch", "Electronics", 3999.00, 15, "Fitness tracking, heart-rate monitor, notifications."),
    ("USB-C Charger 65W", "Electronics", 1299.00, 40, "Fast charger for laptops and phones."),
    ("Bluetooth Speaker", "Electronics", 1799.00, 20, "Portable waterproof speaker with deep bass."),
    ("Cotton T-Shirt", "Fashion", 499.00, 100, "100% cotton, regular fit, available in many colours."),
    ("Denim Jeans", "Fashion", 1499.00, 50, "Slim fit stretchable denim jeans."),
    ("Running Shoes", "Fashion", 2999.00, 30, "Lightweight shoes with cushioned sole."),
    ("Leather Wallet", "Fashion", 799.00, 60, "Genuine leather bi-fold wallet."),
    ("Python Crash Course", "Books", 899.00, 35, "A hands-on, project-based introduction to programming."),
    ("Atomic Habits", "Books", 499.00, 45, "An easy and proven way to build good habits."),
    ("The Alchemist", "Books", 299.00, 55, "A fable about following your dream."),
    ("Non-stick Frying Pan", "Home & Kitchen", 999.00, 25, "28 cm induction-friendly frying pan."),
    ("Coffee Mug Set", "Home & Kitchen", 649.00, 40, "Set of 4 ceramic mugs."),
    ("Table Lamp", "Home & Kitchen", 1199.00, 18, "LED desk lamp with adjustable brightness."),
    ("Yoga Mat", "Sports", 699.00, 35, "6 mm anti-slip exercise mat."),
    ("Cricket Bat", "Sports", 1899.00, 12, "English willow bat for leather ball."),
]


def hash_password(password, salt=None):
    """Return 'salt$hash' using PBKDF2-SHA256."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password, stored):
    salt, _ = stored.split("$", 1)
    return hash_password(password, salt) == stored


class Database:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._seed()

    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS cart_items (
                user_id INTEGER NOT NULL REFERENCES users(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL,
                PRIMARY KEY (user_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                total REAL NOT NULL,
                address TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Placed',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            );
            """
        )
        self.conn.commit()

    def _seed(self):
        if self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            self.conn.executemany(
                "INSERT INTO products (name, category, price, stock, description) VALUES (?, ?, ?, ?, ?)",
                SAMPLE_PRODUCTS,
            )
        if self.conn.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0] == 0:
            self.conn.execute(
                "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 1)",
                ("Admin", "admin@shop.com", hash_password("admin123")),
            )
        self.conn.commit()

    # ---------- users ----------
    def register(self, name, email, password):
        name, email = name.strip(), email.strip().lower()
        if not name or not email or not password:
            raise ValueError("All fields are required.")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Please enter a valid email address.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        try:
            cur = self.conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hash_password(password)),
            )
        except sqlite3.IntegrityError:
            raise ValueError("An account with this email already exists.")
        self.conn.commit()
        return self.get_user(cur.lastrowid)

    def login(self, email, password):
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        if row is None or not verify_password(password, row["password"]):
            raise ValueError("Invalid email or password.")
        return row

    def get_user(self, user_id):
        return self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    # ---------- products ----------
    def categories(self):
        rows = self.conn.execute("SELECT DISTINCT category FROM products ORDER BY category")
        return [r["category"] for r in rows]

    def products(self, search="", category="All", sort="Name"):
        query = "SELECT * FROM products WHERE (name LIKE ? OR description LIKE ?)"
        params = [f"%{search}%", f"%{search}%"]
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        order = {
            "Name": "name",
            "Price: Low to High": "price ASC",
            "Price: High to Low": "price DESC",
        }.get(sort, "name")
        return self.conn.execute(f"{query} ORDER BY {order}", params).fetchall()

    def get_product(self, product_id):
        return self.conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    def add_product(self, name, category, price, stock, description=""):
        self._validate_product(name, category, price, stock)
        cur = self.conn.execute(
            "INSERT INTO products (name, category, price, stock, description) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), category.strip(), float(price), int(stock), description.strip()),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id, name, category, price, stock, description=""):
        self._validate_product(name, category, price, stock)
        self.conn.execute(
            "UPDATE products SET name=?, category=?, price=?, stock=?, description=? WHERE id=?",
            (name.strip(), category.strip(), float(price), int(stock), description.strip(), product_id),
        )
        self.conn.commit()

    def delete_product(self, product_id):
        self.conn.execute("DELETE FROM cart_items WHERE product_id = ?", (product_id,))
        self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()

    @staticmethod
    def _validate_product(name, category, price, stock):
        if not name.strip() or not category.strip():
            raise ValueError("Name and category are required.")
        try:
            price, stock = float(price), int(stock)
        except (TypeError, ValueError):
            raise ValueError("Price must be a number and stock a whole number.")
        if price <= 0 or stock < 0:
            raise ValueError("Price must be positive and stock cannot be negative.")

    # ---------- cart ----------
    def cart(self, user_id):
        return self.conn.execute(
            """SELECT p.id, p.name, p.price, p.stock, c.quantity, p.price * c.quantity AS subtotal
               FROM cart_items c JOIN products p ON p.id = c.product_id
               WHERE c.user_id = ? ORDER BY p.name""",
            (user_id,),
        ).fetchall()

    def cart_count(self, user_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row[0]

    def add_to_cart(self, user_id, product_id, quantity=1):
        product = self.get_product(product_id)
        if product is None:
            raise ValueError("Product not found.")
        row = self.conn.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        new_qty = (row["quantity"] if row else 0) + quantity
        if new_qty > product["stock"]:
            raise ValueError(f"Only {product['stock']} of '{product['name']}' in stock.")
        self.set_cart_quantity(user_id, product_id, new_qty)

    def set_cart_quantity(self, user_id, product_id, quantity):
        if quantity <= 0:
            self.conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id)
            )
        else:
            product = self.get_product(product_id)
            if quantity > product["stock"]:
                raise ValueError(f"Only {product['stock']} of '{product['name']}' in stock.")
            self.conn.execute(
                """INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)
                   ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = excluded.quantity""",
                (user_id, product_id, quantity),
            )
        self.conn.commit()

    def clear_cart(self, user_id):
        self.conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        self.conn.commit()

    # ---------- orders ----------
    def place_order(self, user_id, address, payment_method):
        if not address.strip():
            raise ValueError("Please enter a delivery address.")
        items = self.cart(user_id)
        if not items:
            raise ValueError("Your cart is empty.")
        for item in items:
            if item["quantity"] > item["stock"]:
                raise ValueError(f"Not enough stock for '{item['name']}'.")
        total = sum(item["subtotal"] for item in items)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO orders (user_id, total, address, payment_method, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, total, address.strip(), payment_method,
                 datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            order_id = cur.lastrowid
            for item in items:
                self.conn.execute(
                    "INSERT INTO order_items (order_id, product_id, name, price, quantity) VALUES (?, ?, ?, ?, ?)",
                    (order_id, item["id"], item["name"], item["price"], item["quantity"]),
                )
                self.conn.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?", (item["quantity"], item["id"])
                )
            self.conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        return order_id

    def orders(self, user_id=None):
        if user_id is None:
            return self.conn.execute(
                """SELECT o.*, u.name AS customer FROM orders o JOIN users u ON u.id = o.user_id
                   ORDER BY o.id DESC"""
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()

    def order_items(self, order_id):
        return self.conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
        ).fetchall()

    def update_order_status(self, order_id, status):
        self.conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

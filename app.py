from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, g, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "ukayease-secret-key-change-in-production"

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ukayease.db")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            size TEXT,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Available'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            customer_name TEXT,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # Seed default admin user
    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        hashed = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", hashed)
        )

    # Seed sample thrift products if catalog is empty
    cursor.execute("SELECT COUNT(*) AS cnt FROM products")
    if cursor.fetchone()["cnt"] == 0:
        samples = [
            ("Vintage Levi's Denim Jacket", "Jacket", "M", 450.00, 3, "Available"),
            ("Floral Summer Dress", "Dress", "S", 280.00, 5, "Available"),
            ("Classic White T-Shirt", "T-Shirt", "L", 120.00, 8, "Available"),
            ("High-Waist Mom Jeans", "Pants", "28", 350.00, 4, "Available"),
            ("Leather Crossbody Bag", "Bag", "One Size", 520.00, 2, "Available"),
        ]
        cursor.executemany(
            """INSERT INTO products
               (item_name, category, size, price, quantity, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            samples
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
# Routes – Authentication
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes – Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()

    total_products = conn.execute(
        "SELECT COUNT(*) AS cnt FROM products"
    ).fetchone()["cnt"]

    available_items = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM products WHERE status = 'Available'"
    ).fetchone()["total"]

    sold_items = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM sales"
    ).fetchone()["total"]

    total_sales = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales"
    ).fetchone()["total"]

    recent_products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC LIMIT 5"
    ).fetchall()

    recent_sales = conn.execute(
        "SELECT * FROM sales ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        available_items=available_items,
        sold_items=sold_items,
        total_sales=total_sales,
        recent_products=recent_products,
        recent_sales=recent_sales,
    )


# ---------------------------------------------------------------------------
# Routes – Products
# ---------------------------------------------------------------------------

@app.route("/products")
@login_required
def products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db_connection()
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (item_name LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"
    products_list = conn.execute(query, params).fetchall()

    categories = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    conn.close()

    return render_template(
        "products.html",
        products=products_list,
        categories=categories,
        search=search,
        selected_category=category,
    )


@app.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    categories = [
        "T-Shirt", "Pants", "Dress", "Jacket", "Skirt", "Shoes", "Bag", "Other"
    ]

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        size = request.form.get("size", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()

        errors = []
        if not item_name:
            errors.append("Item name is required.")
        if not category or category not in categories:
            errors.append("Please select a valid category.")
        try:
            price_val = float(price)
            if price_val < 0:
                errors.append("Price must be zero or greater.")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number.")
            price_val = 0
        try:
            qty_val = int(quantity)
            if qty_val < 0:
                errors.append("Quantity must be zero or greater.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a whole number.")
            qty_val = 0

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "add_product.html",
                categories=categories,
                form=request.form,
            )

        status = "Available" if qty_val > 0 else "Sold"

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO products
               (item_name, category, size, price, quantity, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item_name, category, size, price_val, qty_val, status)
        )
        conn.commit()
        conn.close()

        flash(f'Product "{item_name}" added successfully!', "success")
        return redirect(url_for("products"))

    return render_template("add_product.html", categories=categories, form={})


@app.route("/edit-product/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    categories = [
        "T-Shirt", "Pants", "Dress", "Jacket", "Skirt", "Shoes", "Bag", "Other"
    ]

    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()

    if product is None:
        conn.close()
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        size = request.form.get("size", "").strip()
        price = request.form.get("price", "").strip()
        quantity = request.form.get("quantity", "").strip()
        status = request.form.get("status", "").strip()

        errors = []
        if not item_name:
            errors.append("Item name is required.")
        if not category or category not in categories:
            errors.append("Please select a valid category.")
        try:
            price_val = float(price)
            if price_val < 0:
                errors.append("Price must be zero or greater.")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number.")
            price_val = 0
        try:
            qty_val = int(quantity)
            if qty_val < 0:
                errors.append("Quantity must be zero or greater.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a whole number.")
            qty_val = 0

        if status not in ("Available", "Sold"):
            status = "Available" if qty_val > 0 else "Sold"
        # Auto-correct status based on quantity
        if qty_val == 0:
            status = "Sold"
        elif status == "Sold" and qty_val > 0:
            status = "Available"

        if errors:
            for e in errors:
                flash(e, "error")
            conn.close()
            return render_template(
                "edit_product.html",
                product=product,
                categories=categories,
                form=request.form,
            )

        conn.execute(
            """UPDATE products
               SET item_name=?, category=?, size=?, price=?, quantity=?, status=?
               WHERE id=?""",
            (item_name, category, size, price_val, qty_val, status, id)
        )
        conn.commit()
        conn.close()

        flash(f'Product "{item_name}" updated successfully!', "success")
        return redirect(url_for("products"))

    conn.close()
    return render_template(
        "edit_product.html",
        product=product,
        categories=categories,
        form={},
    )


@app.route("/delete-product/<int:id>", methods=["POST"])
@login_required
def delete_product(id):
    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (id,)
    ).fetchone()

    if product is None:
        conn.close()
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    name = product["item_name"]
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash(f'Product "{name}" deleted.', "success")
    return redirect(url_for("products"))


# ---------------------------------------------------------------------------
# Routes – Sales
# ---------------------------------------------------------------------------

@app.route("/sales", methods=["GET", "POST"])
@login_required
def sales():
    conn = get_db_connection()

    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        quantity = request.form.get("quantity", "").strip()
        customer_name = request.form.get("customer_name", "").strip() or "Walk-in"
        sale_date = request.form.get("sale_date", "").strip()

        errors = []
        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            errors.append("Please select a product.")
            product_id = None

        try:
            qty = int(quantity)
            if qty <= 0:
                errors.append("Quantity must be at least 1.")
        except (ValueError, TypeError):
            errors.append("Quantity must be a whole number.")
            qty = 0

        if not sale_date:
            sale_date = date.today().isoformat()

        product = None
        if product_id:
            product = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if product is None:
                errors.append("Selected product not found.")
            elif product["quantity"] < qty:
                errors.append(
                    f'Insufficient stock. Only {product["quantity"]} available.'
                )
            elif product["quantity"] == 0 or product["status"] == "Sold":
                errors.append("This product is out of stock.")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            unit_price = product["price"]
            total = unit_price * qty
            new_qty = product["quantity"] - qty
            new_status = "Sold" if new_qty == 0 else "Available"

            conn.execute(
                """INSERT INTO sales
                   (product_id, product_name, customer_name, quantity,
                    unit_price, total_amount, sale_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    product_id,
                    product["item_name"],
                    customer_name,
                    qty,
                    unit_price,
                    total,
                    sale_date,
                )
            )
            conn.execute(
                "UPDATE products SET quantity=?, status=? WHERE id=?",
                (new_qty, new_status, product_id)
            )
            conn.commit()
            flash(
                f'Sale recorded: {qty} × {product["item_name"]} = ₱{total:,.2f}',
                "success"
            )
            conn.close()
            return redirect(url_for("sales"))

    available_products = conn.execute(
        "SELECT * FROM products WHERE quantity > 0 ORDER BY item_name"
    ).fetchall()

    sales_history = conn.execute(
        "SELECT * FROM sales ORDER BY id DESC"
    ).fetchall()

    conn.close()

    today = date.today().isoformat()
    return render_template(
        "sales.html",
        available_products=available_products,
        sales_history=sales_history,
        today=today,
    )


# ---------------------------------------------------------------------------
# Routes – Reports
# ---------------------------------------------------------------------------

@app.route("/reports")
@login_required
def reports():
    conn = get_db_connection()

    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales"
    ).fetchone()["total"]

    total_transactions = conn.execute(
        "SELECT COUNT(*) AS cnt FROM sales"
    ).fetchone()["cnt"]

    total_items_sold = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM sales"
    ).fetchone()["total"]

    avg_sale = total_revenue / total_transactions if total_transactions else 0

    daily_summary = conn.execute(
        """SELECT sale_date,
                  COUNT(*) AS num_sales,
                  SUM(total_amount) AS day_total
           FROM sales
           GROUP BY sale_date
           ORDER BY sale_date DESC"""
    ).fetchall()

    # Chart data (oldest → newest for proper axis order)
    chart_rows = conn.execute(
        """SELECT sale_date,
                  SUM(total_amount) AS day_total
           FROM sales
           GROUP BY sale_date
           ORDER BY sale_date ASC"""
    ).fetchall()

    chart_labels = [r["sale_date"] for r in chart_rows]
    chart_values = [float(r["day_total"]) for r in chart_rows]

    conn.close()

    return render_template(
        "reports.html",
        total_revenue=total_revenue,
        total_transactions=total_transactions,
        total_items_sold=total_items_sold,
        avg_sale=avg_sale,
        daily_summary=daily_summary,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

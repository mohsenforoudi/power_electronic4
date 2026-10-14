from pathlib import Path
import sqlite3

from flask import (
    Flask,
    abort,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "catalog.db"

app = Flask(__name__)
app.config["DATABASE"] = DATABASE


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
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
            category TEXT NOT NULL,
            power TEXT,
            voltage TEXT,
            current TEXT,
            image TEXT,
            description TEXT NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS quote_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            quantity TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """
    )

    product_count = db.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if product_count == 0:
        products = [
          (
            "اینورتر صنعتی سه‌فاز",
            "اینورتر",
            "11 کیلووات",
            "380 ولت",
            "22 آمپر",
            "inverter.jpg",
            "اینورتر مناسب برای کنترل دور موتورهای صنعتی.",
        ),
        (
            "ماژول IGBT صنعتی",
            "ماژول قدرت",
            "1200 آمپر",
            "1200 ولت",
            "1200 آمپر",
            "igbt.jpg",
            "ماژول IGBT مناسب برای مبدل‌ها و درایوهای قدرت.",
        ),
        (
            "رکتیفایر سه‌فاز",
            "رکتیفایر",
            "30 کیلووات",
            "400 ولت AC",
            "50 آمپر",
            "rectifier.jpg",
            "رکتیفایر سه‌فاز برای تبدیل AC به DC.",
        ),

              (
            "dc to dc converter",
            "converter",
            "30 کیلووات",
            "400 ولت AC",
            "50 آمپر",
            "inverter1.jpg",
            "رکتیفایر سه‌فاز برای تبدیل AC به DC.",
        ),
        ]

        db.executemany(
            """
            INSERT INTO products
            (name, category, power, voltage, current,image, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            products,
        )

    db.commit()
    db.close()


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    db = get_db()

    if query:
        pattern = f"%{query}%"
        products = db.execute(
            """
            SELECT * FROM products
            WHERE name LIKE ?
               OR category LIKE ?
               OR description LIKE ?
            ORDER BY name
            """,
            (pattern, pattern, pattern),
        ).fetchall()
    else:
        products = db.execute(
            "SELECT * FROM products ORDER BY name"
        ).fetchall()

    return render_template(
        "index.html",
        products=products,
        query=query,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()

    product = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if product is None:
        abort(404)

    return render_template("product.html", product=product)


@app.route("/quote", methods=["GET", "POST"])
def quote():
    db = get_db()
    products = db.execute(
        "SELECT * FROM products ORDER BY name"
    ).fetchall()

    selected_id = request.args.get("product_id", type=int)
    error = None

    if request.method == "POST":
        selected_id = request.form.get(
            "product_id",
            type=int,
        )

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        quantity = request.form.get("quantity", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not phone:
            error = "لطفاً نام و شماره تماس را وارد کنید."
        else:
            db.execute(
                """
                INSERT INTO quote_requests
                (product_id, name, phone, email, quantity, message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    selected_id,
                    name,
                    phone,
                    email,
                    quantity,
                    message,
                ),
            )
            db.commit()

            return redirect(url_for("quote_success"))

    return render_template(
        "quote.html",
        products=products,
        selected_id=selected_id,
        error=error,
    )


@app.route("/quote/success")
def quote_success():
    return render_template("quote_success.html")


init_db()

if __name__ == "__main__":
    app.run(debug=True)

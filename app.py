import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = "secret123"

# Postgres bazasına qoşulma funksiyası
def db_conn():
    # Vercel-in Neon vasitəsilə verdiyi POSTGRES_URL-i istifadə edirik
    uri = os.environ.get('POSTGRES_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(uri)

# Cədvəlləri Postgres üçün yaratmaq
def init_db():
    conn = db_conn()
    cur = conn.cursor()
    # Postgres-də SERIAL avtomatik artan ID üçün istifadə olunur
    cur.execute("""CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY, username TEXT, password TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS cars(id SERIAL PRIMARY KEY, brand TEXT, model TEXT, color TEXT, package TEXT, stock INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sales(id SERIAL PRIMARY KEY, car_id INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Admin istifadəçisi yoxdursa əlavə et
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username, password) VALUES('admin', '1234')")
    
    conn.commit()
    cur.close()
    conn.close()

# Sayt işə düşəndə bazanı yoxla
init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session["user"] = u
            return redirect("/dashboard")
    return """
    <style>body{font-family:Arial;background:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:white;padding:30px;border-radius:10px;width:300px}input{width:100%;padding:10px;margin:5px 0}button{width:100%;padding:10px;background:black;color:white;border:none}</style>
    <div class=box><h2>Avtosalon Login</h2><form method=post><input name=username placeholder="istifadəçi adı"><input name=password type=password placeholder="şifrə"><button>Giriş</button></form></div>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    conn = db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM cars ORDER BY id DESC")
    cars = cur.fetchall()
    cur.execute("SELECT COUNT(*) as count FROM sales")
    sales_count = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) as count FROM cars WHERE stock<=1")
    warning_count = cur.fetchone()['count']
    cur.close()
    conn.close()

    rows = ""
    for car in cars:
        stock_val = f"<span style='color:red;font-weight:bold'>TÜKƏNDİ</span>" if car["stock"]==0 else car["stock"]
        rows += f"<tr><td>{car['brand']}</td><td>{car['model']}</td><td>{car['color']}</td><td>{car['package']}</td><td>{stock_val}</td><td><a href='/sell/{car['id']}' style='color:green'>Satıldı</a></td><td><a href='/delete/{car['id']}' style='color:red'>Sil</a></td></tr>"

    return f"<html><body style='font-family:Arial; padding:20px;'><h2>Avtosalon Panel</h2><p>Satış sayı: {sales_count} | Stok xəbərdarlığı: {warning_count}</p><table border=1 style='width:100%; border-collapse:collapse;'><tr><th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th>Sat</th><th>Sil</th></tr>{rows}</table><h3>Maşın əlavə et</h3><form method=post action='/add'><input name=brand placeholder=Marka><input name=model placeholder=Model><input name=color placeholder=Rəng><input name=package placeholder=Paket><input name=stock placeholder=Say><button>Əlavə et</button></form></body></html>"

@app.route("/add", methods=["POST"])
def add():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO cars(brand, model, color, package, stock) VALUES(%s,%s,%s,%s,%s)", (request.form["brand"], request.form["model"], request.form["color"], request.form["package"], int(request.form["stock"])))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

@app.route("/sell/<id>")
def sell(id):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE cars SET stock=stock-1 WHERE id=%s AND stock>0", (id,))
    cur.execute("INSERT INTO sales(car_id) VALUES(%s)", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

@app.route("/delete/<id>")
def delete(id):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cars WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

if __name__ == "__main__":
    app.run()
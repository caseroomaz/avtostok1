import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "avtostok_2026_key"

def get_db_connection():
    uri = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(uri)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS cars (id SERIAL PRIMARY KEY, brand TEXT, model TEXT, color TEXT, package TEXT, stock INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, car_id INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
    conn.commit()
    cur.close()
    conn.close()

try:
    init_db()
except:
    pass

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user:
            session["user"] = u
            return redirect("/dashboard")
    return """
    <style>body{font-family:Arial;background:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh}
    .box{background:white;padding:30px;border-radius:10px;box-shadow:0 0 10px #ccc;width:300px}input{width:100%;padding:10px;margin:10px 0}
    button{width:100%;padding:10px;background:#000;color:#fff;border:none;cursor:pointer}</style>
    <div class='box'><h2>AvtoStok Giriş</h2><form method='POST'><input name='username' placeholder='istifadəçi'><input name='password' type='password' placeholder='şifrə'><button>Giriş</button></form></div>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM cars ORDER BY id DESC")
    cars = cur.fetchall()
    cur.execute("SELECT COUNT(*) as count FROM sales")
    total_sales = cur.fetchone()['count']
    cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{c['brand']}</td><td>{c['model']}</td><td>{c['color']}</td><td>{c['package']}</td><td>{c['stock']}</td><td><a href='/sell/{c['id']}'>Sat</a> | <a href='/delete/{c['id']}' style='color:red'>Sil</a></td></tr>" for c in cars])
    
    return f"""
    <body style='font-family:Arial;padding:20px'>
        <h2>AvtoStok Panel | Satış: {total_sales}</h2>
        <table border='1' style='width:100%;border-collapse:collapse'>
            <tr style='background:#eee'><th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th>Əməliyyat</th></tr>
            {rows if rows else "<tr><td colspan='6' align='center'>Maşın yoxdur</td></tr>"}
        </table>
        <hr><h3>Yeni Maşın</h3>
        <form action='/add' method='POST'><input name='brand' placeholder='Marka'> <input name='model' placeholder='Model'> <input name='color' placeholder='Rəng'> <input name='package' placeholder='Paket'> <input name='stock' type='number' placeholder='Say'> <button>Əlavə et</button></form>
        <br><a href='/logout'>Çıxış</a>
    </body>
    """

@app.route("/add", methods=["POST"])
def add():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO cars (brand, model, color, package, stock) VALUES (%s,%s,%s,%s,%s)", (request.form['brand'], request.form['model'], request.form['color'], request.form['package'], int(request.form['stock'])))
    conn.commit(); cur.close(); conn.close()
    return redirect("/dashboard")

@app.route("/sell/<id>")
def sell(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cars SET stock = stock - 1 WHERE id = %s AND stock > 0", (id,))
    cur.execute("INSERT INTO sales (car_id) VALUES (%s)", (id,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/dashboard")

@app.route("/delete/<id>")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cars WHERE id = %s", (id,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run()

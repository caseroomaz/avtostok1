import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = "secret123"

# Postgres bazasına qoşulma funksiyası (Zəmanətli metod)
def db_conn():
    # Vercel-in verdiyi hər iki mümkün linki yoxlayırıq
    uri = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    if not uri:
        # Əgər baza linki yoxdursa, xəta mesajı veririk
        raise Exception("Verilənlər bazası linki tapılmadı! Vercel-də Storage hissəsini yoxlayın.")
        
    return psycopg2.connect(uri)

# Cədvəlləri Postgres-ə uyğun yaratmaq
def init_db():
    conn = db_conn()
    cur = conn.cursor()
    
    # Postgres-də SERIAL avtomatik artan ID-dir
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY, 
        username TEXT, 
        password TEXT)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS cars(
        id SERIAL PRIMARY KEY, 
        brand TEXT, 
        model TEXT, 
        color TEXT, 
        package TEXT, 
        stock INTEGER)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS sales(
        id SERIAL PRIMARY KEY, 
        car_id INTEGER, 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    # Admin istifadəçisini yoxla və yoxdursa əlavə et
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username, password) VALUES('admin', '1234')")
    
    conn.commit()
    cur.close()
    conn.close()

# Proqram işə düşəndə bazanı hazırla
try:
    init_db()
except Exception as e:
    print(f"Baza yaradılarkən xəta oldu: {e}")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
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
    <style>body{font-family:Arial;background:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:white;padding:30px;border-radius:10px;width:300px}input{width:100%;padding:10px;margin:5px 0}button{width:100%;padding:10px;background:black;color:white;border:none;cursor:pointer}</style>
    <div class=box><h2>Avtosalon Login</h2><form method=post><input name=username placeholder="istifadəçi adı" required><input name=password type=password placeholder="şifrə" required><button>Giriş</button></form></div>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    conn = db_conn()
    # RealDictCursor məlumatları lüğət (dict) kimi çəkməyə imkan verir
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
        rows += f"<tr><td>{car['brand']}</td><td>{car['model']}</td><td>{car['color']}</td><td>{car['package']}</td><td>{stock_val}</td><td><a href='/sell/{car['id']}' style='color:green;text-decoration:none;font-weight:bold'>[Satıldı]</a></td><td><a href='/delete/{car['id']}' style='color:red;text-decoration:none'>[Sil]</a></td></tr>"

    return f"""
    <html>
    <head><title>Avtosalon Dashboard</title></head>
    <body style='font-family:Arial; padding:20px; background:#fafafa;'>
        <div style='max-width:900px; margin:auto; background:white; padding:20px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.1);'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2>Avtosalon Panel</h2>
                <a href='/' style='color:#666;'>Çıxış</a>
            </div>
            <div style='background:#eee; padding:15px; border-radius:5px; margin-bottom:20px;'>
                <b>Statistika:</b> Satış sayı: {sales_count} | Stok xəbərdarlığı: {warning_count}
            </div>
            <table border=1 style='width:100%; border-collapse:collapse; text-align:center;'>
                <tr style='background:#f4f4f4;'><th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th>Sat</th><th>Sil</th></tr>
                {rows if rows else "<tr><td colspan='7'>Hələ maşın əlavə edilməyib</td></tr>"}
            </table>
            <hr style='margin:30px 0;'>
            <h3>Yeni Maşın Əlavə Et</h3>
            <form method=post action='/add' style='display:grid; grid-template-columns: 1fr 1fr; gap:10px;'>
                <input name=brand placeholder=Marka required>
                <input name=model placeholder=Model required>
                <input name=color placeholder=Rəng required>
                <input name=package placeholder=Paket required>
                <input name=stock type=number placeholder=Sayı required>
                <button style='grid-column: span 2; padding:10px; background:green; color:white; border:none; border-radius:5px;'>Əlavə et</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/add", methods=["POST"])
def add():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO cars(brand, model, color, package, stock) VALUES(%s,%s,%s,%s,%s)", 
                (request.form.get("brand"), request.form.get("model"), request.form.get("color"), request.form.get("package"), int(request.form.get("stock", 0))))
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

# Vercel üçün app obyektini təqdim edirik
if __name__ == "__main__":
    app.run()
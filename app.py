import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "avtostok_2026_premium_key"

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
    cur.close(); conn.close()

try:
    init_db()
except:
    pass

# ORTAQ STİL VƏ HEAD HİSSƏSİ
header_html = """
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css'>
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .card { border: none; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .btn-primary { background-color: #0d6efd; border: none; border-radius: 8px; padding: 10px 20px; }
        .table { background: white; border-radius: 10px; overflow: hidden; }
        .navbar { background: #000 !important; color: white; }
    </style>
</head>
"""

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
    return f"""
    {header_html}
    <title>AvtoStok | Giriş</title>
    <div class='container d-flex justify-content-center align-items-center' style='min-height: 100vh;'>
        <div class='card p-4' style='width: 100%; max-width: 400px;'>
            <div class='text-center mb-4'>
                <i class='bi bi-speedometer2' style='font-size: 3rem; color: #0d6efd;'></i>
                <h3 class='mt-2 fw-bold'>AvtoStok Panel</h3>
                <p class='text-muted'>Zəhmət olmasa daxil olun</p>
            </div>
            <form method='POST'>
                <div class='mb-3'>
                    <label class='form-label'>İstifadəçi adı</label>
                    <input name='username' class='form-control form-control-lg' placeholder='admin' required>
                </div>
                <div class='mb-4'>
                    <label class='form-label'>Şifrə</label>
                    <input name='password' type='password' class='form-control form-control-lg' placeholder='****' required>
                </div>
                <button class='btn btn-primary w-100 btn-lg shadow-sm'>Daxil ol</button>
            </form>
        </div>
    </div>
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
    
    rows = ""
    for c in cars:
        stock_badge = f"<span class='badge bg-danger'>Tükəndi</span>" if c['stock'] <= 0 else f"<span class='badge bg-success'>{c['stock']} ədəd</span>"
        rows += f"""
        <tr>
            <td class='fw-bold'>{c['brand']}</td>
            <td>{c['model']}</td>
            <td><span class='badge bg-secondary'>{c['color']}</span></td>
            <td>{c['package']}</td>
            <td>{stock_badge}</td>
            <td>
                <div class='btn-group btn-group-sm'>
                    <a href='/sell/{c['id']}' class='btn btn-outline-success'><i class='bi bi-cart-check'></i> Sat</a>
                    <a href='/delete/{c['id']}' class='btn btn-outline-danger' onclick="return confirm('Silinsin?')"><i class='bi bi-trash'></i></a>
                </div>
            </td>
        </tr>
        """
    
    return f"""
    {header_html}
    <title>Dashboard | AvtoStok</title>
    <nav class='navbar navbar-dark mb-4 py-3 shadow-sm'>
        <div class='container'>
            <span class='navbar-brand mb-0 h1'><i class='bi bi-speedometer2 me-2'></i> AVTOSTOK</span>
            <div class='d-flex align-items-center text-white'>
                <span class='me-3 d-none d-md-inline'>Xoş gəldin, <b>{session['user']}</b></span>
                <a href='/logout' class='btn btn-sm btn-outline-light'>Çıxış</a>
            </div>
        </div>
    </nav>
    <div class='container'>
        <div class='row mb-4'>
            <div class='col-md-4'>
                <div class='card p-3 text-center'>
                    <h6 class='text-muted mb-1 text-uppercase'>Ümumi Satış</h6>
                    <h2 class='fw-bold text-primary mb-0'>{total_sales}</h2>
                </div>
            </div>
        </div>

        <div class='row'>
            <div class='col-lg-8 mb-4'>
                <div class='card p-4 shadow-sm h-100'>
                    <h5 class='mb-4 fw-bold'><i class='bi bi-list-ul me-2'></i> Maşın Siyahısı</h5>
                    <div class='table-responsive'>
                        <table class='table table-hover align-middle'>
                            <thead class='table-light'>
                                <tr><th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th>Əməliyyat</th></tr>
                            </thead>
                            <tbody>
                                {rows if rows else "<tr><td colspan='6' class='text-center py-4 text-muted'>Hələ maşın əlavə edilməyib</td></tr>"}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class='col-lg-4 mb-4'>
                <div class='card p-4 shadow-sm'>
                    <h5 class='mb-4 fw-bold'><i class='bi bi-plus-circle me-2'></i> Yeni Maşın</h5>
                    <form action='/add' method='POST'>
                        <div class='mb-3'><input name='brand' class='form-control' placeholder='Marka (məs: BMW)' required></div>
                        <div class='mb-3'><input name='model' class='form-control' placeholder='Model (məs: M5)' required></div>
                        <div class='mb-3'><input name='color' class='form-control' placeholder='Rəng'></div>
                        <div class='mb-3'><input name='package' class='form-control' placeholder='Paket (məs: Full)'></div>
                        <div class='mb-3'><input name='stock' type='number' class='form-control' placeholder='Stok sayı' required></div>
                        <button class='btn btn-primary w-100 fw-bold'>Əlavə et</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
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

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "avtostok_ultimate_2026"

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

header_html = """
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css'>
    <style>
        :root { --primary-color: #2c3e50; --accent-color: #3498db; }
        body { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
        .navbar { background: var(--primary-color) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card { border: none; border-radius: 12px; transition: transform 0.2s; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .stat-card { border-left: 5px solid var(--accent-color); }
        .table thead { background: #f8f9fa; color: #666; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }
        .btn-sell { background-color: #2ecc71; color: white; border-radius: 6px; border: none; }
        .btn-sell:hover { background-color: #27ae60; color: white; }
        .stock-out { opacity: 0.6; background-color: #fdf2f2; }
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
    <div class='container d-flex justify-content-center align-items-center' style='min-height: 100vh;'>
        <div class='card p-5 shadow-lg' style='width: 100%; max-width: 420px; border-radius: 20px;'>
            <div class='text-center mb-4'>
                <div class='bg-primary d-inline-block p-3 rounded-circle mb-3 shadow'>
                    <i class='bi bi-car-front-fill text-white fs-1'></i>
                </div>
                <h2 class='fw-black' style='letter-spacing: -1px;'>AVTOSTOK <span class='text-primary'>PRO</span></h2>
                <p class='text-muted'>İdarəetmə panelinə giriş</p>
            </div>
            <form method='POST'>
                <div class='form-floating mb-3'>
                    <input name='username' class='form-control' id='u' placeholder='admin' required>
                    <label for='u'>İstifadəçi adı</label>
                </div>
                <div class='form-floating mb-4'>
                    <input name='password' type='password' class='form-control' id='p' placeholder='****' required>
                    <label for='p'>Şifrə</label>
                </div>
                <button class='btn btn-primary w-100 py-3 fw-bold rounded-3 shadow'>DAXİL OL</button>
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
    cur.execute("SELECT SUM(stock) as total_stock FROM cars")
    total_stock = cur.fetchone()['total_stock'] or 0
    cur.close(); conn.close()
    
    rows = ""
    for c in cars:
        is_out = c['stock'] <= 0
        stock_display = f"<span class='badge bg-danger p-2'><i class='bi bi-exclamation-triangle'></i> TÜKƏNDİ</span>" if is_out else f"<span class='badge bg-light text-dark border p-2'>{c['stock']} ədəd</span>"
        sell_btn = "" if is_out else f"<a href='/sell/{c['id']}' class='btn btn-sell btn-sm px-3'><i class='bi bi-cash-stack'></i> SAT</a>"
        
        rows += f"""
        <tr class='{"stock-out" if is_out else ""}'>
            <td class='fw-bold text-dark'>{c['brand']}</td>
            <td>{c['model']}</td>
            <td><span class='badge rounded-pill' style='background:#95a5a6'>{c['color']}</span></td>
            <td><small class='text-muted'>{c['package']}</small></td>
            <td>{stock_display}</td>
            <td class='text-end'>
                <div class='btn-group'>
                    {sell_btn}
                    <a href='/delete/{c['id']}' class='btn btn-link text-danger btn-sm' onclick="return confirm('Silsin?')"><i class='bi bi-trash3'></i></a>
                </div>
            </td>
        </tr>
        """
    
    return f"""
    {header_html}
    <nav class='navbar navbar-dark sticky-top mb-4 py-3'>
        <div class='container'>
            <a class='navbar-brand fw-bold fs-4' href='#'><i class='bi bi-shield-check me-2'></i>AVTOSTOK</a>
            <div class='d-flex align-items-center'>
                <span class='text-white-50 me-3'>Admin: <b>{session['user']}</b></span>
                <a href='/logout' class='btn btn-danger btn-sm rounded-pill px-3'>Çıxış</a>
            </div>
        </div>
    </nav>

    <div class='container pb-5'>
        <div class='row g-4 mb-5'>
            <div class='col-md-6 col-lg-3'>
                <div class='card p-3 stat-card shadow-sm'>
                    <div class='d-flex align-items-center'>
                        <div class='p-3 bg-light rounded-3 me-3'><i class='bi bi-graph-up-arrow text-success fs-3'></i></div>
                        <div><p class='text-muted mb-0 small'>Ümumi Satış</p><h3 class='fw-bold mb-0'>{total_sales}</h3></div>
                    </div>
                </div>
            </div>
            <div class='col-md-6 col-lg-3'>
                <div class='card p-3 stat-card shadow-sm' style='border-left-color: #f1c40f;'>
                    <div class='d-flex align-items-center'>
                        <div class='p-3 bg-light rounded-3 me-3'><i class='bi bi-box-seam text-warning fs-3'></i></div>
                        <div><p class='text-muted mb-0 small'>Anbarda Qalan</p><h3 class='fw-bold mb-0'>{total_stock}</h3></div>
                    </div>
                </div>
            </div>
        </div>

        <div class='row'>
            <div class='col-xl-8 mb-4'>
                <div class='card shadow-sm border-0 overflow-hidden'>
                    <div class='card-header bg-white border-0 py-3 d-flex justify-content-between align-items-center'>
                        <h5 class='mb-0 fw-bold'>Anbar Siyahısı</h5>
                        <input type='text' id='search' class='form-control form-control-sm w-50' placeholder='Marka və ya model axtar...'>
                    </div>
                    <div class='table-responsive'>
                        <table class='table table-hover mb-0' id='carTable'>
                            <thead>
                                <tr><th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th class='text-end'>Əməliyyat</th></tr>
                            </thead>
                            <tbody>
                                {rows if rows else "<tr><td colspan='6' class='text-center py-5'>Siyahı boşdur</td></tr>"}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class='col-xl-4'>
                <div class='card shadow-sm border-0 p-4'>
                    <h5 class='fw-bold mb-4'><i class='bi bi-plus-square-dotted me-2 text-primary'></i>Yeni Maşın Girişi</h5>
                    <form action='/add' method='POST' class='row g-3'>
                        <div class='col-12'><input name='brand' class='form-control bg-light border-0' placeholder='Marka' required></div>
                        <div class='col-12'><input name='model' class='form-control bg-light border-0' placeholder='Model' required></div>
                        <div class='col-6'><input name='color' class='form-control bg-light border-0' placeholder='Rəng'></div>
                        <div class='col-6'><input name='package' class='form-control bg-light border-0' placeholder='Paket'></div>
                        <div class='col-12'><input name='stock' type='number' class='form-control bg-light border-0' placeholder='Stok Sayı' required></div>
                        <div class='col-12'><button class='btn btn-primary w-100 py-2 fw-bold shadow-sm'><i class='bi bi-check-lg me-2'></i>ƏLAVƏ ET</button></div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('search').addEventListener('keyup', function() {{
            let filter = this.value.toUpperCase();
            let rows = document.querySelector("#carTable tbody").rows;
            for (let i = 0; i < rows.length; i++) {{
                let firstCol = rows[i].cells[0].textContent.toUpperCase();
                let secondCol = rows[i].cells[1].textContent.toUpperCase();
                rows[i].style.display = (firstCol.indexOf(filter) > -1 || secondCol.indexOf(filter) > -1) ? "" : "none";
            }}
        }});
    </script>
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

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "avtostok_secret_123"

# Verilənlər bazasına qoşulma funksiyası
def get_db_connection():
    # Vercel-in təmin etdiyi POSTGRES_URL-i götürürük
    database_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("Məlumat bazası linki tapılmadı! Vercel Storage hissəsini yoxlayın.")
    
    # Postgres üçün URL formatını düzəldirik
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    return psycopg2.connect(database_url)

# Cədvəlləri ilkin olaraq yaradan funksiya
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # İstifadəçilər cədvəli
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Maşınlar cədvəli
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id SERIAL PRIMARY KEY,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            color TEXT,
            package TEXT,
            stock INTEGER DEFAULT 0
        )
    """)
    
    # Satışlar cədvəli
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            car_id INTEGER REFERENCES cars(id),
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Defolt admin istifadəçisini əlavə edirik (əgər yoxdursa)
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
    
    conn.commit()
    cur.close()
    conn.close()

# Sayt hər dəfə qalxanda bazanı yoxla
try:
    init_db()
except Exception as e:
    print(f"Baza xətası: {e}")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session["user"] = username
            return redirect("/dashboard")
        return "Səhv istifadəçi adı və ya şifrə! <a href='/'>Geri qayıt</a>"
        
    return """
    <style>body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.login-box{background:white;padding:40px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);width:320px}input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:6px;box-sizing:border-box}button{width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:6px;cursor:pointer;font-size:16px}button:hover{background:#0056b3}</style>
    <div class='login-box'>
        <h2 style='text-align:center'>AvtoStok Giriş</h2>
        <form method='POST'>
            <input name='username' placeholder='İstifadəçi adı' required>
            <input name='password' type='password' placeholder='Şifrə' required>
            <button type='submit'>Daxil ol</button>
        </form>
    </div>
    """

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
        
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM cars ORDER BY id DESC")
    cars = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) as total FROM sales")
    total_sales = cur.fetchone()['total']
    
    cur.close()
    conn.close()
    
    car_rows = ""
    for car in cars:
        stock_status = f"<b style='color:red'>Yoxdur</b>" if car['stock'] <= 0 else car['stock']
        car_rows += f"""
        <tr>
            <td>{car['brand']}</td>
            <td>{car['model']}</td>
            <td>{car['color']}</td>
            <td>{car['package']}</td>
            <td>{stock_status}</td>
            <td>
                <a href='/sell/{car['id']}' style='color:green; text-decoration:none'>[Sat]</a> | 
                <a href='/delete/{car['id']}' style='color:red; text-decoration:none' onclick="return confirm('Silmək istədiyinizə əminsiniz?')">[Sil]</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style='font-family:sans-serif; padding:40px; background:#f8f9fa'>
        <div style='max-width:1000px; margin:auto; background:white; padding:30px; border-radius:15px; shadow: 0 0 10px rgba(0,0,0,0.1)'>
            <div style='display:flex; justify-content:space-between'>
                <h2>AvtoStok Panel</h2>
                <p>Xoş gəldiniz, <b>{session['user']}</b> | <a href='/logout'>Çıxış</a></p>
            </div>
            <div style='background:#e9ecef; padding:20px; border-radius:10px; margin-bottom:20px'>
                <b>Ümumi Satış Sayı: {total_sales}</b>
            </div>
            <table border='1' style='width:100%; border-collapse:collapse; margin-bottom:30px'>
                <tr style='background:#f1f1f1'>
                    <th>Marka</th><th>Model</th><th>Rəng</th><th>Paket</th><th>Stok</th><th>Əməliyyat</th>
                </tr>
                {car_rows if car_rows else "<tr><td colspan='6' style='text-align:center'>Hələ maşın yoxdur</td></tr>"}
            </table>
            
            <h3>Yeni Maşın Əlavə Et</h3>
            <form action='/add' method='POST' style='display:grid; grid-template-columns: 1fr 1fr; gap:10px'>
                <input name='brand' placeholder='Marka' required>
                <input name='model' placeholder='Model' required>
                <input name='color' placeholder='Rəng'>
                <input name='package' placeholder='Paket'>
                <input name='stock' type='number' placeholder='Stok sayı' required>
                <button style='grid-column: span 2; background:black; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer'>Əlavə et</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/add", methods=["POST"])
def add_car():
    if "user" not in session: return redirect("/")
    
    brand = request.form.get("brand")
    model = request.form.get("model")
    color = request.form.get("color")
    package = request.form.get("package")
    stock = request.form.get("stock")
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO cars (brand, model, color, package, stock) VALUES (%s, %s, %s, %s, %s)",
                (brand, model, color, package, stock))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

@app.route("/sell/<int:car_id>")
def sell_car(car_id):
    if "user" not in session: return redirect("/")
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Stoku bir azaldırıq
    cur.execute("UPDATE cars SET stock = stock - 1 WHERE id = %s AND stock > 0", (car_id,))
    # Satışlara əlavə edirik
    cur.execute("INSERT INTO sales (car_id) VALUES (%s)", (car_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

@app.route("/delete/<int:car_id>")
def delete_car(car_id):
    if "user" not in session: return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cars WHERE id = %s", (car_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run()
from flask import Flask,request,redirect,session,jsonify
import sqlite3

app = Flask(__name__)
app.secret_key="secret123"

def db():
    return sqlite3.connect("cars.db")

conn=db()
cur=conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS cars(
id INTEGER PRIMARY KEY AUTOINCREMENT,
brand TEXT,
model TEXT,
color TEXT,
package TEXT,
stock INTEGER)""")

cur.execute("""CREATE TABLE IF NOT EXISTS sales(
id INTEGER PRIMARY KEY AUTOINCREMENT,
car_id INTEGER,
date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

cur.execute("INSERT OR IGNORE INTO users(id,username,password) VALUES(1,'admin','1234')")
conn.commit()


@app.route("/",methods=["GET","POST"])
def login():

    if request.method=="POST":

        u=request.form["username"]
        p=request.form["password"]

        c=db().cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))

        if c.fetchone():
            session["user"]=u
            return redirect("/dashboard")

    return """
    <style>
    body{font-family:Arial;background:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh}
    .box{background:white;padding:30px;border-radius:10px;width:300px}
    input{width:100%;padding:10px;margin:5px 0}
    button{width:100%;padding:10px;background:black;color:white;border:none}
    </style>

    <div class=box>
    <h2>Avtosalon Login</h2>
    <form method=post>
    <input name=username placeholder="istifadəçi adı">
    <input name=password type=password placeholder="şifrə">
    <button>Giriş</button>
    </form>
    </div>
    """


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn=db()
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()

    cars=cur.execute("SELECT * FROM cars").fetchall()

    sales=cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    warning=cur.execute("SELECT COUNT(*) FROM cars WHERE stock<=1").fetchone()[0]

    rows=""

    for car in cars:

        stock = f"<span style='color:red;font-weight:bold'>TÜKƏNDİ</span>" if car["stock"]==0 else car["stock"]

        rows+=f"""
        <tr>
        <td>{car['brand']}</td>
        <td>{car['model']}</td>
        <td>{car['color']}</td>
        <td>{car['package']}</td>
        <td>{stock}</td>
        <td><a class=sell href=/sell/{car['id']}>Satıldı</a></td>
        <td><a class=delete href=/delete/{car['id']}>Sil</a></td>
        </tr>
        """

    return f"""
<style>

body{{font-family:Arial;background:#f4f4f4;margin:0}}

header{{background:#111;color:white;padding:20px;text-align:center}}

table{{width:100%;background:white;border-collapse:collapse}}

td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:center}}

.sell{{background:green;color:white;padding:5px 10px;border-radius:5px;text-decoration:none}}

.delete{{background:red;color:white;padding:5px 10px;border-radius:5px;text-decoration:none}}

.stats{{display:flex;gap:20px;padding:10px}}

#search{{width:100%;padding:10px;margin:10px 0}}

</style>

<header>Avtosalon Panel</header>

<div class=stats>
<div>Satış sayı: {sales}</div>
<div>Stok xəbərdarlığı: {warning}</div>
</div>

<input id=search placeholder="Maşın axtar...">

<table id=table>

<tr>
<th>Marka</th>
<th>Model</th>
<th>Rəng</th>
<th>Komplektasiya</th>
<th>Stok</th>
<th>Sat</th>
<th>Sil</th>
</tr>

{rows}

</table>

<h3>Maşın əlavə et</h3>

<form method=post action=/add>

<input name=brand placeholder="Marka">
<input name=model placeholder="Model">
<input name=color placeholder="Rəng">
<input name=package placeholder="Komplektasiya">
<input name=stock placeholder="Say">

<button>Əlavə et</button>

</form>

<script>

document.getElementById("search").addEventListener("keyup",function(){{

let q=this.value

fetch("/search?q="+q)

.then(r=>r.json())

.then(data=>{{

let table=document.getElementById("table")

let rows=`<tr>
<th>Marka</th>
<th>Model</th>
<th>Rəng</th>
<th>Komplektasiya</th>
<th>Stok</th>
<th>Sat</th>
<th>Sil</th>
</tr>`

data.forEach(car=>{{

rows+=`<tr>

<td>${{car.brand}}</td>
<td>${{car.model}}</td>
<td>${{car.color}}</td>
<td>${{car.package}}</td>

<td>${{car.stock==0?"<span style='color:red;font-weight:bold'>TÜKƏNDİ</span>":car.stock}}</td>

<td><a class=sell href=/sell/${{car.id}}>Satıldı</a></td>
<td><a class=delete href=/delete/${{car.id}}>Sil</a></td>

</tr>`

}})

table.innerHTML=rows

}})

}})

</script>
"""


@app.route("/add",methods=["POST"])
def add():

    conn=db()
    cur=conn.cursor()

    cur.execute("INSERT INTO cars(brand,model,color,package,stock) VALUES(?,?,?,?,?)",
    (request.form["brand"],request.form["model"],request.form["color"],request.form["package"],request.form["stock"]))

    conn.commit()

    return redirect("/dashboard")


@app.route("/sell/<id>")
def sell(id):

    conn=db()
    cur=conn.cursor()

    cur.execute("UPDATE cars SET stock=stock-1 WHERE id=? AND stock>0",(id,))
    cur.execute("INSERT INTO sales(car_id) VALUES(?)",(id,))

    conn.commit()

    return redirect("/dashboard")


@app.route("/delete/<id>")
def delete(id):

    conn=db()
    cur=conn.cursor()

    cur.execute("DELETE FROM cars WHERE id=?",(id,))
    conn.commit()

    return redirect("/dashboard")


@app.route("/search")
def search():

    q=request.args.get("q")

    conn=db()
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()

    cars=cur.execute("SELECT * FROM cars WHERE brand LIKE ? OR model LIKE ?",(f"%{q}%",f"%{q}%")).fetchall()

    return jsonify([dict(x) for x in cars])


app.run(debug=True)
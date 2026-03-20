from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def hello():
    # Bu bizə bazanın bağlı olub-olmadığını göstərəcək
    url = os.environ.get('POSTGRES_URL', 'BAZA BAGLI DEYIL')
    return f"Sayt isleyir! Baza veziyyeti: {url[:15]}..."

if __name__ == "__main__":
    app.run()
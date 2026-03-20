from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "SAYT ISLEYIR! Artiq terminal deyil, birbasa sayt uzerinden kodu deyisdik."

if __name__ == "__main__":
    app.run()

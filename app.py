from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Salam! Sayt isleyir. Demeli problem bazaya qosulma linkindedir."

if __name__ == "__main__":
    app.run()
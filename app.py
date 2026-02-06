# app.py
from flask import Flask, render_template, jsonify
from sensors import get_status

app = Flask(__name__)

@app.route("/")
def index():
    # Página principal con HTML
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    # Devuelve JSON con los datos actuales
    status = get_status()
    return jsonify(status)

if __name__ == "__main__":
    # host="0.0.0.0" para que también se pueda ver desde otra máquina en la red
    app.run(host="0.0.0.0", port=5000, debug=False)
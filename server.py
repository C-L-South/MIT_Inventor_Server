from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
os.makedirs("frames", exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return "server is reachable"

@app.route("/", methods=["POST"])
def upload_frame():
    file = request.files.get("frame")

    if not file:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    file.save("frames/latest.jpg")
    return jsonify({"ok": True})

@app.route("/latest", methods=["GET"])
def latest():
    path = "frames/latest.jpg"
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "no frame yet"}), 404
    return send_file(path, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

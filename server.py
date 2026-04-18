from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
os.makedirs("frames", exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return "server is running"

@app.route("/", methods=["POST"])
def upload_frame():
    file = request.files.get("frame")

    if not file:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    file.save("frames/latest.jpg")
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run()

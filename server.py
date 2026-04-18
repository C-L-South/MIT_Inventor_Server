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
@app.route("/viewer", methods=["GET"])
def viewer():
    return """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Live Viewer</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body { font-family: sans-serif; text-align: center; margin: 20px; }
        img { max-width: 100%; background: black; }
      </style>
    </head>
    <body>
      <h2>Live Feed</h2>
      <img id="feed" src="/latest" alt="live feed">
      <script>
        const img = document.getElementById("feed");

        function refresh() {
          img.src = "/latest?t=" + Date.now();
        }

        setInterval(refresh, 300);
      </script>
    </body>
    </html>
    """
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

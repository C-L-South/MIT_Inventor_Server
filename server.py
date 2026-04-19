from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
os.makedirs("frames", exist_ok=True)

LATEST_IMAGE = "frames/latest.jpg"
LATEST_ID = "frames/latest_frame_id.txt"

@app.route("/", methods=["GET"])
def home():
    return "server is reachable"

@app.route("/", methods=["POST"])
def upload_frame():
    file = request.files.get("frame")
    frame_id = request.form.get("frame_id", "0")

    if not file:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    file.save(LATEST_IMAGE)

    with open(LATEST_ID, "w") as f:
        f.write(frame_id)

    print("Received frame:", frame_id)

    return jsonify({"ok": True, "received_frame_id": frame_id})

@app.route("/viewer", methods=["GET"])
def viewer():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Viewer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      font-family: sans-serif;
      text-align: center;
      margin: 40px;
    }
    #count {
      font-size: 56px;
      font-weight: bold;
      margin-top: 20px;
    }
    #status {
      margin-top: 16px;
      color: #555;
    }
    img {
      margin-top: 20px;
      max-width: 100%;
      background: black;
    }
  </style>
</head>
<body>
  <h2>Latest Received Frame</h2>
  <div id="count">--</div>
  <div id="status">Waiting...</div>
  <img id="img" src="" alt="latest frame">

  <script>
    const count = document.getElementById("count");
    const status = document.getElementById("status");
    const img = document.getElementById("img");

    async function refresh() {
      try {
        const res = await fetch("/frame-count?t=" + Date.now(), {
          cache: "no-store"
        });
        const data = await res.json();

        if (data.ok) {
          count.textContent = data.frame_id;
          status.textContent = "Updated: " + new Date().toLocaleTimeString();
          img.src = "/latest?t=" + Date.now();
        } else {
          status.textContent = "No frame yet";
        }
      } catch (err) {
        status.textContent = "Error: " + err.message;
      }
    }

    refresh();
    setInterval(refresh, 300);
  </script>
</body>
</html>
    """

@app.route("/frame-count", methods=["GET"])
def frame_count():
    if not os.path.exists(LATEST_ID):
        return jsonify({"ok": False, "error": "no frame yet"}), 404

    with open(LATEST_ID, "r") as f:
        frame_id = f.read().strip()

    return jsonify({"ok": True, "frame_id": frame_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

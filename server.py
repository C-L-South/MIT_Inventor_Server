from flask import Flask, request, jsonify, send_file
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

    return jsonify({"ok": True})

@app.route("/latest", methods=["GET"])
def latest():
    if not os.path.exists(LATEST_IMAGE):
        return "no image yet", 404
    return send_file(LATEST_IMAGE, mimetype="image/jpeg")

@app.route("/viewer")
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
        #frame { font-size: 24px; margin: 10px; }
      </style>
    </head>
    <body>
      <h2>Live Feed</h2>
      <div id="frame">Frame: --</div>
      <img id="img">

      <script>
        const img = document.getElementById("img");
        const frameDiv = document.getElementById("frame");

        async function refresh() {
          try {
            // get frame id
            const res = await fetch("/latest_frame_id.txt?t=" + Date.now());
            const frameId = await res.text();

            // update UI
            frameDiv.textContent = "Frame: " + frameId;

            // update image
            img.src = "/latest?t=" + Date.now();

          } catch (err) {
            frameDiv.textContent = "Waiting...";
          }
        }

        setInterval(refresh, 300);
        refresh();
      </script>
    </body>
    </html>
    """

@app.route("/latest_frame_id.txt")
def get_frame_id():
    if not os.path.exists(LATEST_ID):
        return "0"
    with open(LATEST_ID, "r") as f:
        return f.read()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}}
)

os.makedirs("frames", exist_ok=True)

LATEST_IMAGE = "frames/latest.jpg"
LATEST_ID = "frames/latest_frame_id.txt"

@app.route("/", methods=["GET"])
def home():
    print("GET / hit")
    return "server is reachable", 200

@app.route("/", methods=["POST"])
def upload_frame():
    print("POST / hit")
    print("Origin:", request.headers.get("Origin"))
    print("Content-Type:", request.content_type)

    file = request.files.get("frame")
    frame_id = request.form.get("frame_id", "0")

    if not file:
        print("missing frame")
        return jsonify({"ok": False, "error": "missing frame"}), 400

    image_bytes = file.read()
    print("Received frame_id:", frame_id)
    print("Bytes:", len(image_bytes))

    with open(LATEST_IMAGE, "wb") as f:
        f.write(image_bytes)

    with open(LATEST_ID, "w") as f:
        f.write(frame_id)

    # temporary fake points for testing
    pose = [
        {"name": "nose", "x": 0.5, "y": 0.2, "score": 0.99},
        {"name": "left_shoulder", "x": 0.4, "y": 0.4, "score": 0.99},
        {"name": "right_shoulder", "x": 0.6, "y": 0.4, "score": 0.99},
    ]

    return jsonify({
        "ok": True,
        "received_frame_id": frame_id,
        "pose": pose
    }), 200

@app.route("/frame-count", methods=["GET"])
def frame_count():
    if not os.path.exists(LATEST_ID):
        return jsonify({"ok": False, "error": "no frame yet"}), 404

    with open(LATEST_ID, "r") as f:
        frame_id = f.read().strip()

    return jsonify({"ok": True, "frame_id": frame_id}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

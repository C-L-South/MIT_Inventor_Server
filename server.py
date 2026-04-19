from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

app = Flask(__name__)
CORS(app)
os.makedirs("frames", exist_ok=True)

LATEST_IMAGE = "frames/latest.jpg"
LATEST_ID = "frames/latest_frame_id.txt"

# Choose one:
# Lightning: faster, 192x192
# Thunder: more accurate, 256x256
MODEL_URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4"
INPUT_SIZE = 192

# Load once when server starts
movenet = hub.load(MODEL_URL)
movenet_fn = movenet.signatures["serving_default"]


KEYPOINT_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


def load_image_bytes_to_tensor(image_bytes: bytes):
    """
    Returns:
        input_image: tensor shaped [1, INPUT_SIZE, INPUT_SIZE, 3], dtype int32
        original_h: int
        original_w: int
    """
    image = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    image = tf.cast(image, tf.int32)

    original_h = int(image.shape[0])
    original_w = int(image.shape[1])

    input_image = tf.image.resize_with_pad(image, INPUT_SIZE, INPUT_SIZE)
    input_image = tf.expand_dims(input_image, axis=0)
    input_image = tf.cast(input_image, dtype=tf.int32)

    return input_image, original_h, original_w


def run_movenet(image_bytes: bytes):
    """
    Returns MoveNet keypoints in both normalized and pixel coords.
    Output shape from model: [1, 1, 17, 3]
    Each keypoint = [y, x, score]
    """
    input_image, original_h, original_w = load_image_bytes_to_tensor(image_bytes)

    outputs = movenet_fn(input_image)
    # Depending on signature name, this is usually 'output_0'
    keypoints = outputs["output_0"].numpy()[0, 0, :, :]  # [17, 3]

    result = []
    for i, (y, x, score) in enumerate(keypoints):
        result.append({
            "name": KEYPOINT_NAMES[i],
            "x": float(x),              # normalized 0..1
            "y": float(y),              # normalized 0..1
            "score": float(score),
            "pixel_x": int(x * original_w),
            "pixel_y": int(y * original_h),
        })

    return result


@app.route("/", methods=["GET"])
def home():
    return "server is reachable"


@app.route("/", methods=["POST"])
def upload_frame():
    file = request.files.get("frame")
    frame_id = request.form.get("frame_id", "0")

    if not file:
        return jsonify({"ok": False, "error": "missing frame"}), 400

    image_bytes = file.read()

    # Optional: save latest uploaded frame
    with open(LATEST_IMAGE, "wb") as f:
        f.write(image_bytes)

    with open(LATEST_ID, "w") as f:
        f.write(frame_id)

    try:
        keypoints = run_movenet(image_bytes)

        print("Received frame:", frame_id)

        return jsonify({
            "ok": True,
            "received_frame_id": frame_id,
            "pose": keypoints
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "received_frame_id": frame_id,
            "error": str(e)
        }), 500


@app.route("/frame-count", methods=["GET"])
def frame_count():
    if not os.path.exists(LATEST_ID):
        return jsonify({"ok": False, "error": "no frame yet"}), 404

    with open(LATEST_ID, "r") as f:
        frame_id = f.read().strip()

    return jsonify({"ok": True, "frame_id": frame_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

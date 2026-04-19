from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback
import tensorflow as tf
import tensorflow_hub as hub

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

os.makedirs("frames", exist_ok=True)

LATEST_IMAGE = "frames/latest.jpg"
LATEST_ID = "frames/latest_frame_id.txt"

# MoveNet SinglePose Lightning
MODEL_URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4"
INPUT_SIZE = 192

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

print("Loading MoveNet model...")
movenet = hub.load(MODEL_URL)
movenet_fn = movenet.signatures["serving_default"]
print("MoveNet model loaded successfully")


def run_movenet(image_bytes: bytes):
    """
    image_bytes: raw uploaded JPEG/PNG bytes
    returns: list of 17 keypoints with normalized + pixel coordinates
    """
    # Decode image to [H, W, 3]
    image = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
    image = tf.cast(image, dtype=tf.int32)

    original_h = int(image.shape[0])
    original_w = int(image.shape[1])

    # Resize to model input size with padding
    input_image = tf.image.resize_with_pad(image, INPUT_SIZE, INPUT_SIZE)
    input_image = tf.expand_dims(input_image, axis=0)
    input_image = tf.cast(input_image, dtype=tf.int32)

    # Run model
    outputs = movenet_fn(input_image)

    # Usually output_0, shape [1, 1, 17, 3]
    keypoints = outputs["output_0"].numpy()[0, 0, :, :]

    result = []
    for i, (y, x, score) in enumerate(keypoints):
        result.append({
            "name": KEYPOINT_NAMES[i],
            "x": float(x),   # normalized 0..1
            "y": float(y),   # normalized 0..1
            "score": float(score),
            "pixel_x": int(x * original_w),
            "pixel_y": int(y * original_h),
        })

    return result


@app.route("/", methods=["GET"])
def home():
    return "server is reachable", 200


@app.route("/", methods=["POST"])
def upload_frame():
    try:
        print("POST / hit")

        file = request.files.get("frame")
        frame_id = request.form.get("frame_id", "0")

        print("frame_id =", frame_id)
        print("has file =", file is not None)

        if not file:
            return jsonify({
                "ok": False,
                "error": "missing frame"
            }), 400

        image_bytes = file.read()
        print("image byte length =", len(image_bytes))

        # Save latest frame
        with open(LATEST_IMAGE, "wb") as f:
            f.write(image_bytes)

        with open(LATEST_ID, "w") as f:
            f.write(frame_id)

        keypoints = run_movenet(image_bytes)
        print("keypoints detected =", len(keypoints))

        return jsonify({
            "ok": True,
            "received_frame_id": frame_id,
            "pose": keypoints
        }), 200

    except Exception as e:
        print("ERROR IN POST /")
        print(str(e))
        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/frame-count", methods=["GET"])
def frame_count():
    if not os.path.exists(LATEST_ID):
        return jsonify({
            "ok": False,
            "error": "no frame yet"
        }), 404

    with open(LATEST_ID, "r") as f:
        frame_id = f.read().strip()

    return jsonify({
        "ok": True,
        "frame_id": frame_id
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

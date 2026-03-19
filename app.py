import os
import uuid
import base64
from pathlib import Path

import fal_client
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image
import io
import requests as http_requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "curtainviz-secret-2024")

# ── fal.ai setup ───────────────────────────────────────────────────────────────
FAL_KEY = os.getenv("FAL_KEY")
if not FAL_KEY:
    raise RuntimeError("FAL_KEY not found in environment. Check your .env file.")

os.environ["FAL_KEY"] = FAL_KEY  # fal_client reads from env

UPLOAD_FOLDER = Path("static/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_prompt(curtain_type: str, fabric: str, rod_type: str, color: str) -> str:
    """Build a detailed prompt for the curtain visualization."""
    return (
        f"Interior design photo edit: add realistic, high-quality {color} {fabric} {curtain_type} curtains "
        f"to every window visible in the image. "
        f"The curtains are hung on a {rod_type} curtain rod at the top of the window frame. "
        f"The curtains look natural, properly lit, and consistent with the room's existing lighting and style. "
        f"Keep everything else in the image exactly the same — walls, furniture, floor, decor, and ceiling. "
        f"Photorealistic result, looks like a real interior photograph. "
        f"No text, no watermarks, no labels."
    )


def image_to_data_uri(image_path: Path) -> str:
    """Convert a local image file to a base64 data URI for fal.ai."""
    ext = image_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Accept an image upload and save it temporarily. Returns a file key."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PNG, JPG, or WEBP."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    file_key = f"{uuid.uuid4().hex}.{ext}"
    save_path = UPLOAD_FOLDER / file_key
    file.save(str(save_path))

    with open(save_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return jsonify({
        "file_key": file_key,
        "preview": f"data:{mime};base64,{encoded}",
        "mime": mime
    })


@app.route("/generate", methods=["POST"])
def generate():
    """Call fal.ai FLUX image-to-image and return the result image."""
    data = request.get_json(force=True)

    file_key     = data.get("file_key", "")
    curtain_type = data.get("curtain_type", "Panel")
    fabric       = data.get("fabric", "Linen")
    rod_type     = data.get("rod_type", "standard")
    color        = data.get("color", "white")

    if not file_key:
        return jsonify({"error": "No uploaded image found. Please upload a photo first."}), 400

    image_path = UPLOAD_FOLDER / file_key
    if not image_path.exists():
        return jsonify({"error": "Uploaded image not found on server. Please re-upload."}), 404

    prompt = build_prompt(curtain_type, fabric, rod_type, color)

    # Convert image to data URI so fal.ai can read it directly
    try:
        image_data_uri = image_to_data_uri(image_path)
    except Exception as e:
        return jsonify({"error": f"Could not read image: {e}"}), 500

    # Call fal.ai FLUX Dev image-to-image
    try:
        result = fal_client.subscribe(
            "fal-ai/flux/dev/image-to-image",
            arguments={
                "image_url": image_data_uri,
                "prompt": prompt,
                "strength": 0.85,           # how much to change the image (0=none, 1=full)
                "num_inference_steps": 40,
                "guidance_scale": 3.5,
                "num_images": 1,
                "output_format": "jpeg",
                "enable_safety_checker": False,
            },
        )
    except Exception as e:
        return jsonify({"error": f"fal.ai API error: {str(e)}"}), 500

    # Extract the generated image URL from the result
    try:
        generated_url = result["images"][0]["url"]
    except (KeyError, IndexError, TypeError) as e:
        return jsonify({"error": f"Unexpected fal.ai response format: {str(e)}"}), 500

    # Fetch the generated image and convert to base64 to return to frontend
    try:
        img_response = http_requests.get(generated_url, timeout=30)
        img_response.raise_for_status()
        img_bytes = img_response.content
        generated_b64 = base64.b64encode(img_bytes).decode("utf-8")
        generated_mime = img_response.headers.get("Content-Type", "image/jpeg")
    except Exception as e:
        # If we can't fetch, just return the URL directly
        return jsonify({"image_url": generated_url})

    return jsonify({
        "image": f"data:{generated_mime};base64,{generated_b64}",
        "mime": generated_mime
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

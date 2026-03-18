import os
import uuid
import base64
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "curtainviz-secret-2024")

# ── Gemini setup ──────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment. Check your .env file.")

genai.configure(api_key=GOOGLE_API_KEY)

UPLOAD_FOLDER = Path("static/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_prompt(curtain_type: str, fabric: str, rod_type: str, color: str) -> str:
    """Build a detailed Gemini prompt for the curtain visualization."""
    return (
        f"You are an expert interior designer and photo editor. "
        f"The image provided shows a window or glass door area inside a room. "
        f"Add realistic, high-quality {color} {fabric} {curtain_type} curtains to every window in the image. "
        f"The curtains should be hung on a {rod_type} curtain rod at the top of the window frame. "
        f"Make the curtains look natural, properly lit, and consistent with the room's lighting and style. "
        f"Keep everything else in the image exactly the same — walls, furniture, floor, and decor. "
        f"Output a photorealistic result that looks like a real photograph. "
        f"Do not add any text, watermarks, or labels to the image."
    )


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

    # Save with a unique name
    ext = file.filename.rsplit(".", 1)[1].lower()
    file_key = f"{uuid.uuid4().hex}.{ext}"
    save_path = UPLOAD_FOLDER / file_key
    file.save(str(save_path))

    # Read back and encode for preview
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
    """Call Gemini image generation and return the result image."""
    data = request.get_json(force=True)

    file_key   = data.get("file_key", "")
    curtain_type = data.get("curtain_type", "panel")
    fabric     = data.get("fabric", "linen")
    rod_type   = data.get("rod_type", "standard")
    color      = data.get("color", "white")

    if not file_key:
        return jsonify({"error": "No uploaded image found. Please upload a photo first."}), 400

    image_path = UPLOAD_FOLDER / file_key
    if not image_path.exists():
        return jsonify({"error": "Uploaded image not found on server. Please re-upload."}), 404

    # Load image for Gemini
    try:
        pil_image = Image.open(str(image_path)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not open image: {e}"}), 500

    prompt = build_prompt(curtain_type, fabric, rod_type, color)

    # Call Gemini
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")
        response = model.generate_content(
            [prompt, pil_image],
            generation_config=genai.GenerationConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        )
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

    # Extract the generated image from the response
    generated_b64 = None
    generated_mime = "image/png"

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            generated_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
            generated_mime = part.inline_data.mime_type
            break

    if not generated_b64:
        # Fallback: Gemini returned text only
        text_response = response.text if hasattr(response, "text") else "No image generated."
        return jsonify({"error": f"Gemini did not return an image. Response: {text_response}"}), 500

    return jsonify({
        "image": f"data:{generated_mime};base64,{generated_b64}",
        "mime": generated_mime
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

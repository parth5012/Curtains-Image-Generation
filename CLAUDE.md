# CurtainViz – AI-Powered Curtain Visualizer

## Project Overview

CurtainViz is a web application that lets users upload a photo of their window/room and visualize how different curtains would look in that space, powered by **Google Gemini's image generation API**.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · Flask |
| AI / Image Generation | Google Gemini API (`gemini-2.0-flash-exp-image-generation`) |
| Frontend | Vanilla HTML · CSS · JavaScript |
| Image handling | Pillow · base64 |
| Env config | python-dotenv |

## Project Structure

```
cpw/
├── app.py                  # Flask application entry point
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
├── .env.example            # Environment template
├── CLAUDE.md               # This file
├── static/
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   ├── js/
│   │   └── main.js         # Frontend logic
│   └── uploads/            # Temp uploaded images (git-ignored)
└── templates/
    └── index.html          # Single-page application template
```

## Key Features

1. **Image Upload** — Drag-and-drop or click-to-upload a room/window photo.
2. **Curtain Options Sidebar** — Choose from:
   - Curtain Type (Sheer, Blackout, Panel, Roman, Roller, Cafe)
   - Fabric (Linen, Velvet, Silk, Cotton, Polyester, Jute)
   - Rod Type (Standard, Tension, Traverse, Cafe, Bay Window)
   - Color palette picker
3. **AI Visualization** — Sends the uploaded image + user selections to Gemini's image generation model, which renders the curtains in the original room photo.
4. **Result Display** — Side-by-side before/after comparison with download option.

## Environment Variables

```
GEMINI_API_KEY=your_google_gemini_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

## Running the App

```bash
pip install -r requirements.txt
cp .env.example .env   # then add your API key
python app.py
# Visit http://localhost:5000
```

## API Notes

- The app uses `google-generativeai` SDK.
- Model: `gemini-2.0-flash-preview-image-generation` (supports image input + image output).
- The prompt is constructed from the user's sidebar selections and guides Gemini to add realistic curtains to the uploaded scene.
- Images are sent as base64-encoded data URIs.

## Development Notes

- Uploaded images are stored temporarily in `static/uploads/` and cleaned up after processing.
- The Flask app uses a `SECRET_KEY` for session security.
- CORS is not required as frontend and backend share the same Flask server.

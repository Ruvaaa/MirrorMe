# MirrorMe 2.0

MirrorMe is a private desktop companion for reflective conversation, mood check-ins, journaling, discovery, music preferences, and personal growth.

## Run locally

### Flask application

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:5000`.

### Electron desktop app

<<<<<<< HEAD
Backend: Flask (Python)

Desktop App: Electron

NLP: spaCy

Optional: GPT-4 API (or local alternatives), Spotify API

🚀 Getting Started
1. Clone the repo
bash
Copy code
git clone https://github.com/Ruvaaa/MirrorMe.git
cd mirrorme
2. Set up the Python backend
bash
Copy code
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
3. Set up the frontend (React + Tailwind)
bash
Copy code
cd ../frontend
=======
```powershell
>>>>>>> 45affd9 (update)
npm install
npm start
```

Electron starts the Flask process on `127.0.0.1:5000`, with context isolation and Node integration disabled.

## Features

- Contextual Mirri conversations with local response matching
- Estimated mood detection and manual mood correction
- Private local JSON journal storage
- Searchable reflections and guided prompts
- One-item-at-a-time discovery feed with categories and saved content
- Mood trends and journaling history dashboard
- Optional local memory preferences
- Optional LLM and Spotify integration structures
- Warm light and charcoal dark themes
- Focus timer

Local data is stored in `data/` unless `MIRRIME_DATA_DIR` is set.

## Optional providers

Copy `.env.example` to `.env` and configure only the integrations you use.

### OpenAI-compatible LLM

Set:

- `MIRRIME_LLM_URL`
- `MIRRIME_LLM_API_KEY`
- `MIRRIME_LLM_MODEL`

The URL should expose an OpenAI-compatible `/chat/completions` endpoint. If it is absent or unreachable, Mirri uses the existing local conversation data and reflective fallback responses.

### Spotify

Set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and, for a completed account session, `SPOTIFY_ACCESS_TOKEN`. A full OAuth callback and playback control flow requires credentials and registration of a local redirect URI. Until that flow is configured, the app provides mood-based playlist guidance and clearly shows Spotify as unavailable.

## spaCy

spaCy is optional. The application runs with the bundled conversation data and keyword fallbacks when spaCy or `en_core_web_md` is unavailable. To enable semantic matching on a compatible Python runtime:

```powershell
python -m pip install "spacy>=3.8,<3.9"
python -m spacy download en_core_web_md
```

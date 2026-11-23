import json
import os
import random
import re
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import timer


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("MIRRIME_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


DEFAULT_DATA = {
    "moods": [],
    "journal": [],
    "saved_content": [],
    "feed_actions": [],
    "memories": [],
    "preferences": {
        "theme": "light",
        "name": "Friend",
        "music_mode": "match",
        "memory_enabled": True,
        "feed_categories": ["AI", "Programming", "Personal growth"],
    },
}


def _data_file(name):
    return DATA_DIR / f"{name}.json"


def load_data(name):
    path = _data_file(name)
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_DATA[name]))
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_DATA[name]))


def save_data(name, value):
    path = _data_file(name)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    temporary.replace(path)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


EMOTION_RULES = {
    "happy": (["happy", "joy", "glad", "good", "great", "grateful", "love"], 0.82),
    "excited": (["excited", "pumped", "thrilled", "celebrate", "amazing"], 0.78),
    "sad": (["sad", "down", "cry", "lonely", "hurt", "depressed"], 0.84),
    "angry": (["angry", "mad", "furious", "annoyed", "frustrated", "pissed"], 0.80),
    "anxious": (["anxious", "worried", "nervous", "overthinking", "scared", "panic"], 0.80),
    "motivated": (["motivated", "determined", "ready", "focused", "goal"], 0.72),
}


def detect_emotion(text):
    words = set(re.findall(r"[a-z']+", text.lower()))
    for emotion, (phrases, confidence) in EMOTION_RULES.items():
        if words.intersection(phrases):
            return {"emotion": emotion, "confidence": confidence}
    neutral = {"emotion": "neutral", "confidence": 0.55}
    if "!" in text:
        neutral["confidence"] = 0.62
    return neutral


def load_conversations():
    candidates = [
        BASE_DIR / "realistic_chatbot_convo_bestie_style_FULL.json",
        BASE_DIR / "chatbot_conversations.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            conversations = data.get("realistic_chatbot_convo_bestie_style_FULL") or data.get("chatbot_conversations")
            if conversations:
                return {str(k).lower(): str(v) for k, v in conversations.items()}
        except (json.JSONDecodeError, OSError):
            continue
    return {}


CONVERSATIONS = load_conversations()
try:
    import spacy

    try:
        NLP = spacy.load("en_core_web_md")
    except OSError:
        NLP = None
except ImportError:
    NLP = None


def find_local_answer(message):
    normalized = re.sub(r"[^\w\s']", " ", message.lower()).strip()
    if normalized in CONVERSATIONS:
        return CONVERSATIONS[normalized]
    if NLP:
        doc = NLP(normalized)
        best_answer = None
        best_score = 0.0
        for question, answer in CONVERSATIONS.items():
            score = doc.similarity(NLP(question))
            if score > best_score:
                best_score = score
                best_answer = answer
        if best_score >= 0.72:
            return best_answer
    return None


def context_response(message, emotion, context):
    local_answer = find_local_answer(message)
    if local_answer:
        return local_answer

    follow_ups = {
        "sad": "What feels heaviest right now, and what usually gives you even a little relief?",
        "angry": "What boundary or need feels threatened underneath the frustration?",
        "anxious": "What is the next small thing you can control in this moment?",
        "excited": "What are you most looking forward to, and how would you like to celebrate it?",
        "happy": "What has been supporting this feeling lately?",
        "motivated": "What is one concrete step you could finish in the next 20 minutes?",
        "neutral": "What is taking up the most space in your thoughts right now?",
    }
    prompts = {
        "reflection": "Take a moment to separate what happened from the story you're telling yourself about it.",
        "motivation": "You do not need perfect energy to begin. Choose the smallest useful step.",
        "creativity": "Try loosening the idea without judging it; curiosity comes before quality.",
        "growth": "Notice the pattern, then decide what a kinder and more effective next choice could be.",
        "casual": "I'm listening. We can keep this simple or go wherever feels useful.",
    }
    return f"{prompts.get(context, prompts['reflection'])} {follow_ups[emotion['emotion']]}"


def external_llm_response(message, context, memories):
    base_url = os.getenv("MIRRIME_LLM_URL")
    api_key = os.getenv("MIRRIME_LLM_API_KEY")
    if not base_url or not api_key:
        return None
    payload = {
        "model": os.getenv("MIRRIME_LLM_MODEL", "local-model"),
        "messages": [
            {"role": "system", "content": "You are Mirri, a warm reflective companion. Be thoughtful and concise. Ask meaningful follow-up questions. Never claim to diagnose emotions or fabricate memories."},
            *[{"role": "user", "content": f"My saved preference: {item}"} for item in memories[-5:]],
            {"role": "user", "content": f"Context: {context}. Message: {message}"},
        ],
    }
    try:
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Please keep your message under 4,000 characters."}), 400

    context = str(body.get("context", "reflection"))
    if context not in {"reflection", "motivation", "casual", "creativity", "growth"}:
        context = "reflection"

    detected = detect_emotion(message)
    preferences = load_data("preferences")
    memories = load_data("memories") if preferences.get("memory_enabled", True) else []
    response = external_llm_response(message, context, memories)
    provider = "llm" if response else "local"
    if not response:
        response = context_response(message, detected, context)

    mood_entry = {"emotion": detected["emotion"], "confidence": detected["confidence"], "text": message, "created_at": utc_now()}
    moods = load_data("moods")
    moods.append(mood_entry)
    moods[:] = moods[-500:]
    save_data("moods", moods)

    image_map = {
        "happy": "happy.jpg", "excited": "excited.jpg", "sad": "sad.jpg",
        "angry": "angry.jpg", "anxious": "anxious.jpg", "motivated": "motivated.jpg",
    }
    emotion = detected["emotion"]
    return jsonify({
        "response": response,
        "emotion": emotion,
        "confidence": detected["confidence"],
        "image_path": f"/{image_map.get(emotion, 'pic.jpg')}",
        "provider": provider,
    })


@app.route("/api/moods", methods=["GET", "POST"])
def moods():
    items = load_data("moods")
    if request.method == "GET":
        return jsonify(items)
    body = request.get_json(silent=True) or {}
    allowed = {"happy", "excited", "sad", "angry", "anxious", "motivated", "neutral"}
    emotion = str(body.get("emotion", "")).lower()
    if emotion not in allowed:
        return jsonify({"error": "Please select a valid mood."}), 400
    entry = {"emotion": emotion, "confidence": 1.0, "text": "", "source": "manual", "created_at": utc_now()}
    items.append(entry)
    items[:] = items[-500:]
    save_data("moods", items)
    return jsonify(entry), 201


@app.route("/api/journal", methods=["GET", "POST"])
@app.route("/api/journal/<entry_id>", methods=["GET", "PUT", "DELETE"])
def journal(entry_id=None):
    entries = load_data("journal")
    if request.method == "GET" and entry_id:
        entry = next((item for item in entries if item["id"] == entry_id), None)
        return jsonify(entry) if entry else (jsonify({"error": "Entry not found."}), 404)
    if request.method == "GET":
        query = str(request.args.get("q", "")).lower()
        if query:
            entries = [entry for entry in entries if query in entry["title"].lower() or query in entry["body"].lower()]
        return jsonify(sorted(entries, key=lambda item: item["created_at"], reverse=True))

    if request.method == "DELETE":
        entries = [item for item in entries if item["id"] != entry_id]
        save_data("journal", entries)
        return jsonify({"ok": True})

    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip()
    text = str(body.get("body", "")).strip()
    if not text:
        return jsonify({"error": "Write a reflection before saving."}), 400
    if request.method == "PUT":
        entry = next((item for item in entries if item["id"] == entry_id), None)
        if not entry:
            return jsonify({"error": "Entry not found."}), 404
        entry.update({"title": title or "Untitled reflection", "body": text, "mood": str(body.get("mood", "neutral")), "updated_at": utc_now()})
        save_data("journal", entries)
        return jsonify(entry)

    entry = {
        "id": f"entry-{int(time.time() * 1000)}",
        "title": title or "Untitled reflection",
        "body": text,
        "mood": str(body.get("mood", "neutral")),
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    entries.append(entry)
    save_data("journal", entries)
    return jsonify(entry), 201


FEED = [
    {"id": "ai-1", "category": "AI", "title": "A calmer way to learn AI", "summary": "Build understanding by experimenting with one small project at a time.", "source": "MirrorMe curated"},
    {"id": "code-1", "category": "Programming", "title": "Debug less, observe more", "summary": "Before changing code, write down what you know, what you expect, and what actually happened.", "source": "MirrorMe curated"},
    {"id": "f1-1", "category": "F1", "title": "The quiet craft of race strategy", "summary": "Great decisions combine live information, uncertainty, and the discipline to adapt.", "source": "MirrorMe curated"},
    {"id": "creative-1", "category": "Creativity", "title": "Make the first draft intentionally imperfect", "summary": "Set a short timer and give your idea permission to exist before asking it to be good.", "source": "MirrorMe curated"},
    {"id": "growth-1", "category": "Personal growth", "title": "Review the week without grading it", "summary": "Look for patterns in energy, choices, and rest instead of reducing progress to a score.", "source": "MirrorMe curated"},
    {"id": "fun-1", "category": "Entertainment", "title": "A tiny reset between tasks", "summary": "Choose one song, stretch, and let your attention arrive back slowly.", "source": "MirrorMe curated"},
]


@app.route("/api/feed", methods=["GET"])
def feed():
    preferences = load_data("preferences")
    actions = load_data("feed_actions")
    categories = preferences.get("feed_categories", [])
    dismissed = {item["id"] for item in actions if item["action"] == "dismiss"}
    items = [item for item in FEED if item["id"] not in dismissed]
    if categories:
        items = sorted(items, key=lambda item: item["category"] in categories, reverse=True)
    return jsonify(items)


@app.route("/api/feed/action", methods=["POST"])
def feed_action():
    body = request.get_json(silent=True) or {}
    item_id = str(body.get("id", ""))
    action = str(body.get("action", ""))
    if action not in {"like", "save", "dismiss"} or not any(item["id"] == item_id for item in FEED):
        return jsonify({"error": "Invalid feed action."}), 400
    actions = load_data("feed_actions")
    actions.append({"id": item_id, "action": action, "created_at": utc_now()})
    actions[:] = actions[-500:]
    save_data("feed_actions", actions)
    if action == "save":
        saved = load_data("saved_content")
        item = next(item for item in FEED if item["id"] == item_id)
        if not any(saved_item["id"] == item_id for saved_item in saved):
            saved.append(item)
            save_data("saved_content", saved)
    preferences = load_data("preferences")
    if action in {"like", "save"}:
        item = next(item for item in FEED if item["id"] == item_id)
        category = item["category"]
        if category not in preferences["feed_categories"]:
            preferences["feed_categories"].append(category)
            save_data("preferences", preferences)
    return jsonify({"ok": True})


@app.route("/api/preferences", methods=["GET", "POST"])
def preferences():
    items = load_data("preferences")
    if request.method == "GET":
        return jsonify(items)
    body = request.get_json(silent=True) or {}
    allowed = {"theme", "name", "music_mode", "memory_enabled", "feed_categories"}
    for key in allowed.intersection(body):
        items[key] = body[key]
    if items["theme"] not in {"light", "dark"}:
        items["theme"] = "light"
    if items["music_mode"] not in {"match", "improve"}:
        items["music_mode"] = "match"
    save_data("preferences", items)
    return jsonify(items)


@app.route("/api/memories", methods=["GET", "POST", "DELETE"])
def memories():
    items = load_data("memories")
    if request.method == "GET":
        return jsonify(items)
    if request.method == "DELETE":
        save_data("memories", [])
        return jsonify([])
    body = request.get_json(silent=True) or {}
    memory = str(body.get("memory", "")).strip()
    if not memory:
        return jsonify({"error": "Memory cannot be empty."}), 400
    if len(memory) > 500:
        return jsonify({"error": "Keep a memory under 500 characters."}), 400
    items.append({"id": f"memory-{int(time.time() * 1000)}", "text": memory, "created_at": utc_now()})
    save_data("memories", items)
    return jsonify(items), 201


@app.route("/api/memories/<memory_id>", methods=["DELETE"])
def delete_memory(memory_id):
    items = load_data("memories")
    items = [item for item in items if item["id"] != memory_id]
    save_data("memories", items)
    return jsonify(items)


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    moods = load_data("moods")
    journals = load_data("journal")
    saved = load_data("saved_content")
    actions = load_data("feed_actions")
    now = datetime.now(timezone.utc)
    recent_moods = []
    for mood in moods:
        try:
            created = datetime.fromisoformat(mood["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if now - created <= timedelta(days=30):
                recent_moods.append(mood)
        except (KeyError, ValueError):
            continue
    counts = {}
    for mood in recent_moods:
        counts[mood["emotion"]] = counts.get(mood["emotion"], 0) + 1
    return jsonify({
        "moods": recent_moods,
        "mood_counts": counts,
        "journal_count": len(journals),
        "journal_streak": len({datetime.fromisoformat(entry["created_at"]).date().isoformat() for entry in journals[-30:]}),
        "saved_content": saved,
        "feed_interactions": len(actions),
    })


@app.route("/api/spotify/status", methods=["GET"])
def spotify_status():
    client_id = bool(os.getenv("SPOTIFY_CLIENT_ID"))
    client_secret = bool(os.getenv("SPOTIFY_CLIENT_SECRET"))
    configured = client_id and client_secret
    preferences = load_data("preferences")
    connected = bool(os.getenv("SPOTIFY_ACCESS_TOKEN"))
    return jsonify({"configured": configured, "connected": connected, "mode": preferences.get("music_mode", "match")})


@app.route("/api/spotify/recommendations", methods=["GET"])
def spotify_recommendations():
    mood = str(request.args.get("mood", "neutral")).lower()
    catalog = {
        "happy": "Sunlit Indie", "excited": "Positive Energy", "sad": "Soft Landing",
        "angry": "Channel the Fire", "anxious": "Slow the Room", "motivated": "Focus Forward",
        "neutral": "Quiet Discovery",
    }
    name = catalog.get(mood, catalog["neutral"])
    return jsonify({
        "mood": mood,
        "playlist": name,
        "available": bool(os.getenv("SPOTIFY_ACCESS_TOKEN")),
        "message": "Connect Spotify to control playback. This mood-to-playlist guide is available offline.",
    })


@app.route("/start_timer", methods=["POST"])
def start_timer():
    minutes = request.get_json(silent=True) or request.form
    try:
        seconds = max(60, min(60 * 180, int(minutes.get("minutes", 25)) * 60))
    except (TypeError, ValueError):
        return jsonify({"error": "Minutes must be a number."}), 400
    timer.start_timer(seconds)
    return jsonify({"remaining": timer.get_remaining_time()})


@app.route("/get_timer")
def get_timer():
    return jsonify({"remaining": timer.get_remaining_time(), "running": timer.is_running})


@app.route("/stop_timer", methods=["POST"])
def stop_timer():
    timer.stop_timer()
    return jsonify({"remaining": 0, "running": False})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("MIRRIME_PORT", "5000")), debug=os.getenv("MIRRIME_DEBUG") == "1")

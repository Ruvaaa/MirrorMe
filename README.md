# MirrorMe
🌟 MirrorMe — Your Reflective AI Companion
MirrorMe is an interactive AI-powered desktop app that feels like looking into a mirror of your mind. It features a deeply human chatbot named Mirri, mood detection, personalized music reflection via Spotify, and a TikTok-style feed tailored to your growth, creativity, and well-being.

✨ Features
🧠 Human-Like Chatbot (Mirri)
Powered by a locally hosted NLP model, Mirri engages you in emotional, growth-focused, and playful conversations that feel real.

🎵 Spotify Mood Sync (optional)
Detects your emotional tone and plays music to match or uplift your vibe via Spotify integration.

📱 TikTok-Style Feed
Shows short-form videos (coding tips, personal growth, F1, Ray William Johnson, etc.), with one popping up at a time for a calm, mindful experience.

💬 Emotion Detection
Reads your text input and detects your emotional state to personalize replies and content suggestions.

🖥️ Modern UI (React + Tailwind + Electron)
A clean, cozy interface with soft edges and a pink-white ombre gradient background that feels personal and comfortable.

📦 Tech Stack
Frontend: React + Tailwind CSS

Backend: Flask (Python)

Desktop App: Electron

NLP: spaCy

Optional: GPT-4 API (or local alternatives), Spotify API

🚀 Getting Started
1. Clone the repo
bash
Copy code
git clone https://github.com/your-username/mirrorme.git
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
npm install
npm run dev
4. Package with Electron
bash
Copy code
npm run electron
🧪 Demo Mode
Loads default chatbot responses from static/data/chat.json

Loads TikTok embeds from a hardcoded list

Use in offline mode or for hackathons without any paid APIs

📁 Folder Structure
swift
Copy code
MirrorMe/
│
├── backend/
│   ├── app.py
│   └── static/data/chat.json
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   └── components/
│   └── index.html
│
└── README.md

An error occured when loading the folder structure, but all files are there and should arranged in th above order for it to work

🧠 Philosophy
MirrorMe isn't just a chatbot — it's a personal, emotional, and aesthetic tool for self-reflection, motivation, and inspiration. Whether you're feeling down, pumped, or just bored, Mirri is there to connect and reflect your inner world.

🔮 Future Features
🎙️ Voice Input/Output

📆 Personal Tracker Integration

🪞 Real-Time Avatar Reactions

☁️ Cloud Save + Sync

🧩 Plugin System for Personalization

🧑‍💻 Made With Love By
👤 Ruvarashe Nemaramba
— AI dreamer, climate activist, F1 lover, and tech creative from Zimbabwe.

📜 License
This project is licensed under the MIT License.

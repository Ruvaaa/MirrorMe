from flask import Flask, render_template, request, jsonify
import spacy
import random
import json
import timer
import re

app = Flask(__name__, template_folder='template')
nlp = spacy.load('en_core_web_md')

# Load chatbot conversations
def load_fun_convo():
    with open("static/data/realistic_chatbot_convo_bestie_style_FULL.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        return data.get("realistic_chatbot_convo_bestie_style_FULL", {})

fun_convo = load_fun_convo()

# Emotion detection
def detect_emotion_from_text(text):
    text = text.lower()
    happy_words = ["happy", "joy", "glad", "love", 'amazing', 'joyful', 'great']
    sad_words = ["sad", "cry", "unhappy", "depressed", 'hurt']
    angry_words = ["angry", "mad", "furious", "annoyed", 'upset', 'pissed']
    surprise_words = ["wow", "surprised", "shocked", "amazed", 'excited', 'overjoyed', 'yaay']

    if any(word in text for word in happy_words):
        return "happy"
    elif any(word in text for word in sad_words):
        return "sad"
    elif any(word in text for word in angry_words):
        return "angry"
    elif any(word in text for word in surprise_words):
        return "excited"
    elif any(word in text for word in ['anxious', 'overthinking']):
        return 'anxious'
    elif any(word in text for word in ['motivated', 'pumped']):
        return 'motivated'
    else:
        return "pic"

def get_emotion_image(emotion):
    return f"/static/emotions/{emotion}.jpg"

# Keyword extraction (if needed in future)
def extract_keywords(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    stopwords = {'i', 'you', 'the', 'is', 'are', 'and', 'to', 'a', 'of', 'in', 'for', 'on', 'that', 'it', 'with', 'this', 'was'}
    return set(word for word in words if word not in stopwords)

# Main chatbot logic
def chatbot(user_input):
    doc_input = nlp(user_input.lower())
    best_match = None
    highest_similarity = 0

    for question, answer in fun_convo.items():
        doc_question = nlp(question.lower())
        similarity = doc_input.similarity(doc_question)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = answer

    emotion = detect_emotion_from_text(user_input)

    if highest_similarity > 0.7:
        return best_match, emotion
    else:
        return "Hmm, I’m not sure what you mean. Can you say that another way?", emotion

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    response, emotion = chatbot(user_input)
    image_path = get_emotion_image(emotion)
    return jsonify({
        "response": response,
        "emotion": emotion,
        "image_path": image_path
    })

@app.route('/start_timer', methods=['POST'])
def start_timer():
    minutes = int(request.form.get("minutes", 1))
    timer.start_timer(minutes * 60)
    return "Timer started"

@app.route('/get_timer')
def get_timer():
    return jsonify({"remaining": timer.get_remaining_time()})

@app.route('/stop_timer')
def stop_timer():
    timer.stop_timer()
    return "Timer stopped"

if __name__ == '__main__':
    app.run(debug=True)

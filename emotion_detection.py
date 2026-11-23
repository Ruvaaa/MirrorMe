"""Small keyword-based mood estimator kept for compatibility."""

import re


EMOTION_RULES = {
    "happy": ["happy", "joy", "glad", "good", "great", "grateful", "love"],
    "excited": ["excited", "pumped", "thrilled", "celebrate", "amazing"],
    "sad": ["sad", "down", "cry", "lonely", "hurt", "depressed"],
    "angry": ["angry", "mad", "furious", "annoyed", "frustrated", "pissed"],
    "anxious": ["anxious", "worried", "nervous", "overthinking", "scared", "panic"],
    "motivated": ["motivated", "determined", "ready", "focused", "goal"],
}


def detect_emotion_from_text(text):
    words = set(re.findall(r"[a-z']+", (text or "").lower()))
    for emotion, phrases in EMOTION_RULES.items():
        if words.intersection(phrases):
            return emotion
    return "neutral"

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_AUTH_TOKEN = "Bearer LINGOLENS_SECRET_KEY_2026"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def calculate_agent_state(user_memory):
    words_learned = user_memory.get("words_learned", 0)
    streak_days = user_memory.get("streak_days", 1)
    
    if words_learned < 20:
        level = "A1 Beginner"
    elif words_learned < 100:
        level = "A2-B1 Intermediate"
    else:
        level = "B2-C1 Advanced"

    if streak_days > 3:
        mood = "Enthusiastic Coach"
    else:
        mood = "Friendly Mentor"

    return level, mood

@app.route("/api/index", methods=["POST"])
def main_handler():
    auth_header = request.headers.get("Authorization")
    if auth_header != API_AUTH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    mode = data.get("mode", "standard")
    text = data.get("text", "")
    source_lang = data.get("source_lang", "ka")
    target_lang = data.get("target_lang", "en_US")
    image_b64 = data.get("image_data", None)
    memory = data.get("memory", {})

    level, mood = calculate_agent_state(memory)

    # 1. AI AGENT AUTONOMOUS MODE
    if mode == "agent":
        prompt = f"""
        You are LingoLens Autonomous AI Agent. 
        User Level: {level}, Tone: {mood}.
        User input in {source_lang}: "{text}".
        Respond in {target_lang} as an encouraging conversational partner, then provide Georgian translation.
        """
        raw_ai = query_gemini(prompt)
        return jsonify({
            "translated_text": raw_ai,
            "agent_mood": mood,
            "current_level": level
        })

    # 2. AR VISION SCANNER MODE
    elif mode == "vision_ar" and image_b64:
        prompt = f"Extract all visible text from this image and translate it to language '{target_lang}'. Return ONLY translated text."
        raw_ai = query_gemini_vision(prompt, image_b64)
        return jsonify({"translated_text": raw_ai})

    # 3. GRAMMAR ANALYSIS MODE
    elif mode == "grammar":
        prompt = f"Translate '{text}' from {source_lang} to {target_lang}. Then provide bulleted grammar breakdown in Georgian."
        raw_ai = query_gemini(prompt)
        parts = raw_ai.split("\n\n", 1)
        trans = parts[0] if len(parts) > 0 else raw_ai
        gramm = parts[1] if len(parts) > 1 else "გრამატიკული ანალიზი ხელმისაწვდომია."
        return jsonify({"translated_text": trans, "grammar_analysis": gramm})

    # 4. STANDARD REAL-TIME TRANSLATION
    else:
        prompt = f"Translate the following text strictly from {source_lang} to {target_lang}. Return ONLY the final translation:\n\n{text}"
        translated = query_gemini(prompt)
        return jsonify({"translated_text": translated})

def query_gemini(prompt):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY არ არის კონფიგურირებული."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[AI Error: {str(e)}]"

def query_gemini_vision(prompt, image_b64):
    if not GEMINI_API_KEY:
        return "[API Key missing]"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
            ]
        }]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "[Vision Error]"

if __name__ == "__main__":
    app.run(port=5000)

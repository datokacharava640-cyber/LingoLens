import threading
import requests
import speech_recognition as sr
from kivy.app import App

class LiveInterpreter:
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.is_listening = False
        self.recognizer = sr.Recognizer()

    def start_listening(self, src_lang="ka-GE", target_lang="en", callback=None):
        self.is_listening = True
        threading.Thread(target=self._listen_loop, args=(src_lang, target_lang, callback), daemon=True).start()

    def stop_listening(self):
        self.is_listening = False

    def _listen_loop(self, src_lang, target_lang, callback):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio, language=src_lang)
                    
                    if text:
                        # Gemini Live Translation
                        translated = self.translate_with_gemini(text, target_lang)
                        if callback:
                            callback(text, translated)
                except Exception:
                    continue

    def translate_with_gemini(self, text, target_lang):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Translate this in real-time to language code '{target_lang}'. Output ONLY translated text: {text}"}]
            }]
        }
        try:
            res = requests.post(url, json=payload, timeout=5).json()
            return res['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception:
            return text

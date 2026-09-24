import threading
import requests
import json
import config

def translate_text(prompt, text, src_lang, target_lang, callback):
    def _worker():
        try:
            api_key = getattr(config, 'GEMINI_API_KEY', '')
            if not api_key:
                callback("გთხოვთ მიუთითოთ API Key პარამეტრებში")
                return

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            res = requests.post(url, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        callback(parts[0].get('text', ''))
                        return
                callback("თარგმანი ვერ მოიძებნა")
            else:
                callback(f"API შეცდომა: {res.status_code}")
        except Exception as e:
            callback(f"შეცდომა: {str(e)}")

    threading.Thread(target=_worker, daemon=True).start()

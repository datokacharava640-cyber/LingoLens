import requests
import threading
import config

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    """
    სცდილობს Gemini API-ით თარგმნას. 
    შეცდომის (401/400) შემთხვევაში ავტომატურად გადადის Free Google Translate-ზე.
    """
    def worker():
        translated_text = None
        
        # 1. Gemini API
        if config.GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, json=payload, headers=headers, timeout=6)
                if response.status_code == 200:
                    res_data = response.json()
                    translated_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            except Exception:
                pass

        # 2. Fallback Google Translate
        if not translated_text and raw_text:
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={requests.utils.quote(raw_text)}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    translated_text = res.json()[0][0][0]
            except Exception as e:
                translated_text = f"შეცდომა: {str(e)}"

        callback(translated_text)

    threading.Thread(target=worker).start()

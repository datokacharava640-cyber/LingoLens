import threading
import requests
import google.generativeai as genai
import config

# Gemini-ს კონფიგურაცია
try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception:
    model = None

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    def _worker():
        result = None
        # 1. ვცდილობთ Gemini API-ით თარგმნას
        if model and config.GEMINI_API_KEY:
            try:
                response = model.generate_content(prompt)
                if response and response.text:
                    result = response.text.strip()
            except Exception as e:
                print(f"Gemini Error: {e}")

        # 2. თუ Gemini-მ ვერ ითარგმნა, გადავდივართ Google Translate Fallback-ზე
        if not result:
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={requests.utils.quote(raw_text)}"
                res = requests.get(url, timeout=5).json()
                result = "".join([item[0] for item in res[0] if item[0]])
            except Exception as e:
                print(f"Fallback Error: {e}")
                result = "თარგმანი ვერ განხორციელდა"

        callback(result)

    threading.Thread(target=_worker, daemon=True).start()

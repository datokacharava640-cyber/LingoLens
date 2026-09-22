import threading
import requests
import config

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    def _worker():
        result = None
        api_key = getattr(config, 'GEMINI_API_KEY', '')

        # 1. Gemini REST API მოთხოვნა
        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(url, json=data, headers=headers, timeout=10)
                if response.status_code == 200:
                    res_json = response.json()
                    result = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                else:
                    print(f"Gemini API Status Code Error: {response.status_code}")
            except Exception as e:
                print(f"Gemini Request Error: {e}")

        # 2. Google Translate Fallback (თუ Gemini-მ არ იმუშავა)
        if not result:
            try:
                fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={requests.utils.quote(raw_text)}"
                res = requests.get(fallback_url, timeout=5).json()
                result = "".join([item[0] for item in res[0] if item[0]])
            except Exception as e:
                print(f"Fallback Error: {e}")
                result = "თარგმანი ვერ განხორციელდა"

        callback(result)

    threading.Thread(target=_worker, daemon=True).start()

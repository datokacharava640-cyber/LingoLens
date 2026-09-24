import threading
import requests
import urllib3
import config

# SSL Warning-ების გათიშვა (Android-ზე SSL შეცდომების თავიდან ასაცილებლად)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    def _worker():
        result = None
        api_key = getattr(config, 'GEMINI_API_KEY', '')

        # 1. Gemini REST API მოთხოვნა
        if api_key and api_key.strip():
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                # verify=False ამცირებს Android SSL Crash-ის რისკს
                response = requests.post(url, json=data, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    res_json = response.json()
                    # უსაფრთხო წაკითხვა JSON-ის
                    candidates = res_json.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            result = parts[0].get('text', '').strip()
                else:
                    print(f"Gemini API Status Code Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Gemini Request Error: {e}")

        # 2. Google Translate Fallback (თუ Gemini-მ არ იმუშავა ან Key არ არის)
        if not result:
            try:
                quoted_text = requests.utils.quote(raw_text)
                fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={quoted_text}"
                
                res = requests.get(fallback_url, timeout=5, verify=False).json()
                if res and isinstance(res, list) and len(res) > 0 and res[0]:
                    result = "".join([item[0] for item in res[0] if item and item[0]])
            except Exception as e:
                print(f"Fallback Error: {e}")
                result = "თარგმანი ვერ განხორციელდა (შეამოწმეთ ინტერნეტი)"

        # უზრუნველყოფა, რომ callback-ს ყოველთვის გადაეცეს ტექსტი
        if not result:
            result = "შეცდომა თარგმნისას"

        callback(result)

    threading.Thread(target=_worker, daemon=True).start()

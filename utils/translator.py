import threading
import requests
import urllib3
import json
import os
import base64
from urllib.parse import quote
import config

# SSL Warning-ების გათიშვა Android-ზე სტაბილურობისთვის
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SETTINGS_FILE = "settings.json"

def get_api_key():
    """კითხულობს API Key-ს ჯერ settings.json ფაილიდან, ხოლო თუ არ არის - config-იდან"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = data.get("api_key", "").strip()
                if key:
                    return key
        except Exception as e:
            print("Settings read error:", e)
    
    return getattr(config, 'GEMINI_API_KEY', '')

def translate_text(prompt, raw_text, src_lang, target_lang, callback):
    """ტექსტის თარგმნის ფუნქცია (Gemini API + Google Translate Fallback)"""
    def _worker():
        result = None
        api_key = get_api_key()

        # 1. Gemini REST API Request
        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                
                response = requests.post(url, json=data, headers=headers, timeout=10, verify=False)
                
                if response.status_code == 200:
                    res_json = response.json()
                    candidates = res_json.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            result = parts[0].get('text', '').strip()
                else:
                    print(f"Gemini Status Code Error: {response.status_code}")
            except Exception as e:
                print("Gemini Request Error:", e)

        # 2. Google Translate Fallback (თუ Gemini არ იმუშავებს)
        if not result:
            try:
                quoted_text = quote(raw_text)
                fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={target_lang}&dt=t&q={quoted_text}"
                
                res = requests.get(fallback_url, timeout=5, verify=False).json()
                if res and isinstance(res, list) and len(res) > 0 and res[0]:
                    result = "".join([item[0] for item in res[0] if item and item[0]])
            except Exception as e:
                print("Fallback Error:", e)
                result = "თარგმანი ვერ განხორციელდა (შეამოწმეთ ინტერნეტი)"

        if not result:
            result = "შეცდომა თარგმნისას"

        callback(result)

    threading.Thread(target=_worker, daemon=True).start()


def analyze_image_and_translate(image_path, target_lang, callback):
    """სურათიდან ტექსტის ამოცნობისა და თარგმნის ფუნქცია (OCR) Gemini-ს მეშვეობით"""
    def _worker():
        api_key = get_api_key()
        if not api_key:
            callback("გთხოვთ, შეიყვანოთ Gemini API Key პარამეტრებში!")
            return

        try:
            # სურათის წაკითხვა და Base64-ში გადაყვანა
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            prompt_text = f"Extract all text from this image and translate it to language code '{target_lang}'. Return the original text and its translation."
            
            data = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_data
                            }
                        }
                    ]
                }]
            }

            response = requests.post(url, json=data, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        text_result = parts[0].get('text', '').strip()
                        callback(text_result)
                    else:
                        callback("ტექსტი ვერ ამოიცნო.")
                else:
                    callback("სურათის დამუშავება ვერ მოხერხდა.")
            else:
                callback(f"API შეცდომა: {response.status_code}")
        except Exception as e:
            print("OCR Error:", e)
            callback("შეცდომა სურათის წაკითხვისას.")

    threading.Thread(target=_worker, daemon=True).start()

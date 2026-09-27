# ==============================================================================
# LingoLens AI - Translator Utility (Direct Root Endpoint)
# ==============================================================================

import requests
import json
import os
import threading

DEFAULT_BACKEND_URL = "https://lingolens-pied.vercel.app"

def get_active_backend():
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("api_key") or data.get("backend_url")
                if url and url.startswith("http"):
                    return url.strip()
    except Exception as e:
        print("Error reading settings.json:", e)
    
    return DEFAULT_BACKEND_URL

def translate_text(prompt, text, source_lang="ka", target_lang="en", callback=None):
    """
    ტექსტის თარგმნის ფუნქცია — იყენებს პირდაპირ ძირითად მისამართს.
    """
    def run_translation():
        endpoint = get_active_backend().rstrip('/')
        
        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "prompt": prompt
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            print(f"Sending request to: {endpoint}")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    translated = (
                        res_json.get("translated_text") or 
                        res_json.get("result") or 
                        res_json.get("text") or 
                        res_json.get("response")
                    )
                    if not translated and isinstance(res_json, str):
                        translated = res_json
                        
                    if translated and callback:
                        callback(translated)
                        return
                except Exception as json_err:
                    # თუ პასუხი JSON არ არის, შესაძლოა უბრალოდ ტექსტი იყოს
                    if response.text and callback:
                        callback(response.text)
                        return

            if callback:
                callback(f"სერვერის შეცდომა: კოდი {response.status_code}")
        except Exception as e:
            print(f"Connection failed: {e}")
            if callback:
                callback("კავშირის შეცდომა სერვერთან")

    threading.Thread(target=run_translation, daemon=True).start()

def analyze_image_and_translate(image_path, target_lang="ka", callback=None):
    def run_ocr():
        endpoint = get_active_backend().rstrip('/')
        try:
            with open(image_path, "rb") as img_file:
                files = {"file": img_file}
                data = {"target_lang": target_lang}
                response = requests.post(endpoint, files=files, data=data, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    text = res_json.get("text") or res_json.get("translated_text")
                    if callback:
                        callback(text or "ტექსტი ვერ მოიძებნა")
                    return
        except Exception as e:
            print(f"OCR failed: {e}")

        if callback:
            callback("სურათის დამუშავების შეცდომა")

    threading.Thread(target=run_ocr, daemon=True).start()

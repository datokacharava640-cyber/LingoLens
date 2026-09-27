# ==============================================================================
# LingoLens AI - Translator Utility (Expanded Endpoints & Debug Logging)
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
    ტექსტის თარგმნის ფუნქცია გაფართოებული მისამართებით და დებაგინგით.
    """
    def run_translation():
        base_url = get_active_backend().rstrip('/')
        
        # სავარაუდო ბილიკების სია
        endpoints = [
            f"{base_url}/api/translate",
            f"{base_url}/translate",
            f"{base_url}/api",
            base_url
        ]

        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "prompt": prompt
        }

        headers = {
            "Content-Type": "application/json"
        }

        success = False
        for endpoint in endpoints:
            try:
                print(f"Trying translation endpoint: {endpoint}")
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                print(f"Response status from {endpoint}: {response.status_code}")
                print(f"Response body: {response.text[:200]}")
                
                if response.status_code == 200:
                    try:
                        res_json = response.json()
                        translated = res_json.get("translated_text") or res_json.get("result") or res_json.get("text") or res_json.get("response")
                        if translated:
                            if callback:
                                callback(translated)
                            success = True
                            return
                    except Exception as json_err:
                        print("JSON parse error:", json_err)
            except Exception as e:
                print(f"Endpoint {endpoint} failed: {e}")

        if not success and callback:
            callback("სერვერის შეცდომა: ვერ მოიძებნა სწორი მისამართი (404)")

    threading.Thread(target=run_translation, daemon=True).start()

def analyze_image_and_translate(image_path, target_lang="ka", callback=None):
    """
    სურათის ანალიზისა და OCR-ის ფუნქცია
    """
    def run_ocr():
        base_url = get_active_backend().rstrip('/')
        endpoints = [
            f"{base_url}/api/ocr",
            f"{base_url}/ocr",
            f"{base_url}/api",
            base_url
        ]
        
        for endpoint in endpoints:
            try:
                with open(image_path, "rb") as img_file:
                    files = {"file": img_file}
                    data = {"target_lang": target_lang}
                    response = requests.post(endpoint, files=files, data=data, timeout=15)
                    print(f"OCR Response status from {endpoint}: {response.status_code}")
                    if response.status_code == 200:
                        res_json = response.json()
                        text = res_json.get("text") or res_json.get("translated_text")
                        if callback:
                            callback(text or "ტექსტი ვერ მოიძებნა")
                        return
            except Exception as e:
                print(f"OCR endpoint {endpoint} failed: {e}")

        if callback:
            callback("სურათის დამუშავების შეცდომა: სერვერი მიუწვდომელია")

    threading.Thread(target=run_ocr, daemon=True).start()

# ==============================================================================
# LingoLens AI - Translator Utility (Perfect Response Parser)
# ==============================================================================

import requests
import json
import os
import threading

# შენი საკუთარ სერვერზე გადართული მისამართი
DEFAULT_BACKEND_URL = "http://37.27.255.1:8000"

def get_active_backend():
    try:
        # თუ settings.json არ არსებობს, ავტომატურად ვქმნით დეფოლტ ბმულით
        if not os.path.exists("settings.json"):
            default_data = {"backend_url": DEFAULT_BACKEND_URL}
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
                print("settings.json წარმატებით შეიქმნა ავტომატურად!")

        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("api_key") or data.get("backend_url")
                if url and url.startswith("http"):
                    return url.strip()
    except Exception as e:
        print("Error handling settings.json:", e)
    
    return DEFAULT_BACKEND_URL

def translate_text(prompt, text, source_lang="ka", target_lang="en", callback=None):
    def run_translation():
        endpoint = get_active_backend().rstrip('/')
        # ვუერთებთ სწორ ენდპოინტს (თუ სერვერზე ტექსტის სათარგმნი მისამართი გვაქვს)
        url = f"{endpoint}/" if not endpoint.endswith("/") else endpoint
        
        full_prompt = f"Translate the following text from {source_lang} to {target_lang}. Text: {text}. Custom instruction: {prompt}"

        payload = {
            "prompt": full_prompt
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            print(f"Sending translation request to: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    translated = res_json.get("result") or res_json.get("translated_text") or res_json.get("text")
                    
                    if not translated and isinstance(res_json, str):
                        translated = res_json

                    if translated and callback:
                        callback(translated.strip())
                        return
                except Exception as parse_err:
                    if response.text and callback:
                        callback(response.text.strip())
                        return
            
            if callback:
                callback(f"სერვერის შეცდომა: კოდი {response.status_code}")
        except Exception as e:
            print(f"Connection error: {e}")
            if callback:
                callback("კავშირის შეცდომა სერვერთან")

    threading.Thread(target=run_translation, daemon=True).start()

def analyze_image_and_translate(image_path, target_lang="ka", callback=None):
    def run_ocr():
        endpoint = get_active_backend().rstrip('/')
        url = f"{endpoint}/translate-image/"
        try:
            with open(image_path, "rb") as img_file:
                files = {"file": img_file}
                data = {"target_lang": target_lang}
                print(f"Sending image to: {url}")
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    res_json = response.json()
                    text = res_json.get("translated_text") or res_json.get("result") or res_json.get("text")
                    if callback:
                        callback(text or "ტექსტი ვერ მოიძებნა")
                    return
                else:
                    if callback:
                        callback(f"სერვერის შეცდომა: {response.status_code}")
        except Exception as e:
            print(f"OCR error: {e}")
            if callback:
                callback("სურათის დამუშავების შეცდომა")

    threading.Thread(target=run_ocr, daemon=True).start()

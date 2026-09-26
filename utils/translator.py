# ==============================================================================
# LingoLens AI - Translator Utility (Fixed Backend URL)
# ==============================================================================

import requests
import json
import os

# მყარად გაწერილი Vercel ბექენდის მისამართი, რომელიც არასოდეს დაიკარგება
DEFAULT_BACKEND_URL = "https://lingolens-pied.vercel.app"

def get_active_backend():
    """ცდილობს წაიკითხოს მისამართი პარამეტრებიდან, თუ ვერ იპოვა - იყენებს ძირითად Vercel მისამართს"""
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
    ტექსტის თარგმნის მთავარი ფუნქცია, რომელიც აგზავნის მოთხოვნას Vercel სერვერზე.
    """
    def run_translation():
        backend_url = get_active_backend()
        
        # თუ მისამართი ბოლოში არ შეიცავს /translate-ს, ავტომატურად ვამატებთ
        if not backend_url.endswith("/translate") and not backend_url.endswith("/api/translate"):
            # ვცდებით ორივე ვარიანტს ან ძირითად მისამართს
            api_endpoint = f"{backend_url.rstrip('/')}/api/translate" if "vercel.app" in backend_url else f"{backend_url.rstrip('/')}/translate"
        else:
            api_endpoint = backend_url

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
            print(f"Sending translation request to: {api_endpoint}")
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                res_json = response.json()
                translated = res_json.get("translated_text") or res_json.get("result") or res_json.get("text")
                if translated:
                    if callback:
                        callback(translated)
                    return
                else:
                    if callback:
                        callback(f"პასუხის ფორმატი არასწორია: {response.text}")
            else:
                # თუ /api/translate-ზე ვერ იპოვა, ვცდით პირდაპირ ძირითად მისამართს
                alt_endpoint = backend_url.rstrip('/')
                response_alt = requests.post(alt_endpoint, json=payload, headers=headers, timeout=15)
                if response_alt.status_code == 200:
                    res_json = response_alt.json()
                    translated = res_json.get("translated_text") or res_json.get("result") or res_json.get("text")
                    if translated:
                        if callback:
                            callback(translated)
                        return

                if callback:
                    callback(f"სერვერის შეცდომა (კოდი: {response.status_code})")
        except Exception as e:
            error_msg = f"კავშირის შეცდომა: {str(e)}"
            print(error_msg)
            if callback:
                callback(error_msg)

    import threading
    threading.Thread(target=run_translation, daemon=True).start()

def analyze_image_and_translate(image_path, target_lang="ka", callback=None):
    """
    სურათის ანალიზისა და OCR-ის ფუნქცია
    """
    def run_ocr():
        backend_url = get_active_backend()
        api_endpoint = f"{backend_url.rstrip('/')}/api/ocr" if "vercel.app" in backend_url else f"{backend_url.rstrip('/')}/ocr"
        
        try:
            with open(image_path, "rb") as img_file:
                files = {"file": img_file}
                data = {"target_lang": target_lang}
                response = requests.post(api_endpoint, files=files, data=data, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    text = res_json.get("text") or res_json.get("translated_text")
                    if callback:
                        callback(text or "ტექსტი ვერ მოიძებნა")
                else:
                    if callback:
                        callback(f"OCR შეცდომა: {response.status_code}")
        except Exception as e:
            if callback:
                callback(f"სურათის დამუშავების შეცდომა: {str(e)}")

    import threading
    threading.Thread(target=run_ocr, daemon=True).start()

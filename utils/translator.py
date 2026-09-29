# ==============================================================================
# LingoLens AI - Translator & Image Processing Module
# ==============================================================================

import threading
import requests
from kivy.clock import Clock

# სერვერის კონფიგურაცია
BACKEND_URL = "http://37.27.255.1:8001"
APP_NAME = "LingoLens"
VERSION = "6.0.2"

def analyze_image_and_translate(image_path, target_language="ka", callback=None):
    """
    სურათის ფოტოს ატვირთვა და სერვერზე გაგზავნა
    """
    def background_image_request():
        try:
            url = f"{BACKEND_URL.rstrip('/')}/translate-image"
            headers = {
                "User-Agent": f"{APP_NAME}/{VERSION}"
            }
            
            with open(image_path, "rb") as img_file:
                files = {"file": (image_path, img_file, "image/jpeg")}
                data = {"target_lang": target_language}
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    res_data = response.json()
                    result = res_data.get("translated_text", "სურათი წარმატებით ითარგმნა")
                else:
                    result = f"სერვერის შეცდომა: {response.status_code}"
                
                if callback:
                    Clock.schedule_once(lambda dt: callback(result))
                    
        except Exception as e:
            if callback:
                Clock.schedule_once(lambda dt: callback(f"კავშირის შეცდომა: {e}"))

    threading.Thread(target=background_image_request, daemon=True).start()

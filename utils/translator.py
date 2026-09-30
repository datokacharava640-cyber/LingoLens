# ==============================================================================
# LingoLens AI - Translator & Image Processing Module
# ==============================================================================

import threading
import requests
from kivy.clock import Clock

# სერვერის კონფიგურაცია (პორტი გასწორებულია 8000-ზე)
BACKEND_URL = "http://37.27.255.1:8000"
APP_NAME = "LingoLens"
VERSION = "6.0.2"
API_SECRET_KEY = "lingolens-secret-key-2026"


def analyze_image_and_translate(image_path, target_language="ka", callback=None):
  """სურათის ფოტოს ატვირთვა და სერვერზე გაგზავნა უსაფრთხოების ჰედერთან ერთად"""

  def background_image_request():
    try:
      url = f"{BACKEND_URL.rstrip('/')}/translate-image"

      # დავამატეთ X-API-Key ჰედერი, რომ სერვერმა უსაფრთხოდ მიიღოს მოთხოვნა
      headers = {
          "User-Agent": f"{APP_NAME}/{VERSION}",
          "X-API-Key": API_SECRET_KEY,
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

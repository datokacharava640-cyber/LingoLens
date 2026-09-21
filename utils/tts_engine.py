import os
import requests
import threading
from kivy.core.audio import SoundLoader

def speak(text, lang, user_data_dir, status_callback):
    if not text.strip():
        status_callback("⚠️ ტექსტი ცარიელია!")
        return

    status_callback(f"🔊 გახმოვანება ({lang.upper()})...")

    def worker():
        try:
            tts_lang = "ka" if lang == "ka" else lang
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={requests.utils.quote(text)}&tl={tts_lang}&client=tw-ob"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=7)
            
            if res.status_code == 200:
                temp_file = os.path.join(user_data_dir, "temp_audio.mp3") if user_data_dir else "temp_audio.mp3"
                with open(temp_file, "wb") as f:
                    f.write(res.content)
                sound = SoundLoader.load(temp_file)
                if sound:
                    sound.play()
        except Exception as e:
            status_callback(f"TTS შეცდომა: {str(e)}")

    threading.Thread(target=worker).start()

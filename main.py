"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia (საქართველო)
Release Date        : September 10, 2026
Project Name        : LingoLens AI
Version             : 2.5.0 (Production Ready Build)
License             : Proprietary / All Rights Reserved
=============================================================================
"""

import os
import sys
import io
import sqlite3
import threading
import requests
from PIL import Image as PILImage

# Kivy Framework UI Components
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner

try:
    import config
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False

try:
    import languages
    LANGUAGES_LOADED = True
except ImportError:
    LANGUAGES_LOADED = False

try:
    from offline_engine import OfflineEngine
    OFFLINE_ENGINE_LOADED = True
except ImportError:
    OFFLINE_ENGINE_LOADED = False

try:
    from plyer import clipboard, tts
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

# რეალური დეპლოიმენტის რეზერვული მისამართი
FALLBACK_API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app/ocr-translate"


class SecurityManager:
    @classmethod
    def verify_runtime_integrity(cls):
        if sys.gettrace() is not None:
            sys.exit(1)


class StorageManager:
    def __init__(self):
        self.conn = sqlite3.connect("lingolens_secure.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_text TEXT,
                translated_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_translation(self, src, trans):
        if not src.strip() or not trans.strip():
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO history (src_text, translated_text) VALUES (?, ?)", (src, trans))
            self.conn.commit()
        except Exception as e:
            print(f"[DB Error]: {e}")


class CloudTranslationEngine:
    def __init__(self):
        if CONFIG_LOADED and hasattr(config, 'API_ENDPOINT'):
            self.api_endpoint = config.API_ENDPOINT
        else:
            self.api_endpoint = FALLBACK_API_URL

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Android; Mobile)'})

        if OFFLINE_ENGINE_LOADED:
            self.offline_fallback = OfflineEngine()
        else:
            self.offline_fallback = None

    def translate(self, text, src_lang='auto', target_lang='ka', tone="Standard"):
        SecurityManager.verify_runtime_integrity()

        if not text.strip():
            return ""

        try:
            # მოთხოვნა Vercel-ის API-ზე
            payload = {'file': ('text.txt', text.encode('utf-8'), 'text/plain')}
            data = {'target_lang': target_lang}
            response = self.session.post(self.api_endpoint, files=payload, data=data, timeout=5)
            
            if response.status_code == 200:
                res = response.json()
                raw_translation = res.get("translated_text", "")
                if not raw_translation:
                    raw_translation = text

                if tone == "Formal":
                    return f"გთხოვთ იხილოთ: {raw_translation}"
                elif tone == "Casual":
                    return f"აბა ნახე: {raw_translation}"
                return raw_translation
        except Exception as e:
            print(f"[Translation Network Error]: {e}")
            if self.offline_fallback and hasattr(self.offline_fallback, 'translate'):
                return self.offline_fallback.translate(text, src_lang, target_lang) + " (Offline)"

        return text


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def build(self):
        SecurityManager.verify_runtime_integrity()

        if os.path.exists("font.ttf"):
            LabelBase.register(name="CustomFont", fn_regular="font.ttf")

        self.title = "LingoLens AI"
        self.cloud_engine = CloudTranslationEngine()
        self.storage = StorageManager()
        
        self.debounce_timer = None
        self.is_live_ocr = False
        self.live_ocr_event = None

        root = BoxLayout(orientation='vertical', padding=8, spacing=6)

        header = Label(
            text="LingoLens AI - Live Translation",
            font_size='18sp',
            bold=True,
            size_hint_y=0.05,
            color=(0.2, 0.8, 0.4, 1)
        )
        root.add_widget(header)

        selectors = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        selectors.add_widget(Label(text="Tone:", size_hint_x=0.15))
        self.tone_spinner = Spinner(
            text='Standard',
            values=('Standard', 'Formal', 'Casual'),
            size_hint_x=0.35
        )
        selectors.add_widget(self.tone_spinner)

        lang_values = ('ka', 'en', 'es', 'fr', 'de', 'ru')
        if LANGUAGES_LOADED and hasattr(languages, 'SUPPORTED_LANGUAGES'):
            lang_values = tuple(languages.SUPPORTED_LANGUAGES.keys())

        selectors.add_widget(Label(text="Target:", size_hint_x=0.15))
        self.lang_spinner = Spinner(
            text='ka',
            values=lang_values,
            size_hint_x=0.35
        )
        selectors.add_widget(self.lang_spinner)
        root.add_widget(selectors)

        self.camera = Camera(play=True, resolution=(640, 480), size_hint_y=0.35)
        root.add_widget(self.camera)

        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი ან გამოიყენეთ Live კამერა...",
            multiline=True,
            size_hint_y=0.18,
            font_size='15sp'
        )
        self.input_text.bind(text=self.on_text_change)
        root.add_widget(self.input_text)

        self.output_text = TextInput(
            hint_text="ნათარგმნი ტექსტი...",
            multiline=True,
            readonly=True,
            size_hint_y=0.18,
            font_size='15sp'
        )
        root.add_widget(self.output_text)

        btn_grid = GridLayout(cols=3, spacing=6, size_hint_y=0.12)

        self.btn_live = Button(text="▶ Live OCR", background_color=(0.1, 0.6, 0.9, 1))
        self.btn_live.bind(on_press=self.toggle_live_ocr)
        btn_grid.add_widget(self.btn_live)

        btn_tts = Button(text="🔊 Speak", background_color=(0.8, 0.4, 0.1, 1))
        btn_tts.bind(on_press=self.speak_translation)
        btn_grid.add_widget(btn_tts)

        btn_copy = Button(text="📋 Copy", background_color=(0.3, 0.3, 0.8, 1))
        btn_copy.bind(on_press=self.copy_to_clipboard)
        btn_grid.add_widget(btn_copy)

        root.add_widget(btn_grid)

        self.status_label = Label(
            text="Ready | Live OCR Engine Active",
            size_hint_y=0.04,
            font_size='11sp'
        )
        root.add_widget(self.status_label)

        return root

    def on_text_change(self, instance, value):
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = Clock.schedule_once(lambda dt: self.perform_translation(value), 0.4)

    def perform_translation(self, text):
        if not text.strip():
            self.output_text.text = ""
            return

        selected_tone = self.tone_spinner.text
        selected_lang = self.lang_spinner.text

        def async_task():
            result = self.cloud_engine.translate(
                text, src_lang='auto', target_lang=selected_lang, tone=selected_tone
            )
            self.update_output_ui(result, text)

        threading.Thread(target=async_task, daemon=True).start()

    @mainthread
    def update_output_ui(self, result, original_text):
        self.output_text.text = result
        self.storage.save_translation(original_text, result)
        self.status_label.text = "თარგმნა დასრულდა"

    def toggle_live_ocr(self, instance):
        if not self.is_live_ocr:
            self.is_live_ocr = True
            self.btn_live.text = "⏹ Stop Live"
            self.btn_live.background_color = (0.9, 0.2, 0.2, 1)
            self.status_label.text = "Live OCR ჩართულია..."
            self.live_ocr_event = Clock.schedule_interval(self.process_live_frame, 2.5)
        else:
            self.stop_live_ocr()

    def stop_live_ocr(self):
        self.is_live_ocr = False
        self.btn_live.text = "▶ Live OCR"
        self.btn_live.background_color = (0.1, 0.6, 0.9, 1)
        self.status_label.text = "Live OCR გაჩერებულია"
        if self.live_ocr_event:
            self.live_ocr_event.cancel()

    def process_live_frame(self, dt):
        if not self.camera or not self.camera.texture:
            return

        texture = self.camera.texture
        size = texture.size
        pixels = texture.pixels

        api_url = getattr(config, 'API_ENDPOINT', None) if CONFIG_LOADED else None
        if not api_url:
            api_url = FALLBACK_API_URL

        target_lang = self.lang_spinner.text

        def async_frame_send():
            try:
                pil_img = PILImage.frombytes(mode='RGBA', size=size, data=pixels)
                buffer = io.BytesIO()
                pil_img.convert('RGB').save(buffer, format='JPEG')
                buffer.seek(0)

                files = {'file': ('frame.jpg', buffer, 'image/jpeg')}
                data = {'target_lang': target_lang}

                response = requests.post(api_url, files=files, data=data, timeout=5)
                if response.status_code == 200:
                    res = response.json()
                    extracted = res.get("extracted_text", "")
                    translated = res.get("translated_text", "")
                    
                    if extracted.strip():
                        self.apply_live_results(extracted, translated)
            except Exception as e:
                print(f"[Live OCR Frame Error]: {e}")

        threading.Thread(target=async_frame_send, daemon=True).start()

    @mainthread
    def apply_live_results(self, extracted, translated):
        self.input_text.text = extracted
        if translated:
            self.output_text.text = translated
        self.status_label.text = "Live ტექსტი ამოცნობილია!"

    def speak_translation(self, instance):
        if HAS_PLYER and self.output_text.text:
            try:
                tts.speak(self.output_text.text)
            except Exception as e:
                self.status_label.text = f"TTS შეცდომა: {e}"

    def copy_to_clipboard(self, instance):
        if self.output_text.text and HAS_PLYER:
            try:
                clipboard.copy(self.output_text.text)
                self.status_label.text = "ტექსტი დაკოპირდა!"
            except Exception as e:
                self.status_label.text = f"შეცდომა: {e}"


if __name__ == "__main__":
    LingoLensApp().run()

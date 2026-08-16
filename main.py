import os
import json
import sqlite3
import threading
import base64
from datetime import datetime

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# ---------------------------------------------------------
# 0. FONT & PERMISSIONS
# ---------------------------------------------------------
FONT_PATH = "NotoSansGeorgian-Regular.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        except Exception as e:
            print(f"Permissions Error: {e}")

try:
    from modules.config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = ""

try:
    from plyer import tts, filechooser
except Exception:
    tts, filechooser = None, None

# ---------------------------------------------------------
# 1. DATABASE MANAGER
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                db_dir = app_storage_path()
            else:
                db_dir = "."
            self.db_path = os.path.join(db_dir, db_name)
            self.create_tables()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_text TEXT,
                        translated_text TEXT,
                        timestamp DATETIME
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Create Tables Error: {e}")

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            conn.cursor().execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))
            conn.commit()

    def get_setting(self, key, default=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def add_history(self, src, trans):
        try:
            with self.get_connection() as conn:
                conn.cursor().execute("INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                                      (src, trans, datetime.now()))
                conn.commit()
        except Exception as e:
            print(f"DB Add Error: {e}")

    def get_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 15")
                return cursor.fetchall()
        except Exception:
            return []

# ---------------------------------------------------------
# 2. SERVICE MANAGER (AI, OCR & Translation)
# ---------------------------------------------------------
class ServiceManager:
    def __init__(self, db):
        self.db = db
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def get_api_key(self):
        return self.db.get_setting("api_key") or getattr(Config, 'GEMINI_API_KEY', '')

    def translate_text(self, text):
        api_key = self.get_api_key()
        if not api_key:
            return None, "API Key არ არის მითითებული! გადადით Settings-ში."

        prompt = (
            f"Translate the following text accurately between Georgian and English.\n"
            f"Return ONLY a JSON object with key 'translation'.\n"
            f"Text: {text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        try:
            res = requests.post(f"{self.api_url}?key={api_key}", json=payload, timeout=10)
            if res.status_code == 200:
                raw = res.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw.strip())
                return data.get("translation", ""), None
            return None, f"სერვერის შეცდომა: {res.status_code}"
        except Exception as e:
            return None, f"კავშირის შეცდომა: {str(e)}"

    def translate_image(self, image_path):
        api_key = self.get_api_key()
        if not api_key:
            return None, "API Key არ არის მითითებული!"

        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = "Extract text from this image and translate it to Georgian/English. Return ONLY JSON with key 'translation'."
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}
                    ]
                }],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            res = requests.post(f"{self.api_url}?key={api_key}", json=payload, timeout=15)
            if res.status_code == 200:
                raw = res.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw.strip())
                return data.get("translation", ""), None
            return None, f"OCR შეცდომა: {res.status_code}"
        except Exception as e:
            return None, f"ფაილის წაკითხვის შეცდომა: {str(e)}"

# ---------------------------------------------------------
# 3. MAIN UI LAYOUT
# ---------------------------------------------------------
class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8

        self.db = DatabaseManager()
        self.service = ServiceManager(self.db)

        # Header
        header = BoxLayout(size_hint_y=0.1, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='20sp', bold=True)
        btn_settings = Button(text="⚙", size_hint_x=0.2)
        btn_settings.bind(on_press=self.open_settings)
        btn_history = Button(text="📜", size_hint_x=0.2)
        btn_history.bind(on_press=self.open_history)
        header.add_widget(title)
        header.add_widget(btn_history)
        header.add_widget(btn_settings)
        self.add_widget(header)

        # Input
        self.input_text = TextInput(hint_text="შეიყვანეთ ტექსტი...", multiline=True, size_hint_y=0.3)
        self.add_widget(self.input_text)

        # Action Bar
        btn_box = BoxLayout(size_hint_y=0.12, spacing=5)
        self.btn_translate = Button(text="თარგმნა", background_color=(0.1, 0.5, 0.9, 1), bold=True)
        self.btn_translate.bind(on_press=self.on_translate)
        btn_ocr = Button(text="📷 ფოტო", background_color=(0.2, 0.7, 0.3, 1))
        btn_ocr.bind(on_press=self.on_ocr)
        btn_box.add_widget(self.btn_translate)
        btn_box.add_widget(btn_ocr)
        self.add_widget(btn_box)

        # Output
        self.output_label = Label(text="თარგმანი გამოჩნდება აქ...", size_hint_y=0.38, font_size='16sp')
        self.add_widget(self.output_label)

        # Tools
        tools = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_copy = Button(text="📋 კოპირება")
        btn_copy.bind(on_press=self.copy_to_clipboard)
        btn_speak = Button(text="🔊 წაკითხვა")
        btn_speak.bind(on_press=self.speak_text)
        tools.add_widget(btn_copy)
        tools.add_widget(btn_speak)
        self.add_widget(tools)

    def on_translate(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.output_label.text = "გთხოვთ შეიყვანოთ ტექსტი!"
            return

        self.output_label.text = "მიმდინარეობს თარგმნა..."

        def run():
            trans, err = self.service.translate_text(text)
            if trans:
                Clock.schedule_once(lambda dt: self.update_res(text, trans))
            else:
                Clock.schedule_once(lambda dt: self.show_err(err))

        threading.Thread(target=run, daemon=True).start()

    def on_ocr(self, instance):
        if filechooser:
            filechooser.open_file(on_selection=self.process_image_selection)

    def process_image_selection(self, selection):
        if selection:
            img_path = selection[0]
            self.output_label.text = "ფოტოს დამუშავება..."

            def run():
                trans, err = self.service.translate_image(img_path)
                if trans:
                    Clock.schedule_once(lambda dt: self.update_res("[Image Text]", trans))
                else:
                    Clock.schedule_once(lambda dt: self.show_err(err))

            threading.Thread(target=run, daemon=True).start()

    def update_res(self, src, trans):
        self.output_label.text = trans
        self.db.add_history(src, trans)

    def show_err(self, err):
        self.output_label.text = f"[შეცდომა]:\n{err}"

    def copy_to_clipboard(self, instance):
        if self.output_label.text and "[შეცდომა]" not in self.output_label.text:
            Clipboard.copy(self.output_label.text)

    def speak_text(self, instance):
        if tts and self.output_label.text:
            try:
                tts.speak(self.output_label.text)
            except Exception as e:
                print(f"TTS Error: {e}")

    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        key_input = TextInput(text=self.db.get_setting("api_key"), hint_text="ჩასვით Gemini API Key...", multiline=False)
        btn_save = Button(text="შენახვა", size_hint_y=0.4)

        content.add_widget(Label(text="Gemini API Key-ს მართვა:"))
        content.add_widget(key_input)
        content.add_widget(btn_save)

        popup = Popup(title="პარამეტრები", content=content, size_hint=(0.85, 0.4))

        def save_key(inst):
            self.db.set_setting("api_key", key_input.text.strip())
            popup.dismiss()

        btn_save.bind(on_press=save_key)
        popup.open()

    def open_history(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        hist_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        hist_box.bind(minimum_height=hist_box.setter('height'))

        records = self.db.get_history()
        for src, trans in records:
            lbl = Label(text=f"• {src} -> {trans}", size_hint_y=None, height=40, font_size='14sp')
            hist_box.add_widget(lbl)

        scroll.add_widget(hist_box)
        content.add_widget(scroll)
        popup = Popup(title="ბოლო თარგმანები", content=content, size_hint=(0.9, 0.7))
        popup.open()

class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        return LingoLensUI()

if __name__ == "__main__":
    LingoLensApp().run()

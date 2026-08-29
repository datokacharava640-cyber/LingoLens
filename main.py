import os
import json
import sqlite3
import urllib.parse
import threading
import asyncio

# certifi მხარდაჭერა უსაფრთხო SSL კავშირისთვის
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import platform

# Plyer-ის უსაფრთხო იმპორტი
try:
    from plyer import tts, stt
except Exception:
    tts, stt = None, None

APP_VERSION = "3.6.0"
VERCEL_SERVER_URL = "https://lingo-lens-kqxn.vercel.app/api/index"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

LANGUAGES = {
    "ქართული 🇬🇪": "ka",
    "English (US) 🇺🇸": "en_US",
    "English (UK) 🇬🇧": "en_GB",
    "Русский 🇷🇺": "ru_RU",
    "Türkçe 🇹🇷": "tr_TR",
    "Español 🇪🇸": "es_ES",
    "Français 🇫🇷": "fr_FR",
    "Deutsch 🇩🇪": "de_DE",
    "Italiano 🇮🇹": "it_IT",
    "العربية 🇦🇪": "ar",
    "中文 🇨🇳": "zh_CN"
}

# --- 1. ლოკალური SQLite მონაცემთა ბაზა (განახლებული წაშლის ფუნქციით) ---
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_lang TEXT,
                target_lang TEXT,
                original_text TEXT,
                translated_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_history(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip():
            return
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)",
                (src, tgt, original, translated)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Insert Error: {e}")

    def get_history(self, limit=30):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT original_text, translated_text FROM history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []

    def clear_history(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Clear Error: {e}")
            return False

db = DatabaseManager()

# --- 2. Async Network Engine ---
class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _worker():
            import urllib.request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    Clock.schedule_once(lambda dt: callback(True, res_data), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, str(e)), 0)

        threading.Thread(target=_worker, daemon=True).start()

# --- 3. UI/UX KV Layout ---
KV = f'''
<MainScreen>:
    canvas.before:
        Color:
            rgba: 0.05, 0.06, 0.09, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 8

        # Header Bar
        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 6

            Label:
                text: "LingoLens Ultra Pro v{APP_VERSION}"
                bold: True
                font_size: '15sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "📜 ისტორია"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '95dp'
                background_color: 0.2, 0.4, 0.6, 1
                color: 1, 1, 1, 1
                on_release: root.open_history_popup()

            Button:
                text: "🗣️ დიალოგი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '100dp'
                background_color: 0.8, 0.4, 0.1, 1
                color: 1, 1, 1, 1
                on_release: root.open_dialog_mode()

        # Language Selectors
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "ქართული 🇬🇪"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "⇆"
                size_hint_x: None
                width: '42dp'
                background_color: 0.12, 0.15, 0.22, 1
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US) 🇺🇸"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('target')

        # Input Box Layer
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.45
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.09, 0.11, 0.16, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]

            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ ან თქვით ტექსტი..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                font_size: '15sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 6
                Widget:
                Button:
                    text: "✨ გრამატიკა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.9, 0.5, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.translate_with_grammar()
                Button:
                    text: "🎙️ ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '65dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_to_text()

        # Output Box Layer
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.45
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.09, 0.11, 0.16, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]

            TextInput:
                id: output_text
                hint_text: "თარგმანი გამოჩნდება აქ..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                hint_text_color: 0, 0.5, 0.4, 1
                font_size: '15sp'

            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 10

                Button:
                    text: "📋 კოპირება"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.copy_output_text()

                Button:
                    text: "🔊 მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.speak_output_text()
                Widget:
'''

Builder.load_string(KV)

# --- 4. Main Application Logic ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en_US"

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.35)

    def _delayed_translate(self, text):
        payload = {
            "text": text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "mode": "standard"
        }

        def _on_result(success, response):
            if success and isinstance(response, dict):
                translated = response.get('translated_text', '')
                self.ids.output_text.text = translated
                db.add_history(self.source_lang, self.target_lang, text, translated)
            else:
                self.ids.output_text.text = "[კავშირი ვერ დამყარდა - ლოკალური რეჟიმი]"

        AsyncTranslateEngine.async_post_request(VERCEL_SERVER_URL, payload, _on_result)

    def translate_with_grammar(self):
        text = self.ids.input_text.text.strip()
        if not text:
            return
        self.ids.output_text.text = "[AI გრამატიკული ანალიზი მიმდინარეობს...]"
        payload = {
            "text": text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "mode": "grammar"
        }

        def _on_result(success, response):
            if success and isinstance(response, dict):
                translated = response.get('translated_text', '')
                grammar = response.get('grammar_analysis', '')
                res_display = f"✨ თარგმანი:\n{translated}\n\n📊 AI გრამატიკა:\n{grammar}"
                self.ids.output_text.text = res_display
                db.add_history(self.source_lang, self.target_lang, text, translated)
            else:
                self.ids.output_text.text = "[შეცდომა AI გრამატიკის დამუშავებისას]"

        AsyncTranslateEngine.async_post_request(VERCEL_SERVER_URL, payload, _on_result)

    def start_speech_to_text(self):
        if stt:
            try:
                stt.start()
            except Exception as e:
                print(f"STT Error: {e}")
        else:
            self.ids.input_text.text = "ხმოვანი შეყვანა არ არის მხარდაჭერილი ამ მოწყობილობაზე."

    def speak_output_text(self):
        text = self.ids.output_text.text.strip()
        if not text:
            return

        if "ka" in self.target_lang:
            threading.Thread(target=self._play_georgian_audio, args=(text,), daemon=True).start()
        elif tts:
            try:
                tts.speak(text)
            except Exception as e:
                print(f"TTS Error: {e}")

    def _play_georgian_audio(self, text):
        try:
            os.makedirs("audio_cache", exist_ok=True)
            filename = f"audio_cache/{abs(hash(text))}.mp3"
            if not os.path.exists(filename):
                encoded = urllib.parse.quote(text)
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded}"
                import urllib.request
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp, open(filename, 'wb') as out_file:
                    out_file.write(resp.read())

            sound = SoundLoader.load(filename)
            if sound:
                sound.play()
        except Exception as e:
            print(f"Audio Playback Error: {e}")

    # --- 1. გაუმჯობესებული ისტორიის ფანჯარა (წაშლის ფუნქციით) ---
    def open_history_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()
        
        history_data = db.get_history(limit=25)
        formatted_history = "\n\n".join([f"🔹 {row[0]}\n   ➡️ {row[1]}" for row in history_data]) if history_data else "ისტორია ცარიელია."
        
        hist_label = Label(text=formatted_history, font_name=FONT_PATH, size_hint_y=None, font_size='14sp', color=(0.9, 0.9, 0.9, 1))
        hist_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(hist_label)
        content.add_widget(scroll)

        btn_bar = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        
        clear_btn = Button(text="🗑️ გასუფთავება", font_name=FONT_PATH, background_color=(0.9, 0.2, 0.2, 1))
        close_btn = Button(text="დახურვა", font_name=FONT_PATH, background_color=(0.3, 0.3, 0.3, 1))
        
        btn_bar.add_widget(clear_btn)
        btn_bar.add_widget(close_btn)
        content.add_widget(btn_bar)

        popup = Popup(title="ნათარგმნი ისტორია (SQLite)", content=content, size_hint=(0.9, 0.8))
        
        def _clear_action(instance):
            if db.clear_history():
                hist_label.text = "ისტორია ცარიელია."
                
        clear_btn.bind(on_release=_clear_action)
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def open_language_menu(self, mode):
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        list_box.bind(minimum_height=list_box.setter('height'))
        popup = Popup(title='აირჩიეთ ენა', content=scroll, size_hint=(0.85, 0.75))

        for lang_name, code in LANGUAGES.items():
            btn = Button(text=lang_name, font_name=FONT_PATH, size_hint_y=None, height='42dp', background_color=(0.14, 0.17, 0.24, 1))
            btn.bind(on_release=lambda x, name=lang_name, c=code: self.select_language(mode, name, c, popup))
            list_box.add_widget(btn)

        scroll.add_widget(list_box)
        popup.open()

    def select_language(self, mode, name, code, popup):
        if mode == 'source':
            self.source_lang = code
            self.ids.btn_source_lang.text = name
        else:
            self.target_lang = code
            self.ids.btn_target_lang.text = name
        popup.dismiss()

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src

    def copy_output_text(self):
        txt = self.ids.output_text.text.strip()
        if txt:
            Clipboard.copy(txt)

    # --- 2. ინტეგრირებული ცოცხალი დიალოგის (Live Dialogue) რეჟიმი ---
    def open_dialog_mode(self):
        dialog_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        status_lbl = Label(text="ორმხრივი ხმოვანი დიალოგი აქტიურია.\nდააჭირეთ ღილაკს სალაპარაკოდ:", font_name=FONT_PATH, halign='center')
        dialog_layout.add_widget(status_lbl)

        btn_mic1 = Button(text=f"🎤 ლაპარაკი ({self.source_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp', background_color=(0.2, 0.6, 0.9, 1))
        btn_mic2 = Button(text=f"🎤 ლაპარაკი ({self.target_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp', background_color=(0.9, 0.5, 0.2, 1))
        close_btn = Button(text="გამოსვლა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.4, 0.4, 0.4, 1))

        dialog_layout.add_widget(btn_mic1)
        dialog_layout.add_widget(btn_mic2)
        dialog_layout.add_widget(close_btn)

        popup = Popup(title="Live Dialogue Mode", content=dialog_layout, size_hint=(0.85, 0.6))

        def _mic_action(lang):
            status_lbl.text = f"🎙️ მოსმენა ({lang.upper()})..."
            self.start_speech_to_text()

        btn_mic1.bind(on_release=lambda x: _mic_action(self.source_lang))
        btn_mic2.bind(on_release=lambda x: _mic_action(self.target_lang))
        close_btn.bind(on_release=popup.dismiss)
        
        popup.open()

class LingoLensApp(App):
    def build(self):
        self.request_android_permissions()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

    def request_android_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

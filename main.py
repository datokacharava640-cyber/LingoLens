# ==============================================================================
# LingoLens Ultra Pro v4.0 - Auto Offline/Online Mode
# ==============================================================================

import os
import json
import urllib.parse
import urllib.request
import threading
import sqlite3
import socket
from datetime import datetime

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

APP_VERSION = "4.0.0"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

LANGUAGES = {
    "Georgian (ქართული)": "ka",
    "English (US)": "en",
    "Italian (Italiano)": "it",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Russian (Русский)": "ru",
    "Turkish (Türkçe)": "tr",
    "Ukrainian (Українська)": "uk",
    "Polish (Polski)": "pl",
    "Portuguese (Português)": "pt",
    "Dutch (Nederlands)": "nl",
    "Greek (Ελληνικά)": "el",
    "Arabic (العربية)": "ar",
    "Chinese Simplified (中文)": "zh-CN",
    "Japanese (日本語)": "ja",
    "Korean (한국어)": "ko",
    "Hindi (हिन्दी)": "hi"
}

# Offline რეჟიმისთვის ჩაშენებული ლოკალური ლექსიკონი
OFFLINE_DICTIONARY = {
    ("ka", "en"): {
        "გამარჯობა": "Hello",
        "როგორ ხარ": "How are you",
        "მადლობა": "Thank you",
        "ნახვამდის": "Goodbye",
        "კი": "Yes",
        "არა": "No"
    },
    ("en", "ka"): {
        "hello": "გამარჯობა",
        "how are you": "როგორ ხარ",
        "thank you": "მადლობა",
        "goodbye": "ნახვამდის",
        "yes": "კი",
        "no": "არა"
    }
}

class AgentMemoryDB:
    def __init__(self, db_path="lingolens_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT,
                translated_text TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def add_history(self, src, tgt):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO translation_history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                       (src, tgt, datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.conn.commit()

    def get_history(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT source_text, translated_text, timestamp FROM translation_history ORDER BY id DESC LIMIT 50")
        return cursor.fetchall()

KV = '''
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

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 6

            Button:
                text: "მენიუ"
                font_name: 'font.ttf'
                size_hint_x: None
                width: '85dp'
                background_color: 0.15, 0.2, 0.3, 1
                color: 1, 1, 1, 1
                on_release: root.open_main_menu()

            Label:
                id: status_label
                text: "LingoLens v4.0"
                bold: True
                font_size: '13sp'
                font_name: 'font.ttf'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "Live"
                font_name: 'font.ttf'
                size_hint_x: None
                width: '65dp'
                background_color: 0.8, 0.4, 0.1, 1
                color: 1, 1, 1, 1

            Button:
                text: "AR"
                font_name: 'font.ttf'
                size_hint_x: None
                width: '55dp'
                background_color: 0.6, 0.1, 0.8, 1
                color: 1, 1, 1, 1

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "Georgian"
                font_name: 'font.ttf'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "<->"
                size_hint_x: None
                width: '42dp'
                background_color: 0.12, 0.15, 0.22, 1
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US)"
                font_name: 'font.ttf'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('target')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.35
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
                hint_text: "ჩაწერეთ ტექსტი..."
                font_name: 'font.ttf'
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
                    text: "Agent"
                    font_name: 'font.ttf'
                    size_hint_x: None
                    width: '75dp'
                    background_color: 0.2, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    on_release: root.on_live_translate(input_text.text)
                Button:
                    text: "STT"
                    size_hint_x: None
                    width: '55dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                Button:
                    text: "TTS"
                    size_hint_x: None
                    width: '55dp'
                    background_color: 0.12, 0.15, 0.22, 1
                    color: 0.2, 0.7, 1, 1

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.55
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
                hint_text: "თარგმანი..."
                font_name: 'font.ttf'
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
                    text: "კოპირება"
                    font_name: 'font.ttf'
                    size_hint_x: None
                    width: '100dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.copy_output_text()

                Button:
                    text: "მოსმენა"
                    font_name: 'font.ttf'
                    size_hint_x: None
                    width: '100dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en"
        self.db = AgentMemoryDB()

    def copy_output_text(self):
        text = self.ids.output_text.text.strip()
        if text: Clipboard.copy(text)

    def open_language_menu(self, mode='source'):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        layout.bind(minimum_height=layout.setter('height'))

        popup = Popup(title="ენის არჩევა", title_font=FONT_PATH, content=box, size_hint=(0.85, 0.8))

        for name, code in LANGUAGES.items():
            btn = Button(text=name, font_name=FONT_PATH, size_hint_y=None, height='45dp', background_color=(0.15, 0.2, 0.3, 1))
            def _select(instance, c=code, n=name):
                if mode == 'source':
                    self.source_lang = c
                    self.ids.btn_source_lang.text = n.split(' ')[0]
                else:
                    self.target_lang = c
                    self.ids.btn_target_lang.text = n.split(' ')[0]
                popup.dismiss()
                if self.ids.input_text.text.strip():
                    self.on_live_translate(self.ids.input_text.text)
            btn.bind(on_release=_select)
            layout.add_widget(btn)

        scroll.add_widget(layout)
        box.add_widget(scroll)
        popup.open()

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        for name, code in LANGUAGES.items():
            if code == self.source_lang:
                self.ids.btn_source_lang.text = name.split(' ')[0]
            if code == self.target_lang:
                self.ids.btn_target_lang.text = name.split(' ')[0]
        if self.ids.input_text.text.strip():
            self.on_live_translate(self.ids.input_text.text)

    def open_main_menu(self):
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        btn_history = Button(text="ისტორია", font_name=FONT_PATH, size_hint_y=None, height='45dp')
        btn_close = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp')
        box.add_widget(btn_history)
        box.add_widget(btn_close)
        
        popup = Popup(title="მენიუ", title_font=FONT_PATH, content=box, size_hint=(0.8, 0.35))
        btn_history.bind(on_release=lambda x: (popup.dismiss(), self.open_history_view()))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def open_history_view(self):
        box = BoxLayout(orientation='vertical', padding=10)
        scroll = ScrollView()
        history_data = self.db.get_history()
        history_text = "\n\n".join([f"{item[0]} ➔ {item[1]}" for item in history_data]) or "ისტორია ცარიელია"
        lbl = Label(text=history_text, font_name=FONT_PATH, size_hint_y=None, font_size='14sp', color=(1, 1, 1, 1))
        lbl.bind(texture_size=lambda instance, val: setattr(instance, 'height', val[1]))
        scroll.add_widget(lbl)
        box.add_widget(scroll)
        
        popup = Popup(title="ისტორია", title_font=FONT_PATH, content=box, size_hint=(0.9, 0.8))
        popup.open()

    def has_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    def on_live_translate(self, text):
        cleaned = text.strip()
        Clock.unschedule(self._delayed_translate)
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.3)

    def _delayed_translate(self, text):
        threading.Thread(target=self._process_translation, args=(text,), daemon=True).start()

    def _process_translation(self, text):
        if self.has_internet():
            # ონლაინ თარგმანი
            Clock.schedule_once(lambda dt: setattr(self.ids.status_label, 'text', 'LingoLens (Online)'), 0)
            try:
                encoded_text = urllib.parse.quote(text)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.source_lang}&tl={self.target_lang}&dt=t&q={encoded_text}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    translated_parts = [item[0] for item in result[0] if item[0]]
                    full_translated = "".join(translated_parts)
                    Clock.schedule_once(lambda dt: self._update_ui_output(full_translated, text), 0)
                    return
            except Exception:
                pass

        # ოფლაინ თარგმანი (ინტერნეტის გარეშე)
        Clock.schedule_once(lambda dt: setattr(self.ids.status_label, 'text', 'LingoLens (Offline)'), 0)
        dict_key = (self.source_lang, self.target_lang)
        local_db = OFFLINE_DICTIONARY.get(dict_key, {})
        offline_res = local_db.get(text.lower(), f"[Offline] {text}")
        
        Clock.schedule_once(lambda dt: self._update_ui_output(offline_res, text), 0)

    def _update_ui_output(self, translated_text, original_text):
        self.ids.output_text.text = translated_text
        self.db.add_history(original_text, translated_text)

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

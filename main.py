# ==============================================================================
# LingoLens Ultra Pro v4.0 - Global Fix
# ==============================================================================

import os
import json
import base64
import urllib.parse
import urllib.request
import threading
import time
import sqlite3
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
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.camera import Camera
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

APP_VERSION = "4.0.0"
VERCEL_SERVER_URL = "https://lingo-lens-kqxn.vercel.app/api/index"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"
API_AUTH_TOKEN = "Bearer LINGOLENS_SECRET_KEY_2026"

# 50+ მსოფლიო ენების სრული სია
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
    "Hindi (हिन्दी)": "hi",
    "Hebrew (עברית)": "he",
    "Swedish (Svenska)": "sv",
    "Norwegian (Norsk)": "no",
    "Danish (Dansk)": "da",
    "Finnish (Suomi)": "fi",
    "Czech (Čeština)": "cs",
    "Hungarian (Magyar)": "hu",
    "Romanian (Română)": "ro",
    "Bulgarian (Български)": "bg",
    "Croatian (Hrvatski)": "hr",
    "Serbian (Српски)": "sr",
    "Slovak (Slovenčina)": "sk",
    "Lithuanian (Lietuvių)": "lt",
    "Latvian (Latviešu)": "lv",
    "Estonian (Eesti)": "et",
    "Azerbaijani (Azərbaycan)": "az",
    "Armenian (Հայերեն)": "hy",
    "Persian (فارسی)": "fa",
    "Thai (ไทย)": "th",
    "Vietnamese (Tiếng Việt)": "vi",
    "Indonesian (Bahasa)": "id",
    "Malay (Bahasa Melayu)": "ms",
    "Filipino": "tl",
    "Bengali (বাংলা)": "bn",
    "Urdu (اردو)": "ur",
    "Kazakh (Қазақ)": "kk",
    "Uzbek (Oʻzbek)": "uz"
}

ADVANCED_OFFLINE_DB = {
    ("ka", "en"): {"გამარჯობა": "Hello", "მადლობა": "Thank you", "როგორ ხარ": "How are you"},
    ("ka", "it"): {"გამარჯობა": "Ciao", "მადლობა": "Grazie", "როგორ ხარ": "Come stai"}
}

class AgentMemoryDB:
    def __init__(self, db_path="lingolens_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                words_learned INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 1,
                last_active TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT,
                translated_text TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM stats")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO stats (words_learned, streak_days, last_active) VALUES (0, 1, ?)", 
                           (datetime.now().isoformat(),))
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
                text: "LingoLens v4.0 AI Agent"
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
                text: "Italian"
                font_name: 'font.ttf'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('target')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.3
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
                    width: '80dp'
                    background_color: 0.2, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    on_release: root.ask_ai_agent()
                Button:
                    text: "STT"
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_to_text(root.source_lang)
                Button:
                    text: "TTS"
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.12, 0.15, 0.22, 1
                    color: 0.2, 0.7, 1, 1
                    on_release: root.speak_text(input_text.text, root.source_lang)

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.6
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
                    on_release: root.speak_text(output_text.text, root.target_lang)
                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "it"
        self.db = AgentMemoryDB()

    def copy_output_text(self):
        text = self.ids.output_text.text.strip()
        if text: Clipboard.copy(text)

    def open_language_menu(self, mode='source'):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        layout.bind(minimum_height=layout.setter('height'))

        popup = Popup(
            title="ენის არჩევა", 
            title_font=FONT_PATH, 
            content=box, 
            size_hint=(0.85, 0.8)
        )

        for name, code in LANGUAGES.items():
            btn = Button(
                text=name, 
                font_name=FONT_PATH, 
                size_hint_y=None, 
                height='45dp', 
                background_color=(0.15, 0.2, 0.3, 1)
            )
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
        
        popup = Popup(
            title="მენიუ", 
            title_font=FONT_PATH, 
            content=box, 
            size_hint=(0.8, 0.35)
        )
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
        
        popup = Popup(
            title="ისტორია", 
            title_font=FONT_PATH, 
            content=box, 
            size_hint=(0.9, 0.8)
        )
        popup.open()

    def ask_ai_agent(self):
        text = self.ids.input_text.text.strip()
        if not text: return
        self.ids.output_text.text = "[LingoLens AI Agent...]"
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "agent"})
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}

        def _on_success(req, res):
            response_text = res.get('translated_text', '')
            self.ids.output_text.text = response_text
            self.db.add_history(text, response_text)

        def _on_error(req, err):
            threading.Thread(target=self._fallback_online_translate, args=(text,), daemon=True).start()

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=5)

    def on_live_translate(self, text):
        cleaned = text.strip()
        Clock.unschedule(self._delayed_translate)
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.4)

    def _delayed_translate(self, text):
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "standard"})
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
        
        def _on_success(req, res):
            translated = res.get('translated_text', '')
            self.ids.output_text.text = translated
            self.db.add_history(text, translated)

        def _on_error(req, err):
            threading.Thread(target=self._fallback_online_translate, args=(text,), daemon=True).start()

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=4)

    def _fallback_online_translate(self, text):
        try:
            lang_pair = f"{self.source_lang}|{self.target_lang}"
            encoded_text = urllib.parse.quote(text)
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={lang_pair}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                translated = data.get('responseData', {}).get('translatedText', '')
                if translated and "MYMEMORY WARNING" not in translated:
                    Clock.schedule_once(lambda dt: self._update_ui_output(translated, text), 0)
                    return
        except Exception:
            pass
        
        offline_res = self.smart_offline_translate(text)
        Clock.schedule_once(lambda dt: self._update_ui_output(f"[Offline] {offline_res}", text), 0)

    def _update_ui_output(self, translated_text, original_text):
        self.ids.output_text.text = translated_text
        self.db.add_history(original_text, translated_text)

    def smart_offline_translate(self, text):
        cleaned = text.lower().strip()
        db = ADVANCED_OFFLINE_DB.get((self.source_lang, self.target_lang), {})
        return db.get(cleaned, cleaned)

    def start_speech_to_text(self, lang_code):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                PythonActivity.mActivity.startActivityForResult(intent, 1001)
            except Exception:
                pass

    def speak_text(self, text, lang_code):
        cleaned = text.strip()
        if not cleaned: return
        
        if lang_code == 'ka':
            threading.Thread(target=self._play_online_tts, args=(cleaned, 'ka'), daemon=True).start()
        elif platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                
                class TTSListener(autoclass('android.speech.tts.TextToSpeech$OnInitListener')):
                    def onInit(self, status): pass
                
                tts = TextToSpeech(PythonActivity.mActivity, TTSListener())
                tts.setLanguage(Locale(lang_code))
                tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception:
                pass

    def _play_online_tts(self, text, lang):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                with open("tts_temp.mp3", "wb") as f:
                    f.write(data)
                Clock.schedule_once(lambda dt: self._play_sound_file("tts_temp.mp3"), 0)
        except Exception:
            pass

    def _play_sound_file(self, path):
        sound = SoundLoader.load(path)
        if sound: sound.play()

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

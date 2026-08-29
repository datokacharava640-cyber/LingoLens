import os
import json
import base64
import urllib.parse
import threading
import sqlite3

# SSL სერტიფიკატის ფიქსი
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
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

# Plyer-ის უსაფრთხო იმპორტი
try:
    from plyer import tts, stt
except Exception:
    tts, stt = None, None

APP_VERSION = "3.4.0"
VERCEL_SERVER_URL = "https://lingo-lens-kqxn.vercel.app/api/index"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

LANGUAGES = {
    "ქართული 🇬🇪": "ka", "English (US) 🇺🇸": "en_US", "English (UK) 🇬🇧": "en_GB", 
    "Русский 🇷🇺": "ru_RU", "Türkçe 🇹🇷": "tr_TR", "Español 🇪🇸": "es_ES", "Français 🇫🇷": "fr_FR", 
    "Deutsch 🇩🇪": "de_DE", "Italiano 🇮🇹": "it_IT", "العربية 🇦🇪": "ar", "中文 🇨🇳": "zh_CN"
}

# ლოკალური SQLite ბაზის ინიციალიზაცია
def init_db():
    conn = sqlite3.connect("lingolens.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, src TEXT, tgt TEXT, original TEXT, translated TEXT)''')
    conn.commit()
    conn.close()

init_db()

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

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 6

            Label:
                text: "LingoLens v{APP_VERSION} 🇬🇪"
                bold: True
                font_size: '15sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "📜 ისტორია"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '90dp'
                background_color: 0.2, 0.4, 0.6, 1
                color: 1, 1, 1, 1
                on_release: root.open_history()

            Button:
                text: "🗣️ დიალოგი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '100dp'
                background_color: 0.8, 0.4, 0.1, 1
                color: 1, 1, 1, 1
                on_release: root.open_conversation_mode()

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
                hint_text: "ჩაწერეთ ტექსტი..."
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
                    text: "📖 გრამატიკა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '100dp'
                    background_color: 0.9, 0.5, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.translate_with_grammar()
                Button:
                    text: "🎙️ ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_stt()

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
                    on_release: root.speak_text(output_text.text, root.target_lang)
                Widget:
'''

Builder.load_string(KV)

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
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "standard"})
        headers = {'Content-Type': 'application/json'}
        
        def _on_success(req, res):
            translated = res.get('translated_text', '')
            self.ids.output_text.text = translated
            self.save_to_history(text, translated)

        def _on_error(req, err):
            self.ids.output_text.text = "[ონლაინ სერვერი მიუწვდომელია]"

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, 
                   on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=4)

    def save_to_history(self, original, translated):
        if not original or not translated: return
        try:
            conn = sqlite3.connect("lingolens.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (src, tgt, original, translated) VALUES (?, ?, ?, ?)",
                           (self.source_lang, self.target_lang, original, translated))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def open_history(self):
        try:
            conn = sqlite3.connect("lingolens.db")
            cursor = conn.cursor()
            cursor.execute("SELECT original, translated FROM history ORDER BY id DESC LIMIT 20")
            rows = cursor.fetchall()
            conn.close()

            content = BoxLayout(orientation='vertical', padding=10, spacing=8)
            scroll = ScrollView()
            hist_label = Label(text="\n".join([f"🔹 {r[0]}\n   ➡️ {r[1]}" for r in rows]), 
                               font_name=FONT_PATH, size_hint_y=None, font_size='14sp')
            hist_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
            scroll.add_widget(hist_label)
            content.add_widget(scroll)

            close_btn = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp')
            content.add_widget(close_btn)

            popup = Popup(title="ნათარგმნი ისტორია", content=content, size_hint=(0.9, 0.8))
            close_btn.bind(on_release=popup.dismiss)
            popup.open()
        except Exception as e:
            print(f"History Open Error: {e}")

    def start_stt(self):
        if stt:
            try:
                stt.start()
            except Exception as e:
                print(f"STT Error: {e}")
        else:
            self.ids.input_text.text = "STT არ არის მხარდაჭერილი ამ მოწყობილობაზე."

    def speak_text(self, text, lang_code):
        if not text.strip(): return
        if "ka" in lang_code:
            threading.Thread(target=self._play_georgian_tts, args=(text,), daemon=True).start()
        elif tts:
            try:
                tts.speak(text)
            except Exception as e:
                print(f"TTS Error: {e}")

    def _play_georgian_tts(self, text):
        try:
            os.makedirs("audio_cache", exist_ok=True)
            filename = f"audio_cache/{abs(hash(text))}.mp3"
            if not os.path.exists(filename):
                encoded = urllib.parse.quote(text)
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded}"
                import urllib.request
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                    out_file.write(response.read())

            sound = SoundLoader.load(filename)
            if sound: sound.play()
        except Exception as e: print(f"Audio Error: {e}")

    def translate_with_grammar(self):
        text = self.ids.input_text.text.strip()
        if not text: return
        self.ids.output_text.text = "[AI გრამატიკული დამუშავება...]"
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "grammar"})
        headers = {'Content-Type': 'application/json'}
        UrlRequest(
            VERCEL_SERVER_URL, req_body=payload, req_headers=headers,
            on_success=lambda req, res: setattr(self.ids.output_text, 'text', f"✨ თარგმანი:\n{res.get('translated_text', '')}\n\n📊 გრამატიკა:\n{res.get('grammar_analysis', '')}"),
            on_error=lambda req, err: setattr(self.ids.output_text, 'text', "[შეცდომა გრამატიკის დამუშავებისას]"),
            timeout=6
        )

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
        if self.ids.output_text.text.strip():
            Clipboard.copy(self.ids.output_text.text.strip())

    def open_conversation_mode(self):
        pass

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

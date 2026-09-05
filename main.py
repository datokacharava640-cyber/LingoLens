import os
import json
import sqlite3
import threading
import requests

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
from kivy.graphics import Color, Ellipse
from kivy.utils import platform

APP_VERSION = "3.6.0"
VERCEL_BASE_URL = "https://lingo-lens-eight.vercel.app"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

LANGUAGES = {
    "Georgian": "ka",
    "English (US)": "en",
    "English (UK)": "en",
    "Ukrainian": "uk",
    "Turkish": "tr",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Russian": "ru",
    "Armenian": "hy",
    "Azerbaijani": "az",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Polish": "pl",
    "Dutch": "nl",
    "Greek": "el",
    "Hindi": "hi",
    "Swedish": "sv",
    "Norwegian": "no",
    "Finnish": "fi",
    "Czech": "cs",
    "Romanian": "ro",
    "Hungarian": "hu"
}

class NetworkIndicator(Widget):
    def set_status(self, status):
        self.canvas.before.clear()
        with self.canvas.before:
            if status == "green":
                Color(0.1, 0.8, 0.2, 1)
            elif status == "yellow":
                Color(0.9, 0.7, 0.1, 1)
            else:
                Color(0.9, 0.2, 0.2, 1)
            
            size = min(self.width, self.height) * 0.5
            px = self.x + (self.width - size) / 2
            py = self.y + (self.height - size) / 2
            Ellipse(pos=(px, py), size=(size, size))

class DatabaseManager:
    def __init__(self):
        self.db_path = None

    def _get_db_path(self):
        if not self.db_path:
            if platform == 'android':
                app = App.get_running_app()
                base_dir = app.user_data_dir if app else "."
            else:
                base_dir = "."
            self.db_path = os.path.join(base_dir, "lingolens.db")
            self.init_db()
        return self.db_path

    def init_db(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
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
        except Exception as e:
            print(f"DB Init Error: {e}")

    def add_history(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip():
            return
        try:
            conn = sqlite3.connect(self._get_db_path())
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
            conn = sqlite3.connect(self._get_db_path())
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
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Clear Error: {e}")
            return False

db = DatabaseManager()

class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _worker():
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36'
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    res_data = response.json()
                    Clock.schedule_once(lambda dt: callback(True, res_data), 0)
                else:
                    Clock.schedule_once(lambda dt: callback(False, f"HTTP {response.status_code}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, str(e)), 0)

        threading.Thread(target=_worker, daemon=True).start()

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

            NetworkIndicator:
                id: net_indicator
                size_hint_x: None
                width: '24dp'

            Label:
                text: "LingoLens Ultra Pro v{APP_VERSION}"
                bold: True
                font_size: '13sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "დიალოგი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '75dp'
                background_color: 0.8, 0.4, 0.1, 1
                color: 1, 1, 1, 1
                on_release: root.open_dialog_mode()

            Button:
                text: "AI"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '45dp'
                background_color: 0.5, 0.2, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.activate_voice_assistant()

            Button:
                text: "ისტორია"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '70dp'
                background_color: 0.2, 0.4, 0.6, 1
                color: 1, 1, 1, 1
                on_release: root.open_history_popup()

        # Language Selectors
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "Georgian"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "<->"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '42dp'
                background_color: 0.12, 0.15, 0.22, 1
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US)"
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
                    text: "გრამატიკა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.9, 0.5, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.translate_with_grammar()
                Button:
                    text: "ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '65dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_to_text(root.source_lang)

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
                    text: "კოპირება"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.copy_output_text()

                Button:
                    text: "მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.speak_output_text()
                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en"
        self.assistant_popup = None

    def on_enter(self):
        Clock.schedule_interval(self.check_network_status, 5)
        self.check_network_status(0)

    def check_network_status(self, dt):
        def _check():
            try:
                res = requests.get(f"{VERCEL_BASE_URL}/api/index", timeout=3)
                if res.status_code == 200:
                    status = "green"
                else:
                    status = "yellow"
            except Exception:
                status = "red"

            Clock.schedule_once(lambda d: self.ids.net_indicator.set_status(status), 0)

        threading.Thread(target=_check, daemon=True).start()

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.35)

    def trigger_retranslate(self):
        text = self.ids.input_text.text.strip()
        if text:
            self._delayed_translate(text)

    def _delayed_translate(self, text, callback_after=None):
        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {
            "text": text,
            "source_lang": self.source_lang[:2],
            "target_lang": self.target_lang[:2],
            "mode": "standard"
        }

        def _on_result(success, response):
            if success and isinstance(response, dict):
                translated = response.get('translated_text', '')
                self.ids.output_text.text = translated
                db.add_history(self.source_lang, self.target_lang, text, translated)
                if callback_after:
                    callback_after(translated)
            else:
                self.ids.output_text.text = f"[კავშირი ვერ დამყარდა: {response}]"

        AsyncTranslateEngine.async_post_request(url, payload, _on_result)

    # --- ორმხრივი ხმოვანი დიალოგის რეჟიმი ---
    def open_dialog_mode(self):
        dialog_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        status_lbl = Label(
            text="ორმხრივი ხმოვანი დიალოგი\nდააჭირეთ შესაბამის ღილაკს საუბრის დასაწყებად:",
            font_name=FONT_PATH,
            halign='center',
            color=(0.2, 0.8, 1, 1)
        )
        dialog_layout.add_widget(status_lbl)

        btn_mic1 = Button(
            text=f"ლაპარაკი ({self.source_lang.upper()})",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='50dp',
            background_color=(0.2, 0.6, 0.9, 1)
        )
        btn_mic2 = Button(
            text=f"ლაპარაკი ({self.target_lang.upper()})",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='50dp',
            background_color=(0.9, 0.5, 0.2, 1)
        )
        close_btn = Button(
            text="გამოსვლა",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='40dp',
            background_color=(0.4, 0.4, 0.4, 1)
        )

        dialog_layout.add_widget(btn_mic1)
        dialog_layout.add_widget(btn_mic2)
        dialog_layout.add_widget(close_btn)

        popup = Popup(
            title="Live Dialogue Mode",
            title_font=FONT_PATH,
            content=dialog_layout,
            size_hint=(0.85, 0.6)
        )

        def _on_dialog_speech_captured(spoken_text):
            status_lbl.text = f"ითარგმნება: \"{spoken_text}\"..."
            self._delayed_translate(spoken_text, callback_after=lambda translated: self._on_dialog_translated(translated, status_lbl))

        def _mic1_action(instance):
            status_lbl.text = f"გისმენთ ({self.source_lang.upper()})..."
            self.start_speech_to_text(self.source_lang, _on_dialog_speech_captured)

        def _mic2_action(instance):
            status_lbl.text = f"გისმენთ ({self.target_lang.upper()})..."
            self.swap_languages()
            self.start_speech_to_text(self.source_lang, _on_dialog_speech_captured)

        btn_mic1.bind(on_release=_mic1_action)
        btn_mic2.bind(on_release=_mic2_action)
        close_btn.bind(on_release=popup.dismiss)

        popup.open()

    def _on_dialog_translated(self, translated_text, status_lbl):
        status_lbl.text = f"ნათარგმნი:\n{translated_text}"
        self.speak_output_text(translated_text)

    # --- AI ასისტენტი ---
    def activate_voice_assistant(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        lbl_status = Label(
            text="LingoLens AI ასისტენტი\n\nდააჭირეთ ღილაკს და თქვით ფრაზა:\nმაგალითად: \"გადამითარგმნე ეს ფრანგულად: გამარჯობა\"",
            font_name=FONT_PATH,
            halign='center',
            font_size='15sp',
            color=(0.2, 0.8, 1, 1)
        )
        layout.add_widget(lbl_status)

        btn_listen = Button(
            text="ლაპარაკი (დააჭირეთ)",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='50dp',
            background_color=(0.5, 0.2, 0.8, 1)
        )
        
        btn_close = Button(
            text="დახურვა",
            font_name=FONT_PATH,
            size_hint_y=None,
            height='40dp',
            background_color=(0.3, 0.3, 0.3, 1)
        )

        layout.add_widget(btn_listen)
        layout.add_widget(btn_close)

        self.assistant_popup = Popup(
            title="LingoLens Voice Assistant",
            title_font=FONT_PATH,
            content=layout,
            size_hint=(0.9, 0.6)
        )

        def _listen_action(instance):
            lbl_status.text = "გისმენთ..."
            self.start_speech_to_text("ka", lambda text: self.process_assistant_command(text, lbl_status))

        btn_listen.bind(on_release=_listen_action)
        btn_close.bind(on_release=self.assistant_popup.dismiss)

        self.assistant_popup.open()

    def process_assistant_command(self, user_command, lbl_status):
        if not user_command:
            lbl_status.text = "ხმა ვერ იქნა ამოცნობილი. სცადეთ ხელახლა."
            return

        lbl_status.text = f"მუშავდება: \"{user_command}\"..."

        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {
            "text": f"You are LingoLens Voice Assistant. User asked: '{user_command}'. Process any translation or query directly and reply in GEORGIAN with result.",
            "source_lang": "ka",
            "target_lang": self.target_lang[:2],
            "mode": "standard"
        }

        def _on_assistant_reply(success, response):
            if success and isinstance(response, dict):
                reply = response.get('translated_text', '')
                lbl_status.text = f"LingoLens AI:\n{reply}"
                self.speak_output_text(reply)
            else:
                lbl_status.text = "შეცდომა ასისტენტის პასუხის მიღებისას."

        AsyncTranslateEngine.async_post_request(url, payload, _on_assistant_reply)

    def translate_with_grammar(self):
        text = self.ids.input_text.text.strip()
        if not text:
            return
        self.ids.output_text.text = "[AI გრამატიკული ანალიზი მიმდინარეობს...]"
        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {
            "text": text,
            "source_lang": self.source_lang[:2],
            "target_lang": self.target_lang[:2],
            "mode": "grammar"
        }

        def _on_result(success, response):
            if success and isinstance(response, dict):
                translated = response.get('translated_text', '')
                grammar = response.get('grammar_analysis', '')
                res_display = f"თარგმანი:\n{translated}\n\n--- AI გრამატიკული ანალიზი ---\n{grammar}"
                self.ids.output_text.text = res_display
                db.add_history(self.source_lang, self.target_lang, text, translated)
            else:
                self.ids.output_text.text = "[შეცდომა AI გრამატიკის დამუშავებისას]"

        AsyncTranslateEngine.async_post_request(url, payload, _on_result)

    def start_speech_to_text(self, lang_code="ka", on_complete_callback=None):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                AndroidPythonActivity = PythonActivity.mActivity
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)

                def on_activity_result(request_code, result_code, data):
                    if request_code == 1001 and data is not None:
                        results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                        if results and results.size() > 0:
                            spoken_text = results.get(0)
                            Clock.schedule_once(lambda dt: self._set_speech_input(spoken_text, on_complete_callback), 0)

                AndroidPythonActivity.bind(on_activity_result=on_activity_result)
                AndroidPythonActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                print(f"STT Exception: {e}")
        else:
            self.ids.input_text.text = "[ხმოვანი შეყვანა ხელმისაწვდომია მხოლოდ Android-ზე]"

    def _set_speech_input(self, text, callback=None):
        self.ids.input_text.text = text
        if callback:
            callback(text)

    def speak_output_text(self, custom_text=None):
        text = custom_text if custom_text else self.ids.output_text.text.strip()
        if not text or text.startswith("["):
            return

        lang_code = self.target_lang.split()[0].lower()
        if lang_code in LANGUAGES:
            lang_code = LANGUAGES[lang_code]
        elif len(lang_code) > 2:
            lang_code = self.target_lang[:2].lower()

        threading.Thread(target=self._download_and_play_tts_stream, args=(text, lang_code), daemon=True).start()

    def _download_and_play_tts_stream(self, text, lang_code):
        try:
            if platform == 'android':
                app = App.get_running_app()
                cache_dir = os.path.join(app.user_data_dir, "audio_cache")
            else:
                cache_dir = "audio_cache"

            os.makedirs(cache_dir, exist_ok=True)
            safe_hash = abs(hash(f"{text}_{lang_code}"))
            filepath = os.path.abspath(os.path.join(cache_dir, f"speech_{safe_hash}.mp3"))

            tts_url = f"{VERCEL_BASE_URL}/api/tts"
            payload = {"text": text, "lang": lang_code}
            
            res = requests.post(tts_url, json=payload, timeout=12)

            if res.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(res.content)

                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    if platform == 'android':
                        from jnius import autoclass
                        MediaPlayer = autoclass('android.media.MediaPlayer')
                        player = MediaPlayer()
                        player.setDataSource(f"file://{filepath}")
                        player.prepare()
                        player.start()
                    else:
                        sound = SoundLoader.load(filepath)
                        if sound:
                            sound.play()
            else:
                print(f"Server TTS Status Code: {res.status_code}")

        except Exception as e:
            print(f"TTS Engine Error: {e}")

    def open_history_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()

        history_data = db.get_history(limit=25)
        formatted_history = "\n\n".join([f"-> {row[0]}\n   => {row[1]}" for row in history_data]) if history_data else "ისტორია ცარიელია."

        hist_label = Label(text=formatted_history, font_name=FONT_PATH, size_hint_y=None, font_size='14sp', color=(0.9, 0.9, 0.9, 1))
        hist_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(hist_label)
        content.add_widget(scroll)

        btn_bar = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        clear_btn = Button(text="გასუფთავება", font_name=FONT_PATH, background_color=(0.9, 0.2, 0.2, 1))
        close_btn = Button(text="დახურვა", font_name=FONT_PATH, background_color=(0.3, 0.3, 0.3, 1))

        btn_bar.add_widget(clear_btn)
        btn_bar.add_widget(close_btn)
        content.add_widget(btn_bar)

        popup = Popup(title="ნათარგმნი ისტორია (SQLite)", title_font=FONT_PATH, content=content, size_hint=(0.9, 0.8))

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
        popup = Popup(title='აირჩიეთ ენა', title_font=FONT_PATH, content=scroll, size_hint=(0.85, 0.75))

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
        self.trigger_retranslate()

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src_text = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src_text

        in_val = self.ids.input_text.text
        out_val = self.ids.output_text.text

        self.ids.input_text.text = out_val
        self.ids.output_text.text = in_val
        self.trigger_retranslate()

    def copy_output_text(self):
        txt = self.ids.output_text.text.strip()
        if txt:
            Clipboard.copy(txt)

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

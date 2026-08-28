# ==============================================================================
# LingoLens Ultra Pro v4.0 - Autonomous AI Agent & Real-Time Engine
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

LANGUAGES = {
    "Georgian": "ka",
    "English (US)": "en_US",
    "English (UK)": "en_GB",
    "Spanish": "es_ES",
    "French": "fr_FR",
    "German": "de_DE",
    "Italian": "it_IT",
    "Russian": "ru_RU",
    "Turkish": "tr_TR",
    "Chinese (Simplified)": "zh_CN",
    "Chinese (Traditional)": "zh_TW",
    "Arabic": "ar",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese (Brazil)": "pt_BR",
    "Portuguese (Portugal)": "pt_PT",
    "Hindi": "hi",
    "Bengali": "bn",
    "Urdu": "ur",
    "Persian": "fa",
    "Ukrainian": "uk",
    "Polish": "pl",
    "Dutch": "nl",
    "Greek": "el",
    "Hebrew": "he",
    "Swedish": "sv",
    "Norwegian": "no",
    "Danish": "da",
    "Finnish": "fi",
    "Czech": "cs",
    "Hungarian": "hu",
    "Romanian": "ro",
    "Bulgarian": "bg",
    "Slovak": "sk",
    "Croatian": "hr",
    "Serbian": "sr",
    "Slovenian": "sl",
    "Lithuanian": "lt",
    "Latvian": "lv",
    "Estonian": "et",
    "Indonesian": "id",
    "Malay": "ms",
    "Vietnamese": "vi",
    "Thai": "th",
    "Filipino": "fil",
    "Swahili": "sw",
    "Azerbaijani": "az",
    "Armenian": "hy",
    "Kazakh": "kk",
    "Uzbek": "uz",
    "Mongolian": "mn",
    "Nepali": "ne",
    "Sinhala": "si",
    "Tamil": "ta",
    "Telugu": "te",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Afrikaans": "af",
    "Albanian": "sq",
    "Amharic": "am",
    "Basque": "eu",
    "Belarusian": "be",
    "Bosnian": "bs",
    "Catalan": "ca",
    "Esperanto": "eo",
    "Galician": "gl",
    "Icelandic": "is",
    "Irish": "ga",
    "Macedonian": "mk",
    "Maltese": "mt",
    "Maori": "mi",
    "Welsh": "cy",
    "Yiddish": "yi"
}

ADVANCED_OFFLINE_DB = {
    ("ka", "en_US"): {
        "გამარჯობა": "Hello", "მადლობა": "Thank you", "დიდი მადლობა": "Thank you very much",
        "როგორ ხარ": "How are you", "კარგად": "I am fine", "ნახვამდის": "Goodbye",
        "დიახ": "Yes", "არა": "No", "ინებეთ": "Here you go", "ბოდიში": "Sorry",
        "სად არის სასტუმრო": "Where is the hotel", "რა ღირს": "How much does it cost",
        "წყალი": "Water", "პური": "Bread", "ყავა": "Coffee", "ჩაი": "Tea",
        "დახმარება": "Help", "ექიმი": "Doctor", "ტაქსი": "Taxi", "აეროპორტი": "Airport"
    },
    ("en_US", "ka"): {
        "hello": "გამარჯობა", "thank you": "მადლობა", "thanks": "მადლობა",
        "how are you": "როგორ ხარ", "goodbye": "ნახვამდის", "yes": "დიახ", "no": "არა",
        "sorry": "ბოდიში", "where is the hotel": "სად არის სასტუმრო",
        "how much": "რა ღირს", "water": "წყალი", "coffee": "ყავა", "help": "დახმარება"
    }
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
            CREATE TABLE IF NOT EXISTS memory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp TEXT
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

    def get_summary(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT words_learned, streak_days FROM stats WHERE id=1")
        row = cursor.fetchone()
        return {
            "words_learned": row[0] if row else 0,
            "streak_days": row[1] if row else 1
        }

    def increment_words(self, count=1):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE stats SET words_learned = words_learned + ? WHERE id=1", (count,))
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

    def clear_history(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM translation_history")
        self.conn.commit()


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
                text: "☰"
                font_name: 'font.ttf'
                size_hint_x: None
                width: '45dp'
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
                on_release: root.open_conversation_mode()

            Button:
                text: "AR"
                font_name: 'font.ttf'
                size_hint_x: None
                width: '55dp'
                background_color: 0.6, 0.1, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.open_ar_camera_mode()

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
            size_hint_y: 0.40
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
                hint_text: "ჩაწერეთ ტექსტი ან გამოიყენეთ ხმოვანი ღილაკი..."
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
                    width: '85dp'
                    background_color: 0.2, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    on_release: root.ask_ai_agent()
                Button:
                    text: "გრამატიკა"
                    font_name: 'font.ttf'
                    size_hint_x: None
                    width: '100dp'
                    background_color: 0.9, 0.5, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.translate_with_grammar()
                Button:
                    text: "STT"
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_to_text(root.source_lang, target_field='input')
                Button:
                    text: "TTS"
                    size_hint_x: None
                    width: '45dp'
                    background_color: 0.12, 0.15, 0.22, 1
                    color: 0.2, 0.7, 1, 1
                    on_release: root.speak_text(input_text.text, root.source_lang)

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.50
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
                hint_text: "პასუხი / თარგმანი გამოჩნდება აქ..."
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
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.copy_output_text()

                Button:
                    text: "მოსმენა"
                    font_name: 'font.ttf'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.speak_text(output_text.text, root.target_lang)
                Widget:
'''

Builder.load_string(KV)

class NativeARCameraWidget(FloatLayout):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        self.camera = Camera(play=True, resolution=(640, 480), size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.camera)

        self.ar_label = Label(
            text="[AR Vision მზადაა...]",
            font_name=FONT_PATH, font_size='16sp', color=(0, 1, 0.8, 1),
            size_hint=(0.9, None), height='50dp', pos_hint={'center_x': 0.5, 'y': 0.05}
        )
        self.add_widget(self.ar_label)
        self.is_processing = False
        self.clock_event = Clock.schedule_interval(self.capture_and_process, 2.0)

    def capture_and_process(self, dt):
        if self.is_processing or not self.camera.texture: return
        self.is_processing = True
        try:
            tex = self.camera.texture
            pixels = tex.pixels
            threading.Thread(target=self._send_frame_to_cloud, args=(pixels, tex.width, tex.height), daemon=True).start()
        except Exception:
            self.is_processing = False

    def _send_frame_to_cloud(self, pixels, w, h):
        try:
            from PIL import Image as PILImage
            img = PILImage.frombytes(mode='RGBA', size=(w, h), data=pixels)
            
            # სურათის შეტრიალება Android-ზე
            if platform == 'android':
                img = img.rotate(-90, expand=True)
            else:
                img = img.rotate(180, expand=True)

            import io
            buffer = io.BytesIO()
            img.convert('RGB').save(buffer, format="JPEG", quality=85)
            jpg_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            payload = json.dumps({
                "image_data": jpg_base64,
                "source_lang": self.main_screen.source_lang,
                "target_lang": self.main_screen.target_lang,
                "mode": "vision_ar"
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': API_AUTH_TOKEN,
                'User-Agent': 'Mozilla/5.0'
            }

            def _on_success(req, res):
                text = res.get('translated_text', '') or res.get('text', '')
                Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', text if text else "[ტექსტი ვერ მოიძებნა]"), 0)
                self.is_processing = False

            def _on_error(req, err):
                Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', "[სერვერის შეცდომა / Offline]"), 0)
                self.is_processing = False

            UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=8)
        except Exception:
            self.is_processing = False

    def stop_camera(self):
        if self.clock_event:
            Clock.unschedule(self.clock_event)
        self.camera.play = False


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en_US"
        self.dialog_history = []
        self.conv_popup = None
        self.conv_label = None
        self.is_auto_loop_active = False
        self.current_turn = 'dialog_a'
        self._current_stt_field = 'input'
        self.db = AgentMemoryDB()
        self._init_android_stt_listener()

    def _init_android_stt_listener(self):
        if platform == 'android':
            try:
                from jnius import autoclass, PythonJavaClass, java_method
                Activity = autoclass('org.kivy.android.PythonActivity').mActivity
                
                class ActivityResultListener(PythonJavaClass):
                    __javainterfaces__ = ['org/kivy/android/ActivityResultListener']
                    def __init__(self, callback):
                        super().__init__()
                        self.callback = callback

                    @java_method('(IILandroid/content/Intent;)V')
                    def onActivityResult(self, requestCode, resultCode, data):
                        if requestCode == 1001 and resultCode == -1 and data is not None:
                            results = data.getStringArrayListExtra('android.speech.extra.RESULTS')
                            if results and results.size() > 0:
                                text = results.get(0)
                                self.callback(text)

                self.listener = ActivityResultListener(self.on_native_stt_result)
                Activity.registerActivityResultListener(self.listener)
            except Exception as e:
                print(f"Android Listener Init Error: {e}")

    def on_native_stt_result(self, text):
        Clock.schedule_once(lambda dt: self._process_stt_text_ui(text), 0)

    def _process_stt_text_ui(self, text):
        if self._current_stt_field == 'input':
            self.ids.input_text.text = text
        elif 'dialog' in self._current_stt_field:
            self.handle_conversation_speech(text, self._current_stt_field)

    def ask_ai_agent(self):
        text = self.ids.input_text.text.strip()
        if not text: return
        self.ids.output_text.text = "[LingoLens AI Agent ფიქრობს...]"
        
        memory_summary = self.db.get_summary()
        payload = json.dumps({
            "text": text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "mode": "agent",
            "memory": memory_summary
        })
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}

        def _on_success(req, res):
            response_text = res.get('translated_text', '')
            mood = res.get('agent_mood', 'Friendly')
            level = res.get('current_level', 'A1')
            
            self.ids.output_text.text = f"[{mood} | {level}]\n{response_text}"
            self.ids.status_label.text = f"LingoLens AI [{mood}]"
            self.db.increment_words(1)
            self.db.add_history(text, response_text)

        def _on_error(req, err):
            offline_res = self.smart_offline_translate(text)
            self.ids.output_text.text = f"[Offline AI]\n{offline_res}"
            self.db.add_history(text, offline_res)

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=10)

    def open_main_menu(self):
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        btn_history = Button(text="📜 თარგმანების ისტორია", font_name=FONT_PATH, size_hint_y=None, height='45dp', background_color=(0.15, 0.25, 0.4, 1))
        btn_clear = Button(text="🗑️ ისტორიის გასუფთავება", font_name=FONT_PATH, size_hint_y=None, height='45dp', background_color=(0.7, 0.2, 0.2, 1))
        btn_close = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.3, 0.3, 0.3, 1))

        box.add_widget(btn_history)
        box.add_widget(btn_clear)
        box.add_widget(btn_close)

        popup = Popup(title="მენიუ", content=box, size_hint=(0.8, 0.5))
        
        btn_history.bind(on_release=lambda x: (popup.dismiss(), self.open_history_view()))
        btn_clear.bind(on_release=lambda x: (self.db.clear_history(), popup.dismiss(), self.show_toast("ისტორია გასუფთავდა")))
        btn_close.bind(on_release=popup.dismiss)
        
        popup.open()

    def open_history_view(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView(size_hint_y=0.85)
        
        history_data = self.db.get_history()
        history_text = ""
        for item in history_data:
            history_text += f"[color=888888]{item[2]}[/color]\n[color=00d4ff]ტექსტი:[/color] {item[0]}\n[color=00ffbf]თარგმანი:[/color] {item[1]}\n-------------------\n"
        
        if not history_data:
            history_text = "ისტორია ცარიელია."

        lbl = Label(text=history_text, font_name=FONT_PATH, size_hint_y=None, markup=True, font_size='14sp', color=(1, 1, 1, 1))
        lbl.bind(texture_size=lambda instance, val: setattr(instance, 'height', val[1]))
        scroll.add_widget(lbl)
        
        box.add_widget(scroll)
        btn_close = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.3, 0.3, 0.3, 1))
        box.add_widget(btn_close)

        popup = Popup(title="თარგმანების ისტორია", content=box, size_hint=(0.9, 0.85))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

    def show_toast(self, msg):
        box = BoxLayout(padding=10)
        lbl = Label(text=msg, font_name=FONT_PATH, color=(0, 1, 0.5, 1))
        box.add_widget(lbl)
        popup = Popup(title="შეტყობინება", content=box, size_hint=(0.7, 0.25))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

    def open_conversation_mode(self):
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        scroll = ScrollView(size_hint_y=0.7)
        self.conv_label = Label(
            text="[ორმხრივი დიალოგი მზადაა]\nდააჭირეთ 'Start Live Loop'-ს საუბრისთვის.",
            font_name=FONT_PATH, size_hint_y=None, markup=True, color=(1, 1, 1, 1), font_size='14sp'
        )
        self.conv_label.bind(texture_size=lambda instance, val: setattr(instance, 'height', val[1]))
        scroll.add_widget(self.conv_label)
        box.add_widget(scroll)

        btns_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=8)
        self.btn_auto = Button(text="Start Live Loop", font_name=FONT_PATH, background_color=(0.1, 0.7, 0.3, 1), color=(1, 1, 1, 1))
        self.btn_auto.bind(on_release=self.toggle_auto_dialog_loop)
        btns_layout.add_widget(self.btn_auto)
        box.add_widget(btns_layout)

        close_btn = Button(text="დასრულება", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.3, 0.3, 0.3, 1))
        box.add_widget(close_btn)

        self.conv_popup = Popup(title="Real-Time Conversation", content=box, size_hint=(0.95, 0.85))
        close_btn.bind(on_release=self._stop_and_close_dialog)
        self.conv_popup.open()

    def toggle_auto_dialog_loop(self, instance):
        self.is_auto_loop_active = not self.is_auto_loop_active
        if self.is_auto_loop_active:
            self.btn_auto.text = "შეჩერება"
            self.btn_auto.background_color = (0.8, 0.2, 0.2, 1)
            self.current_turn = 'dialog_a'
            self._trigger_next_turn()
        else:
            self.btn_auto.text = "Start Live Loop"
            self.btn_auto.background_color = (0.1, 0.7, 0.3, 1)

    def _trigger_next_turn(self):
        if not self.is_auto_loop_active: return
        lang = self.source_lang if self.current_turn == 'dialog_a' else self.target_lang
        self.start_speech_to_text(lang, target_field=self.current_turn)

    def handle_conversation_speech(self, spoken_text, speaker):
        if not spoken_text.strip():
            if self.is_auto_loop_active:
                Clock.schedule_once(lambda dt: self._trigger_next_turn(), 1.0)
            return
        
        src = self.source_lang if speaker == 'dialog_a' else self.target_lang
        tgt = self.target_lang if speaker == 'dialog_a' else self.source_lang

        payload = json.dumps({"text": spoken_text, "source_lang": src, "target_lang": tgt, "mode": "standard"})
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
        
        def _on_success(req, res):
            translated = res.get('translated_text', '')
            self._add_to_dialog_ui(spoken_text, translated, speaker, tgt)

        def _on_error(req, err):
            translated = self.smart_offline_translate(spoken_text)
            self._add_to_dialog_ui(spoken_text, translated, speaker, tgt)

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=4)

    def _add_to_dialog_ui(self, original, translated, speaker, speak_lang):
        speaker_name = "მოსაუბრე 1" if speaker == 'dialog_a' else "მოსაუბრე 2"
        entry = f"[color=00d4ff]{speaker_name}:[/color] {original}\n[color=00ffbf]თარგმანი:[/color] {translated}\n---"
        self.dialog_history.append(entry)
        if self.conv_label: self.conv_label.text = "\n".join(self.dialog_history)

        self.speak_text(translated, speak_lang)
        self.db.add_history(original, translated)
        
        if self.is_auto_loop_active:
            self.current_turn = 'dialog_b' if speaker == 'dialog_a' else 'dialog_a'
            Clock.schedule_once(lambda dt: self._trigger_next_turn(), 2.5)

    def _stop_and_close_dialog(self, instance):
        self.is_auto_loop_active = False
        if self.conv_popup: self.conv_popup.dismiss()

    def start_speech_to_text(self, lang_code, target_field='input'):
        self._current_stt_field = target_field
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
            except Exception as e:
                if target_field == 'input': self.ids.input_text.text = f"[STT Error: {e}]"
        else:
            dummy = "გამარჯობა, სად არის სასტუმრო?" if "ka" in lang_code else "Hello, where is the hotel?"
            self._process_stt_text_ui(dummy)

    def translate_with_grammar(self):
        text = self.ids.input_text.text.strip()
        if not text: return
        self.ids.output_text.text = "[AI გრამატიკული დამუშავება...]"
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "grammar"})
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
        
        def _on_success(req, res):
            res_text = f"თარგმანი:\n{res.get('translated_text', '')}\n\nგრამატიკა:\n{res.get('grammar_analysis', '')}"
            self.ids.output_text.text = res_text
            self.db.add_history(text, res.get('translated_text', ''))

        def _on_error(req, err):
            off_res = self.smart_offline_translate(text)
            self.ids.output_text.text = f"[Offline]\n{off_res}"
            self.db.add_history(text, off_res)

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=8)

    def smart_offline_translate(self, text):
        cleaned = text.lower().strip()
        key = (self.source_lang, self.target_lang)
        db = ADVANCED_OFFLINE_DB.get(key, {})
        if cleaned in db: return db[cleaned]
        words = cleaned.split()
        return " ".join([db.get(w, w) for w in words])

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.3)

    def _delayed_translate(self, text):
        self.ids.status_label.text = "ითარგმნება..."
        payload = json.dumps({"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang, "mode": "standard"})
        headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
        
        def _on_success(req, res):
            translated = res.get('translated_text', '')
            self.ids.output_text.text = translated
            self.ids.status_label.text = "LingoLens v4.0 AI Agent"
            self.db.add_history(text, translated)

        def _on_error(req, err):
            offline_res = self.smart_offline_translate(text)
            self.ids.output_text.text = f"[Offline] {offline_res}"
            self.ids.status_label.text = "LingoLens (Offline)"
            self.db.add_history(text, offline_res)

        UrlRequest(VERCEL_SERVER_URL, req_body=payload, req_headers=headers, on_success=_on_success, on_error=_on_error, on_failure=_on_error, timeout=4)

    def speak_text(self, text, lang_code):
        cleaned = text.strip()
        if not cleaned: return
        if "ka" in lang_code:
            threading.Thread(target=self._play_georgian_tts, args=(cleaned,), daemon=True).start()
        elif platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                parts = lang_code.split('_')
                locale_obj = Locale(parts[0], parts[1]) if len(parts) > 1 else Locale(parts[0])
                
                class TTSListener(autoclass('android.speech.tts.TextToSpeech$OnInitListener')):
                    def onInit(self, status): pass
                
                tts = TextToSpeech(PythonActivity.mActivity, TTSListener())
                tts.setLanguage(locale_obj)
                tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e: print(f"TTS Error: {e}")

    def _play_georgian_tts(self, text):
        try:
            os.makedirs("audio_cache", exist_ok=True)
            filename = f"audio_cache/{abs(hash(text))}.mp3"
            if os.path.exists(filename):
                sound = SoundLoader.load(filename)
                if sound: sound.play()
                return

            encoded = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())

            sound = SoundLoader.load(filename)
            if sound: sound.play()
        except Exception as e: print(f"Audio Error: {e}")

    def open_ar_camera_mode(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.ar_cam = NativeARCameraWidget(main_screen=self)
        box.add_widget(self.ar_cam)
        close_btn = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='45dp', background_color=(0.8, 0.2, 0.2, 1))
        box.add_widget(close_btn)
        popup = Popup(title="Live AR Vision", content=box, size_hint=(0.95, 0.9))
        
        def _close_popup(instance):
            if self.ar_cam: self.ar_cam.stop_camera()
            popup.dismiss()

        close_btn.bind(on_release=_close_popup)
        popup.open()

    def open_language_menu(self, mode):
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        list_box.bind(minimum_height=list_box.setter('height'))
        popup = Popup(title='აირჩიეთ ენა', content=scroll, size_hint=(0.85, 0.75))

        for lang_name, code in LANGUAGES.items():
            btn = Button(text=lang_name, font_name=FONT_PATH, size_hint_y=None, height='42dp', background_color=(0.14, 0.17, 0.24, 1), color=(1, 1, 1, 1))
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
        self.on_live_translate(self.ids.input_text.text)

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src
        self.on_live_translate(self.ids.input_text.text)

    def copy_output_text(self):
        if self.ids.output_text.text.strip():
            Clipboard.copy(self.ids.output_text.text.strip())


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
                    Permission.ACCESS_NETWORK_STATE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE,
                    "android.permission.READ_MEDIA_IMAGES"
                ])
            except Exception as e:
                print(f"Permissions Request Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

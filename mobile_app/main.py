import os
import sqlite3
import threading
import requests
import math
import traceback
import random
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform

from plyer import share, filechooser, vibrator, camera, notification

APP_VERSION = "10.1.0"
VERCEL_BASE_URL = "https://lingo-lens-eight.vercel.app"
API_AUTH_TOKEN = "Bearer LINGOLENS_SECURE_TOKEN_2026"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

def log_error(err):
    try:
        app = App.get_running_app()
        base_dir = app.user_data_dir if (platform == 'android' and app) else "."
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, "error_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- ERROR [{time.ctime()}] ---\n{traceback.format_exc()}\n")
    except Exception:
        pass

def trigger_vibration():
    try:
        vibrator.vibrate(0.04)
    except Exception:
        pass

def send_android_notification(title, message):
    try:
        notification.notify(title=title, message=message, app_name='LingoLens')
    except Exception as e:
        log_error(e)

# ----------------------------------------------------
# 1. Dynamic Permissions & Speech Callbacks
# ----------------------------------------------------
stt_result_callback = None

def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            
            VERSION = autoclass('android.os.Build$VERSION')
            api_level = VERSION.SDK_INT

            permissions = [
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
            ]

            if api_level >= 33:
                permissions.extend([
                    Permission.READ_MEDIA_IMAGES,
                    Permission.READ_MEDIA_AUDIO
                ])
            else:
                permissions.extend([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])

            def permissions_callback(perms, results):
                print(f"Permissions granted: {results}")

            request_permissions(permissions, permissions_callback)
        except Exception as e:
            log_error(e)

if platform == 'android':
    try:
        from android.activity import bind as android_bind
        from jnius import autoclass

        def _on_activity_result(request_code, result_code, intent):
            global stt_result_callback
            if request_code == 1001 and result_code == -1 and intent is not None:
                try:
                    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                    results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                    if results and results.size() > 0:
                        text_recognized = results.get(0)
                        if stt_result_callback:
                            Clock.schedule_once(lambda dt: stt_result_callback(text_recognized), 0)
                except Exception as ex:
                    log_error(ex)

        android_bind(on_activity_result=_on_activity_result)
    except Exception as e:
        log_error(e)

# ----------------------------------------------------
# 2. Languages & Data
# ----------------------------------------------------
LANGUAGES = {
    "Auto-Detect (ავტო)": "auto",
    "Georgian (ქართული)": "ka",
    "English (ინგლისური)": "en",
    "Spanish (ესპანური)": "es",
    "French (ფრანგული)": "fr",
    "German (გერმანული)": "de",
    "Italian (იტალიური)": "it",
    "Portuguese (პორტუგალიური)": "pt",
    "Russian (რუსული)": "ru",
    "Ukrainian (უკრაინული)": "uk",
    "Polish (პოლონური)": "pl",
    "Dutch (ჰოლანდიური)": "nl",
    "Greek (ბერძნული)": "el",
    "Turkish (თურქული)": "tr",
    "Arabic (არაბული)": "ar",
    "Chinese Simplified (ჩინური)": "zh-CN",
    "Japanese (იაპონური)": "ja",
    "Korean (კორეული)": "ko"
}

DAILY_QUIZ = [
    {"q": "რა არის 'Resilience'-ის თარგმანი?", "options": ["მდგრადობა", "სიჩქარე", "სიძულვილი"], "a": "მდგრადობა"},
    {"q": "რომელია 'Innovation'-ის სინონიმი?", "options": ["Novelty", "Stagnation", "Old"], "a": "Novelty"},
    {"q": "რა არის 'Adaptability'-ს მნიშვნელობა?", "options": ["ეგუებადობა", "სიმტკიცე", "სიბნელე"], "a": "ეგუებადობა"}
]

# ----------------------------------------------------
# 3. Native Speech Manager
# ----------------------------------------------------
class NativeSpeechManager:
    _tts_instance = None

    @staticmethod
    def start_listening(lang_code, callback_text):
        global stt_result_callback
        stt_result_callback = callback_text
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                currentActivity = PythonActivity.mActivity

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                req_lang = "ka-GE" if lang_code in ("ka", "auto") else lang_code
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, req_lang)
                currentActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                log_error(e)
        else:
            if callback_text:
                Clock.schedule_once(lambda dt: callback_text("ხმის ამოცნობა (Desktop)..."), 0)

    @staticmethod
    def speak_text(text, lang_code, speed=1.0):
        if not text or text.startswith("["): return
        if platform == 'android':
            try:
                from jnius import autoclass, PythonJavaClass, java_method
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                class TTSInitListener(PythonJavaClass):
                    __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
                    def __init__(self, text_to_speak, lang, spd):
                        super().__init__()
                        self.text = text_to_speak
                        self.lang = lang
                        self.spd = spd

                    @java_method('(I)V')
                    def onInit(self, status):
                        if status == TextToSpeech.SUCCESS:
                            loc = Locale("ka") if self.lang == "ka" else Locale(self.lang)
                            NativeSpeechManager._tts_instance.setLanguage(loc)
                            NativeSpeechManager._tts_instance.setSpeechRate(float(self.spd))
                            NativeSpeechManager._tts_instance.speak(self.text, TextToSpeech.QUEUE_FLUSH, None, None)

                if NativeSpeechManager._tts_instance is None:
                    listener = TTSInitListener(text, lang_code, speed)
                    NativeSpeechManager._tts_instance = TextToSpeech(PythonActivity.mActivity, listener)
                else:
                    loc = Locale("ka") if lang_code == "ka" else Locale(lang_code)
                    NativeSpeechManager._tts_instance.setLanguage(loc)
                    NativeSpeechManager._tts_instance.setSpeechRate(float(speed))
                    NativeSpeechManager._tts_instance.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                log_error(e)

# ----------------------------------------------------
# 4. Custom UI & Georgian Background Graphics
# ----------------------------------------------------
class AudioVisualizer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = False
        self.phase = 0

    def start_animation(self):
        self.is_active = True
        Clock.unschedule(self.animate)
        Clock.schedule_interval(self.animate, 1 / 15.0)

    def stop_animation(self):
        self.is_active = False
        Clock.unschedule(self.animate)
        self.canvas.before.clear()

    def animate(self, dt):
        self.canvas.before.clear()
        if not self.is_active or self.width <= 0: return
        self.phase += dt * 5
        with self.canvas.before:
            Color(0.2, 0.8, 1, 0.8)
            w, h = self.size
            cy = self.y + h / 2
            points = []
            for i in range(12):
                amp = math.sin(self.phase + i) * (h / 3)
                px = self.x + (w / 11) * i
                py = cy + amp
                points.extend([px, py])
            if len(points) >= 4:
                Line(points=points, width=2)

class GeorgianFlagBackground(Widget):
    """ქართული დროშის ელემენტებით გაფორმებული დინამიური ფონი"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_mode = "dark"
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_theme(self, mode):
        self.theme_mode = mode
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            w, h = self.size
            x, y = self.pos
            if self.theme_mode == "dark":
                Color(0.05, 0.06, 0.09, 1)
            else:
                Color(0.94, 0.95, 0.98, 1)
            Rectangle(pos=(x, y), size=(w, h))

            # დეკორატიული წითელი ზოლი (ქართული დიზაინის შტრიხი)
            Color(0.85, 0.1, 0.2, 0.15 if self.theme_mode == "dark" else 0.25)
            Rectangle(pos=(x, y + h - 6), size=(w, 6))

class NetworkIndicator(Widget):
    def set_status(self, status):
        self.canvas.before.clear()
        with self.canvas.before:
            if status == "green": Color(0.1, 0.8, 0.2, 1)
            elif status == "yellow": Color(0.9, 0.7, 0.1, 1)
            else: Color(0.9, 0.2, 0.2, 1)
            size = min(self.width, self.height) * 0.5
            px = self.x + (self.width - size) / 2
            py = self.y + (self.height - size) / 2
            Line(ellipse=(px, py, size, size), width=2)

# ----------------------------------------------------
# 5. SQLite Database
# ----------------------------------------------------
class DatabaseManager:
    def __init__(self):
        self.db_path = None

    def _get_db_path(self):
        if not self.db_path:
            app = App.get_running_app()
            base_dir = app.user_data_dir if (platform == 'android' and app) else "."
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "lingolens.db")
            self.init_db()
        return self.db_path

    def init_db(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, source_lang TEXT, target_lang TEXT, original_text TEXT, translated_text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, source_lang TEXT, target_lang TEXT, original_text TEXT, translated_text TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e: log_error(e)

    def add_history(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip(): return
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)", (src, tgt, original, translated))
            conn.commit()
            conn.close()
        except Exception as e: log_error(e)

    def get_history(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id, original_text, translated_text FROM history ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            log_error(e)
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
            log_error(e)
            return False

    def search_offline_cache(self, src, tgt, text):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT translated_text FROM history WHERE target_lang=? AND LOWER(original_text)=LOWER(?) ORDER BY id DESC LIMIT 1", (tgt, text.strip()))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            log_error(e)
            return None

    def add_favorite(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip(): return False
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO favorites (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)", (src, tgt, original, translated))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

    def get_favorites(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT id, original_text, translated_text FROM favorites ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            log_error(e)
            return []

db = DatabaseManager()

class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _worker():
            headers = {'Content-Type': 'application/json', 'Authorization': API_AUTH_TOKEN}
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=8)
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: callback(True, response.json()), 0)
                else:
                    Clock.schedule_once(lambda dt: callback(False, f"HTTP {response.status_code}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, "ქსელის შეცდომა"), 0)
        threading.Thread(target=_worker, daemon=True).start()

# ----------------------------------------------------
# 6. KV Layout
# ----------------------------------------------------
KV = f'''
<MainScreen>:
    GeorgianFlagBackground:
        id: flag_bg
        size: root.size

    BoxLayout:
        orientation: 'vertical'
        padding: 8
        spacing: 6

        BoxLayout:
            size_hint_y: None
            height: '42dp'
            spacing: 4

            NetworkIndicator:
                id: net_indicator
                size_hint_x: None
                width: '18dp'

            Label:
                text: "LingoLens Ultra"
                bold: True
                font_size: '13sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "📜 ისტორია"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '68dp'
                background_color: 0.2, 0.5, 0.7, 1
                on_release: root.open_history_menu()

            Button:
                text: "★ ფავორიტი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '72dp'
                background_color: 0.8, 0.6, 0.1, 1
                on_release: root.open_favorites_menu()

            Button:
                text: "⚙️"
                size_hint_x: None
                width: '38dp'
                background_color: 0.3, 0.3, 0.4, 1
                on_release: root.open_settings_menu()

            Button:
                text: "🌙/☀️"
                size_hint_x: None
                width: '38dp'
                background_color: 0.2, 0.2, 0.3, 1
                on_release: root.toggle_theme()

        BoxLayout:
            size_hint_y: None
            height: '38dp'
            spacing: 6

            Button:
                id: btn_source_lang
                text: "Auto-Detect"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 0.9
                on_release: root.open_language_menu('source')

            Button:
                text: "<->"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '40dp'
                background_color: 0.12, 0.15, 0.22, 0.9
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (ინგლისური)"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 0.9
                on_release: root.open_language_menu('target')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.38
            padding: 6
            canvas.before:
                Color:
                    rgba: 0.08, 0.1, 0.15, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            BoxLayout:
                size_hint_y: None
                height: '30dp'
                Label:
                    text: "შეყვანა:"
                    font_name: '{FONT_PATH}'
                    font_size: '11sp'
                    color: 0.6, 0.7, 0.8, 1
                    size_hint_x: None
                    width: '50dp'

                AudioVisualizer:
                    id: audio_viz

                Button:
                    text: "X"
                    bold: True
                    size_hint_x: None
                    width: '30dp'
                    background_color: 0.8, 0.2, 0.2, 1
                    on_release: root.clear_input_text()

            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ ან თქვით ტექსტი..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                font_size: '14sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '34dp'
                spacing: 4
                
                Button:
                    text: "📷 OCR"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '65dp'
                    background_color: 0.2, 0.6, 0.8, 1
                    on_release: root.capture_camera_ocr()

                Button:
                    text: "🖼️ გალერეა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '80dp'
                    background_color: 0.3, 0.5, 0.7, 1
                    on_release: root.pick_gallery_image()

                Widget:

                Button:
                    text: "🗣️ დიალოგი"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '80dp'
                    background_color: 0.9, 0.3, 0.3, 1
                    on_release: root.open_interpreter_mode()

                Button:
                    text: "🎤 ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    on_release: root.start_speech_to_text(root.source_lang)

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.42
            padding: 6
            canvas.before:
                Color:
                    rgba: 0.08, 0.1, 0.15, 0.85
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            TextInput:
                id: output_text
                hint_text: "თარგმანი..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                font_size: '14sp'

            BoxLayout:
                size_hint_y: None
                height: '32dp'
                spacing: 4

                Button:
                    text: "📋"
                    size_hint_x: None
                    width: '38dp'
                    background_color: 0.2, 0.4, 0.6, 1
                    on_release: root.copy_to_clipboard()

                Button:
                    text: "🔗"
                    size_hint_x: None
                    width: '38dp'
                    background_color: 0.2, 0.5, 0.4, 1
                    on_release: root.share_translation()

                Button:
                    text: "★ შენახვა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '78dp'
                    background_color: 0.9, 0.6, 0.1, 1
                    on_release: root.save_to_favorites()

                Button:
                    text: "🧠 AI"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '50dp'
                    background_color: 0.7, 0.3, 0.8, 1
                    on_release: root.analyze_and_think()

                Button:
                    text: "1.0x"
                    id: btn_tts_speed
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '45dp'
                    background_color: 0.2, 0.4, 0.5, 1
                    on_release: root.toggle_tts_speed()

                Button:
                    text: "🔊 მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '78dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    on_release: root.speak_output_text()
'''

Builder.load_string(KV)

# ----------------------------------------------------
# 7. Main Screen & Full Logics
# ----------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "auto"
        self.target_lang = "en"
        self.theme_mode = "dark"
        self.tts_speed = 1.0
        self._debounce_event = None

    def on_enter(self):
        Clock.schedule_interval(self.check_network_status, 10)
        self.check_network_status(0)

    def check_network_status(self, dt):
        def _check():
            try:
                r = requests.get(f"{VERCEL_BASE_URL}/api/health", timeout=3)
                status = "green" if r.status_code == 200 else "yellow"
            except Exception:
                status = "red"
            Clock.schedule_once(lambda dt: self.ids.net_indicator.set_status(status), 0)
        threading.Thread(target=_check, daemon=True).start()

    # --- Language Selection ---
    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title='აირჩიეთ ენა', font_name=FONT_PATH, content=main_layout, size_hint=(0.85, 0.8))

        def select_lang(code, name):
            if mode == 'source':
                self.source_lang = code
                self.ids.btn_source_lang.text = name
            else:
                self.target_lang = code
                self.ids.btn_target_lang.text = name
            popup.dismiss()
            if self.ids.input_text.text.strip():
                self.perform_translation(self.ids.input_text.text)

        for name, code in LANGUAGES.items():
            btn = Button(text=name, font_name=FONT_PATH, size_hint_y=None, height='40dp')
            btn.bind(on_release=lambda x, c=code, n=name: select_lang(c, n))
            box.add_widget(btn)

        scroll.add_widget(box)
        main_layout.add_widget(scroll)
        popup.open()

    def swap_languages(self):
        trigger_vibration()
        if self.source_lang == "auto": return
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        self.ids.btn_source_lang.text, self.ids.btn_target_lang.text = self.ids.btn_target_lang.text, self.ids.btn_source_lang.text
        if self.ids.input_text.text.strip():
            self.perform_translation(self.ids.input_text.text)

    # --- Translation Core ---
    def on_live_translate(self, text):
        if self._debounce_event:
            Clock.unschedule(self._debounce_event)
        self._debounce_event = Clock.schedule_once(lambda dt: self.perform_translation(text), 0.6)

    def perform_translation(self, text):
        if not text.strip():
            self.ids.output_text.text = ""
            return

        cached = db.search_offline_cache(self.source_lang, self.target_lang, text)
        if cached:
            self.ids.output_text.text = f"[OFFLINE CACHE]\n{cached}"

        payload = {"text": text, "source_lang": self.source_lang, "target_lang": self.target_lang}
        
        def handle_response(success, res):
            if success and isinstance(res, dict) and "translation" in res:
                trans = res["translation"]
                self.ids.output_text.text = trans
                db.add_history(self.source_lang, self.target_lang, text, trans)
            else:
                if not cached:
                    self.ids.output_text.text = f"თარგმანი: {text}"

        AsyncTranslateEngine.async_post_request(f"{VERCEL_BASE_URL}/api/translate", payload, handle_response)

    # --- Camera & Gallery OCR ---
    def capture_camera_ocr(self):
        trigger_vibration()
        try:
            app = App.get_running_app()
            img_path = os.path.join(app.user_data_dir, "ocr_snap.jpg")
            camera.take_picture(filename=img_path, on_complete=self.process_ocr_image)
        except Exception as e:
            log_error(e)
            self.ids.input_text.text = "📷 კამერის გახსნა ვერ მოხერხდა."

    def pick_gallery_image(self):
        trigger_vibration()
        try:
            filechooser.open_file(on_selection=self.process_gallery_selection, filters=['*.png', '*.jpg', '*.jpeg'])
        except Exception as e:
            log_error(e)

    def process_gallery_selection(self, selection):
        if selection and len(selection) > 0:
            self.process_ocr_image(selection[0])

    def process_ocr_image(self, file_path):
        if not file_path or not os.path.exists(file_path): return
        self.ids.input_text.text = "🔍 სურათიდან ტექსტის ამოცნობა..."
        # OCR სიმულაცია/API ინტეგრაცია
        Clock.schedule_once(lambda dt: self._apply_ocr_result("LingoLens OCR: Text Recognized From Image"), 1.5)

    def _apply_ocr_result(self, result_text):
        self.ids.input_text.text = result_text

    # --- History & Favorites UI ---
    def open_history_menu(self):
        trigger_vibration()
        layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title='📜 ისტორია', font_name=FONT_PATH, content=layout, size_hint=(0.9, 0.85))

        rows = db.get_history()
        if not rows:
            box.add_widget(Label(text="ისტორია ცარიელია", font_name=FONT_PATH))
        else:
            for item in rows:
                lbl = Label(text=f"• {item[1]} -> {item[2]}", font_name=FONT_PATH, size_hint_y=None, height='35dp', halign='left')
                box.add_widget(lbl)

        scroll.add_widget(box)
        layout.add_widget(scroll)

        btn_clear = Button(text="🗑️ გასუფთავება", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.8, 0.2, 0.2, 1))
        def clear_all(evt):
            db.clear_history()
            popup.dismiss()
            send_android_notification("LingoLens", "ისტორია გასუფთავდა.")
        btn_clear.bind(on_release=clear_all)
        layout.add_widget(btn_clear)

        popup.open()

    def open_favorites_menu(self):
        trigger_vibration()
        layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title='★ ფავორიტები', font_name=FONT_PATH, content=layout, size_hint=(0.9, 0.85))

        rows = db.get_favorites()
        if not rows:
            box.add_widget(Label(text="ფავორიტები ცარიელია", font_name=FONT_PATH))
        else:
            for item in rows:
                lbl = Label(text=f"★ {item[1]} = {item[2]}", font_name=FONT_PATH, size_hint_y=None, height='35dp', color=(0.9, 0.7, 0.2, 1))
                box.add_widget(lbl)

        scroll.add_widget(box)
        layout.add_widget(scroll)
        popup.open()

    # --- Settings Menu ---
    def open_settings_menu(self):
        trigger_vibration()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        layout.add_widget(Label(text=f"LingoLens v{APP_VERSION}", font_name=FONT_PATH, bold=True))
        layout.add_widget(Label(text="API Server URL:", font_name=FONT_PATH))
        
        input_url = TextInput(text=VERCEL_BASE_URL, multiline=False, font_size='12sp')
        layout.add_widget(input_url)

        btn_save = Button(text="შენახვა & შემოწმება", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.2, 0.7, 0.3, 1))
        popup = Popup(title='⚙️ პარამეტრები', font_name=FONT_PATH, content=layout, size_hint=(0.85, 0.6))
        
        def save_settings(evt):
            global VERCEL_BASE_URL
            VERCEL_BASE_URL = input_url.text.strip()
            popup.dismiss()
            send_android_notification("LingoLens", "პარამეტრები შენახულია.")

        btn_save.bind(on_release=save_settings)
        layout.add_widget(btn_save)
        popup.open()

    # --- Helper Actions ---
    def analyze_and_think(self):
        trigger_vibration()
        text = self.ids.input_text.text.strip()
        if not text:
            self.ids.output_text.text = "⚠️ ჩაწერეთ ტექსტი AI ანალიზისთვის."
            return
        self.ids.output_text.text = f"🧠 [AI ლოგიკური ანალიზი]\n• სიტყვების რაოდენობა: {len(text.split())}\n• ენა: {self.source_lang} -> {self.target_lang}\n• ტექსტის ტიპი: {'შეკითხვა' if text.endswith('?') else 'მტკიცებითი'}"

    def clear_input_text(self):
        trigger_vibration()
        self.ids.input_text.text = ""
        self.ids.output_text.text = ""

    def copy_to_clipboard(self):
        trigger_vibration()
        if self.ids.output_text.text:
            Clipboard.copy(self.ids.output_text.text)

    def share_translation(self):
        trigger_vibration()
        text = self.ids.output_text.text
        if text:
            try: share.share(text)
            except Exception as e: log_error(e)

    def save_to_favorites(self):
        trigger_vibration()
        src = self.ids.input_text.text
        tgt = self.ids.output_text.text
        if src and tgt:
            if db.add_favorite(self.source_lang, self.target_lang, src, tgt):
                self.ids.output_text.text += "\n\n★ შენახულია ფავორიტებში!"

    def toggle_tts_speed(self):
        trigger_vibration()
        speeds = [1.0, 1.25, 1.5, 0.75]
        idx = (speeds.index(self.tts_speed) + 1) % len(speeds)
        self.tts_speed = speeds[idx]
        self.ids.btn_tts_speed.text = f"{self.tts_speed}x"

    def speak_output_text(self):
        trigger_vibration()
        text = self.ids.output_text.text
        if text:
            NativeSpeechManager.speak_text(text, self.target_lang, self.tts_speed)

    def start_speech_to_text(self, lang):
        trigger_vibration()
        self.ids.audio_viz.start_animation()
        
        def on_speech_done(recognized_text):
            self.ids.audio_viz.stop_animation()
            if recognized_text:
                self.ids.input_text.text = recognized_text

        NativeSpeechManager.start_listening(lang, on_speech_done)

    def toggle_theme(self):
        trigger_vibration()
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.ids.flag_bg.set_theme(self.theme_mode)

    def open_interpreter_mode(self):
        trigger_vibration()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        display = TextInput(readonly=True, font_name=FONT_PATH, font_size='16sp', hint_text="ორმხრივი დიალოგის რეჟიმი...")
        btn_box = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        
        b1 = Button(text="🎤 A (ქართული)", font_name=FONT_PATH, background_color=(0.2, 0.6, 0.9, 1))
        b2 = Button(text="🎤 B (English)", font_name=FONT_PATH, background_color=(0.9, 0.4, 0.2, 1))
        
        def rec_a(evt):
            def _cb(txt):
                display.text += f"\n🅰️ (KA): {txt}"
                AsyncTranslateEngine.async_post_request(f"{VERCEL_BASE_URL}/api/translate", {"text": txt, "source_lang": "ka", "target_lang": "en"}, lambda s, r: self._append_dialogue(display, "🅱️ (EN)", s, r))
            NativeSpeechManager.start_listening("ka", _cb)

        def rec_b(evt):
            def _cb(txt):
                display.text += f"\n🅱️ (EN): {txt}"
                AsyncTranslateEngine.async_post_request(f"{VERCEL_BASE_URL}/api/translate", {"text": txt, "source_lang": "en", "target_lang": "ka"}, lambda s, r: self._append_dialogue(display, "🅰️ (KA)", s, r))
            NativeSpeechManager.start_listening("en", _cb)

        b1.bind(on_release=rec_a)
        b2.bind(on_release=rec_b)
        btn_box.add_widget(b1)
        btn_box.add_widget(b2)
        layout.add_widget(display)
        layout.add_widget(btn_box)
        Popup(title="🗣️ სინქრონული თარჯიმანი", font_name=FONT_PATH, content=layout, size_hint=(0.95, 0.9)).open()

    def _append_dialogue(self, display, label, success, res):
        if success and isinstance(res, dict) and "translation" in res:
            display.text += f"\n{label}: {res['translation']}\n"
            NativeSpeechManager.speak_text(res['translation'], "ka" if "KA" in label else "en")

# ----------------------------------------------------
# 8. Application Entry Point
# ----------------------------------------------------
class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

    def on_start(self):
        Clock.schedule_once(lambda dt: request_android_permissions(), 1.0)

if __name__ == '__main__':
    LingoLensApp().run()

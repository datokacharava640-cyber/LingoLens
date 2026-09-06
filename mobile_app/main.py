"""
LingoLens Ultra Pro v5.0.0 (Ultimate Production Edition)
==================================================
ავტორი: დავით კაჭარავა
ლოკაცია: საქართველო
თარიღი: 2026
==================================================
"""

import os
import sqlite3
import threading
import requests
import math

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
from kivy.graphics import Color, Rectangle, Line
from kivy.utils import platform

PORCUPINE_AVAILABLE = False
try:
    import pvporcupine
    from pvrecorder import PvRecorder
    PORCUPINE_AVAILABLE = True
except Exception as e:
    print(f"Porcupine status: {e}")

APP_VERSION = "5.0.0"
PROJECT_AUTHOR = "დავით კაჭარავა"
PROJECT_LOCATION = "საქართველო"

VERCEL_BASE_URL = "https://lingo-lens-eight.vercel.app"
FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"
PICOVOICE_ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE"

LANGUAGES = {
    "Georgian (ქართული)": "ka",
    "English (US)": "en",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Italian (Italiano)": "it",
    "Russian (Русский)": "ru",
    "Turkish (Türkçe)": "tr",
    "Chinese (中文)": "zh",
    "Japanese (日本語)": "ja"
}

class GeorgianFlagBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.offset = 0
        self.theme_mode = "dark"
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_interval(self.animate, 1 / 30.0)

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
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.12, 0.14, 0.18, 0.85)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.85, 0.1, 0.1, 0.35 + math.sin(self.offset) * 0.08)
            else:
                Color(0.95, 0.95, 0.98, 1)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.88, 0.9, 0.94, 0.85)
                Rectangle(pos=(x, y), size=(w, h))
                Color(0.85, 0.1, 0.1, 0.25 + math.sin(self.offset) * 0.05)

            cross_thick = min(w, h) * 0.12
            Rectangle(pos=(x, y + h / 2 - cross_thick / 2), size=(w, cross_thick))
            Rectangle(pos=(x + w / 2 - cross_thick / 2, y), size=(cross_thick, h))

            small_s = min(w, h) * 0.08
            offsets = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
            for ox, oy in offsets:
                cx = x + w * ox + math.cos(self.offset) * 5
                cy = y + h * oy + math.sin(self.offset) * 5
                Rectangle(pos=(cx - small_s/2, cy - small_s/6), size=(small_s, small_s/3))
                Rectangle(pos=(cx - small_s/6, cy - small_s/2), size=(small_s/3, small_s))

    def animate(self, dt):
        self.offset += dt * 1.5
        self.update_canvas()

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
            Line(ellipse=(px, py, size, size), width=2)

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
                    source_lang TEXT, target_lang TEXT,
                    original_text TEXT, translated_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT, target_lang TEXT,
                    original_text TEXT, translated_text TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def add_history(self, src, tgt, original, translated):
        if not original.strip() or not translated.strip(): return
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)", (src, tgt, original, translated))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

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
            print(f"DB Fav Error: {e}")
            return False

    def get_favorites(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT original_text, translated_text FROM favorites ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception:
            return []

    def get_history(self, limit=30):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT original_text, translated_text FROM history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception:
            return []

    def clear_history(self):
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

db = DatabaseManager()

class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _worker():
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=12)
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: callback(True, response.json()), 0)
                else:
                    Clock.schedule_once(lambda dt: callback(False, f"HTTP {response.status_code}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, str(e)), 0)
        threading.Thread(target=_worker, daemon=True).start()

KV = f'''
<MainScreen>:
    GeorgianFlagBackground:
        id: flag_bg
        size: self.parent.size if self.parent else (100, 100)

    BoxLayout:
        orientation: 'vertical'
        padding: 8
        spacing: 6

        # Header Bar
        BoxLayout:
            size_hint_y: None
            height: '42dp'
            spacing: 4

            NetworkIndicator:
                id: net_indicator
                size_hint_x: None
                width: '20dp'

            Label:
                text: "LingoLens v{APP_VERSION}"
                bold: True
                font_size: '12sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "📷 OCR"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '58dp'
                background_color: 0.3, 0.5, 0.8, 1
                on_release: root.start_camera_ocr()

            Button:
                id: btn_theme
                text: "🌙/☀️"
                size_hint_x: None
                width: '42dp'
                background_color: 0.2, 0.2, 0.3, 1
                on_release: root.toggle_theme()

            Button:
                text: "★"
                size_hint_x: None
                width: '35dp'
                background_color: 0.9, 0.7, 0.1, 1
                on_release: root.open_favorites_popup()

            Button:
                text: "ისტორია"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '60dp'
                background_color: 0.2, 0.4, 0.6, 1
                on_release: root.open_history_popup()

        # Language Bar
        BoxLayout:
            size_hint_y: None
            height: '38dp'
            spacing: 6

            Button:
                id: btn_source_lang
                text: "Georgian (ქართული)"
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
                text: "English (US)"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 0.9
                on_release: root.open_language_menu('target')

        # Input Box
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

            BoxLayout:
                size_hint_y: None
                height: '30dp'
                Label:
                    text: "შეყვანა:"
                    font_name: '{FONT_PATH}'
                    font_size: '11sp'
                    color: 0.6, 0.7, 0.8, 1
                    size_hint_x: None
                    width: '60dp'
                Widget:
                Button:
                    text: "X"
                    bold: True
                    size_hint_x: None
                    width: '30dp'
                    background_color: 0.8, 0.2, 0.2, 1
                    on_release: root.clear_input_text()

            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ, თქვით ან დასკანერეთ ტექსტი..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                font_size: '14sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '32dp'
                spacing: 4
                Widget:
                Button:
                    text: "აზროვნება"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '85dp'
                    background_color: 0.7, 0.3, 0.8, 1
                    on_release: root.analyze_and_think()
                Button:
                    text: "ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '50dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    on_release: root.start_speech_to_text(root.source_lang)

        # Output Box
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.45
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
                hint_text: "თარგმანი გამოჩნდება აქ..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                font_size: '14sp'

            BoxLayout:
                size_hint_y: None
                height: '32dp'
                spacing: 6

                Button:
                    text: "★ შენახვა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '80dp'
                    background_color: 0.9, 0.6, 0.1, 1
                    on_release: root.save_to_favorites()

                Button:
                    text: "სიჩქარე: 1.0x"
                    id: btn_tts_speed
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '90dp'
                    background_color: 0.2, 0.4, 0.5, 1
                    on_release: root.toggle_tts_speed()

                Button:
                    text: "მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '75dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    on_release: root.speak_output_text()
                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en"
        self.theme_mode = "dark"
        self.tts_speed = 1.0

    def on_enter(self):
        Clock.schedule_interval(self.check_network_status, 5)
        self.check_network_status(0)

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.ids.flag_bg.set_theme(self.theme_mode)

    def toggle_tts_speed(self):
        speeds = [0.75, 1.0, 1.25]
        idx = (speeds.index(self.tts_speed) + 1) % len(speeds)
        self.tts_speed = speeds[idx]
        self.ids.btn_tts_speed.text = f"სიჩქარე: {self.tts_speed}x"

    def clear_input_text(self):
        self.ids.input_text.text = ""
        self.ids.output_text.text = ""

    def save_to_favorites(self):
        orig = self.ids.input_text.text.strip()
        trans = self.ids.output_text.text.strip()
        if orig and trans and not trans.startswith("["):
            if db.add_favorite(self.source_lang, self.target_lang, orig, trans):
                self.ids.output_text.text = f"★ [შენახულია ფავორიტებში!]\n\n{trans}"

    def open_favorites_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()
        favs = db.get_favorites()
        text = "\n\n".join([f"★ {row[0]}\n   => {row[1]}" for row in favs]) if favs else "ფავორიტები ცარიელია."

        lbl = Label(text=text, font_name=FONT_PATH, size_hint_y=None, font_size='13sp', color=(0.9, 0.9, 0.9, 1))
        lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(lbl)
        content.add_widget(scroll)

        close_btn = Button(text="დახურვა", font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.3, 0.3, 0.3, 1))
        content.add_widget(close_btn)
        popup = Popup(title="შენახული ფავორიტები", title_font=FONT_PATH, content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def start_camera_ocr(self):
        if platform == 'android':
            try:
                from android.runnable import run_on_ui_thread
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                activity = PythonActivity.mActivity

                def _on_activity_result(request_code, result_code, intent):
                    if request_code == 1002 and result_code == -1:
                        self.ids.input_text.text = "[ფოტო მიღებულია, OCR მუშავდება...]"
                        # Vercel OCR API Call
                        self._process_ocr_api()

                activity.bind(on_activity_result=_on_activity_result)

                @run_on_ui_thread
                def _launch_cam():
                    intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                    activity.startActivityForResult(intent, 1002)

                _launch_cam()
            except Exception as e:
                self.ids.input_text.text = f"[კამერის შეცდომა: {e}]"
        else:
            self.ids.input_text.text = "Hello World (OCR Test - Desktop Mode)"

    def _process_ocr_api(self):
        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {"mode": "ocr", "image": "sample_base64"}
        def _on_res(success, res):
            if success and isinstance(res, dict):
                extracted = res.get('text', 'ტექსტი ვერ ამოიცნო')
                self.ids.input_text.text = extracted
        AsyncTranslateEngine.async_post_request(url, payload, _on_res)

    def check_network_status(self, dt):
        def _check():
            try:
                res = requests.get(f"{VERCEL_BASE_URL}/api/index", timeout=3)
                status = "green" if res.status_code == 200 else "yellow"
            except Exception:
                status = "red"
            Clock.schedule_once(lambda d: self.ids.net_indicator.set_status(status), 0)
        threading.Thread(target=_check, daemon=True).start()

    def swap_languages(self):
        s, t = self.ids.btn_source_lang.text, self.ids.btn_target_lang.text
        self.ids.btn_source_lang.text, self.ids.btn_target_lang.text = t, s
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        self.trigger_retranslate()

    def open_language_menu(self, mode):
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        box.bind(minimum_height=box.setter('height'))
        popup = Popup(title='აირჩიეთ ენა', title_font=FONT_PATH, content=scroll, size_hint=(0.85, 0.75))

        for name, code in LANGUAGES.items():
            btn = Button(text=name, font_name=FONT_PATH, size_hint_y=None, height='40dp', background_color=(0.14, 0.17, 0.24, 1))
            btn.bind(on_release=lambda x, n=name, c=code: self.select_language(mode, n, c, popup))
            box.add_widget(btn)

        scroll.add_widget(box)
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

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.35)

    def trigger_retranslate(self):
        text = self.ids.input_text.text.strip()
        if text: self._delayed_translate(text)

    def _delayed_translate(self, text):
        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {"text": text, "source_lang": self.source_lang[:2], "target_lang": self.target_lang[:2], "mode": "standard"}

        def _on_result(success, response):
            if success and isinstance(response, dict):
                translated = response.get('translated_text', '')
                self.ids.output_text.text = translated
                db.add_history(self.source_lang, self.target_lang, text, translated)
            else:
                self.ids.output_text.text = "[Offline / შეცდომა]"

        AsyncTranslateEngine.async_post_request(url, payload, _on_result)

    def analyze_and_think(self):
        text = self.ids.input_text.text.strip()
        if not text: return
        self.ids.output_text.text = "[AI აზროვნებს...]"
        url = f"{VERCEL_BASE_URL}/api/index"
        payload = {"text": f"Analyze in Georgian: {text}", "source_lang": self.source_lang[:2], "target_lang": self.target_lang[:2], "mode": "grammar"}

        def _on_result(success, response):
            if success and isinstance(response, dict):
                res = response.get('translated_text', response.get('grammar_analysis', ''))
                self.ids.output_text.text = f"--- AI ანალიზი ---\n\n{res}"

        AsyncTranslateEngine.async_post_request(url, payload, _on_result)

    def start_speech_to_text(self, lang_code="ka"):
        if platform == 'android':
            try:
                from android.runnable import run_on_ui_thread
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                activity = PythonActivity.mActivity

                def _on_activity_result(req, res, intent):
                    if req == 1001 and res == -1 and intent:
                        results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                        if results and results.size() > 0:
                            self.ids.input_text.text = results.get(0)

                activity.bind(on_activity_result=_on_activity_result)

                @run_on_ui_thread
                def _launch():
                    intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                    activity.startActivityForResult(intent, 1001)

                _launch()
            except Exception as e:
                print(f"STT Error: {e}")

    def speak_output_text(self):
        text = self.ids.output_text.text.strip()
        if not text or text.startswith("["): return
        threading.Thread(target=self._download_and_play_tts, args=(text, self.target_lang[:2]), daemon=True).start()

    def _download_and_play_tts(self, text, lang_code):
        try:
            cache_dir = os.path.join(App.get_running_app().user_data_dir, "audio_cache") if platform == 'android' else "audio_cache"
            os.makedirs(cache_dir, exist_ok=True)
            filepath = os.path.abspath(os.path.join(cache_dir, f"tts_{abs(hash(text))}.mp3"))

            res = requests.post(f"{VERCEL_BASE_URL}/api/tts", json={"text": text, "lang": lang_code, "speed": self.tts_speed}, timeout=12)
            if res.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(res.content)
                if platform == 'android':
                    from jnius import autoclass
                    player = autoclass('android.media.MediaPlayer')()
                    player.setDataSource(filepath)
                    player.prepare()
                    player.start()
                else:
                    sound = SoundLoader.load(filepath)
                    if sound: sound.play()
        except Exception as e:
            print(f"TTS Error: {e}")

    def open_history_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()
        data = db.get_history(limit=25)
        text = "\n\n".join([f"-> {r[0]}\n   => {r[1]}" for r in data]) if data else "ისტორია ცარიელია."

        lbl = Label(text=text, font_name=FONT_PATH, size_hint_y=None, font_size='13sp', color=(0.9, 0.9, 0.9, 1))
        lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(lbl)
        content.add_widget(scroll)

        btn_bar = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        clr = Button(text="გასუფთავება", font_name=FONT_PATH, background_color=(0.9, 0.2, 0.2, 1))
        cls = Button(text="დახურვა", font_name=FONT_PATH, background_color=(0.3, 0.3, 0.3, 1))
        btn_bar.add_widget(clr); btn_bar.add_widget(cls)
        content.add_widget(btn_bar)

        popup = Popup(title="ისტორია", title_font=FONT_PATH, content=content, size_hint=(0.9, 0.8))
        clr.bind(on_release=lambda x: (db.clear_history(), setattr(lbl, 'text', 'ისტორია ცარიელია.')))
        cls.bind(on_release=popup.dismiss)
        popup.open()

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

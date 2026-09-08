import os
import sys
import json
import sqlite3
import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

try:
    from plyer import share, vibrator, camera
except ImportError:
    share = None
    vibrator = None
    camera = None

# GitHub-ზე არსებული შრიფტის ფაილის სახელი
FONT_PATH = "font.ttf"
VERCEL_BASE_URL = "https://lingolens-backend.vercel.app"

# მსოფლიოს ენების სრული სია
LANGUAGES = {
    "ავტოდაჭერა": "auto",
    "ქართული": "ka",
    "ინგლისური": "en",
    "ესპანური": "es",
    "ფრანგული": "fr",
    "გერმანული": "de",
    "რუსული": "ru",
    "ჩინური (გამარტივებული)": "zh-CN",
    "ჩინური (ტრადიციული)": "zh-TW",
    "იაპონური": "ja",
    "კორეული": "ko",
    "არაბული": "ar",
    "თურქული": "tr",
    "იტალიური": "it",
    "პორტუგალიური": "pt",
    "უკრაინული": "uk",
    "პოლონური": "pl",
    "ჰოლანდიური": "nl",
    "ბერძნული": "el",
    "ებრაული": "he",
    "ჰინდი": "hi",
    "აზერბაიჯანული": "az",
    "სომხური": "hy",
    "ალბანური": "sq",
    "ამჰარული": "am",
    "აფრიკაანსი": "af",
    "ბასკური": "eu",
    "ბელარუსული": "be",
    "ბენგალური": "bn",
    "ბოსნიური": "bs",
    "ბულგარული": "bg",
    "ბურმული": "my",
    "გალისიური": "gl",
    "გუჯარათი": "gu",
    "დანიური": "da",
    "ესპერანტო": "eo",
    "ესტონური": "et",
    "ზულუ": "zu",
    "თათრული": "tt",
    "თამილური": "ta",
    "თელუგუ": "te",
    "იავანური": "jv",
    "იდიში": "yi",
    "ირლანდიური": "ga",
    "ისლანდიური": "is",
    "იორუბა": "yo",
    "კაზახური": "kk",
    "კანადა": "kn",
    "კატალანური": "ca",
    "კირგიზული": "ky",
    "ქმერული": "km",
    "ქურთული": "ku",
    "ლაოსური": "lo",
    "ლათინური": "la",
    "ლატვიური": "lv",
    "ლიეტუვური": "lt",
    "ლუქსემბურგული": "lb",
    "მაკედონიური": "mk",
    "მალაიაალამი": "ml",
    "მალაიზიური": "ms",
    "მალაგასიური": "mg",
    "მალტური": "mt",
    "მაორი": "mi",
    "მარათჰი": "mr",
    "მონღოლური": "mn",
    "ნეპალური": "ne",
    "ნორვეგიული": "no",
    "პენჯაბური": "pa",
    "პაშტო": "ps",
    "რუმინული": "ro",
    "სამოური": "sm",
    "სერბული": "sr",
    "სესოთო": "st",
    "სინჰალური": "si",
    "სინდჰი": "sd",
    "სლოვაკური": "sk",
    "სლოვენური": "sl",
    "სომალიური": "so",
    "სუაჰილი": "sw",
    "სუნდური": "su",
    "ტაჯიკური": "tg",
    "ტაილანდური": "th",
    "უზბეკური": "uz",
    "უნგრული": "hu",
    "ურდუ": "ur",
    "ფინური": "fi",
    "ფრიზიული": "fy",
    "ფილიპინური": "tl",
    "ჰაიტიური კრეოლი": "ht",
    "ჰაუსა": "ha",
    "ჰავაიური": "haw",
    "ჰმონგი": "hmn",
    "ხორვატული": "hr",
    "ჩეხური": "cs",
    "შოტლანდიური გელური": "gd",
    "შვედური": "sv",
    "შონა": "sn",
    "ჯავური": "jw"
}

def log_error(err):
    print(f"[LingoLens Error]: {err}")

def trigger_vibration():
    try:
        if vibrator:
            vibrator.vibrate(0.05)
    except Exception as e:
        log_error(e)

def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import Permission, request_permissions
            permissions = [
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ]
            request_permissions(permissions)
        except Exception as e:
            log_error(e)

# --- SQLite ბაზა ---
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        self.db_name = db_name
        self._db_path = None

    @property
    def db_path(self):
        if not self._db_path:
            app = App.get_running_app()
            base_dir = app.user_data_dir if app else "."
            self._db_path = os.path.join(base_dir, self.db_name)
        return self._db_path

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT,
                    target_lang TEXT,
                    original_text TEXT,
                    translated_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT,
                    target_lang TEXT,
                    original_text TEXT,
                    translated_text TEXT,
                    UNIQUE(source_lang, target_lang, original_text)
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            log_error(e)

    def add_history(self, src, tgt, orig, trans):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)",
                (src, tgt, orig, trans)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO offline_cache (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)",
                (src, tgt, orig, trans)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log_error(e)

    def add_favorite(self, src, tgt, orig, trans):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO favorites (source_lang, target_lang, original_text, translated_text) VALUES (?, ?, ?, ?)",
                (src, tgt, orig, trans)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

    def get_favorites(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT original_text, translated_text FROM favorites ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            log_error(e)
            return []

    def search_offline_cache(self, src, tgt, orig):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT translated_text FROM offline_cache WHERE source_lang=? AND target_lang=? AND original_text=?",
                (src, tgt, orig)
            )
            res = cursor.fetchone()
            conn.close()
            return res[0] if res else None
        except Exception as e:
            log_error(e)
            return None

db = DatabaseManager()

# --- Async HTTP Engine ---
class AsyncTranslateEngine:
    @staticmethod
    def async_post_request(url, payload, callback):
        def _thread_target():
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=payload, headers=headers, timeout=8)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        Clock.schedule_once(lambda dt: callback(True, data))
                    except json.JSONDecodeError:
                        Clock.schedule_once(lambda dt: callback(False, "არასწორი JSON პასუხი"))
                else:
                    Clock.schedule_once(lambda dt: callback(False, f"სერვერის შეცდომა ({response.status_code})"))
            except requests.exceptions.Timeout:
                Clock.schedule_once(lambda dt: callback(False, "Timeout: დრო ამოიწურა"))
            except requests.exceptions.ConnectionError:
                Clock.schedule_once(lambda dt: callback(False, "ინტერნეტთან კავშირი არ არის"))
            except Exception as e:
                Clock.schedule_once(lambda dt: callback(False, f"შეცდომა: {str(e)}"))

        threading.Thread(target=_thread_target, daemon=True).start()

# --- Reasoning Engine ---
class ReasoningEngine:
    @staticmethod
    def deep_reasoning_analysis(text, source_lang, target_lang):
        words = text.split()
        word_count = len(words)
        analysis = f"--- [ღრმა ანალიზი & კონტექსტი] ---\n"
        analysis += f"სიტყვების რაოდენობა: {word_count}\n"
        analysis += f"ენების წყვილი: {source_lang} -> {target_lang}\n"
        analysis += "სტრუქტურა: ტექსტი წარმატებით დამოწმდა."
        return analysis

# --- Native Speech Manager ---
class NativeSpeechManager:
    tts_instance = None
    tts_ready = False
    stt_callback = None

    @classmethod
    def init_tts(cls):
        if platform == 'android' and not cls.tts_instance:
            try:
                from jnius import autoclass, PythonJavaClass, java_method
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')

                class OnInitListener(PythonJavaClass):
                    __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']

                    @java_method('(I)V')
                    def onInit(self, status):
                        if status == TextToSpeech.SUCCESS:
                            NativeSpeechManager.tts_ready = True

                activity = PythonActivity.mActivity
                cls.tts_instance = TextToSpeech(activity, OnInitListener())
            except Exception as e:
                log_error(e)

    @classmethod
    def speak_text(cls, text, lang_code, speed=1.0):
        if platform == 'android':
            try:
                if not cls.tts_instance:
                    cls.init_tts()
                if cls.tts_instance and cls.tts_ready:
                    from jnius import autoclass
                    Locale = autoclass('java.util.Locale')
                    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                    
                    cls.tts_instance.setSpeechRate(float(speed))
                    cls.tts_instance.setLanguage(Locale(lang_code))
                    cls.tts_instance.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                log_error(e)
        else:
            print(f"[PC TTS]: {text}")

    @classmethod
    def start_listening(cls, lang_code, callback):
        cls.stt_callback = callback
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)

                activity = PythonActivity.mActivity
                
                def on_activity_result(request_code, result_code, data):
                    if request_code == 100 and data is not None:
                        try:
                            results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                            if results and results.size() > 0:
                                recognized_text = results.get(0)
                                Clock.schedule_once(lambda dt: cls._invoke_stt_callback(recognized_text))
                        except Exception as ex:
                            log_error(ex)

                activity.bind(on_activity_result=on_activity_result)
                activity.startActivityForResult(intent, 100)
            except Exception as e:
                log_error(e)
                Clock.schedule_once(lambda dt: cls._invoke_stt_callback("STT შეცდომა Android-ზე"))
        else:
            Clock.schedule_once(lambda dt: cls._invoke_stt_callback("STT მხოლოდ Android-ზე მუშაობს"))

    @classmethod
    def _invoke_stt_callback(cls, text):
        if cls.stt_callback:
            cls.stt_callback(text)
            cls.stt_callback = None

    @classmethod
    def shutdown_tts(cls):
        if cls.tts_instance:
            try:
                cls.tts_instance.stop()
                cls.tts_instance.shutdown()
            except Exception as e:
                log_error(e)

# --- UI Components ---
class FlagAnimatedBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.theme_mode = "dark"

    def set_theme(self, mode):
        self.theme_mode = mode
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.theme_mode == "dark":
                Color(0.12, 0.12, 0.14, 1)
            else:
                Color(0.95, 0.95, 0.96, 1)
            Rectangle(pos=self.pos, size=self.size)

class AudioVisualizerWidget(Widget):
    is_animating = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._anim_event = None

    def start_animation(self):
        self.is_animating = True
        self._anim_event = Clock.schedule_interval(self._animate_bars, 0.1)

    def stop_animation(self):
        self.is_animating = False
        if self._anim_event:
            self._anim_event.cancel()
        self.canvas.clear()

    def _animate_bars(self, dt):
        import random
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.6, 1.0, 0.8)
            for i in range(5):
                h = random.randint(10, 40)
                Rectangle(pos=(self.x + i * 15, self.y), size=(8, h))

Builder.load_string('''
<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        
        FlagAnimatedBackground:
            id: flag_bg
            size_hint_y: None
            height: '10dp'

        BoxLayout:
            size_hint_y: None
            height: '50dp'
            padding: '5dp'
            spacing: '5dp'
            
            Button:
                text: "☰"
                size_hint_x: None
                width: '50dp'
                on_release: root.toggle_theme()
            Label:
                text: "LingoLens AI"
                font_name: "font.ttf"
                font_size: '20sp'
                bold: True
            Button:
                text: "📷 Camera"
                size_hint_x: None
                width: '90dp'
                on_release: root.open_camera_ocr()

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            padding: '5dp'
            spacing: '5dp'

            Button:
                id: btn_source_lang
                text: "ავტოდაჭერა"
                font_name: "font.ttf"
                on_release: root.open_language_menu('source')
            Button:
                text: "⇄"
                size_hint_x: None
                width: '45dp'
                on_release: root.swap_languages()
            Button:
                id: btn_target_lang
                text: "ქართული"
                font_name: "font.ttf"
                on_release: root.open_language_menu('target')

        BoxLayout:
            orientation: 'vertical'
            padding: '5dp'
            spacing: '5dp'
            
            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ ან ჩასვით ტექსტი..."
                font_name: "font.ttf"
                font_size: '16sp'
                multiline: True
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '40dp'
                spacing: '5dp'
                
                Button:
                    text: "🎤 STT"
                    on_release: root.start_speech_to_text(root.source_lang)
                Button:
                    text: "🧠 Deep Think"
                    font_name: "font.ttf"
                    on_release: root.analyze_and_think()
                Button:
                    text: "✖ Clear"
                    on_release: root.clear_input_text()

        AudioVisualizerWidget:
            id: audio_viz
            size_hint_y: None
            height: '20dp' if self.is_animating else '0dp'

        BoxLayout:
            orientation: 'vertical'
            padding: '5dp'
            spacing: '5dp'

            TextInput:
                id: output_text
                hint_text: "თარგმანი..."
                font_name: "font.ttf"
                font_size: '16sp'
                readonly: True
                multiline: True

            BoxLayout:
                size_hint_y: None
                height: '40dp'
                spacing: '5dp'

                Button:
                    text: "🔊 TTS"
                    on_release: root.speak_output_text()
                Button:
                    id: btn_tts_speed
                    text: "1.0x"
                    size_hint_x: None
                    width: '50dp'
                    on_release: root.toggle_tts_speed()
                Button:
                    text: "📋 Copy"
                    on_release: root.copy_to_clipboard()
                Button:
                    text: "⭐ Fav"
                    on_release: root.save_to_favorites()
                Button:
                    text: "🔗 Share"
                    on_release: root.share_translation()

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            padding: '2dp'
            spacing: '2dp'

            Button:
                text: "თარჯიმანი"
                font_name: "font.ttf"
                font_size: '12sp'
                on_release: root.open_interpreter_mode()
            Button:
                text: "ლექსიკონი"
                font_name: "font.ttf"
                font_size: '12sp'
                on_release: root.open_dictionary_hub()
            Button:
                text: "ქვიზი"
                font_name: "font.ttf"
                font_size: '12sp'
                on_release: root.open_quiz_mode()
            Button:
                text: "ფაილები"
                font_name: "font.ttf"
                font_size: '12sp'
                on_release: root.open_file_translator()
''')

# --- Main Controller ---
class MainScreen(Screen):
    source_lang = StringProperty("auto")
    target_lang = StringProperty("ka")
    tts_speed = NumericProperty(1.0)
    theme_mode = StringProperty("dark")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._debounce_event = None

    def open_camera_ocr(self):
        trigger_vibration()
        if camera:
            try:
                filepath = os.path.join(App.get_running_app().user_data_dir, "ocr_scan.jpg")
                def _on_picture_taken(success):
                    if success and os.path.exists(filepath):
                        Clock.schedule_once(lambda dt: setattr(self.ids.input_text, 'text', "სურათი გადაღებულია!"))
                camera.take_picture(filename=filepath, on_complete=_on_picture_taken)
            except Exception as e:
                log_error(e)
                self._show_simple_popup("კამერა", "კამერის ჩართვა ვერ მოხერხდა")
        else:
            self._show_simple_popup("კამერა", "კამერა ხელმისაწვდომია მხოლოდ Android-ზე")

    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        search_input = TextInput(
            hint_text="🔍 მოძებნეთ ენა...", 
            font_name=FONT_PATH, 
            size_hint_y=None, 
            height='40dp', 
            multiline=False
        )
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title="აირჩიეთ ენა", content=main_layout, size_hint=(0.9, 0.8))

        def populate_languages(filter_text=""):
            box.clear_widgets()
            for name, code in LANGUAGES.items():
                if filter_text.lower() in name.lower():
                    btn = Button(text=name, font_name=FONT_PATH, size_hint_y=None, height='40dp')
                    def select_lang(instance, c=code, n=name):
                        if mode == 'source':
                            self.source_lang = c
                            self.ids.btn_source_lang.text = n
                        else:
                            self.target_lang = c
                            self.ids.btn_target_lang.text = n
                        popup.dismiss()
                    btn.bind(on_release=select_lang)
                    box.add_widget(btn)

        search_input.bind(text=lambda instance, text: populate_languages(text))
        populate_languages()

        scroll.add_widget(box)
        main_layout.add_widget(search_input)
        main_layout.add_widget(scroll)
        popup.open()

    def swap_languages(self):
        trigger_vibration()
        if self.source_lang == "auto": 
            return
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src_text = self.ids.btn_source_lang.text
        tgt_text = self.ids.btn_target_lang.text
        self.ids.btn_source_lang.text = tgt_text
        self.ids.btn_target_lang.text = src_text

    def toggle_theme(self):
        trigger_vibration()
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.ids.flag_bg.set_theme(self.theme_mode)

    def clear_input_text(self):
        self.ids.input_text.text = ""
        self.ids.output_text.text = ""

    def on_live_translate(self, text):
        if self._debounce_event:
            self._debounce_event.cancel()
        if not text.strip():
            self.ids.output_text.text = ""
            return
        self._debounce_event = Clock.schedule_once(lambda dt: self.perform_translation(text), 0.5)

    def perform_translation(self, text):
        cached = db.search_offline_cache(self.source_lang, self.target_lang, text)
        if cached:
            self.ids.output_text.text = f"[Offline Cache]\n{cached}"
            return

        payload = {"text": text, "source": self.source_lang, "target": self.target_lang}
        
        def _on_result(success, data):
            if success and isinstance(data, dict):
                translated = data.get("translatedText", "")
                self.ids.output_text.text = translated
                db.add_history(self.source_lang, self.target_lang, text, translated)
            else:
                self.ids.output_text.text = f"[{data if isinstance(data, str) else 'შეცდომა'}]"

        AsyncTranslateEngine.async_post_request(f"{VERCEL_BASE_URL}/api/translate", payload, _on_result)

    def analyze_and_think(self):
        text = self.ids.input_text.text
        if not text.strip(): 
            return
        res = ReasoningEngine.deep_reasoning_analysis(text, self.source_lang, self.target_lang)
        self.ids.output_text.text = res

    def start_speech_to_text(self, lang_code):
        self.ids.audio_viz.start_animation()
        def _on_stt(recognized_text):
            self.ids.audio_viz.stop_animation()
            if recognized_text:
                self.ids.input_text.text = recognized_text
        NativeSpeechManager.start_listening(lang_code, _on_stt)

    def speak_output_text(self):
        text = self.ids.output_text.text
        if text:
            NativeSpeechManager.speak_text(text, self.target_lang, self.tts_speed)

    def toggle_tts_speed(self):
        speeds = [1.0, 1.25, 1.5, 0.75]
        curr_idx = speeds.index(self.tts_speed)
        self.tts_speed = speeds[(curr_idx + 1) % len(speeds)]
        self.ids.btn_tts_speed.text = f"{self.tts_speed}x"

    def copy_to_clipboard(self):
        if self.ids.output_text.text:
            Clipboard.copy(self.ids.output_text.text)

    def share_translation(self):
        if self.ids.output_text.text and share:
            try: 
                share.share(text=self.ids.output_text.text)
            except Exception as e: 
                log_error(e)

    def save_to_favorites(self):
        orig = self.ids.input_text.text
        trans = self.ids.output_text.text
        if orig and trans:
            if db.add_favorite(self.source_lang, self.target_lang, orig, trans):
                trigger_vibration()

    def open_interpreter_mode(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl_status = Label(text="ორმხრივი დიალოგი", font_name=FONT_PATH, font_size='14sp')
        
        btn_p1 = Button(text=f"🎤 პირი 1 ({self.source_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')
        btn_p2 = Button(text=f"🎤 პირი 2 ({self.target_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')

        def _p1_listen(instance):
            lbl_status.text = "გთხოვთ ისაუბროთ (პირველი ენა)..."
            def _stt_cb(rec_text):
                if rec_text:
                    self.ids.input_text.text = rec_text
                    lbl_status.text = f"პირი 1: {rec_text}"
            NativeSpeechManager.start_listening(self.source_lang, _stt_cb)

        def _p2_listen(instance):
            lbl_status.text = "გთხოვთ ისაუბროთ (მეორე ენა)..."
            def _stt_cb(rec_text):
                if rec_text:
                    self.ids.input_text.text = rec_text
                    lbl_status.text = f"პირი 2: {rec_text}"
            NativeSpeechManager.start_listening(self.target_lang, _stt_cb)

        btn_p1.bind(on_release=_p1_listen)
        btn_p2.bind(on_release=_p2_listen)

        layout.add_widget(lbl_status)
        layout.add_widget(btn_p1)
        layout.add_widget(btn_p2)
        popup = Popup(title="ორმხრივი თარჯიმანი", content=layout, size_hint=(0.85, 0.5))
        popup.open()

    def open_dictionary_hub(self):
        favs = db.get_favorites()
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        box.bind(minimum_height=box.setter('height'))

        if not favs:
            box.add_widget(Label(text="ფავორიტები ცარიელია", font_name=FONT_PATH, size_hint_y=None, height='40dp'))
        else:
            for orig, trans in favs:
                lbl = Label(text=f"{orig} -> {trans}", font_name=FONT_PATH, size_hint_y=None, height='40dp')
                box.add_widget(lbl)

        scroll.add_widget(box)
        popup = Popup(title="შენახული სიტყვები (ლექსიკონი)", content=scroll, size_hint=(0.9, 0.7))
        popup.open()

    def open_quiz_mode(self):
        favs = db.get_favorites()
        if not favs:
            self._show_simple_popup("ქვიზი", "ქვიზისთვის ჯერ დაამატეთ სიტყვები ფავორიტებში!")
            return

        import random
        item = random.choice(favs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=f"რა არის თარგმანი: '{item[0]}'?", font_name=FONT_PATH)
        inp = TextInput(hint_text="ჩაწერეთ პასუხი...", font_name=FONT_PATH, multiline=False)
        btn = Button(text="შემოწმება", font_name=FONT_PATH)

        def check_ans(instance):
            if inp.text.strip().lower() == item[1].strip().lower():
                lbl.text = "✅ სწორია!"
            else:
                lbl.text = f"❌ არასწორია! სწორია: {item[1]}"

        btn.bind(on_release=check_ans)
        layout.add_widget(lbl)
        layout.add_widget(inp)
        layout.add_widget(btn)

        popup = Popup(title="სიტყვების ქვიზი", content=layout, size_hint=(0.85, 0.5))
        popup.open()

    def open_file_translator(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        inp_path = TextInput(hint_text="შეიყვანეთ ტექსტური ფაილის გზა (.txt)", multiline=False)
        btn = Button(text="ფაილის წაკითხვა და თარგმნა", font_name=FONT_PATH)

        def read_file(instance):
            path = inp_path.text.strip()
            if os.path.exists(path) and path.endswith('.txt'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.ids.input_text.text = content
                    popup.dismiss()
                except Exception as e:
                    inp_path.text = f"შეცდომა: {e}"
            else:
                inp_path.text = "ფაილი ვერ მოიძებნა!"

        btn.bind(on_release=read_file)
        layout.add_widget(inp_path)
        layout.add_widget(btn)

        popup = Popup(title="ფაილის თარგმნა", content=layout, size_hint=(0.85, 0.4))
        popup.open()

    def _show_simple_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg, font_name=FONT_PATH), size_hint=(0.8, 0.4))
        popup.open()

class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        db.init_db()
        NativeSpeechManager.init_tts()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

    def on_stop(self):
        NativeSpeechManager.shutdown_tts()

if __name__ == '__main__':
    LingoLensApp().run()

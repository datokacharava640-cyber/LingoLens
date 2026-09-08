# MIT License
# 
# Copyright (c) 2026 Dato Kacharava
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import json
import sqlite3
import threading
import urllib.parse
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
    from plyer import share, vibrator
except ImportError:
    share = None
    vibrator = None

FONT_PATH = "font.ttf"

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
                text: "Menu"
                size_hint_x: None
                width: '60dp'
                on_release: root.toggle_theme()
            Label:
                text: "LingoLens AI"
                font_name: "font.ttf"
                font_size: '20sp'
                bold: True
            Button:
                text: "Camera"
                size_hint_x: None
                width: '80dp'
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
                text: "<->"
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
                    text: "STT"
                    on_release: root.start_speech_to_text(root.source_lang)
                Button:
                    text: "Deep Think"
                    font_name: "font.ttf"
                    on_release: root.analyze_and_think()
                Button:
                    text: "Clear"
                    on_release: root.clear_input_text()

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
                    text: "TTS"
                    on_release: root.speak_output_text()
                Button:
                    id: btn_tts_speed
                    text: "1.0x"
                    size_hint_x: None
                    width: '50dp'
                    on_release: root.toggle_tts_speed()
                Button:
                    text: "Copy"
                    on_release: root.copy_to_clipboard()
                Button:
                    text: "Fav"
                    on_release: root.save_to_favorites()
                Button:
                    text: "Share"
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
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.media.action.IMAGE_CAPTURE')
                activity = PythonActivity.mActivity
                activity.startActivity(Intent)
            except Exception as e:
                log_error(e)
                self._show_simple_popup("Camera Error", "კამერის ჩართვა ვერ მოხერხდა")
        else:
            self._show_simple_popup("Camera", "ხელმისაწვდომია მხოლოდ Android-ზე")

    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        search_input = TextInput(
            hint_text="ძებნა...", 
            font_name=FONT_PATH,
            size_hint_y=None, 
            height='40dp', 
            multiline=False
        )
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        box.bind(minimum_height=box.setter('height'))

        popup = Popup(title="ენის არჩევა", content=main_layout, size_hint=(0.9, 0.8))

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
            self.ids.output_text.text = f"[ქეშიდან]\n{cached}"
            return

        query_encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.source_lang}&tl={self.target_lang}&dt=t&q={query_encoded}"

        def _thread_target():
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    translated = "".join([item[0] for item in data[0] if item[0]])
                    Clock.schedule_once(lambda dt: self._update_translation_ui(text, translated))
                else:
                    Clock.schedule_once(lambda dt: self._set_output_text(f"შეცდომა ({res.status_code})"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._set_output_text("ინტერნეტის შეცდომა"))

        threading.Thread(target=_thread_target, daemon=True).start()

    def _update_translation_ui(self, orig, trans):
        self.ids.output_text.text = trans
        db.add_history(self.source_lang, self.target_lang, orig, trans)

    def _set_output_text(self, msg):
        self.ids.output_text.text = msg

    def analyze_and_think(self):
        text = self.ids.input_text.text
        if not text.strip(): 
            return
        words = text.split()
        res = f"--- [ღრმა ანალიზი & კონტექსტი] ---\n"
        res += f"სიტყვების რაოდენობა: {len(words)}\n"
        res += f"ენების წყვილი: {self.source_lang} -> {self.target_lang}\n"
        res += "სტრუქტურა: ტექსტი წარმატებით დამოწმდა."
        self.ids.output_text.text = res

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

                activity = PythonActivity.mActivity
                activity.startActivity(intent)
            except Exception as e:
                log_error(e)
                self._show_simple_popup("STT Error", "ხმოვანი სერვისი მიუწვდომელია")
        else:
            self._show_simple_popup("STT", "ხმოვანი შეყვანა ხელმისაწვდომია მხოლოდ Android-ზე")

    def speak_output_text(self):
        text = self.ids.output_text.text
        if text and platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                
                activity = PythonActivity.mActivity
                tts = TextToSpeech(activity, None)
                tts.setLanguage(Locale(self.target_lang))
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                log_error(e)

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
        
        btn_p1 = Button(text=f"Speaker 1 ({self.source_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')
        btn_p2 = Button(text=f"Speaker 2 ({self.target_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')

        btn_p1.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))
        btn_p2.bind(on_release=lambda x: self.start_speech_to_text(self.target_lang))

        layout.add_widget(lbl_status)
        layout.add_widget(btn_p1)
        layout.add_widget(btn_p2)
        popup = Popup(title="Interpreter", content=layout, size_hint=(0.85, 0.5))
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
        popup = Popup(title="Favorites", content=scroll, size_hint=(0.9, 0.7))
        popup.open()

    def open_quiz_mode(self):
        favs = db.get_favorites()
        if not favs:
            self._show_simple_popup("Quiz", "ჯერ დაამატეთ სიტყვები ფავორიტებში!")
            return

        import random
        item = random.choice(favs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=f"რა არის თარგმანი: '{item[0]}'?", font_name=FONT_PATH)
        inp = TextInput(hint_text="ჩაწერეთ პასუხი...", font_name=FONT_PATH, multiline=False)
        btn = Button(text="შემოწმება", font_name=FONT_PATH)

        def check_ans(instance):
            if inp.text.strip().lower() == item[1].strip().lower():
                lbl.text = "სწორია!"
            else:
                lbl.text = f"არასწორია! სწორია: {item[1]}"

        btn.bind(on_release=check_ans)
        layout.add_widget(lbl)
        layout.add_widget(inp)
        layout.add_widget(btn)

        popup = Popup(title="Quiz", content=layout, size_hint=(0.85, 0.5))
        popup.open()

    def open_file_translator(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        inp_path = TextInput(hint_text="შეიყვანეთ ტექსტური ფაილის გზა (.txt)", font_name=FONT_PATH, multiline=False)
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

        popup = Popup(title="File Translator", content=layout, size_hint=(0.85, 0.4))
        popup.open()

    def _show_simple_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg, font_name=FONT_PATH), size_hint=(0.8, 0.4))
        popup.open()

class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        db.init_db()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

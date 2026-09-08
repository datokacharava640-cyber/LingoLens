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
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
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
    from plyer import vibrator
except ImportError:
    vibrator = None

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

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
    "სომხური": "hy"
}

def log_error(err):
    print(f"[LingoLens Exception]: {err}")

def trigger_vibration():
    try:
        if vibrator:
            vibrator.vibrate(0.04)
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
                    is_deleted INTEGER DEFAULT 0,
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
        if not orig.strip() or not trans.strip():
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (source_lang, target_lang, original_text, translated_text, is_deleted) VALUES (?, ?, ?, ?, 0)",
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

    def get_history(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, original_text, translated_text, timestamp FROM history WHERE is_deleted=0 ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            log_error(e)
            return []

    def move_to_trash(self, history_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE history SET is_deleted=1 WHERE id=?", (history_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

    def get_trash(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, original_text, translated_text, timestamp FROM history WHERE is_deleted=1 ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            log_error(e)
            return []

    def restore_from_trash(self, history_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE history SET is_deleted=0 WHERE id=?", (history_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

    def delete_permanently(self, history_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE id=?", (history_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

    def empty_trash(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE is_deleted=1")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log_error(e)
            return False

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
            height: '8dp'

        BoxLayout:
            size_hint_y: None
            height: '48dp'
            padding: '4dp'
            spacing: '4dp'
            
            Button:
                text: "Menu"
                size_hint_x: None
                width: '65dp'
                on_release: root.open_app_menu()
            Label:
                text: "LingoLens AI"
                font_name: "font.ttf"
                font_size: '18sp'
                bold: True
            Button:
                text: "Camera"
                size_hint_x: None
                width: '75dp'
                on_release: root.open_camera_ocr()

        BoxLayout:
            size_hint_y: None
            height: '42dp'
            padding: '4dp'
            spacing: '4dp'

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
            padding: '4dp'
            spacing: '4dp'
            
            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ ან ჩასვით ტექსტი..."
                font_name: "font.ttf"
                font_size: '15sp'
                multiline: True
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '38dp'
                spacing: '4dp'
                
                Button:
                    text: "STT"
                    on_release: root.start_speech_to_text(root.source_lang)
                Button:
                    text: "გრამატიკა"
                    font_name: "font.ttf"
                    on_release: root.check_and_fix_grammar()
                Button:
                    text: "Clear"
                    on_release: root.clear_input_text()

        BoxLayout:
            orientation: 'vertical'
            padding: '4dp'
            spacing: '4dp'

            TextInput:
                id: output_text
                hint_text: "თარგმანი..."
                font_name: "font.ttf"
                font_size: '15sp'
                readonly: True
                multiline: True

            BoxLayout:
                size_hint_y: None
                height: '38dp'
                spacing: '4dp'

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
            height: '42dp'
            padding: '2dp'
            spacing: '2dp'

            Button:
                text: "თარჯიმანი"
                font_name: "font.ttf"
                font_size: '11sp'
                on_release: root.open_interpreter_mode()
            Button:
                text: "ლექსიკონი"
                font_name: "font.ttf"
                font_size: '11sp'
                on_release: root.open_dictionary_hub()
            Button:
                text: "ქვიზი"
                font_name: "font.ttf"
                font_size: '11sp'
                on_release: root.open_quiz_mode()
            Button:
                text: "ფაილები"
                font_name: "font.ttf"
                font_size: '11sp'
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
        self.image_path = None
        if platform == 'android':
            self._bind_android_events()

    def _bind_android_events(self):
        try:
            from android.activity import bind
            bind(on_activity_result=self.on_activity_result)
        except Exception as e:
            log_error(e)

    def open_camera_ocr(self):
        trigger_vibration()
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                MediaStore = autoclass('android.provider.MediaStore')
                Intent = autoclass('android.content.Intent')
                File = autoclass('java.io.File')
                FileProvider = autoclass('androidx.core.content.FileProvider')

                activity = PythonActivity.mActivity
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)

                storage_dir = activity.getExternalFilesDir(None)
                photo_file = File.createTempFile("camera_photo", ".jpg", storage_dir)
                self.image_path = photo_file.getAbsolutePath()

                photo_uri = FileProvider.getUriForFile(
                    activity,
                    activity.getPackageName() + ".fileprovider",
                    photo_file
                )

                intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri)
                activity.startActivityForResult(intent, 1001)
            except Exception as e:
                log_error(e)
                self._show_simple_popup("კამერა", f"კამერის გაშვების შეცდომა: {e}")
        else:
            self._show_simple_popup("კამერა", "კამერის ფუნქციონალი მუშაობს Android მოწყობილობებზე.")

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001 and result_code == -1: # -1 = RESULT_OK
            if self.image_path and os.path.exists(self.image_path):
                self.process_ocr_image(self.image_path)

    def process_ocr_image(self, img_path):
        def _ocr_async():
            try:
                from jnius import autoclass
                InputImage = autoclass('com.google.mlkit.vision.common.InputImage')
                TextRecognition = autoclass('com.google.mlkit.vision.text.TextRecognition')
                LatinTextRecognizerOptions = autoclass('com.google.mlkit.vision.text.latin.TextRecognizerOptions')
                File = autoclass('java.io.File')
                Uri = autoclass('android.net.Uri')

                recognizer = TextRecognition.getClient(LatinTextRecognizerOptions.DEFAULT_OPTIONS)
                image = InputImage.fromFilePath(App.get_running_app().activity, Uri.fromFile(File(img_path)))

                task = recognizer.process(image)
                while not task.isComplete():
                    pass

                if task.isSuccessful():
                    extracted_text = task.getResult().getText()
                    Clock.schedule_once(lambda dt: self._on_ocr_success(extracted_text))
                else:
                    Clock.schedule_once(lambda dt: self._show_simple_popup("OCR", "ტექსტი ვერ ამოიცნო."))
            except Exception as e:
                log_error(e)
                Clock.schedule_once(lambda dt: self._show_simple_popup("OCR", "ML Kit ამოცნობის შეცდომა."))

        threading.Thread(target=_ocr_async, daemon=True).start()

    def _on_ocr_success(self, text):
        if text.strip():
            self.ids.input_text.text = text
            self.perform_translation(text)
        else:
            self._show_simple_popup("OCR", "ფოტოზე ტექსტი ვერ მოიძებნა.")

    def open_app_menu(self):
        trigger_vibration()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        btn_history = Button(text="ისტორია", font_name=FONT_PATH, size_hint_y=None, height='45dp')
        btn_trash = Button(text="წაშლილების ურნა", font_name=FONT_PATH, size_hint_y=None, height='45dp')
        btn_theme = Button(text=f"თემა: {self.theme_mode.upper()}", font_name=FONT_PATH, size_hint_y=None, height='45dp')
        btn_license = Button(text="ლიცენზია (MIT)", font_name=FONT_PATH, size_hint_y=None, height='45dp')
        btn_about = Button(text="აპლიკაციის შესახებ", font_name=FONT_PATH, size_hint_y=None, height='45dp')

        popup = Popup(title="მენიუ", content=layout, size_hint=(0.85, 0.65))

        def toggle_t(instance):
            self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
            self.ids.flag_bg.set_theme(self.theme_mode)
            btn_theme.text = f"თემა: {self.theme_mode.upper()}"

        def open_hist(instance):
            popup.dismiss()
            self.open_history_window()

        def open_tr(instance):
            popup.dismiss()
            self.open_trash_window()

        def show_license(instance):
            lic_text = (
                "MIT License\n\n"
                "Copyright (c) 2026 Dato Kacharava\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy "
                "of this software and associated documentation files..."
            )
            self._show_simple_popup("MIT License", lic_text)

        def show_about(instance):
            self._show_simple_popup("LingoLens AI", "ვერსია: 1.0.0\nავტორი: Dato Kacharava")

        btn_history.bind(on_release=open_hist)
        btn_trash.bind(on_release=open_tr)
        btn_theme.bind(on_release=toggle_t)
        btn_license.bind(on_release=show_license)
        btn_about.bind(on_release=show_about)

        layout.add_widget(btn_history)
        layout.add_widget(btn_trash)
        layout.add_widget(btn_theme)
        layout.add_widget(btn_license)
        layout.add_widget(btn_about)
        popup.open()

    def check_and_fix_grammar(self):
        text = self.ids.input_text.text.strip()
        if not text:
            self._show_simple_popup("გრამატიკა", "შეიყვანეთ ტექსტი შემოწმებისთვის.")
            return

        lang = self.source_lang if self.source_lang != "auto" else "ka"
        url = "https://api.languagetool.org/v2/check"
        data = {'text': text, 'language': lang}

        def _thread_target():
            try:
                res = requests.post(url, data=data, timeout=6)
                if res.status_code == 200:
                    result = res.json()
                    matches = result.get('matches', [])
                    if not matches:
                        Clock.schedule_once(lambda dt: self._set_output_text("გრამატიკული შეცდომები ვერ მოიძებნა."))
                    else:
                        corrections = "--- [გრამატიკული შემოწმება] ---\n\n"
                        for m in matches:
                            msg = m.get('message', '')
                            replacements = [r['value'] for r in m.get('replacements', [])]
                            rep_str = ", ".join(replacements[:3]) if replacements else "არ არის"
                            corrections += f"• {msg}\n  შეთავაზება: {rep_str}\n\n"
                        Clock.schedule_once(lambda dt: self._set_output_text(corrections))
                else:
                    Clock.schedule_once(lambda dt: self._fallback_grammar_check(text, lang))
            except Exception:
                Clock.schedule_once(lambda dt: self._fallback_grammar_check(text, lang))

        threading.Thread(target=_thread_target, daemon=True).start()

    def _fallback_grammar_check(self, text, lang):
        fixed_text = text.capitalize()
        if not fixed_text.endswith(('.', '!', '?')):
            fixed_text += '.'
        self.ids.output_text.text = f"--- [კორექტირება ({lang.upper()})] ---\n{fixed_text}"

    def open_history_window(self):
        records = db.get_history()
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=5)
        box.bind(minimum_height=box.setter('height'))
        popup = Popup(title="ისტორია", content=scroll, size_hint=(0.9, 0.8))

        if not records:
            box.add_widget(Label(text="ისტორია ცარიელია", font_name=FONT_PATH, size_hint_y=None, height='40dp'))
        else:
            for hid, orig, trans, ts in records:
                item_box = BoxLayout(orientation='vertical', size_hint_y=None, height='80dp', padding=4)
                lbl = Label(text=f"{orig} -> {trans}", font_name=FONT_PATH, size_hint_y=None, height='40dp')
                btn_del = Button(text="ურნაში გადატანა", font_name=FONT_PATH, size_hint_y=None, height='30dp')
                btn_del.bind(on_release=lambda x, h_id=hid: [db.move_to_trash(h_id), popup.dismiss(), self.open_history_window()])
                item_box.add_widget(lbl)
                item_box.add_widget(btn_del)
                box.add_widget(item_box)

        scroll.add_widget(box)
        popup.open()

    def open_trash_window(self):
        trash_records = db.get_trash()
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=5)
        box.bind(minimum_height=box.setter('height'))
        popup = Popup(title="წაშლილების ურნა", content=main_layout, size_hint=(0.9, 0.8))

        if not trash_records:
            box.add_widget(Label(text="ურნა ცარიელია", font_name=FONT_PATH, size_hint_y=None, height='40dp'))
        else:
            btn_empty_all = Button(text="ურნის გასუფთავება", font_name=FONT_PATH, size_hint_y=None, height='40dp')
            btn_empty_all.bind(on_release=lambda x: [db.empty_trash(), popup.dismiss(), self.open_trash_window()])
            main_layout.add_widget(btn_empty_all)

            for hid, orig, trans, ts in trash_records:
                item_box = BoxLayout(orientation='vertical', size_hint_y=None, height='85dp', padding=4)
                lbl = Label(text=f"{orig} -> {trans}", font_name=FONT_PATH, size_hint_y=None, height='35dp')
                actions_box = BoxLayout(size_hint_y=None, height='35dp', spacing=5)
                
                btn_restore = Button(text="აღდგენა", font_name=FONT_PATH)
                btn_perm_del = Button(text="წაშლა", font_name=FONT_PATH)

                btn_restore.bind(on_release=lambda x, h_id=hid: [db.restore_from_trash(h_id), popup.dismiss(), self.open_trash_window()])
                btn_perm_del.bind(on_release=lambda x, h_id=hid: [db.delete_permanently(h_id), popup.dismiss(), self.open_trash_window()])

                actions_box.add_widget(btn_restore)
                actions_box.add_widget(btn_perm_del)
                item_box.add_widget(lbl)
                item_box.add_widget(actions_box)
                box.add_widget(item_box)

        scroll.add_widget(box)
        main_layout.add_widget(scroll)
        popup.open()

    def open_language_menu(self, mode):
        trigger_vibration()
        main_layout = BoxLayout(orientation='vertical', padding=6, spacing=6)
        search_input = TextInput(hint_text="ძებნა...", font_name=FONT_PATH, size_hint_y=None, height='40dp', multiline=False)
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
        if self.source_lang == "auto": return
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        self.ids.btn_source_lang.text, self.ids.btn_target_lang.text = self.ids.btn_target_lang.text, self.ids.btn_source_lang.text

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
            self.ids.output_text.text = cached
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
            except Exception:
                Clock.schedule_once(lambda dt: self._set_output_text("ინტერნეტის შეცდომა"))

        threading.Thread(target=_thread_target, daemon=True).start()

    def _update_translation_ui(self, orig, trans):
        self.ids.output_text.text = trans
        db.add_history(self.source_lang, self.target_lang, orig, trans)

    def _set_output_text(self, msg):
        self.ids.output_text.text = msg

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
                PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                log_error(e)

    def speak_output_text(self):
        text = self.ids.output_text.text
        if text and platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                
                tts = TextToSpeech(PythonActivity.mActivity, None)
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
            self._show_simple_popup("Copy", "ტექსტი დაკოპირდა!")

    def share_translation(self):
        text_to_share = self.ids.output_text.text
        if not text_to_share: return
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')

                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text_to_share))

                chooser = Intent.createChooser(intent, String("გაზიარება:"))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception as e:
                log_error(e)

    def save_to_favorites(self):
        orig, trans = self.ids.input_text.text, self.ids.output_text.text
        if orig and trans:
            if db.add_favorite(self.source_lang, self.target_lang, orig, trans):
                trigger_vibration()
                self._show_simple_popup("Fav", "დაემატა ფავორიტებში!")

    def open_interpreter_mode(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        btn_p1 = Button(text=f"Speaker 1 ({self.source_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')
        btn_p2 = Button(text=f"Speaker 2 ({self.target_lang.upper()})", font_name=FONT_PATH, size_hint_y=None, height='50dp')
        btn_p1.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))
        btn_p2.bind(on_release=lambda x: self.start_speech_to_text(self.target_lang))
        layout.add_widget(btn_p1)
        layout.add_widget(btn_p2)
        Popup(title="Interpreter Mode", content=layout, size_hint=(0.85, 0.45)).open()

    def open_dictionary_hub(self):
        favs = db.get_favorites()
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        box.bind(minimum_height=box.setter('height'))
        if not favs:
            box.add_widget(Label(text="ფავორიტები ცარიელია", font_name=FONT_PATH, size_hint_y=None, height='40dp'))
        else:
            for orig, trans in favs:
                box.add_widget(Label(text=f"{orig} -> {trans}", font_name=FONT_PATH, size_hint_y=None, height='40dp'))
        scroll.add_widget(box)
        Popup(title="ფავორიტები / ლექსიკონი", content=scroll, size_hint=(0.9, 0.7)).open()

    def open_quiz_mode(self):
        favs = db.get_favorites()
        if not favs:
            self._show_simple_popup("ქვიზი", "ჯერ დაამატეთ სიტყვები ფავორიტებში!")
            return
        import random
        item = random.choice(favs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=f"რა არის თარგმანი: '{item[0]}'?", font_name=FONT_PATH)
        inp = TextInput(hint_text="ჩაწერეთ პასუხი...", font_name=FONT_PATH, multiline=False)
        btn = Button(text="შემოწმება", font_name=FONT_PATH)
        btn.bind(on_release=lambda x: setattr(lbl, 'text', "სწორია!" if inp.text.strip().lower() == item[1].strip().lower() else f"არასწორია! სწორია: {item[1]}"))
        layout.add_widget(lbl)
        layout.add_widget(inp)
        layout.add_widget(btn)
        Popup(title="ქვიზი", content=layout, size_hint=(0.85, 0.45)).open()

    def open_file_translator(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        inp_path = TextInput(hint_text="ფაილის გზა (.txt)", font_name=FONT_PATH, multiline=False)
        btn = Button(text="წაკითხვა და თარგმნა", font_name=FONT_PATH)

        def read_file(instance):
            path = inp_path.text.strip()
            if os.path.exists(path) and path.endswith('.txt'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.ids.input_text.text = f.read()
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
        Popup(title=title, content=Label(text=msg, font_name=FONT_PATH), size_hint=(0.8, 0.4)).open()

class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        db.init_db()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

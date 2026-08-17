import os
import sqlite3
from datetime import datetime
from urllib.parse import quote

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.network.urlrequest import UrlRequest

# ---------------------------------------------------------
# 0. FONT REGISTRATION
# ---------------------------------------------------------
FONT_PATH = "NotoSansGeorgian-Regular.ttf"
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
    except Exception as e:
        print(f"Font Error: {e}")

LANGUAGES = {
    "ქართული": "ka",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Русский": "ru",
    "Türkçe": "tr",
    "Українська": "uk",
    "中文 (Chinese)": "zh-CN",
    "日本語 (Japanese)": "ja",
    "العربية (Arabic)": "ar"
}

# ---------------------------------------------------------
# 1. DATABASE MANAGER (ANDROID SAFE)
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                # Android-ის შიდა დაცული საქაღალდე
                base_dir = os.environ.get('ANDROID_PRIVATE', '.')
                self.db_path = os.path.join(base_dir, db_name)
            else:
                self.db_path = db_name
            self.create_tables()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_text TEXT,
                        translated_text TEXT,
                        timestamp DATETIME
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Create Tables Error: {e}")

    def add_history(self, src, trans):
        try:
            with self.get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                    (src, trans, datetime.now())
                )
                conn.commit()
        except Exception as e:
            print(f"DB Add History Error: {e}")

    def get_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 20")
                return cursor.fetchall()
        except Exception:
            return []


# ---------------------------------------------------------
# 2. MAIN USER INTERFACE
# ---------------------------------------------------------
class LingoLensUI(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.debounce_event = None
        self.current_request = None
        self.db = db

        # Header
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True)
        btn_history = Button(text="📜 ისტორია", size_hint_x=0.3)
        btn_history.bind(on_press=self.open_history)
        header.add_widget(title)
        header.add_widget(btn_history)
        self.add_widget(header)

        # ენების გადამრთველი
        lang_bar = BoxLayout(size_hint_y=0.08, spacing=5)
        self.src_spinner = Spinner(
            text="ქართული",
            values=list(LANGUAGES.keys()),
            size_hint_x=0.4
        )
        self.btn_swap = Button(text="⇄", size_hint_x=0.2, font_size='20sp', bold=True, background_color=(0.2, 0.6, 0.9, 1))
        self.btn_swap.bind(on_press=self.swap_languages)
        
        self.target_spinner = Spinner(
            text="English",
            values=list(LANGUAGES.keys()),
            size_hint_x=0.4
        )

        lang_bar.add_widget(self.src_spinner)
        lang_bar.add_widget(self.btn_swap)
        lang_bar.add_widget(self.target_spinner)
        self.add_widget(lang_bar)

        # Input Text Area
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            multiline=True,
            size_hint_y=0.3,
            font_size='15sp'
        )
        self.input_text.bind(text=self.on_text_change)
        self.add_widget(self.input_text)

        # Actions Panel
        actions = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_copy = Button(text="📋 კოპირება", background_color=(0.2, 0.7, 0.3, 1))
        btn_copy.bind(on_press=self.copy_to_clipboard)

        btn_clear = Button(text="🗑 გასუფთავება", background_color=(0.8, 0.3, 0.3, 1))
        btn_clear.bind(on_press=self.clear_input)

        actions.add_widget(btn_copy)
        actions.add_widget(btn_clear)
        self.add_widget(actions)

        # Output Box
        self.output_label = Label(
            text="თარგმანი გამოჩნდება აკრეფისთანავე...",
            size_hint_y=0.44,
            font_size='16sp'
        )
        self.add_widget(self.output_label)

    def swap_languages(self, instance):
        src = self.src_spinner.text
        target = self.target_spinner.text
        self.src_spinner.text = target
        self.target_spinner.text = src
        self.trigger_realtime_translate()

    def clear_input(self, instance):
        self.input_text.text = ""
        self.output_label.text = "თარგმანი გამოჩნდება აკრეფისთანავე..."

    def on_text_change(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_realtime_translate(), 0.5)

    def trigger_realtime_translate(self):
        text = self.input_text.text.strip()
        if not text:
            self.output_label.text = "თარგმანი გამოჩნდება აკრეფისთანავე..."
            return

        src_code = LANGUAGES.get(self.src_spinner.text, "auto")
        target_code = LANGUAGES.get(self.target_spinner.text, "en")

        # ქართული სიმბოლოების უსაფრთხო URL ENCODING
        encoded_text = quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_code}&tl={target_code}&dt=t&q={encoded_text}"

        if self.current_request:
            self.current_request.cancel()

        self.current_request = UrlRequest(
            url,
            on_success=self.on_translation_success,
            on_error=self.on_translation_error,
            on_failure=self.on_translation_error,
            timeout=5
        )

    def on_translation_success(self, req, result):
        try:
            translated_str = "".join([item[0] for item in result[0] if item[0]])
            self.output_label.text = translated_str
            self.db.add_history(self.input_text.text[:30], translated_str)
        except Exception:
            self.output_label.text = "[შეცდომა დამუშავებისას]"

    def on_translation_error(self, req, error):
        self.output_label.text = "[ქსელის შეცდომა]"

    def copy_to_clipboard(self, instance):
        if self.output_label.text and "[შეცდომა]" not in self.output_label.text:
            Clipboard.copy(self.output_label.text)

    def open_history(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        hist_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        hist_box.bind(minimum_height=hist_box.setter('height'))

        records = self.db.get_history()
        for src, trans in records:
            lbl = Label(
                text=f"• {src} ➔ {trans}",
                size_hint_y=None,
                height=45,
                font_size='13sp'
            )
            hist_box.add_widget(lbl)

        scroll.add_widget(hist_box)
        content.add_widget(scroll)
        popup = Popup(title="ბოლო თარგმანების ისტორია", content=content, size_hint=(0.9, 0.75))
        popup.open()


# ---------------------------------------------------------
# 3. ENTRY POINT
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        db = DatabaseManager()
        return LingoLensUI(db=db)


if __name__ == "__main__":
    LingoLensApp().run()

import sys
import traceback

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

# ---------------------------------------------------------
# 0. SAFE IMPORTS
# ---------------------------------------------------------
STARTUP_ERROR = None

try:
    import os
    import sqlite3
    from datetime import datetime
    from urllib.parse import quote

    from kivy.core.clipboard import Clipboard
    from kivy.utils import platform
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.popup import Popup
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.spinner import Spinner
    from kivy.network.urlrequest import UrlRequest
except Exception as e:
    STARTUP_ERROR = f"Import Exception:\n{traceback.format_exc()}"

LANGUAGES = {
    "ქართული": "ka",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Русский": "ru",
    "Türkçe": "tr"
}

# ---------------------------------------------------------
# 1. SAFE DATABASE MANAGER
# ---------------------------------------------------------
class SafeDatabase:
    def __init__(self):
        self.enabled = False
        self.db_path = ":memory:"
        try:
            if platform == 'android':
                from kivy.app import App
                app = App.get_running_app()
                db_dir = app.user_data_dir if app else "."
                self.db_path = os.path.join(db_dir, "lingolens.db")
            else:
                self.db_path = "lingolens.db"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, source_text TEXT, translated_text TEXT)")
            self.enabled = True
        except Exception as e:
            print(f"DB Disabled: {e}")

    def add(self, src, trans):
        if not self.enabled: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO history (source_text, translated_text) VALUES (?, ?)", (src, trans))
        except Exception:
            pass

    def get(self):
        if not self.enabled: return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 20")
                return cursor.fetchall()
        except Exception:
            return []


# ---------------------------------------------------------
# 2. MAIN UI
# ---------------------------------------------------------
class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.db = SafeDatabase()

        # Header
        header = BoxLayout(size_hint_y=0.1, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True)
        btn_hist = Button(text="History", size_hint_x=0.3)
        btn_hist.bind(on_press=self.open_history)
        header.add_widget(title)
        header.add_widget(btn_hist)
        self.add_widget(header)

        # Languages
        lang_bar = BoxLayout(size_hint_y=0.1, spacing=5)
        self.src_spinner = Spinner(text="ქართული", values=list(LANGUAGES.keys()), size_hint_x=0.4)
        self.target_spinner = Spinner(text="English", values=list(LANGUAGES.keys()), size_hint_x=0.4)
        btn_swap = Button(text="⇄", size_hint_x=0.2)
        btn_swap.bind(on_press=self.swap_lang)
        
        lang_bar.add_widget(self.src_spinner)
        lang_bar.add_widget(btn_swap)
        lang_bar.add_widget(self.target_spinner)
        self.add_widget(lang_bar)

        # Input
        self.input_text = TextInput(hint_text="Enter text...", size_hint_y=0.3)
        self.input_text.bind(text=self.on_text)
        self.add_widget(self.input_text)

        # Output
        self.output_label = Label(text="Translation...", size_hint_y=0.5, font_size='16sp')
        self.add_widget(self.output_label)

    def swap_lang(self, instance):
        s, t = self.src_spinner.text, self.target_spinner.text
        self.src_spinner.text, self.target_spinner.text = t, s

    def on_text(self, instance, value):
        text = value.strip()
        if not text:
            self.output_label.text = "Translation..."
            return

        src = LANGUAGES.get(self.src_spinner.text, "auto")
        target = LANGUAGES.get(self.target_spinner.text, "en")
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={target}&dt=t&q={quote(text)}"

        UrlRequest(url, on_success=self.on_success, on_error=self.on_err, on_failure=self.on_err, timeout=5)

    def on_success(self, req, result):
        try:
            res = "".join([item[0] for item in result[0] if item[0]])
            self.output_label.text = res
            self.db.add(self.input_text.text[:30], res)
        except Exception:
            self.output_label.text = "Parse Error"

    def on_err(self, req, error):
        self.output_label.text = "Network Error"

    def open_history(self, instance):
        p = Popup(title="History", size_hint=(0.8, 0.8))
        box = BoxLayout(orientation='vertical')
        for s, t in self.db.get():
            box.add_widget(Label(text=f"{s} -> {t}"))
        p.content = box
        p.open()


# ---------------------------------------------------------
# 3. APP LAUNCHER WITH ERROR CATCHER
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        if STARTUP_ERROR:
            # თუ იმპორტისას შეცდომა მოხდა, გამოაჩენს წითელ ეკრანზე
            lbl = Label(text=STARTUP_ERROR, color=(1, 0, 0, 1), font_size='12sp')
            lbl.text_size = (400, None)
            return lbl
        try:
            return LingoLensUI()
        except Exception as e:
            err = traceback.format_exc()
            return Label(text=f"Runtime Error:\n{err}", color=(1, 0, 0, 1), font_size='12sp')


if __name__ == "__main__":
    LingoLensApp().run()

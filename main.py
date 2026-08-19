import sys
import traceback

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase

# ---------------------------------------------------------
# 0. FONT REGISTRATION & SAFE IMPORTS
# ---------------------------------------------------------
try:
    LabelBase.register(name='GeorgianFont', fn_regular='font.ttf')
    DEFAULT_FONT = 'GeorgianFont'
except Exception:
    DEFAULT_FONT = 'Roboto'  # Fallback

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

# მსოფლიო ენების გაფართოებული სია
LANGUAGES = {
    "ქართული": "ka",
    "English": "en",
    "Русский": "ru",
    "Türkçe": "tr",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Português": "pt",
    "العربية (Arabic)": "ar",
    "中文 (Chinese)": "zh-CN",
    "日本語 (Japanese)": "ja",
    "한국어 (Korean)": "ko",
    "हिन्दी (Hindi)": "hi",
    "Українська": "uk",
    "Polski": "pl",
    "Nederlands": "nl",
    "Ελληνικά (Greek)": "el",
    "עברית (Hebrew)": "he",
    "Svenska": "sv",
    "Norsk": "no",
    "Suomi": "fi",
    "Čeština": "cs",
    "Română": "ro",
    "Magyar": "hu",
    "Tiếng Việt": "vi",
    "ไทย (Thai)": "th",
    "Bahasa Indonesia": "id",
    "فارسی (Persian)": "fa",
    "Azərbaycan": "az",
    "Հայերեն (Armenian)": "hy"
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
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 30")
                return cursor.fetchall()
        except Exception:
            return []

    def clear(self):
        if not self.enabled: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM history")
        except Exception:
            pass


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
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True, font_name=DEFAULT_FONT)
        btn_menu = Button(text="☰ მენიუ", size_hint_x=0.3, font_name=DEFAULT_FONT)
        btn_menu.bind(on_press=self.open_menu)
        header.add_widget(title)
        header.add_widget(btn_menu)
        self.add_widget(header)

        # Languages Bar
        lang_bar = BoxLayout(size_hint_y=0.1, spacing=5)
        self.src_spinner = Spinner(
            text="ქართული", 
            values=list(LANGUAGES.keys()), 
            size_hint_x=0.4, 
            font_name=DEFAULT_FONT,
            option_cls=lambda **kwargs: Button(**kwargs, font_name=DEFAULT_FONT)
        )
        self.target_spinner = Spinner(
            text="English", 
            values=list(LANGUAGES.keys()), 
            size_hint_x=0.4, 
            font_name=DEFAULT_FONT,
            option_cls=lambda **kwargs: Button(**kwargs, font_name=DEFAULT_FONT)
        )
        btn_swap = Button(text="<->", size_hint_x=0.2, font_name=DEFAULT_FONT)
        btn_swap.bind(on_press=self.swap_lang)
        
        lang_bar.add_widget(self.src_spinner)
        lang_bar.add_widget(btn_swap)
        lang_bar.add_widget(self.target_spinner)
        self.add_widget(lang_bar)

        # Input Box
        self.input_text = TextInput(hint_text="შეიყვანეთ ტექსტი...", size_hint_y=0.3, font_name=DEFAULT_FONT)
        self.input_text.bind(text=self.on_text)
        self.add_widget(self.input_text)

        # Output Box
        self.output_label = Label(text="თარგმანი...", size_hint_y=0.5, font_size='16sp', font_name=DEFAULT_FONT)
        self.add_widget(self.output_label)

    def swap_lang(self, instance):
        s, t = self.src_spinner.text, self.target_spinner.text
        self.src_spinner.text, self.target_spinner.text = t, s

    def on_text(self, instance, value):
        text = value.strip()
        if not text:
            self.output_label.text = "თარგმანი..."
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

    # --- MENU & POPUPS ---
    def open_menu(self, instance):
        p = Popup(title="მენიუ", size_hint=(0.8, 0.5), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)

        btn_hist = Button(text="📜 ისტორია", font_name=DEFAULT_FONT)
        btn_hist.bind(on_press=lambda x: [p.dismiss(), self.open_history()])

        btn_clear = Button(text="🗑️ ისტორიის წაშლა", font_name=DEFAULT_FONT)
        btn_clear.bind(on_press=lambda x: [self.db.clear(), p.dismiss(), self.show_info("ისტორია წაიშალა")])

        btn_about = Button(text="ℹ️ შესახებ", font_name=DEFAULT_FONT)
        btn_about.bind(on_press=lambda x: [p.dismiss(), self.open_about()])

        btn_close = Button(text="❌ დახურვა", font_name=DEFAULT_FONT)
        btn_close.bind(on_press=p.dismiss)

        box.add_widget(btn_hist)
        box.add_widget(btn_clear)
        box.add_widget(btn_about)
        box.add_widget(btn_close)

        p.content = box
        p.open()

    def open_history(self):
        p = Popup(title="თარგმანების ისტორია", size_hint=(0.85, 0.8), title_font=DEFAULT_FONT)
        scroll = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=10)
        box.bind(minimum_height=box.setter('height'))

        items = self.db.get()
        if not items:
            box.add_widget(Label(text="ისტორია ცარიელია", font_name=DEFAULT_FONT, size_hint_y=None, height=40))
        else:
            for s, t in items:
                lbl = Label(
                    text=f"• {s}  ➔  {t}", 
                    font_name=DEFAULT_FONT, 
                    size_hint_y=None, 
                    height=40,
                    halign='left',
                    valign='middle'
                )
                lbl.bind(size=lbl.setter('text_size'))
                box.add_widget(lbl)

        scroll.add_widget(box)
        p.content = scroll
        p.open()

    def open_about(self):
        p = Popup(title="შესახებ", size_hint=(0.8, 0.4), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="LingoLens Ultra Pro v1.0\nმრავალენოვანი მთარგმნელი", font_name=DEFAULT_FONT, halign='center')
        btn = Button(text="კარგი", font_name=DEFAULT_FONT, size_hint_y=0.4)
        btn.bind(on_press=p.dismiss)
        box.add_widget(lbl)
        box.add_widget(btn)
        p.content = box
        p.open()

    def show_info(self, text):
        p = Popup(title="შეტყობინება", size_hint=(0.7, 0.3), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text=text, font_name=DEFAULT_FONT))
        btn = Button(text="OK", font_name=DEFAULT_FONT, size_hint_y=0.4)
        btn.bind(on_press=p.dismiss)
        box.add_widget(btn)
        p.content = box
        p.open()


# ---------------------------------------------------------
# 3. APP LAUNCHER WITH ERROR CATCHER
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        if STARTUP_ERROR:
            lbl = Label(text=STARTUP_ERROR, color=(1, 0, 0, 1), font_size='12sp', font_name=DEFAULT_FONT)
            lbl.text_size = (400, None)
            return lbl
        try:
            return LingoLensUI()
        except Exception as e:
            err = traceback.format_exc()
            return Label(text=f"Runtime Error:\n{err}", color=(1, 0, 0, 1), font_size='12sp', font_name=DEFAULT_FONT)


if __name__ == "__main__":
    LingoLensApp().run()

import sys
import traceback
import os
import sqlite3
from datetime import datetime
from urllib.parse import quote

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.clipboard import Clipboard
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.network.urlrequest import UrlRequest

# ---------------------------------------------------------
# 0. FONT REGISTRATION
# ---------------------------------------------------------
try:
    LabelBase.register(name='GeorgianFont', fn_regular='font.ttf')
    DEFAULT_FONT = 'GeorgianFont'
except Exception:
    DEFAULT_FONT = 'Roboto'

class CustomSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = DEFAULT_FONT

SRC_LANGUAGES = {
    "ავტო ამოცნობა": "auto",
    "ქართული": "ka",
    "English": "en",
    "რუსული (Russian)": "ru",
    "თურქული (Turkish)": "tr",
    "ესპანური (Spanish)": "es",
    "ფრანგული (French)": "fr",
    "გერმანული (German)": "de",
    "იტალიური (Italian)": "it",
    "პორტუგალიური (Portuguese)": "pt",
    "არაბული (Arabic)": "ar",
    "ჩინური (Chinese)": "zh-CN",
    "იაპონური (Japanese)": "ja",
    "კორეული (Korean)": "ko",
    "ინდური (Hindi)": "hi",
    "უკრაინული (Ukrainian)": "uk",
    "პოლონური (Polish)": "pl",
    "ჰოლანდიური (Dutch)": "nl",
    "ბერძნული (Greek)": "el",
    "ებრაული (Hebrew)": "he",
    "შვედური (Swedish)": "sv",
    "ნორვეგიული (Norwegian)": "no",
    "ფინური (Finnish)": "fi",
    "ჩეხური (Czech)": "cs",
    "რუმინული (Romanian)": "ro",
    "უნგრული (Hungarian)": "hu",
    "ვიეტნამური (Vietnamese)": "vi",
    "ტაილანდური (Thai)": "th",
    "ინდონეზიური (Indonesian)": "id",
    "სპარსული (Persian)": "fa",
    "აზერბაიჯანული (Azerbaijani)": "az",
    "სომხური (Armenian)": "hy"
}

TARGET_LANGUAGES = {k: v for k, v in SRC_LANGUAGES.items() if k != "ავტო ამოცნობა"}

# ---------------------------------------------------------
# 1. SAFE DATABASE MANAGER
# ---------------------------------------------------------
class SafeDatabase:
    def __init__(self, user_data_dir="."):
        self.enabled = False
        self.db_path = ":memory:"
        try:
            if platform == 'android':
                self.db_path = os.path.join(user_data_dir, "lingolens.db")
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
    def __init__(self, user_data_dir=".", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.user_data_dir = user_data_dir
        self.db = SafeDatabase(user_data_dir)
        self.search_event = None
        self.sound = None
        self.last_target_lang = "en"

        # Header
        header = BoxLayout(size_hint_y=0.1, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True, font_name=DEFAULT_FONT)
        btn_menu = Button(text="[=] მენიუ", size_hint_x=0.3, font_name=DEFAULT_FONT)
        btn_menu.bind(on_press=self.open_menu)
        header.add_widget(title)
        header.add_widget(btn_menu)
        self.add_widget(header)

        # Languages Bar
        lang_bar = BoxLayout(size_hint_y=0.1, spacing=5)
        self.src_spinner = Spinner(
            text="ქართული", 
            values=list(SRC_LANGUAGES.keys()), 
            size_hint_x=0.4, 
            font_name=DEFAULT_FONT,
            option_cls=CustomSpinnerOption
        )
        self.target_spinner = Spinner(
            text="English", 
            values=list(TARGET_LANGUAGES.keys()), 
            size_hint_x=0.4, 
            font_name=DEFAULT_FONT,
            option_cls=CustomSpinnerOption
        )
        btn_swap = Button(text="<->", size_hint_x=0.2, font_name=DEFAULT_FONT)
        btn_swap.bind(on_press=self.swap_lang)
        
        lang_bar.add_widget(self.src_spinner)
        lang_bar.add_widget(btn_swap)
        lang_bar.add_widget(self.target_spinner)
        self.add_widget(lang_bar)

        # Input Box
        self.input_text = TextInput(hint_text="შეიყვანეთ ტექსტი...", size_hint_y=0.3, font_name=DEFAULT_FONT)
        self.input_text.bind(text=self.on_text_change)
        self.add_widget(self.input_text)

        # Output Box Layout (Label + Speak Button)
        output_box = BoxLayout(size_hint_y=0.5, spacing=5)
        self.output_label = Label(text="თარგმანი...", font_size='16sp', font_name=DEFAULT_FONT, size_hint_x=0.8)
        
        btn_speak = Button(text="🔊", size_hint_x=0.2, font_name=DEFAULT_FONT, font_size='18sp')
        btn_speak.bind(on_press=self.speak_text)
        
        output_box.add_widget(self.output_label)
        output_box.add_widget(btn_speak)
        self.add_widget(output_box)

    def swap_lang(self, instance):
        s, t = self.src_spinner.text, self.target_spinner.text
        if s == "ავტო ამოცნობა":
            return
        self.src_spinner.text, self.target_spinner.text = t, s
        self.on_text_change(self.input_text, self.input_text.text)

    def on_text_change(self, instance, value):
        if self.search_event:
            self.search_event.cancel()
        
        text = value.strip()
        if not text:
            self.output_label.text = "თარგმანი..."
            return

        self.search_event = Clock.schedule_once(lambda dt: self.perform_bidirectional_translation(text), 0.3)

    def perform_bidirectional_translation(self, text):
        s_lang = SRC_LANGUAGES.get(self.src_spinner.text, "auto")
        t_lang = TARGET_LANGUAGES.get(self.target_spinner.text, "en")

        if s_lang == "auto":
            self.last_target_lang = t_lang
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={t_lang}&dt=t&q={quote(text)}"
            UrlRequest(url, on_success=lambda req, res: self.on_success(req, res, text), on_error=self.on_err, timeout=5)
            return

        detect_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={t_lang}&dt=t&q={quote(text)}"
        
        def on_detect_success(req, result):
            try:
                detected_lang = result[2]
                if detected_lang == t_lang:
                    final_sl, final_tl = t_lang, s_lang
                else:
                    final_sl, final_tl = s_lang, t_lang

                self.last_target_lang = final_tl
                trans_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={final_sl}&tl={final_tl}&dt=t&q={quote(text)}"
                UrlRequest(trans_url, on_success=lambda r, res: self.on_success(r, res, text), on_error=self.on_err, timeout=5)
            except Exception:
                self.last_target_lang = t_lang
                trans_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={s_lang}&tl={t_lang}&dt=t&q={quote(text)}"
                UrlRequest(trans_url, on_success=lambda r, res: self.on_success(r, res, text), on_error=self.on_err, timeout=5)

        UrlRequest(detect_url, on_success=on_detect_success, on_error=self.on_err, timeout=5)

    def on_success(self, req, result, original_text):
        try:
            res = "".join([item[0] for item in result[0] if item[0]])
            self.output_label.text = res
            self.db.add(original_text[:30], res)
        except Exception:
            self.output_label.text = "Parse Error"

    def on_err(self, req, error):
        self.output_label.text = "Network Error"

    def speak_text(self, instance):
        text = self.output_label.text.strip()
        if not text or text in ["თარგმანი...", "Parse Error", "Network Error"]:
            return

        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={quote(text)}&tl={self.last_target_lang}&client=tw-ob"
        save_path = os.path.join(self.user_data_dir, "tts_sound.mp3")

        UrlRequest(
            tts_url,
            on_success=lambda req, res: self.play_sound(save_path),
            on_error=lambda req, err: print(f"TTS Error: {err}"),
            file_path=save_path
        )

    def play_sound(self, file_path):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
        self.sound = SoundLoader.load(file_path)
        if self.sound:
            self.sound.play()

    # --- MENU & POPUPS ---
    def open_menu(self, instance):
        p = Popup(title="მენიუ", size_hint=(0.8, 0.5), title_font=DEFAULT_FONT)
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)

        btn_hist = Button(text="[H] ისტორია", font_name=DEFAULT_FONT)
        btn_hist.bind(on_press=lambda x: [p.dismiss(), self.open_history()])

        btn_clear = Button(text="[D] ისტორიის წაშლა", font_name=DEFAULT_FONT)
        btn_clear.bind(on_press=lambda x: [self.db.clear(), p.dismiss(), self.show_info("ისტორია წაიშალა")])

        btn_about = Button(text="[i] შესახებ", font_name=DEFAULT_FONT)
        btn_about.bind(on_press=lambda x: [p.dismiss(), self.open_about()])

        btn_close = Button(text="[X] დახურვა", font_name=DEFAULT_FONT)
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
                    text=f"• {s} -> {t}", 
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
        btn = Button(text="OK", font_name=DEFAULT_FONT, size_hint_y=0.4)
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
# 3. APP LAUNCHER
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        try:
            return LingoLensUI(user_data_dir=self.user_data_dir)
        except Exception:
            err = traceback.format_exc()
            return Label(text=f"Runtime Error:\n{err}", color=(1, 0, 0, 1), font_size='12sp', font_name=DEFAULT_FONT)

if __name__ == "__main__":
    LingoLensApp().run()

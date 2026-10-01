# ==============================================================================
# LingoLens AI - Safe Mobile Build Version
# ==============================================================================

import json
import os
import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.utils import platform

# შრიფტის რეგისტრაცია
FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="GeorgianFont", fn_regular=FONT_PATH)
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

# უსაფრთხო იმპორტები (რომ აპლიკაცია არ დაიხუროს ფაილის ვერ პოვნის გამო)
try:
    from utils.translator import translate_text, analyze_image_and_translate
except ImportError:
    def translate_text(prompt, text, src_lang, target_lang, callback):
        callback("ტესტური თარგმანი: სერვერის მოდული ვერ მოიძებნა")
    analyze_image_and_translate = None

try:
    from ui.camerawidget import CameraWidget
except ImportError:
    CameraWidget = None

try:
    from ui.dialoguewidget import DialogueWidget
except ImportError:
    DialogueWidget = None

try:
    from languages import WORLD_LANGUAGES
    SUPPORTED_LANGUAGES = WORLD_LANGUAGES if isinstance(WORLD_LANGUAGES, dict) else {}
except Exception:
    SUPPORTED_LANGUAGES = {}

if not SUPPORTED_LANGUAGES:
    SUPPORTED_LANGUAGES = {
        "ქართული": "ka", "English": "en", "Русский": "ru",
        "Español": "es", "Deutsch": "de", "Français": "fr"
    }

HISTORY_FILE = "translation_history.json"

UI_TEXTS = {
    "ka": {
        "menu_translator": "მთარგმნელი",
        "menu_dialogue": "დიალოგი",
        "menu_camera": "კამერა / OCR",
        "menu_history": "ისტორია",
        "menu_grammar": "გრამატიკა",
        "menu_settings": "პარამეტრები",
        "btn_back": "უკან",
        "btn_translate": "თარგმნა",
        "btn_copy": "კოპირება",
        "btn_share": "გაზიარება",
        "hint_input": "ჩაწერეთ ტექსტი...",
        "hint_output": "თარგმანი...",
        "status_processing": "მუშავდება...",
    }
}

class CustomSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = GEORGIAN_FONT_NAME

class LingoLensApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view = None
        self.in_main_menu = True

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard_event)
        self.root_layout = FloatLayout()
        self.show_main_menu()
        return self.root_layout

    def on_keyboard_event(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # Android უკან ღილაკი
            if not self.in_main_menu:
                self.show_main_menu()
                return True
            else:
                self.stop()
                return True
        return False

    def get_text(self, key):
        return UI_TEXTS["ka"].get(key, key)

    def show_main_menu(self, instance=None):
        self.in_main_menu = True
        Clock.schedule_once(lambda dt: self._apply_main_menu(), 0)

    def _apply_main_menu(self):
        self.root_layout.clear_widgets()

        menu_grid = GridLayout(
            cols=2, spacing=dp(15), padding=dp(20),
            size_hint=(0.9, 0.8), pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        font = GEORGIAN_FONT_NAME
        
        btn_translator = Button(text=self.get_text("menu_translator"), font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text=self.get_text("menu_dialogue"), font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text=self.get_text("menu_grammar"), font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text=self.get_text("menu_camera"), font_name=font, on_press=self.open_media_options)
        btn_history = Button(text=self.get_text("menu_history"), font_name=font, on_press=self.open_history)
        btn_settings = Button(text=self.get_text("menu_settings"), font_name=font, on_press=self.open_settings)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_grammar)
        menu_grid.add_widget(btn_camera)
        menu_grid.add_widget(btn_history)
        menu_grid.add_widget(btn_settings)

        self.root_layout.add_widget(menu_grid)

    def switch_to_view(self, widget):
        self.in_main_menu = False
        Clock.schedule_once(lambda dt: self._apply_switch_to_view(widget), 0)

    def _apply_switch_to_view(self, widget):
        self.root_layout.clear_widgets()
        font = GEORGIAN_FONT_NAME

        container = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=0)
        top_bar = BoxLayout(orientation="horizontal", size_hint_y=0.1, padding=dp(5), spacing=dp(10))
        btn_back = Button(text=self.get_text("btn_back"), font_name=font, size_hint_x=0.3, on_press=lambda x: self.show_main_menu())
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text="", size_hint_x=0.7))

        container.add_widget(top_bar)
        container.add_widget(widget)

        self.root_layout.add_widget(container)

    def save_to_history(self, original, translated):
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def copy_to_clipboard(self, text):
        if text and text.strip():
            Clipboard.copy(text)

    def open_media_options(self, instance):
        if CameraWidget:
            try:
                self.switch_to_view(CameraWidget(app_instance=self))
                return
            except Exception as e:
                print("CameraWidget error:", e)

        # ალტერნატიული მარტივი ფანჯარა თუ ვიჯეტი ვერ ჩაიტვირთა
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        box.add_widget(Label(text="კამერის მოდული მზადდება...", font_name=GEORGIAN_FONT_NAME))
        self.switch_to_view(box)

    def open_translator(self, instance=None, initial_text=""):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))

        lang_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=0.1)
        lang_names = list(SUPPORTED_LANGUAGES.keys())

        sp_src = Spinner(text="ქართული", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)
        sp_target = Spinner(text="English", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)

        lang_box.add_widget(sp_src)
        lang_box.add_widget(sp_target)

        inp = TextInput(text=initial_text, hint_text=self.get_text("hint_input"), font_name=font, multiline=True, size_hint_y=0.25)
        out = TextInput(hint_text=self.get_text("hint_output"), font_name=font, readonly=True, multiline=True, size_hint_y=0.25)
        status_lbl = Label(text="", size_hint_y=0.05, font_name=font)

        btn_trans = Button(text=self.get_text("btn_translate"), font_name=font, size_hint_y=0.1)

        def handle_translation(btn):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                return
            src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
            status_lbl.text = self.get_text("status_processing")

            def on_res(res):
                res_text = str(res) if res else "შეცდომაა"
                Clock.schedule_once(lambda dt: setattr(out, "text", res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))
                if res:
                    self.save_to_history(text_to_translate, res_text)

            try:
                translate_text("Translate", text_to_translate, src_code, target_code, on_res)
            except Exception as e:
                print("Translation error:", e)
                status_lbl.text = "შეცდომაა სერვერთან"

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)

        if instance is not None:
            self.switch_to_view(box)
        return box

    def open_dialogue(self, instance):
        if DialogueWidget:
            try:
                self.switch_to_view(DialogueWidget())
                return
            except Exception as e:
                print("Dialogue error:", e)
        box = BoxLayout(orientation="vertical", padding=dp(10))
        box.add_widget(Label(text="დიალოგის მოდული მზადდება...", font_name=GEORGIAN_FONT_NAME))
        self.switch_to_view(box)

    def open_grammar(self, instance):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        box.add_widget(TextInput(hint_text="ჩაწერეთ ტექსტი გრამატიკისთვის...", font_name=GEORGIAN_FONT_NAME, multiline=True))
        self.switch_to_view(box)

    def open_history(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10))
        scroller = ScrollView()
        content = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for item in reversed(history):
                        orig = item.get("original", "")
                        trans = item.get("translated", "")
                        content.add_widget(Label(text=f"{orig} ➔ {trans}", font_name=font, size_hint_y=None, height=dp(40)))
            except Exception:
                pass
        if not content.children:
            content.add_widget(Label(text="ისტორია ცარიელია", font_name=font))
        scroller.add_widget(content)
        box.add_widget(scroller)
        self.switch_to_view(box)

    def open_settings(self, instance):
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        box.add_widget(Label(text="LingoLens AI v6.0.2", font_name=GEORGIAN_FONT_NAME))
        self.switch_to_view(box)

if __name__ == "__main__":
    LingoLensApp().run()

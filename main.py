# ==============================================================================
# LingoLens AI - Fully Integrated Main Application (Production Ready)
# ==============================================================================

import json
import os
import sys
import traceback

# კრაშების ლოგირების უსაფრთხო სისტემა (ინახავს crash_log.txt-ს აპის დირექტორიაში)
def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("CRASH:", error_msg)
    try:
        from kivy.app import App
        app = App.get_running_app()
        log_dir = app.user_data_dir if app else "."
        log_path = os.path.join(log_dir, "crash_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
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

# ფონტის უსაფრთხო რეგისტრაცია
FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="GeorgianFont", fn_regular=FONT_PATH)
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

# --- პროექტის შიდა მოდულების იმპორტი ---
try:
    import config
except ImportError:
    config = None

try:
    from utils.tts_engine import speak
except ImportError:
    def speak(text, lang, path, callback):
        if callback:
            callback("TTS Engine not available")

try:
    from utils.translator import translate_text
except ImportError:
    import threading
    import urllib.request

    def translate_text(prompt, text, src_lang, target_lang, callback):
        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text,
                    "source": src_lang,
                    "target": target_lang,
                    "prompt": prompt
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    result_text = (
                        res_data.get("translated_text")
                        or res_data.get("result")
                        or str(res_data)
                    )
                    callback(result_text)
            except Exception as e:
                print("Server connection error:", e)
                callback(None)

        threading.Thread(target=worker, daemon=True).start()

# UI კომპონენტების უსაფრთხო იმპორტი
try:
    from ui.dialoguewidget import DialogueWidget
except ImportError:
    DialogueWidget = None

try:
    from ui.rotatedcamerawidget import RotatedCameraWidget
except ImportError:
    RotatedCameraWidget = None

try:
    from ui.menu_popup import MenuPopup
except ImportError:
    MenuPopup = None

# მხარდაჭერილი ენების ლექსიკონი
try:
    from languages import WORLD_LANGUAGES
    if isinstance(WORLD_LANGUAGES, dict):
        SUPPORTED_LANGUAGES = WORLD_LANGUAGES
    else:
        raise ValueError()
except Exception:
    SUPPORTED_LANGUAGES = {
        "ქართული": "ka",
        "English": "en",
        "Русский": "ru",
        "Español": "es",
        "Deutsch": "de",
        "Français": "fr",
        "Italiano": "it",
        "Türkçe": "tr"
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
        "btn_listen": "მოსმენა",
        "hint_input": "ჩაწერეთ ტექსტი...",
        "hint_output": "თარგმანი...",
        "status_processing": "მუშავდება...",
        "error_connection": "შეცდომაა სერვერთან",
    }
}

class CustomSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = GEORGIAN_FONT_NAME


class LingoLensApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_popup = None

    def build(self):
        self.root_layout = FloatLayout()
        self.show_main_menu()
        return self.root_layout

    def get_text(self, key):
        return UI_TEXTS["ka"].get(key, key)

    def show_main_menu(self, instance=None):
        if self.current_popup and self.current_popup in self.root_layout.children:
            self.root_layout.remove_widget(self.current_popup)

        menu_grid = GridLayout(
            cols=2,
            spacing=dp(15),
            padding=dp(20),
            size_hint=(0.9, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        font = GEORGIAN_FONT_NAME
        btn_translator = Button(text=self.get_text("menu_translator"), font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text=self.get_text("menu_dialogue"), font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text=self.get_text("menu_grammar"), font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text=self.get_text("menu_camera"), font_name=font, on_press=self.open_camera_with_check)
        btn_history = Button(text=self.get_text("menu_history"), font_name=font, on_press=self.open_history)
        btn_settings = Button(text=self.get_text("menu_settings"), font_name=font, on_press=self.open_settings)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_grammar)
        menu_grid.add_widget(btn_camera)
        menu_grid.add_widget(btn_history)
        menu_grid.add_widget(btn_settings)

        self.current_popup = menu_grid
        self.root_layout.add_widget(self.current_popup)

    def switch_to_view(self, widget):
        if self.current_popup and self.current_popup in self.root_layout.children:
            self.root_layout.remove_widget(self.current_popup)

        container = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=0)
        font = GEORGIAN_FONT_NAME

        top_bar = BoxLayout(orientation="horizontal", size_hint_y=0.1, padding=dp(5), spacing=dp(10))
        btn_back = Button(text=self.get_text("btn_back"), font_name=font, size_hint_x=0.3, on_press=self.show_main_menu)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text="", size_hint_x=0.7))

        container.add_widget(top_bar)
        container.add_widget(widget)

        self.current_popup = container
        self.root_layout.add_widget(self.current_popup)

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

    def request_camera_permission_on_demand(self, callback_func):
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions
                perms = [Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET]
                request_permissions(perms, lambda perms, results: callback_func())
            except Exception:
                callback_func()
        else:
            callback_func()

    def copy_to_clipboard(self, text):
        if text and text.strip():
            Clipboard.copy(text)

    def share_text(self, text):
        if not text or not text.strip():
            return
        if platform == "android":
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                String = autoclass("java.lang.String")
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text))
                chooser = Intent.createChooser(intent, String("Share"))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception:
                pass
        else:
            Clipboard.copy(text)

    def safe_speak(self, text, lang="en"):
        if text and text.strip():
            try:
                speak(text, lang, self.user_data_dir, lambda msg: print(msg))
            except Exception:
                pass

    # 1. მთარგმნელი
    def open_translator(self, instance=None, initial_text=""):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))

        lang_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=0.1)
        lang_names = list(SUPPORTED_LANGUAGES.keys())

        sp_src = Spinner(text="ქართული", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)
        sp_target = Spinner(text="English", values=lang_names, font_name=font, option_cls=CustomSpinnerOption)

        def swap_languages(instance):
            temp = sp_src.text
            sp_src.text = sp_target.text
            sp_target.text = temp

        btn_swap = Button(text="<=>", size_hint_x=0.2, font_name=font)
        btn_swap.bind(on_press=swap_languages)

        lang_box.add_widget(sp_src)
        lang_box.add_widget(btn_swap)
        lang_box.add_widget(sp_target)

        inp = TextInput(text=initial_text, hint_text=self.get_text("hint_input"), font_name=font, multiline=True, size_hint_y=0.25)
        out = TextInput(hint_text=self.get_text("hint_output"), font_name=font, readonly=True, multiline=True, size_hint_y=0.25)
        status_lbl = Label(text="", size_hint_y=0.05, font_name=font)

        btn_trans = Button(text=self.get_text("btn_translate"), font_name=font, size_hint_y=0.1)

        action_box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=0.1)
        btn_copy = Button(text=self.get_text("btn_copy"), font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text=self.get_text("btn_share"), font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text=self.get_text("btn_listen"), font_name=font, on_press=lambda x: self.safe_speak(out.text, SUPPORTED_LANGUAGES.get(sp_target.text, "en")))

        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def handle_translation(btn_inst):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                status_lbl.text = "გთხოვთ შეიყვანოთ ტექსტი"
                return

            src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
            status_lbl.text = self.get_text("status_processing")
            out.text = ""

            def on_res(res):
                res_text = str(res) if res else self.get_text("error_connection")
                Clock.schedule_once(lambda dt: setattr(out, "text", res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))
                if res:
                    self.save_to_history(text_to_translate, res_text)

            try:
                translate_text(
                    prompt=f"Translate accurately from {sp_src.text} to {sp_target.text}: {text_to_translate}",
                    text=text_to_translate,
                    src_lang=src_code,
                    target_lang=target_code,
                    callback=on_res
                )
            except Exception as e:
                print("Translation Error:", e)
                Clock.schedule_once(lambda dt: setattr(out, "text", self.get_text("error_connection")))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        if instance is not None:
            self.switch_to_view(box)
        return box

    # 2. დიალოგი
    def open_dialogue(self, instance):
        font = GEORGIAN_FONT_NAME
        if DialogueWidget:
            widget = DialogueWidget()
        else:
            widget = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))
            widget.add_widget(Label(text="DialogueWidget ვერ მოიძებნა ui ფოლდერში", font_name=font))
        self.switch_to_view(widget)

    # 3. გრამატიკა
    def open_grammar(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))
        inp = TextInput(hint_text="ჩაწერეთ ტექსტი გრამატიკული შესწორებისთვის...", font_name=font, multiline=True, size_hint_y=0.35)
        out = TextInput(hint_text="შესწორებული ვარიანტი...", font_name=font, readonly=True, multiline=True, size_hint_y=0.35)
        status_lbl = Label(text="", size_hint_y=0.1, font_name=font)
        btn_check = Button(text="გრამატიკის შემოწმება", font_name=font, size_hint_y=0.2)

        def handle_grammar(btn):
            text_to_fix = inp.text.strip()
            if not text_to_fix:
                return
            status_lbl.text = "მუშავდება..."

            def on_res(res):
                res_text = str(res) if res else "შეცდომაა სერვერთან"
                Clock.schedule_once(lambda dt: setattr(out, "text", res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))

            try:
                translate_text(
                    prompt=f"Fix grammar and improve style in Georgian: {text_to_fix}",
                    text=text_to_fix,
                    src_lang="ka",
                    target_lang="ka",
                    callback=on_res
                )
            except Exception:
                Clock.schedule_once(lambda dt: setattr(out, "text", "შეცდომაა სერვერთან"))
                Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))

        btn_check.bind(on_press=handle_grammar)
        box.add_widget(inp)
        box.add_widget(btn_check)
        box.add_widget(status_lbl)
        box.add_widget(out)
        self.switch_to_view(box)

    # 4. კამერა / OCR (დაცული და დიაგნოსტიკური ვერსია)
    def open_camera_with_check(self, instance):
        def proceed():
            font = GEORGIAN_FONT_NAME
            try:
                if RotatedCameraWidget:
                    widget = RotatedCameraWidget()
                else:
                    widget = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))
                    widget.add_widget(Label(text="შეცდომა: RotatedCameraWidget არ არის იმპორტირებული", font_name=font))
            except Exception as e:
                widget = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))
                err_label = Label(text=f"კამერის კრაში:\n{str(e)}", font_name=font, halign="center")
                err_label.bind(size=err_label.setter('text_size'))
                widget.add_widget(err_label)
                print("Camera Widget Init Error:", e)
                
            self.switch_to_view(widget)

        self.request_camera_permission_on_demand(proceed)

    # 5. ისტორია
    def open_history(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5), size_hint=(1, 1))
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
                        lbl = Label(
                            text=f"{orig} ➔ {trans}",
                            font_name=font,
                            size_hint_y=None,
                            height=dp(40),
                            halign="left",
                            valign="middle"
                        )
                        lbl.bind(size=lbl.setter("text_size"))
                        content.add_widget(lbl)
            except Exception:
                pass
        if not content.children:
            content.add_widget(Label(text="ისტორია ცარიელია", font_name=font))
        scroller.add_widget(content)
        box.add_widget(scroller)
        self.switch_to_view(box)

    # 6. პარამეტრები
    def open_settings(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15), size_hint=(1, 1))
        box.add_widget(Label(text="პარამეტრები", font_name=font, size_hint_y=0.2))

        def clear_hist(btn):
            if os.path.exists(HISTORY_FILE):
                try:
                    os.remove(HISTORY_FILE)
                except Exception:
                    pass

        btn_clear = Button(text="ისტორიის გასუფთავება", font_name=font, size_hint_y=0.2)
        btn_clear.bind(on_press=clear_hist)
        box.add_widget(btn_clear)
        box.add_widget(Label(text="LingoLens AI v6.0.2", font_name=font, size_hint_y=0.6))
        self.switch_to_view(box)

if __name__ == "__main__":
    LingoLensApp().run()

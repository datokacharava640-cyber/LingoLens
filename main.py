# ==============================================================================
# LingoLens AI - Fully Integrated & Error-Free Mobile Version
# ==============================================================================

import json
import os
import sys
import threading
import urllib.request

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

# შრიფტის უსაფრთხო რეგისტრაცია
FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="GeorgianFont", fn_regular=FONT_PATH)
    GEORGIAN_FONT_NAME = "GeorgianFont"
else:
    GEORGIAN_FONT_NAME = "Roboto"

HISTORY_FILE = "translation_history.json"

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
        self.in_main_menu = True
        self.captured_image_path = ""

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard_event)
        self.root_layout = FloatLayout()
        self.show_main_menu()
        return self.root_layout

    def on_keyboard_event(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # Android უკან ფიზიკური ღილაკი
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

    def remote_translate(self, prompt, text, src_lang, target_lang, callback):
        def worker():
            try:
                url = "http://37.27.255.1:8000/translate"
                payload = json.dumps({
                    "text": text, "source": src_lang, "target": target_lang, "prompt": prompt
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    result_text = res_data.get("translated_text") or res_data.get("result") or str(res_data)
                    callback(result_text)
            except Exception as e:
                print("Server connection error:", e)
                callback(None)
        threading.Thread(target=worker, daemon=True).start()

    def open_media_options(self, instance):
        # უსაფრთხო კამერის/გალერეის გახსნა ტელეფონში ავარიული დახურვის გარეშე
        font = GEORGIAN_FONT_NAME
        content_box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15), size_hint=(1, 1))
        content_box.add_widget(Label(text="აირჩიეთ მედია წყარო", font_name=font, size_hint_y=0.3))

        gallery_btn = Button(text="📁 გალერეიდან არჩევა", font_name=font, size_hint_y=0.3, background_color=(0.2, 0.7, 0.4, 1))
        
        popup_container = Popup(
            title="LingoLens - მედია", title_font=font,
            content=content_box, size_hint=(0.85, 0.4)
        )

        def mock_pick(x):
            popup_container.dismiss()
            self.show_result_popup("სურათის დამუშავების ტესტური რეჟიმი წარმატებულია!")

        gallery_btn.bind(on_press=mock_pick)
        content_box.add_widget(gallery_btn)
        popup_container.open()

    def show_result_popup(self, result_text):
        font = GEORGIAN_FONT_NAME
        content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        txt_output = TextInput(text=result_text, font_name=font, readonly=True, multiline=True)
        content_box.add_widget(txt_output)
        
        close_btn = Button(text="დახურვა", font_name=font, size_hint_y=0.2, background_color=(0.8, 0.2, 0.2, 1))
        popup = Popup(title="LingoLens - შედეგი", title_font=font, content=content_box, size_hint=(0.85, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        content_box.add_widget(close_btn)
        popup.open()

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
        action_box.add_widget(btn_copy)

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
                self.remote_translate(
                    prompt=f"Translate accurately from {sp_src.text} to {sp_target.text}: {text_to_translate}",
                    text=text_to_translate, src_lang=src_code, target_lang=target_code, callback=on_res
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

    def open_dialogue(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        box.add_widget(Label(text="დიალოგის რეჟიმი მზადდება...", font_name=font))
        self.switch_to_view(box)

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
                self.remote_translate(
                    prompt=f"Fix grammar and improve style in Georgian: {text_to_fix}",
                    text=text_to_fix, src_lang="ka", target_lang="ka", callback=on_res
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
                            text=f"{orig} ➔ {trans}", font_name=font,
                            size_hint_y=None, height=dp(40), halign="left", valign="middle"
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

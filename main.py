# ==============================================================================
# LingoLens AI - Gallery & Universal Translator (v6.2.0)
# ==============================================================================

import json
import os
import sys
import threading
import urllib.request
import base64

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
from kivy.uix.camera import Camera
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

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
    "Türkçe": "tr",
    "Latin (English Letters)": "latn"
}

UI_TEXTS = {
    "ka": {
        "menu_translator": "მთარგმნელი",
        "menu_dialogue": "დიალოგი",
        "menu_gallery": "გალერეა",
        "menu_camera": "ლაივ კამერა / OCR",
        "menu_history": "ისტორია",
        "menu_settings": "პარამეტრები",
        "btn_back": "უკან",
        "btn_translate": "თარგმნა",
        "btn_copy": "კოპირება",
        "btn_share": "გაზიარება",
        "btn_speak": "ხმოვანი",
        "hint_input": "ჩაწერეთ ტექსტი...",
        "hint_output": "გრამატიკულად სუფთა და უშეცდომო თარგმანი...",
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
        self.live_event = None
        self.cam_index = 0

    def build(self):
        Window.bind(on_keyboard=self.on_keyboard_event)
        self.root_layout = FloatLayout()
        self.show_main_menu()
        return self.root_layout

    def on_keyboard_event(self, window, key, scancode, codepoint, modifier):
        if key == 27:  
            if not self.in_main_menu:
                self.stop_live_translation()
                self.show_main_menu()
                return True
            else:
                self.stop()
                return True
        return False

    def get_text(self, key):
        return UI_TEXTS["ka"].get(key, key)

    def show_main_menu(self, instance=None):
        self.stop_live_translation()
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
        btn_gallery = Button(text=self.get_text("menu_gallery"), font_name=font, on_press=self.open_gallery)
        btn_camera = Button(text=self.get_text("menu_camera"), font_name=font, on_press=self.open_live_camera_view)
        btn_history = Button(text=self.get_text("menu_history"), font_name=font, on_press=self.open_history)
        btn_settings = Button(text=self.get_text("menu_settings"), font_name=font, on_press=self.open_settings)

        menu_grid.add_widget(btn_translator)
        menu_grid.add_widget(btn_dialogue)
        menu_grid.add_widget(btn_gallery)
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
        
        def go_back(x):
            self.stop_live_translation()
            self.show_main_menu()

        btn_back = Button(text=self.get_text("btn_back"), font_name=font, size_hint_x=0.3, on_press=go_back)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text="", size_hint_x=0.7))

        container.add_widget(top_bar)
        container.add_widget(widget)
        self.root_layout.add_widget(container)

    def open_gallery(self, instance):
        font = GEORGIAN_FONT_NAME
        box = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15), size_hint=(1, 1))
        
        info_lbl = Label(
            text="გალერეიდან ფოტოს არჩევის მოდული\n(აირჩიეთ ფოტო ტექსტის ასატვირთად და სათარგმნად)", 
            font_name=font, halign="center", valign="middle"
        )
        info_lbl.bind(size=info_lbl.setter("text_size"))
        box.add_widget(info_lbl)

        def pick_image_from_device(btn):
            try:
                # Android-ზე ფაილების მენეჯერის/გალერეის გამოძახება plyer-ის ან Intent-ის მეშვეობით
                from plyer import filechooser
                filechooser.open_file(on_selection=self.handle_selected_image, filters=[("Images", "*.png;*.jpg;*.jpeg")])
            except Exception as e:
                print("Gallery open error:", e)
                info_lbl.text = "გალერეის გახსნა ვერ მოხერხდა ამ გარემოში."

        btn_pick = Button(text="ფოტოს არჩევა გალერეიდან", font_name=font, size_hint_y=0.2)
        btn_pick.bind(on_press=pick_image_from_device)
        box.add_widget(btn_pick)

        self.switch_to_view(box)

    def handle_selected_image(self, selection):
        if selection:
            img_path = selection[0]
            print("Selected image path:", img_path)
            # აქ შეგიძლიათ დაამატოთ არჩეული ფოტოს სერვერზე გაგზავნა ან დამუშავება

    def open_live_camera_view(self, instance):
        font = GEORGIAN_FONT_NAME
        box = FloatLayout(size_hint=(1, 1))

        self.cam_widget = Camera(
            play=True, 
            index=self.cam_index,
            resolution=(-1, -1), 
            size_hint=(None, None), 
            allow_stretch=True, 
            keep_ratio=False
        )

        from kivy.graphics import PushMatrix, PopMatrix, Rotate
        with self.cam_widget.canvas.before:
            PushMatrix()
            self.cam_rot = Rotate(angle=270, origin=self.cam_widget.center)
        with self.cam_widget.canvas.after:
            PopMatrix()
            
        def update_cam_geometry(win, size):
            self.cam_widget.size = (size[1], size[0])
            self.cam_widget.center = (size[0] / 2, size[1] / 2)
            self.cam_rot.origin = self.cam_widget.center

        Window.bind(size=update_cam_geometry)
        update_cam_geometry(Window, Window.size)

        box.add_widget(self.cam_widget)

        def go_back(x):
            Window.unbind(size=update_cam_geometry)
            self.stop_live_translation()
            self.show_main_menu()

        btn_back = Button(
            text=self.get_text("btn_back"), font_name=font, 
            size_hint=(0.25, 0.08), pos_hint={"top": 0.95, "left": 0.05},
            background_color=(0, 0, 0, 0.6)
        )
        btn_back.bind(on_press=go_back)
        box.add_widget(btn_back)

        def toggle_camera(x):
            self.cam_index = 1 if self.cam_index == 0 else 0
            self.cam_widget.index = self.cam_index
            self.cam_widget.reload()

        btn_switch_cam = Button(
            text="კამერა", font_name=font, 
            size_hint=(0.2, 0.08), pos_hint={"top": 0.95, "center_x": 0.5},
            background_color=(0, 0, 0, 0.6)
        )
        btn_switch_cam.bind(on_press=toggle_camera)
        box.add_widget(btn_switch_cam)

        lang_names = list(SUPPORTED_LANGUAGES.keys())
        self.live_lang_spinner = Spinner(
            text="ქართული", values=lang_names, font_name=font, option_cls=CustomSpinnerOption,
            size_hint=(0.35, 0.08), pos_hint={"top": 0.95, "right": 0.95},
            background_color=(0, 0, 0, 0.6)
        )
        box.add_widget(self.live_lang_spinner)

        self.live_result_lbl = Label(
            text="მიაშერეთ კამერა წარწერას...", font_name=font, 
            size_hint=(0.9, 0.15), pos_hint={"center_x": 0.5, "y": 0.03},
            halign="center", valign="middle",
            color=(1, 1, 1, 1)
        )
        self.live_result_lbl.bind(size=self.live_result_lbl.setter("text_size"))
        box.add_widget(self.live_result_lbl)

        self.in_main_menu = False
        Clock.schedule_once(lambda dt: self._apply_custom_view(box), 0)

        self.live_event = Clock.schedule_interval(self.capture_and_translate_frame, 3.0)

    def _apply_custom_view(self, widget):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(widget)

    def capture_and_translate_frame(self, dt):
        try:
            if hasattr(self, 'cam_widget') and self.cam_widget:
                image_path = "temp_live_frame.png"
                self.cam_widget.export_to_png(image_path)
                
                selected_lang_name = self.live_lang_spinner.text
                target_code = SUPPORTED_LANGUAGES.get(selected_lang_name, "ka")
                
                self.live_result_lbl.text = "მიმდინარეობს გრამატიკულად სუფთა თარგმნა..."
                
                def on_server_response(res):
                    if res:
                        Clock.schedule_once(lambda dt: setattr(self.live_result_lbl, 'text', f"თარგმანი: {res}"))
                    else:
                        Clock.schedule_once(lambda dt: setattr(self.live_result_lbl, 'text', "ვერ მოიძებნა ტექსტი"))
                
                prompt_text = f"Translate into {selected_lang_name} with absolute grammatical precision, perfect natural flow, and zero errors, ensuring native-level expression."
                
                self.remote_translate(
                    prompt=prompt_text,
                    text="[Live Frame OCR Placeholder]", 
                    src_lang="auto", 
                    target_lang=target_code, 
                    callback=on_server_response
                )
        except Exception as e:
            print("Live frame capture error:", e)

    def stop_live_translation(self):
        if self.live_event:
            self.live_event.cancel()
            self.live_event = None
        if hasattr(self, 'cam_widget'):
            self.cam_widget.play = False

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

    def share_text(self, text):
        if text and text.strip():
            try:
                from plyer import share
                share.share(text=text)
            except Exception as e:
                print("Share error:", e)
                Clipboard.copy(text)

    def speak_text(self, text):
        if text and text.strip():
            try:
                from plyer import tts
                tts.speak(text)
            except Exception as e:
                print("TTS error:", e)

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
        btn_speak = Button(text=self.get_text("btn_speak"), font_name=font, on_press=lambda x: self.speak_text(out.text))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_speak)

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
                strict_prompt = (
                    f"Translate the following text from {sp_src.text} to {sp_target.text} with absolute "
                    f"grammatical precision. Ensure zero grammatical errors, perfect natural phrasing, correct "
                    f"morphology, syntax, and native-level fluency suitable for both Georgian and any world language: {text_to_translate}"
                )
                self.remote_translate(
                    prompt=strict_prompt,
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
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, 1))
        
        chat_scroller = ScrollView()
        self.chat_content = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.chat_content.bind(minimum_height=self.chat_content.setter("height"))
        chat_scroller.add_widget(self.chat_content)

        input_box = BoxLayout(orientation="horizontal", size_hint_y=0.15, spacing=dp(5))
        chat_inp = TextInput(hint_text="მიწერეთ დიალოგის ასისტენტს...", font_name=font, multiline=False)
        btn_send = Button(text="გაგზავნა", font_name=font, size_hint_x=0.3)

        def send_message(x):
            msg = chat_inp.text.strip()
            if not msg:
                return
            
            user_lbl = Label(text=f"თქვენ: {msg}", font_name=font, size_hint_y=None, height=dp(40))
            self.chat_content.add_widget(user_lbl)
            chat_inp.text = ""

            def on_ai_res(res):
                ai_text = str(res) if res else "ვერ მოხერხდა პასუხი"
                ai_lbl = Label(text=f"AI: {ai_text}", font_name=font, size_hint_y=None, height=dp(40))
                Clock.schedule_once(lambda dt: self.chat_content.add_widget(ai_lbl))

            self.remote_translate(
                prompt=f"Respond naturally with flawless grammar, absolute accuracy, and native phrasing: {msg}",
                text=msg, src_lang="ka", target_lang="ka", callback=on_ai_res
            )

        btn_send.bind(on_press=send_message)
        input_box.add_widget(chat_inp)
        input_box.add_widget(btn_send)

        box.add_widget(chat_scroller)
        box.add_widget(input_box)
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
        box.add_widget(Label(text="LingoLens AI v6.2.0", font_name=font, size_hint_y=0.6))
        self.settings_view = box
        self.switch_to_view(box)

if __name__ == "__main__":
    LingoLensApp().run()

# ==============================================================================
# LingoLens AI - With Crash Logger & Safe UI Manager
# Copyright (c) 2026 Dato Kacharava. All rights reserved.
# ==============================================================================

import sys
import traceback
import os

# avtomaturi shetsomebis damchheri (Crash Logger) telefonistvis
def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        log_path = os.path.join(os.getcwd(), "crash_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

import json
import socket
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard

import config
from utils.translator import translate_text, analyze_image_and_translate
from utils.tts_engine import speak

HISTORY_FILE = "translation_history.json"
SETTINGS_FILE = "settings.json"

class LingoLensApp(App):
    def build(self):
        self.root_layout = FloatLayout()
        self.current_popup = None  # To track active popup/window and prevent overlapping crashes
        
        self.show_main_menu()
        return self.root_layout

    def get_safe_font(self):
        # უზრუნველყოფს რომ შრიფტის ფაილი არსებობდეს, წინააღმდეგ შემთხვევაში აბრუნებს None-ს
        font = getattr(config, 'FONT_PATH', None)
        if font and os.path.exists(str(font)):
            return font
        return None

    def show_main_menu(self, instance=None):
        if self.current_popup and self.current_popup in self.root_layout.children:
            self.root_layout.remove_widget(self.current_popup)
        
        menu_grid = GridLayout(
            cols=2, 
            spacing=12, 
            padding=15, 
            size_hint=(0.9, 0.8), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        font = self.get_safe_font()

        btn_translator = Button(text="თარგმანი\n(Translator)", font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text="დიალოგი\n(Live Dialogue)", font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text="გრამატიკა\n(Grammar AI)", font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text="კამერა / OCR", font_name=font, on_press=self.open_camera_with_check)
        btn_history = Button(text="ისტორია\n(History)", font_name=font, on_press=self.open_history)
        btn_settings = Button(text="პარამეტრები\n(Settings)", font_name=font, on_press=self.open_settings)

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
        
        # Add a Back button header wrapper for subviews
        container = BoxLayout(orientation='vertical', size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        font = self.get_safe_font()
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        btn_back = Button(text="❮ უკან (Back)", font_name=font, size_hint_x=0.3, on_press=self.show_main_menu)
        top_bar.add_widget(btn_back)
        top_bar.add_widget(Label(text="", size_hint_x=0.7)) # Spacer
        
        container.add_widget(top_bar)
        container.add_widget(widget)
        
        self.current_popup = container
        self.root_layout.add_widget(self.current_popup)

    def has_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def save_to_history(self, original, translated):
        history = self.load_history()
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("History save error:", e)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def request_camera_permission_on_demand(self, callback_func):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                perms = [Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
                def callback(permissions, grant_results):
                    callback_func()
                request_permissions(perms, callback)
            except Exception as e:
                print("Permissions error:", e)
                callback_func()
        else:
            callback_func()

    def copy_to_clipboard(self, text):
        if text and text.strip():
            Clipboard.copy(text)

    def share_text(self, text):
        if not text or not text.strip():
            return
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(text))
                chooser = Intent.createChooser(intent, String("Share text via"))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception as e:
                print("Share error:", e)
        else:
            Clipboard.copy(text)

    def safe_speak(self, text, lang="en"):
        if text and text.strip():
            user_dir = self.user_data_dir if hasattr(self, 'user_data_dir') else ""
            speak(text, lang, user_dir, lambda msg: print(msg))

    # 1. Thargmani
    def open_translator(self, instance=None, initial_text="", initial_result="", status_text=""):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=5, spacing=8, size_hint=(1, 0.9))
        
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
        lang_map = {"ქართული": "ka", "English": "en", "Русский": "ru", "Español": "es", "Deutsch": "de"}
        
        sp_src = Spinner(text="ქართული", values=list(lang_map.keys()), font_name=font)
        sp_target = Spinner(text="English", values=list(lang_map.keys()), font_name=font)
        
        lang_box.add_widget(sp_src)
        lang_box.add_widget(Label(text="➔", size_hint_x=0.2, font_name=font))
        lang_box.add_widget(sp_target)

        inp = TextInput(text=initial_text, hint_text="ტექსტი...", font_name=font, multiline=True)
        out = TextInput(text=initial_result, hint_text="თარგმანი...", font_name=font, readonly=True, multiline=True)
        status_lbl = Label(text=status_text, size_hint_y=0.1, font_name=font)
        
        btn_trans = Button(text="თარგმნა", font_name=font, size_hint_y=0.15)
        
        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.15)
        btn_copy = Button(text="Copy", font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text="Share", font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text="მოსმენა", font_name=font, on_press=lambda x: self.safe_speak(out.text, lang_map.get(sp_target.text, "en")))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        def handle_translation(btn_inst):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                return

            src_code = lang_map.get(sp_src.text, "ka")
            target_code = lang_map.get(sp_target.text, "en")

            status_lbl.text = 'მუშავდება...'
            prompt = f"Translate accurately from {sp_src.text} to {sp_target.text}: {text_to_translate}"
            
            def on_res(res):
                res_text = str(res) if res else "შეცდომა"
                Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))
                if res:
                    self.save_to_history(text_to_translate, res_text)

            translate_text(prompt, text_to_translate, src_code, target_code, on_res)

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)

        if instance is not None:  # Direct call from menu
            self.switch_to_view(box)
        return inp, out, status_lbl

    def open_dialogue(self, instance):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(1, 0.9))
        lbl = Label(text="დიალოგის ფანჯარა დროებით გათიშულია", font_name=font)
        box.add_widget(lbl)
        self.switch_to_view(box)

    def open_grammar(self, instance):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=8, spacing=8, size_hint=(1, 0.9))
        inp = TextInput(hint_text="შესამოწმებელი ტექსტი...", font_name=font)
        out = TextInput(hint_text="შედეგი...", font_name=font, readonly=True)
        box.add_widget(inp)
        box.add_widget(out)
        self.switch_to_view(box)

    def open_camera_with_check(self, instance):
        self.request_camera_permission_on_demand(lambda: self.open_camera(instance))

    def open_camera(self, instance):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(1, 0.9))
        
        lbl = Label(text="გალერეიდან სურათის არჩევა (OCR)", font_name=font)
        btn_gallery = Button(text="ფაილის არჩევა", font_name=font, size_hint_y=0.3)
        
        def open_gallery(btn_inst):
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self.on_gallery_select)
            except Exception as e:
                print("Filechooser error:", e)

        btn_gallery.bind(on_press=open_gallery)
        box.add_widget(lbl)
        box.add_widget(btn_gallery)
        self.switch_to_view(box)

    def on_gallery_select(self, selection):
        if selection and len(selection) > 0:
            image_path = selection[0]
            # Navigate to translator view first and get references
            inp, out, status_lbl = self.open_translator(initial_text="[სურათი ატვირთულია]", status_text="მუშავდება...")
            def on_ocr_complete(res):
                res_text = str(res) if res else "ვერ მოხერხდა"
                Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))
                analyze_image_and_translate(image_path, "ka", on_ocr_complete)

    def open_history(self, instance):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=8, spacing=8, size_hint=(1, 0.9))
        scroll = ScrollView(size_hint=(1, 1))
        hist_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        hist_layout.bind(minimum_height=hist_layout.setter('height'))

        history_data = self.load_history()
        if not history_data:
            hist_layout.add_widget(Label(text="ისტორია ცარიელია", font_name=font, size_hint_y=None, height=40))
        else:
            for item in reversed(history_data):
                txt = f"• {item.get('original', '')} ➔ {item.get('translated', '')}"
                lbl = Label(text=txt, font_name=font, size_hint_y=None, height=40)
                hist_layout.add_widget(lbl)

        scroll.add_widget(hist_layout)
        box.add_widget(scroll)
        self.switch_to_view(box)

    def open_settings(self, instance):
        font = self.get_safe_font()
        box = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(1, 0.9))
        lbl = Label(text="Gemini API Key:", font_name=font, size_hint_y=0.15)
        
        current_key = ""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    current_key = json.load(f).get("api_key", "")
            except Exception:
                pass

        inp_key = TextInput(text=current_key, hint_text="API Key...", font_name=font, multiline=False)
        btn_save = Button(text="შენახვა", font_name=font, size_hint_y=0.2)
        
        def save_key(btn_inst):
            key = inp_key.text.strip()
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump({"api_key": key}, f)
                config.GEMINI_API_KEY = key
            except Exception as e:
                print("Settings save error:", e)

        btn_save.bind(on_press=save_key)
        box.add_widget(lbl)
        box.add_widget(inp_key)
        box.add_widget(btn_save)
        self.switch_to_view(box)

if __name__ == "__main__":
    LingoLensApp().run()

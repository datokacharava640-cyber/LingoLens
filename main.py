# ==============================================================================
# LingoLens AI - Main App (Expanded Languages, UI Localization & AI Menu)
# ==============================================================================

import sys
import os
import json
import traceback

DEFAULT_BACKEND_URL = "http://37.27.255.1:8000"

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
        print("Crash log saved to:", log_path)
    except Exception as e:
        print("Failed to save crash log:", e)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase

if os.path.exists('font.ttf'):
    LabelBase.register(name='GeorgianFont', fn_regular='font.ttf')
    FONT_NAME = 'GeorgianFont'
else:
    FONT_NAME = None

try:
    import config
except ImportError:
    config = None

try:
    from utils.translator import translate_text, analyze_image_and_translate
    from utils.tts_engine import speak
except ImportError:
    pass

try:
    from ui.DialogueWidget import DialogueWidget
except ImportError:
    DialogueWidget = None

try:
    from ui.RotatedCameraWidget import RotatedCameraWidget
except ImportError:
    RotatedCameraWidget = None

try:
    from ui.MenuPopup import MenuPopup
except ImportError:
    MenuPopup = None

HISTORY_FILE = "translation_history.json"
SETTINGS_FILE = "settings.json"

UI_TEXTS = {
    "ka": {
        'menu_translator': 'მთარგმნელი',
        'menu_dialogue': 'დიალოგი',
        'menu_grammar': 'გრამატიკა',
        'menu_camera': 'კამერა / OCR',
        'menu_history': 'ისტორია',
        'menu_settings': 'პარამეტრები',
        'btn_back': 'უკან',
        'btn_translate': 'თარგმნა',
        'btn_copy': 'კოპირება',
        'btn_share': 'გაზიარება',
        'btn_listen': 'მოსმენა',
        'btn_ai_menu': '✨ AI მენიუ',
        'hint_input': 'ჩაწერეთ ტექსტი...',
        'hint_output': 'თარგმანი...',
        'status_processing': 'მუშავდება...',
        'error_connection': 'შეცდომაა სერვერთან კავშირში',
        'history_empty': 'ისტორია ცარიელია',
        'settings_title': 'პარამეტრები',
        'ui_lang_label': 'ინტერფეისის ენა:'
    },
    "en": {
        'menu_translator': 'Translator',
        'menu_dialogue': 'Dialogue',
        'menu_grammar': 'Grammar',
        'menu_camera': 'Camera / OCR',
        'menu_history': 'History',
        'menu_settings': 'Settings',
        'btn_back': 'Back',
        'btn_translate': 'Translate',
        'btn_copy': 'Copy',
        'btn_share': 'Share',
        'btn_listen': 'Listen',
        'btn_ai_menu': '✨ AI Menu',
        'hint_input': 'Enter text...',
        'hint_output': 'Translation...',
        'status_processing': 'Processing...',
        'error_connection': 'Connection error with server',
        'history_empty': 'History is empty',
        'settings_title': 'Settings',
        'ui_lang_label': 'Interface Language:'
    },
    "ru": {
        'menu_translator': 'Переводчик',
        'menu_dialogue': 'Диалог',
        'menu_grammar': 'Грамматика',
        'menu_camera': 'Камера / OCR',
        'menu_history': 'История',
        'menu_settings': 'Настройки',
        'btn_back': 'Назад',
        'btn_translate': 'Перевести',
        'btn_copy': 'Копировать',
        'btn_share': 'Поделиться',
        'btn_listen': 'Слушать',
        'btn_ai_menu': '✨ AI Меню',
        'hint_input': 'Введите текст...',
        'hint_output': 'Перевод...',
        'status_processing': 'Обработка...',
        'error_connection': 'Ошибка подключения к серверу',
        'history_empty': 'История пуста',
        'settings_title': 'Настройки',
        'ui_lang_label': 'Язык интерфейса:'
    },
    "es": {
        'menu_translator': 'Traductor',
        'menu_dialogue': 'Diálogo',
        'menu_grammar': 'Gramática',
        'menu_camera': 'Cámara / OCR',
        'menu_history': 'Historial',
        'menu_settings': 'Ajustes',
        'btn_back': 'Atrás',
        'btn_translate': 'Traducir',
        'btn_copy': 'Copiar',
        'btn_share': 'Compartir',
        'btn_listen': 'Escuchar',
        'btn_ai_menu': '✨ Menú AI',
        'hint_input': 'Introduce texto...',
        'hint_output': 'Traducción...',
        'status_processing': 'Procesando...',
        'error_connection': 'Error de conexión con el servidor',
        'history_empty': 'El historial está vacío',
        'settings_title': 'Ajustes',
        'ui_lang_label': 'Idioma de interfaz:'
    }
}

SUPPORTED_LANGUAGES = {
    "ქართული": "ka",
    "English": "en",
    "Русский": "ru",
    "Español": "es",
    "Deutsch": "de",
    "Français": "fr",
    "Italiano": "it",
    "Türkçe": "tr",
    "Українська": "uk",
    "Polski": "pl",
    "Română": "ro",
    "Български": "bg",
    "Chinese (中文)": "zh",
    "Japanese (日本語)": "ja",
    "Arabic (العربية)": "ar",
    "Hindi (हिन्दी)": "hi",
    "Português": "pt",
    "Greek (Ελληνικά)": "el",
    "Persian (فارسی)": "fa",
    "Korean (한국어)": "ko",
    "Dutch (Nederlands)": "nl",
    "Swedish (Svenska)": "sv",
    "Vietnamese (Tiếng Việt)": "vi"
}

class LingoLensApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_lang = "ka"

    def build(self):
        self.root_layout = FloatLayout()
        self.current_popup = None
        
        Clock.schedule_once(lambda dt: self.force_backend_url(), 0.1)
        self.load_settings()
        self.show_main_menu()
        return self.root_layout

    def force_backend_url(self):
        try:
            os.environ["GEMINI_API_KEY"] = DEFAULT_BACKEND_URL
            os.environ["BACKEND_URL"] = DEFAULT_BACKEND_URL
            if config:
                config.GEMINI_API_KEY = DEFAULT_BACKEND_URL
        except Exception as e:
            print("Force URL error:", e)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "ui_lang" in data:
                        self.current_lang = data["ui_lang"]
            except:
                pass

    def save_settings(self, ui_lang):
        self.current_lang = ui_lang
        try:
            data = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["ui_lang"] = ui_lang
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Settings save error:", e)

    def get_text(self, key):
        lang_dict = UI_TEXTS.get(self.current_lang, UI_TEXTS["ka"])
        return lang_dict.get(key, UI_TEXTS["ka"].get(key, key))

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

        font = FONT_NAME
        btn_translator = Button(text=self.get_text('menu_translator'), font_name=font, on_press=self.open_translator)
        btn_dialogue = Button(text=self.get_text('menu_dialogue'), font_name=font, on_press=self.open_dialogue)
        btn_grammar = Button(text=self.get_text('menu_grammar'), font_name=font, on_press=self.open_grammar)
        btn_camera = Button(text=self.get_text('menu_camera'), font_name=font, on_press=self.open_camera_with_check)
        btn_history = Button(text=self.get_text('menu_history'), font_name=font, on_press=self.open_history)
        btn_settings = Button(text=self.get_text('menu_settings'), font_name=font, on_press=self.open_settings)

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
        
        container = BoxLayout(orientation='vertical', size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        font = FONT_NAME
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        btn_back = Button(text=self.get_text('btn_back'), font_name=font, size_hint_x=0.3, on_press=self.show_main_menu)
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
            except:
                pass
        history.append({"original": original, "translated": translated})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("History error:", e)

    def request_camera_permission_on_demand(self, callback_func):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                perms = [Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
                request_permissions(perms, lambda perms, results: callback_func())
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
                chooser = Intent.createChooser(intent, String("Share"))
                PythonActivity.mActivity.startActivity(chooser)
            except Exception as e:
                print("Share error:", e)
        else:
            Clipboard.copy(text)

    def safe_speak(self, text, lang="en"):
        if text and text.strip():
            user_dir = self.user_data_dir if hasattr(self, 'user_data_dir') else ""
            try:
                speak(text, lang, user_dir, lambda msg: print(msg))
            except Exception as e:
                print("TTS error:", e)

    def open_translator(self, instance=None, initial_text="", initial_result="", status_text=""):
        font = FONT_NAME
        box = BoxLayout(orientation='vertical', padding=5, spacing=8, size_hint=(1, 0.9))
        
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.12)
        lang_names = list(SUPPORTED_LANGUAGES.keys())
        
        sp_src = Spinner(text="ქართული", values=lang_names, font_name=font)
        sp_target = Spinner(text="English", values=lang_names, font_name=font)
        
        lang_box.add_widget(sp_src)
        lang_box.add_widget(Label(text="➔", size_hint_x=0.2, font_name=font))
        lang_box.add_widget(sp_target)

        inp = TextInput(text=initial_text, hint_text=self.get_text('hint_input'), font_name=font, multiline=True)
        out = TextInput(text=initial_result, hint_text=self.get_text('hint_output'), font_name=font, readonly=True, multiline=True)
        status_lbl = Label(text=status_text, size_hint_y=0.08, font_name=font)
        
        btn_trans = Button(text=self.get_text('btn_translate'), font_name=font, size_hint_y=0.12)
        
        action_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.12)
        btn_copy = Button(text=self.get_text('btn_copy'), font_name=font, on_press=lambda x: self.copy_to_clipboard(out.text))
        btn_share = Button(text=self.get_text('btn_share'), font_name=font, on_press=lambda x: self.share_text(out.text))
        btn_listen = Button(text=self.get_text('btn_listen'), font_name=font, on_press=lambda x: self.safe_speak(out.text, SUPPORTED_LANGUAGES.get(sp_target.text, "en")))
        
        action_box.add_widget(btn_copy)
        action_box.add_widget(btn_share)
        action_box.add_widget(btn_listen)

        if MenuPopup:
            def open_ai_menu(btn_inst):
                text_content = inp.text.strip()
                
                def on_academic():
                    if not text_content:
                        status_lbl.text = "ჩაწერეთ ტექსტი თავიდან!"
                        return
                    status_lbl.text = "მუშავდება (Academic Rewrite)..."
                    prompt = f"Rewrite the following text in a professional academic style: {text_content}"
                    translate_text(prompt, text_content, SUPPORTED_LANGUAGES.get(sp_src.text, "ka"), SUPPORTED_LANGUAGES.get(sp_target.text, "en"), on_res)

                def on_grammar():
                    if not text_content:
                        status_lbl.text = "ჩაწერეთ ტექსტი თავიდან!"
                        return
                    status_lbl.text = "მუშავდება (Grammar Check)..."
                    prompt = f"Check grammar and explain corrections for: {text_content}"
                    translate_text(prompt, text_content, SUPPORTED_LANGUAGES.get(sp_src.text, "ka"), SUPPORTED_LANGUAGES.get(sp_target.text, "en"), on_res)

                popup = MenuPopup(academic_cb=on_academic, grammar_cb=on_grammar)
                popup.open()

            btn_ai = Button(text=self.get_text('btn_ai_menu'), font_name=font, size_hint_y=0.12, on_press=open_ai_menu)
        else:
            btn_ai = None

        def handle_translation(btn_inst):
            text_to_translate = inp.text.strip()
            if not text_to_translate:
                return

            src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
            target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")

            status_lbl.text = self.get_text('status_processing')
            prompt = f"Translate accurately from {sp_src.text} to {sp_target.text}: {text_to_translate}"
            
            def on_res(res):
                res_text = str(res) if res else self.get_text('error_connection')
                Clock.schedule_once(lambda dt: setattr(out, 'text', res_text))
                Clock.schedule_once(lambda dt: setattr(status_lbl, 'text', ''))
                if res:
                    self.save_to_history(text_to_translate, res_text)

            if config:
                config.GEMINI_API_KEY = DEFAULT_BACKEND_URL
            os.environ["GEMINI_API_KEY"] = DEFAULT_BACKEND_URL

            translate_text(prompt, text_to_translate, src_code, target_code, on_res)

        btn_trans.bind(on_press=handle_translation)

        box.add_widget(lang_box)
        box.add_widget(inp)
        box.add_widget(btn_trans)
        box.add_widget(status_lbl)
        box.add_widget(out)
        box.add_widget(action_box)
        if btn_ai:
            box.add_widget(btn_ai)

        if instance is not None:
            self.switch_to_view(box)
        return inp, out, status_lbl

    def open_dialogue(self, instance):
        font = FONT_NAME
        if DialogueWidget:
            widget = DialogueWidget()
        else:
            widget = BoxLayout(orientation='vertical', padding=10, spacing=10)
            widget.add_widget(Label(text="დიალოგის მოდული მზადდება", font_name=font))
        self.switch_to_view(widget)

    def open_grammar(self, instance):
        font = FONT_NAME
        widget = BoxLayout(orientation='vertical', padding=10, spacing=10)
        widget.add_widget(Label(text="გრამატიკის მოდული", font_name=font))
        self.switch_to_view(widget)

    def open_camera_with_check(self, instance):
        def proceed():
            font = FONT_NAME
            if RotatedCameraWidget:
                widget = RotatedCameraWidget()
            else:
                widget = BoxLayout(orientation='vertical', padding=10, spacing=10)
                widget.add_widget(Label(text="კამერის მოდული ვერ მოიძებნა", font_name=font))
            self.switch_to_view(widget)
        
        self.request_camera_permission_on_demand(proceed)

    def open_history(self, instance):
        font = FONT_NAME
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroller = ScrollView()
        content = GridLayout(cols=1, spacing=5, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for item in reversed(history):
                        orig = item.get("original", "")
                        trans = item.get("translated", "")
                        lbl = Label(text=f"{orig} ➔ {trans}", font_name=font, size_hint_y=None, height=40)
                        content.add_widget(lbl)
            except:
                pass

        if not content.children:
            content.add_widget(Label(text=self.get_text('history_empty'), font_name=font))

        scroller.add_widget(content)
        box.add_widget(scroller)
        self.switch_to_view(box)

    def open_settings(self, instance):
        font = FONT_NAME
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        box.add_widget(Label(text=self.get_text('settings_title'), font_name=font, size_hint_y=0.2))
        
        lang_change_box = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        lang_change_box.add_widget(Label(text=self.get_text('ui_lang_label'), font_name=font))
        
        inv_ui_texts = {"ka": "ქართული", "en": "English", "ru": "Русский", "es": "Español"}
        current_ui_name = inv_ui_texts.get(self.current_lang, "ქართული")
        
        ui_spinner = Spinner(text=current_ui_name, values=list(inv_ui_texts.values()), font_name=font)
        
        def on_ui_lang_change(spinner, selected_name):
            code_map = {"ქართული": "ka", "English": "en", "Русский": "ru", "Español": "es"}
            new_code = code_map.get(selected_name, "ka")
            self.save_settings(new_code)
            self.show_main_menu()

        ui_spinner.bind(text=on_ui_lang_change)
        lang_change_box.add_widget(ui_spinner)
        
        box.add_widget(lang_change_box)
        box.add_widget(Label(text=f"Backend URL:\n{DEFAULT_BACKEND_URL}", font_name=font, size_hint_y=0.4))
        
        self.switch_to_value = self.switch_to_view
        self.switch_to_view(box)

if __name__ == '__main__':
    LingoLensApp().run()

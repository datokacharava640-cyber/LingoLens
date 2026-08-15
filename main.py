import os
import sys
import json
import threading
import requests

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock

# =====================================================================
# 1. UI დიზაინის შაბლონები (Cyber Dark Theme)
# =====================================================================
KV_DESIGN = """
<RoundedButton>:
    background_color: (0, 0, 0, 0)
    background_normal: ''
    color: (1, 1, 1, 1)
    bold: True
    font_size: '12sp'
    canvas.before:
        Color:
            rgba: self.bg_color if hasattr(self, 'bg_color') else (0.2, 0.4, 0.8, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [12,]

<CardLayout>:
    orientation: 'vertical'
    padding: 10
    spacing: 6
    canvas.before:
        Color:
            rgba: (0.1, 0.12, 0.18, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [14,]
"""

Builder.load_string(KV_DESIGN)

DEFAULT_API_KEY = ""  
CONFIG_FILE = "lingolens_config.json"

class RoundedButton(Button):
    def __init__(self, bg_color=(0.2, 0.4, 0.8, 1), **kwargs):
        self.bg_color = bg_color
        super().__init__(**kwargs)

class CardLayout(BoxLayout):
    pass

# =====================================================================
# 2. ქართული შრიფტის ჩატვირთვა
# =====================================================================
GEORGIAN_FONT = None

possible_fonts = [
    "NotoSansGeorgian-Regular.ttf",
    "NotoSansGeorgian.ttf",
    "georgian.ttf",
    "font.ttf"
]
font_path = None

for f in possible_fonts:
    if os.path.exists(f):
        font_path = f
        break

if font_path:
    try:
        LabelBase.register(name="Roboto", fn_regular=font_path)
        LabelBase.register(name="GeorgianFont", fn_regular=font_path)
        GEORGIAN_FONT = "GeorgianFont"
    except Exception as font_err:
        print(f"Font Load Warning: {font_err}")

# =====================================================================
# 3. მთავარი აპლიკაცია
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8
        self.api_key = self.load_saved_api_key()
        self.tts = None

        if platform == 'android':
            Clock.schedule_once(self.init_android_tts, 1)

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Ultra Pro[/b]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.06,
            color=(0.38, 0.72, 1, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.title_label)

        # Status Bar
        status_txt = "Gemini AI აქტიურია | მზადაა" if self.api_key else "მზადაა | AI მოდულები ჩატვირთულია"
        self.status_label = Label(
            text=status_txt,
            color=(0.3, 0.9, 0.5, 1),
            font_size='12sp',
            size_hint_y=0.04,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.status_label)

        # Input & Output Display Card
        display_card = CardLayout(size_hint_y=0.45)

        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            multiline=True,
            size_hint_y=0.55,
            font_size='14sp',
            background_color=(0.06, 0.07, 0.1, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.38, 0.72, 1, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.text_input)

        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='14sp',
            size_hint_y=0.45,
            color=(0.85, 0.88, 0.95, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.output_label)

        self.add_widget(display_card)

        # ---------------- ძირითადი ფუნქციების პანელი ----------------
        main_actions = GridLayout(cols=3, spacing=6, size_hint_y=0.1)

        btn_trans = RoundedButton(text="AI თარგმნა", bg_color=(0.1, 0.6, 0.4, 1), font_name=GEORGIAN_FONT if GEORGIAN_FONT else None)
        btn_trans.bind(on_press=self.translate_text)

        btn_tts = RoundedButton(text="წაკითხვა", bg_color=(0.2, 0.4, 0.8, 1), font_name=GEORGIAN_FONT if GEORGIAN_FONT else None)
        btn_tts.bind(on_press=self.speak_georgian)

        btn_copy = RoundedButton(text="დაკოპირება", bg_color=(0.3, 0.5, 0.6, 1), font_name=GEORGIAN_FONT if GEORGIAN_FONT else None)
        btn_copy.bind(on_press=self.copy_translation)

        main_actions.add_widget(btn_trans)
        main_actions.add_widget(btn_tts)
        main_actions.add_widget(btn_copy)

        self.add_widget(main_actions)

        # ---------------- ჩამოშლადი მენიუ (Dropdown Menu) ----------------
        self.menu_btn = RoundedButton(
            text="☰ აირჩიეთ მოდული / მენიუ",
            bg_color=(0.15, 0.2, 0.3, 1),
            size_hint_y=0.08,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.dropdown = DropDown()

        modules_list = [
            ("🚀 Next-Gen Features (5 ინოვაციური ფუნქცია)", "next_gen_features"),
            ("⚡ Super Features (5 ახალი ფუნქცია)", "super_features"),
            ("💬 SMS Translator (ენების გადამრთველით)", "sms_translator"),
            ("📷 AR Camera OCR", "ar_camera"),
            ("🎙️ Hands-Free Live", "live_interpreter"),
            ("💬 Floating Bubble", "floating_bubble"),
            ("🗣️ Voice Clone", "voice_clone"),
            ("📻 Walkie Talkie", "walkie_talkie"),
            ("📄 Doc Summarizer", "doc_summarizer"),
            ("🎓 Coach Mode", "coach_mode"),
            ("🔍 Slang Decoder", "slang_decoder"),
            ("🚨 Travel SOS", "travel_sos"),
            ("⌚ Smartwatch Sync", "smartwatch"),
            ("✈️ Offline Mode", "offline_mode"),
            ("🔥 Streak System", "streak_system"),
            ("🎁 Referral System", "referral_system"),
            ("🚀 Viral Share", "viral_share"),
            ("🛠️ Design & Tools", "design_and_tools"),
            ("💡 Smart Features", "smart_features"),
            ("🔊 Wake Word", "wake_word")
        ]

        for title, mod_name in modules_list:
            btn = Button(
                text=title,
                size_hint_y=None,
                height=48,
                background_color=(0.1, 0.15, 0.25, 1),
                color=(1, 1, 1, 1),
                font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
            )
            
            if mod_name == "floating_bubble":
                btn.bind(on_release=lambda x: (self.run_floating_bubble(None), self.dropdown.dismiss()))
            else:
                btn.bind(on_release=lambda x, m=mod_name: (self.run_module(m), self.dropdown.dismiss()))
                
            self.dropdown.add_widget(btn)

        self.menu_btn.bind(on_release=self.dropdown.open)
        self.add_widget(self.menu_btn)

        # ---------------- API Key ღილაკი ----------------
        api_btn = RoundedButton(
            text="Gemini API Key პარამეტრები",
            bg_color=(0.25, 0.25, 0.35, 1),
            size_hint_y=0.07,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        api_btn.bind(on_press=self.open_api_popup)
        self.add_widget(api_btn)

    def load_saved_api_key(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    saved_key = data.get("api_key", "")
                    if saved_key:
                        return saved_key
            except Exception as e:
                print(f"Config Load Error: {e}")
        return DEFAULT_API_KEY

    def save_api_key(self, key):
        self.api_key = key
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"api_key": key}, f)
        except Exception as e:
            print(f"Config Save Error: {e}")

    def init_android_tts(self, dt):
        try:
            from jnius import autoclass
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            self.tts = TextToSpeech(PythonActivity.mActivity, None)
            georgian_locale = Locale("ka", "GE")
            self.tts.setLanguage(georgian_locale)
        except Exception as e:
            print(f"TTS Init Warning: {e}")

    def copy_translation(self, instance):
        if self.output_label.text and not self.output_label.text.startswith("["):
            Clipboard.copy(self.output_label.text)
            self.status_label.text = "ტექსტი დაკოპირდა!"

    def start_background_wake_word(self):
        def listen_loop():
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                modules_dir = os.path.join(base_dir, 'modules')
                if modules_dir not in sys.path:
                    sys.path.append(modules_dir)

                import wake_word
                for func in ['start', 'run', 'main', 'listen']:
                    if hasattr(wake_word, func):
                        getattr(wake_word, func)(api_key=self.api_key)
                        break
            except Exception as e:
                print(f"Wake Word Warning: {e}")

        threading.Thread(target=listen_loop, daemon=True).start()

    def translate_text(self, instance):
        input_txt = self.text_input.text.strip()
        if not input_txt:
            self.output_label.text = "გთხოვთ, ჩაწეროთ ტექსტი!"
            return

        self.status_label.text = "AI თარგმნის..."

        if self.api_key and self.api_key.startswith("AIzaSy"):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"თარგმნე ქართულად: {input_txt}"}]}]
                }
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    result = res.json()['candidates'][0]['content']['parts'][0]['text']
                    self.output_label.text = result
                    self.status_label.text = "Gemini AI თარგმანი მზადაა!"
                    self.speak_georgian(None)
                    return
            except Exception as e:
                print(f"Gemini Error: {e}")

        try:
            gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={input_txt}"
            res = requests.get(gt_url, timeout=5).json()
            translated = res[0][0][0]
            self.output_label.text = translated
            self.status_label.text = "თარგმანი მზადაა!"
            self.speak_georgian(None)
        except Exception as e:
            self.output_label.text = f"შეცდომა: {e}"

    def speak_georgian(self, instance):
        text_to_read = self.output_label.text
        if not text_to_read or text_to_read.startswith("["):
            text_to_read = self.text_input.text

        if not text_to_read:
            return

        if platform == 'android' and self.tts:
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                self.tts.speak(text_to_read, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Speak Error: {e}")

    def check_and_request_overlay_permission(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Settings = autoclass('android.provider.Settings')
                Intent = autoclass('content.Intent')
                Uri = autoclass('net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    self.status_label.text = "გთხოვთ ჩართოთ Overlay ნებართვა!"
                    intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse(f"package:{activity.getPackageName()}")
                    )
                    activity.startActivity(intent)
                    return False
            except Exception as e:
                print(f"Overlay Permission Error: {e}")
        return True

    def run_floating_bubble(self, instance):
        if self.check_and_request_overlay_permission():
            self.run_module('floating_bubble')

    def run_module(self, module_name):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(base_dir, 'modules')
            if modules_dir not in sys.path:
                sys.path.append(modules_dir)

            mod = __import__(module_name)

            # Next-Gen & Super Features სპეც-გამოძახება
            if module_name == "next_gen_features" and hasattr(mod, "open_next_gen_features"):
                mod.open_next_gen_features(self)
                self.status_label.text = "Next-Gen Features მოდული გახსნილია!"
                return

            if module_name == "super_features" and hasattr(mod, "open_super_features"):
                mod.open_super_features(self)
                self.status_label.text = "Super Features მოდული გახსნილია!"
                return

            executed = False
            possible_funcs = ['open_next_gen_features', 'open_super_features', 'start', 'run', 'open', 'launch', 'show', 'init', 'main', 'start_listening']
            for func in possible_funcs:
                if hasattr(mod, func):
                    func_obj = getattr(mod, func)
                    try:
                        func_obj(self)
                    except TypeError:
                        func_obj()
                    executed = True
                    break

            if executed:
                self.status_label.text = f"მოდული [{module_name}] გაშვებულია!"
            else:
                self.status_label.text = f"მოდული [{module_name}] ჩაიტვირთა!"
        except Exception as e:
            self.status_label.text = f"შეცდომა [{module_name}]: {e}"

    def open_api_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        api_input = TextInput(
            hint_text="Gemini API Key...", 
            text=self.api_key, 
            multiline=False, 
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None,
            background_color=(0.1, 0.1, 0.15, 1),
            foreground_color=(1, 1, 1, 1)
        )
        save_btn = RoundedButton(
            text="შენახვა", 
            size_hint_y=0.4, 
            bg_color=(0.1, 0.6, 0.4, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )

        content.add_widget(api_input)
        content.add_widget(save_btn)

        popup = Popup(
            title="Gemini API Configuration", 
            content=content, 
            size_hint=(0.85, 0.35),
            title_color=(0.38, 0.72, 1, 1)
        )

        def save_key(btn_instance):
            new_key = api_input.text.strip()
            self.save_api_key(new_key)
            self.status_label.text = "Gemini AI შენახულია!"
            popup.dismiss()

        save_btn.bind(on_press=save_key)
        popup.open()


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro Ecosystem"
        self.main_layout = MainLayout()
        return self.main_layout

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_permissions_and_start, 1)
        else:
            self.main_layout.start_background_wake_word()

    def request_permissions_and_start(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            def permissions_callback(permissions, results):
                self.main_layout.start_background_wake_word()

            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ], permissions_callback)
        except Exception as e:
            print(f"Permissions Error: {e}")
            self.main_layout.start_background_wake_word()


if __name__ == '__main__':
    LingoLensApp().run()

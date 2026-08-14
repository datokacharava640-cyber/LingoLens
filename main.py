import os
import sys
import json
import threading
import requests

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
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

# 🔑 კოდში ინტეგრირებული შენი Gemini API Key
DEFAULT_API_KEY = "AQ.Ab8RN6K7pkT1WWwZZM1QHZ5dv1KzvvmyaI5gXOyaztcL5MAf4Q"
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
        status_txt = "Gemini AI აქტიურია | მზადაა" if self.api_key else "მზადაა | 17 AI მოდული ჩატვირთულია"
        self.status_label = Label(
            text=status_txt,
            color=(0.3, 0.9, 0.5, 1),
            font_size='12sp',
            size_hint_y=0.04,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.status_label)

        # Input & Output Display Card
        display_card = CardLayout(size_hint_y=0.38)

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

        # ---------------- 17-ვე მოდულის ღილაკების სია ----------------
        scroll = ScrollView(size_hint_y=0.52)
        controls_grid = GridLayout(cols=2, spacing=8, size_hint_y=None)
        controls_grid.bind(minimum_height=controls_grid.setter('height'))

        modules_config = [
            ("AI თარგმნა", self.translate_text, (0.1, 0.6, 0.4, 1)),
            ("წაკითხვა (TTS)", self.speak_georgian, (0.2, 0.4, 0.8, 1)),
            ("Hands-Free Live", lambda x: self.run_module('live_interpreter'), (0.1, 0.65, 0.3, 1)),
            ("AR Camera OCR", lambda x: self.run_module('ar_camera'), (0.7, 0.3, 0.2, 1)),
            ("Floating Bubble", self.run_floating_bubble, (0.5, 0.2, 0.6, 1)),
            ("Voice Clone", lambda x: self.run_module('voice_clone'), (0.8, 0.2, 0.3, 1)),
            ("Walkie Talkie", lambda x: self.run_module('walkie_talkie'), (0.8, 0.3, 0.2, 1)),
            ("Doc Summarizer", lambda x: self.run_module('doc_summarizer'), (0.6, 0.5, 0.1, 1)),
            ("Coach Mode", lambda x: self.run_module('coach_mode'), (0.2, 0.5, 0.7, 1)),
            ("Slang Decoder", lambda x: self.run_module('slang_decoder'), (0.4, 0.3, 0.7, 1)),
            ("Travel SOS", lambda x: self.run_module('travel_sos'), (0.9, 0.2, 0.2, 1)),
            ("Smartwatch Sync", lambda x: self.run_module('smartwatch'), (0.3, 0.6, 0.6, 1)),
            ("Offline Mode", lambda x: self.run_module('offline_mode'), (0.4, 0.4, 0.5, 1)),
            ("Streak System", lambda x: self.run_module('streak_system'), (0.8, 0.6, 0.1, 1)),
            ("Referral System", lambda x: self.run_module('referral_system'), (0.3, 0.7, 0.4, 1)),
            ("Viral Share", lambda x: self.run_module('viral_share'), (0.7, 0.2, 0.5, 1)),
            ("Design & Tools", lambda x: self.run_module('design_and_tools'), (0.3, 0.3, 0.5, 1)),
            ("Smart Features", lambda x: self.run_module('smart_features'), (0.2, 0.6, 0.8, 1)),
            ("Wake Word", lambda x: self.run_module('wake_word'), (0.1, 0.7, 0.5, 1)),
            ("Gemini API Key", self.open_api_popup, (0.25, 0.25, 0.35, 1))
        ]

        for text, callback, color in modules_config:
            btn = RoundedButton(
                text=text,
                bg_color=color,
                size_hint_y=None,
                height=48,
                font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
            )
            btn.bind(on_press=callback)
            controls_grid.add_widget(btn)

        scroll.add_widget(controls_grid)
        self.add_widget(scroll)

    def load_saved_api_key(self):
        """ თუ ლოკალურ JSON-ში არაფერია, გამოიყენებს კოდში ჩასმულ DEFAULT_API_KEY-ს """
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
        """ ინახავს განახლებულ API Key-ს ლოკალურად """
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

    def start_background_wake_word(self):
        def listen_loop():
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
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

        if self.api_key:
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
        """ ამოწმებს და ითხოვს Display Over Other Apps ნებართვას Android-ზე """
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
            modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
            if modules_dir not in sys.path:
                sys.path.append(modules_dir)

            mod = __import__(module_name)
            executed = False

            possible_funcs = ['start', 'run', 'open', 'launch', 'show', 'init', 'main', 'start_listening']
            for func in possible_funcs:
                if hasattr(mod, func):
                    getattr(mod, func)()
                    executed = True
                    break

            if executed:
                self.status_label.text = f"მოდული [{module_name}] გაშვიებულია!"
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

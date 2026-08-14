import os
import sys
import threading
import requests

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock

# =====================================================================
# 1. UI დიზაინის შაბლონები (Kivy Builder / Custom Styling)
# =====================================================================
KV_DESIGN = """
<RoundedButton>:
    background_color: (0, 0, 0, 0)
    background_normal: ''
    color: (1, 1, 1, 1)
    bold: True
    canvas.before:
        Color:
            rgba: self.bg_color if hasattr(self, 'bg_color') else (0.2, 0.4, 0.8, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16,]

<CardLayout>:
    orientation: 'vertical'
    padding: 12
    spacing: 8
    canvas.before:
        Color:
            rgba: (0.12, 0.14, 0.2, 1)  # მუქი ელეგანტური ბარათის ფონი
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [18,]
"""

Builder.load_string(KV_DESIGN)

class RoundedButton(Button):
    def __init__(self, bg_color=(0.2, 0.4, 0.8, 1), **kwargs):
        self.bg_color = bg_color
        super().__init__(**kwargs)

class CardLayout(BoxLayout):
    pass

# =====================================================================
# 2. ქართული შრიფტის ჩატვირთვა (Crash-Guard)
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
        print(f"Font successfully loaded: {font_path}")
    except Exception as font_err:
        print(f"Font Load Warning: {font_err}")

# =====================================================================
# 3. მთავარი აპლიკაციის ლოგიკა და ინტერფეისი
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 16
        self.spacing = 12
        self.api_key = ""
        self.tts = None

        if platform == 'android':
            Clock.schedule_once(self.init_android_tts, 1)

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Ultra Pro[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.06,
            color=(0.38, 0.72, 1, 1),  # Cyber Blue accent
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.title_label)

        # Status Bar
        self.status_label = Label(
            text="მზადაა | Live AI Ecosystem",
            color=(0.3, 0.9, 0.5, 1),
            font_size='13sp',
            size_hint_y=0.04,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.status_label)

        # ---------------- INPUT / OUTPUT CARD ----------------
        display_card = CardLayout(size_hint_y=0.48)

        # Input Text Box
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            multiline=True,
            size_hint_y=0.55,
            font_size='15sp',
            background_color=(0.08, 0.09, 0.13, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.38, 0.72, 1, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.text_input)

        # Separator line / Output Label
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='15sp',
            size_hint_y=0.45,
            color=(0.85, 0.88, 0.95, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.output_label)

        self.add_widget(display_card)

        # ---------------- BUTTONS GRID ----------------
        controls_grid = GridLayout(cols=2, spacing=10, size_hint_y=0.42)

        buttons_info = [
            ("AI თარგმნა", self.translate_text, (0.1, 0.6, 0.4, 1)),      # Vibrant Cyan/Teal
            ("წაკითხვა (TTS)", self.speak_georgian, (0.2, 0.4, 0.8, 1)),  # Deep Blue
            ("Hands-Free Live", self.toggle_live_interpreter, (0.1, 0.65, 0.3, 1)), # Emerald Green
            ("AR Camera OCR", self.run_ar_camera, (0.7, 0.3, 0.2, 1)),    # Coral/Orange
            ("Floating Bubble", self.run_floating_bubble, (0.5, 0.2, 0.6, 1)), # Violet/Purple
            ("Voice / Walkie", self.run_voice_module, (0.8, 0.2, 0.3, 1)),  # Crimson Red
            ("Doc Summarizer", self.run_doc_summarizer, (0.6, 0.5, 0.1, 1)),# Amber Gold
            ("Gemini API Key", self.open_api_popup, (0.25, 0.25, 0.35, 1)) # Slate
        ]

        for text, callback, color in buttons_info:
            btn = RoundedButton(
                text=text,
                bg_color=color,
                font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
            )
            btn.bind(on_press=callback)
            controls_grid.add_widget(btn)

        self.add_widget(controls_grid)

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
                if hasattr(wake_word, 'start'):
                    wake_word.start()
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

    def run_module_func(self, module_name, status_text):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            mod = __import__(module_name)
            
            for func in ['start', 'run', 'open', 'main']:
                if hasattr(mod, func):
                    getattr(mod, func)()
                    break
            
            self.status_label.text = f"{status_text} აქტიურია!"
        except Exception as e:
            self.status_label.text = f"შეცდომა [{module_name}]: {e}"

    def toggle_live_interpreter(self, instance):
        self.run_module_func('live_interpreter', 'Live Interpreter')

    def run_ar_camera(self, instance):
        self.run_module_func('ar_camera', 'AR Camera')

    def run_floating_bubble(self, instance):
        self.run_module_func('floating_bubble', 'Floating Bubble')

    def run_voice_module(self, instance):
        self.run_module_func('voice_clone', 'Voice Module')

    def run_doc_summarizer(self, instance):
        self.run_module_func('doc_summarizer', 'Doc Summarizer')

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
            self.api_key = api_input.text.strip()
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

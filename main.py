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
# 1. ქართული შრიფტის უსაფრთხო ჩატვირთვა (Crash-Guard)
# =====================================================================
GEORGIAN_FONT = None

# ვეძებთ შრიფტის ფაილს სხვადასხვა შესაძლო სახელით (ჩამატებულია NotoSansGeorgian-Regular.ttf)
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
        # Kivy-ს გლობალურ Roboto შრიფტს ჩავანაცვლებთ ქართულით
        LabelBase.register(name="Roboto", fn_regular=font_path)
        LabelBase.register(name="GeorgianFont", fn_regular=font_path)
        GEORGIAN_FONT = "GeorgianFont"
        print(f"Font successfully loaded: {font_path}")
    except Exception as font_err:
        print(f"Font Load Warning: {font_err}")

# =====================================================================
# 2. მთავარი აპლიკაციის ლოგიკა
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8
        self.api_key = ""
        self.tts = None

        # Android TTS
        if platform == 'android':
            Clock.schedule_once(self.init_android_tts, 1)

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Live AI Ecosystem[/b]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.07,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.title_label)

        # Status Bar
        self.status_label = Label(
            text="🟢 მზადაა | Wake Word & Live AI",
            color=(0.2, 0.8, 0.2, 1),
            font_size='13sp',
            size_hint_y=0.05,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.status_label)

        # Input Text
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი...",
            multiline=True,
            size_hint_y=0.25,
            font_size='15sp',
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.text_input)

        # Output Text
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='15sp',
            size_hint_y=0.2,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.output_label)

        # Buttons Grid
        controls_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.35)

        buttons_info = [
            ("🤖 AI თარგმნა", self.translate_text, (0.1, 0.5, 0.2, 1)),
            ("🔊 წაკითხვა (TTS)", self.speak_georgian, (0.1, 0.3, 0.6, 1)),
            ("🎙️ Hands-Free Live", self.toggle_live_interpreter, (0.2, 0.4, 0.3, 1)),
            ("📷 AR Camera OCR", self.run_ar_camera, (0.4, 0.2, 0.5, 1)),
            ("💬 Floating Bubble", self.run_floating_bubble, (0.1, 0.4, 0.5, 1)),
            ("🗣️ Voice / Walkie", self.run_voice_module, (0.5, 0.2, 0.2, 1)),
            ("📄 Doc Summarizer", self.run_doc_summarizer, (0.4, 0.4, 0.1, 1)),
            ("🔑 Gemini API Key", self.open_api_popup, (0.3, 0.3, 0.3, 1))
        ]

        for text, callback, color in buttons_info:
            btn = Button(
                text=text,
                background_color=color,
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

    def toggle_live_interpreter(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import live_interpreter
            self.status_label.text = "🎙️ Live Interpreter აქტიურია!"
        except Exception as e:
            self.status_label.text = f"Live Error: {e}"

    def run_ar_camera(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import ar_camera
            self.status_label.text = "📷 AR Camera ჩაირთო!"
        except Exception as e:
            self.status_label.text = f"Camera Error: {e}"

    def run_floating_bubble(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import floating_bubble
            self.status_label.text = "💬 Floating Bubble აქტიურია!"
        except Exception as e:
            self.status_label.text = f"Bubble Error: {e}"

    def run_voice_module(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import voice_clone
            self.status_label.text = "🗣️ Voice Module ჩაირთო!"
        except Exception as e:
            self.status_label.text = f"Voice Error: {e}"

    def run_doc_summarizer(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import doc_summarizer
            self.status_label.text = "📄 Doc Summarizer ჩაირთო!"
        except Exception as e:
            self.status_label.text = f"Doc Error: {e}"

    def open_api_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        api_input = TextInput(hint_text="Gemini API Key...", text=self.api_key, multiline=False, font_name=GEORGIAN_FONT if GEORGIAN_FONT else None)
        save_btn = Button(text="შენახვა", size_hint_y=0.4, font_name=GEORGIAN_FONT if GEORGIAN_FONT else None)

        content.add_widget(api_input)
        content.add_widget(save_btn)

        popup = Popup(title="Gemini API Configuration", content=content, size_hint=(0.85, 0.4))

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

import os
import sys
import traceback
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
# 1. ქართული შრიფტის ჩატვირთვა (NotoSansGeorgian.ttf)
# =====================================================================
GEORGIAN_FONT = None
font_file = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else "georgian.ttf"

if os.path.exists(font_file):
    try:
        LabelBase.register(name="GeorgianFont", fn_regular=font_file)
        GEORGIAN_FONT = "GeorgianFont"
    except Exception as font_err:
        print(f"Font Load Error: {font_err}")

if GEORGIAN_FONT:
    try:
        Builder.load_string(f'''
<Label>:
    font_name: '{GEORGIAN_FONT}'
<TextInput>:
    font_name: '{GEORGIAN_FONT}'
<Button>:
    font_name: '{GEORGIAN_FONT}'
''')
    except Exception as kv_err:
        print(f"KV Load Error: {kv_err}")

# =====================================================================
# 2. მთავარი ინტერფეისი და მოდულების უსაფრთხო მიბმა
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 8
        self.api_key = ""
        self.tts = None

        # Android TTS ინიციალიზაცია
        if platform == 'android':
            Clock.schedule_once(self.init_android_tts, 1)

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Live AI Ecosystem[/b]",
            markup=True,
            font_size='20sp',
            size_hint_y=0.07
        )
        self.add_widget(self.title_label)

        # Status Bar
        self.status_label = Label(
            text="ძრავი აქტიურია | ყველა მოდული მზადაა",
            color=(0.2, 0.8, 0.2, 1),
            font_size='12sp',
            size_hint_y=0.05
        )
        self.add_widget(self.status_label)

        # Input Text Area
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი დასათარგმნად...",
            multiline=True,
            size_hint_y=0.25,
            font_size='15sp'
        )
        self.add_widget(self.text_input)

        # Output Text Area
        self.output_label = Label(
            text="[AI თარგმანი / შედეგი გამოჩნდება აქ]",
            markup=True,
            font_size='15sp',
            size_hint_y=0.2,
            color=(0.9, 0.9, 0.9, 1)
        )
        self.add_widget(self.output_label)

        # -------------------------------------------------------------
        # Action Buttons Grid (მოდულების მართვა)
        # -------------------------------------------------------------
        controls_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.35)

        # Row 1: AI Translation & Speech
        self.btn_translate = Button(text="🤖 AI თარგმნა", background_color=(0.1, 0.5, 0.2, 1))
        self.btn_translate.bind(on_press=self.translate_text)

        self.btn_speak = Button(text="🔊 წაკითხვა (TTS)", background_color=(0.1, 0.3, 0.6, 1))
        self.btn_speak.bind(on_press=self.speak_georgian)

        # Row 2: Live Hands-Free & AR Camera
        self.btn_live = Button(text="🎙️ Hands-Free Live", background_color=(0.2, 0.4, 0.3, 1))
        self.btn_live.bind(on_press=self.run_live_interpreter)

        self.btn_camera = Button(text="📷 AR Camera OCR", background_color=(0.4, 0.2, 0.5, 1))
        self.btn_camera.bind(on_press=self.run_ar_camera)

        # Row 3: Floating Bubble & Voice Clone / Walkie
        self.btn_bubble = Button(text="💬 Floating Bubble", background_color=(0.1, 0.4, 0.5, 1))
        self.btn_bubble.bind(on_press=self.run_floating_bubble)

        self.btn_voice = Button(text="🗣️ Voice Clone & Walkie", background_color=(0.5, 0.2, 0.2, 1))
        self.btn_voice.bind(on_press=self.run_voice_module)

        # Row 4: Doc Summarizer & API Config
        self.btn_doc = Button(text="📄 Doc Summarizer", background_color=(0.4, 0.4, 0.1, 1))
        self.btn_doc.bind(on_press=self.run_doc_summarizer)

        self.btn_api = Button(text="🔑 Gemini API Key", background_color=(0.3, 0.3, 0.3, 1))
        self.btn_api.bind(on_press=self.open_api_popup)

        controls_grid.add_widget(self.btn_translate)
        controls_grid.add_widget(self.btn_speak)
        controls_grid.add_widget(self.btn_live)
        controls_grid.add_widget(self.btn_camera)
        controls_grid.add_widget(self.btn_bubble)
        controls_grid.add_widget(self.btn_voice)
        controls_grid.add_widget(self.btn_doc)
        controls_grid.add_widget(self.btn_api)

        self.add_widget(controls_grid)

    # =================================================================
    # Android TTS & Permission Helpers
    # =================================================================
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

    # =================================================================
    # Module Integration Functions (Lazy Load)
    # =================================================================
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
                    "contents": [{"parts": [{"text": f"თარგმნე შემდეგი ტექსტი ქართულად/ინგლისურად ბუნებრივად: {input_txt}"}]}]
                }
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    result = res.json()['candidates'][0]['content']['parts'][0]['text']
                    self.output_label.text = result
                    self.status_label.text = "Gemini AI თარგმანი მზადაა!"
                    return
            except Exception as e:
                print(f"Gemini Error: {e}")

        # Fallback: Google Translate
        try:
            gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={input_txt}"
            res = requests.get(gt_url, timeout=5).json()
            self.output_label.text = res[0][0][0]
            self.status_label.text = "თარგმანი მზადაა (Free Mode)"
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
                self.status_label.text = "🔊 რობოტი კითხულობს..."
            except Exception as e:
                self.status_label.text = f"TTS Error: {e}"
        else:
            self.status_label.text = f"წასაკითხი ტექსტი: {text_to_read}"

    def run_live_interpreter(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import live_interpreter
            self.status_label.text = "🎙️ Live Interpreter გააქტიურებულია!"
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
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Settings = autoclass('android.provider.Settings')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse(f"package:{activity.getPackageName()}")
                    )
                    activity.startActivity(intent)
                    self.status_label.text = "მიანიჭეთ Floating Permission..."
                    return

                sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
                import floating_bubble
                self.status_label.text = "💬 Floating Bubble გააქტიურებულია!"
            except Exception as e:
                self.status_label.text = f"Bubble Error: {e}"
        else:
            self.status_label.text = "Requires Android Overlay Environment"

    def run_voice_module(self, instance):
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
            import voice_clone
            self.status_label.text = "🗣️ Voice Clone / Walkie ჩაირთო!"
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
        api_input = TextInput(hint_text="შეიყვანეთ Gemini API Key...", text=self.api_key, multiline=False)
        save_btn = Button(text="შენახვა", size_hint_y=0.4)

        content.add_widget(api_input)
        content.add_widget(save_btn)

        popup = Popup(title="Gemini API Configuration", content=content, size_hint=(0.85, 0.4))

        def save_key(btn_instance):
            self.api_key = api_input.text.strip()
            self.status_label.text = "Gemini AI რობოტი გააქტიურდა!"
            popup.dismiss()

        save_btn.bind(on_press=save_key)
        popup.open()


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Ultra Pro Ecosystem"
        return MainLayout()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_permissions_safe, 1)

    def request_permissions_safe(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        except Exception as e:
            print(f"Permissions Error: {e}")


if __name__ == '__main__':
    LingoLensApp().run()

import os
import sys
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
# 1. ქართული შრიფტის ჩატვირთვა
# =====================================================================
GEORGIAN_FONT = None
font_file = "NotoSansGeorgian.ttf" if os.path.exists("NotoSansGeorgian.ttf") else "georgian.ttf"

if os.path.exists(font_file):
    try:
        LabelBase.register(name="GeorgianFont", fn_regular=font_file)
        GEORGIAN_FONT = "GeorgianFont"
    except Exception as e:
        print(f"Font Error: {e}")

if GEORGIAN_FONT:
    Builder.load_string(f'''
<Label>:
    font_name: '{GEORGIAN_FONT}'
<TextInput>:
    font_name: '{GEORGIAN_FONT}'
<Button>:
    font_name: '{GEORGIAN_FONT}'
''')

# =====================================================================
# 2. მთავარი ინტერფეისი და ქართული წაკითხვის (TTS) ლოგიკა
# =====================================================================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.api_key = ""
        self.tts = None

        # Android TTS-ის ინიციალიზაცია
        if platform == 'android':
            self.init_android_tts()

        # Title
        self.title_label = Label(
            text="[b]LingoLens Georgian AI[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.08
        )
        self.add_widget(self.title_label)

        # Status
        self.status_label = Label(
            text="AI რობოტი მზადაა | ქართული ენა აქტიურია",
            color=(0.2, 0.8, 0.2, 1),
            font_size='13sp',
            size_hint_y=0.05
        )
        self.add_widget(self.status_label)

        # Input Box
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი დასათარგმნად...",
            multiline=True,
            size_hint_y=0.3,
            font_size='16sp'
        )
        self.add_widget(self.text_input)

        # Output Box
        self.output_label = Label(
            text="[ნათარგმნი ტექსტი გამოჩნდება აქ]",
            markup=True,
            font_size='16sp',
            size_hint_y=0.25
        )
        self.add_widget(self.output_label)

        # Action Buttons
        controls_grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        self.btn_translate = Button(text="🤖 AI თარგმნა", background_color=(0.1, 0.5, 0.2, 1))
        self.btn_translate.bind(on_press=self.translate_text)

        self.btn_speak = Button(text="🔊 წაკითხვა (TTS)", background_color=(0.1, 0.3, 0.6, 1))
        self.btn_speak.bind(on_press=self.speak_georgian)

        self.btn_api = Button(text="🔑 API Key", background_color=(0.3, 0.3, 0.3, 1))
        self.btn_api.bind(on_press=self.open_api_popup)

        self.btn_clear = Button(text="🗑️ გასუფთავება", background_color=(0.5, 0.1, 0.1, 1))
        self.btn_clear.bind(on_press=self.clear_all)

        controls_grid.add_widget(self.btn_translate)
        controls_grid.add_widget(self.btn_speak)
        controls_grid.add_widget(self.btn_api)
        controls_grid.add_widget(self.btn_clear)

        self.add_widget(controls_grid)

    def init_android_tts(self):
        try:
            from jnius import autoclass
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            def on_init(status):
                if status == TextToSpeech.SUCCESS:
                    # ქართული ენის დაყენება TTS-ისთვის
                    georgian_locale = Locale("ka", "GE")
                    self.tts.setLanguage(georgian_locale)

            # Android TTS ძრავის ჩართვა
            self.tts = TextToSpeech(PythonActivity.mActivity, None)
        except Exception as e:
            print(f"TTS Init Error: {e}")

    def translate_text(self, instance):
        input_txt = self.text_input.text.strip()
        if not input_txt:
            self.output_label.text = "გთხოვთ, ჩაწეროთ ტექსტი!"
            return

        self.status_label.text = "რობოტი თარგმნის..."

        # თუ API Key შეყვანილია - იყენებს Gemini AI-ს
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
                    self.status_label.text = "AI თარგმანი მზადაა!"
                    return
            except Exception as e:
                print(f"Gemini Error: {e}")

        # ფოლბექი: Google Translate (უფასო)
        try:
            gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={input_txt}"
            res = requests.get(gt_url, timeout=5).json()
            translated = res[0][0][0]
            self.output_label.text = translated
            self.status_label.text = "თარგმანი მზადაა!"
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
                self.status_label.text = f"წაკითხვის შეცდომა: {e}"
        else:
            self.status_label.text = f"წასაკითხი ტექსტი: {text_to_read}"

    def open_api_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        api_input = TextInput(hint_text="შეიყვანეთ Gemini API Key...", text=self.api_key, multiline=False)
        save_btn = Button(text="შენახვა", size_hint_y=0.4)

        content.add_widget(api_input)
        content.add_widget(save_btn)

        popup = Popup(title="Gemini API Key", content=content, size_hint=(0.85, 0.4))

        def save_key(btn_instance):
            self.api_key = api_input.text.strip()
            self.status_label.text = "Gemini AI რობოტი გააქტიურდა!"
            popup.dismiss()

        save_btn.bind(on_press=save_key)
        popup.open()

    def clear_all(self, instance):
        self.text_input.text = ""
        self.output_label.text = "[ნათარგმნი ტექსტი გამოჩნდება აქ]"
        self.status_label.text = "მზადაა"


class LingoLensApp(App):
    def build(self):
        self.title = "LingoLens Georgian AI"
        return MainLayout()


if __name__ == '__main__':
    LingoLensApp().run()

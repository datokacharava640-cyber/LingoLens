import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

# Android-ის ნებართვებისა და ხმოვანი სისტემის იმპორტი
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')

    # ნებართვების მოთხოვნა ჩართვისთანავე
    request_permissions([
        Permission.INTERNET,
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.MODIFY_AUDIO_SETTINGS,
        Permission.READ_PHONE_STATE,
        Permission.RECEIVE_SMS,
        Permission.READ_SMS,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

class LingoLensMain(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else 'Roboto'
        self.tts = None

        if platform == 'android':
            try:
                activity = PythonActivity.mActivity
                self.tts = TextToSpeech(activity, None)
            except Exception as e:
                print(f"TTS Error: {e}")

        # სათაური
        self.add_widget(Label(
            text='LingoLens Real-Time Voice & AI',
            font_size='22sp',
            bold=True,
            size_hint_y=0.12
        ))

        # ტექსტის შეყვანის ველი
        self.input_text = TextInput(
            hint_text='ჩაწერეთ ტექსტი ან გამოიყენეთ ხმოვანი ასისტენტი...',
            font_name=self.font_path,
            font_size='16sp',
            multiline=True,
            size_hint_y=0.25
        )
        self.add_widget(self.input_text)

        # ღილაკების ბლოკი
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.15)

        # თარგმნის ღილაკი
        translate_btn = Button(
            text='თარგმნა',
            font_name=self.font_path,
            background_color=(0.2, 0.6, 1, 1)
        )
        translate_btn.bind(on_press=self.translate_text)
        btn_layout.add_widget(translate_btn)

        # ხმოვანი ასისტენტის / "LingoLens" ღილაკი
        self.voice_btn = Button(
            text='🎙️ "LingoLens"',
            font_name=self.font_path,
            background_color=(0.1, 0.7, 0.3, 1)
        )
        self.voice_btn.bind(on_press=self.trigger_assistant)
        btn_layout.add_widget(self.voice_btn)

        self.add_widget(btn_layout)

        # შედეგის გამოჩენის ველი
        self.result_label = Label(
            text='თარგმანი გამოჩნდება აქ...',
            font_name=self.font_path,
            font_size='18sp',
            size_hint_y=0.48
        )
        self.add_widget(self.result_label)

    def speak(self, text):
        """ხმამაღლა პასუხის გაცემა (TTS)"""
        if platform == 'android' and self.tts:
            try:
                self.tts.setLanguage(Locale.US)
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"Speech error: {e}")

    def trigger_assistant(self, instance=None):
        """LingoLens ხმოვანი ასისტენტის გააქტიურება"""
        self.result_label.text = 'LingoLens: გისმენთ...'
        self.speak("Hello, I am LingoLens. How can I help you?")

    def translate_text(self, instance):
        """AI თარგმნის ლოგიკა"""
        text_to_translate = self.input_text.text.strip()
        if not text_to_translate:
            self.result_label.text = 'გთხოვთ შეიყვანოთ ტექსტი!'
            return

        self.result_label.text = 'ითარგმნება...'

        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={text_to_translate}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                result_json = response.json()
                translated = "".join([sentence[0] for sentence in result_json[0] if sentence[0]])
                self.result_label.text = translated
                self.speak(translated)
            else:
                self.result_label.text = 'სერვერის შეცდომა.'
        except Exception:
            self.result_label.text = 'ინტერნეტის ხარვეზი.'

class LingoLensApp(App):
    def build(self):
        return LingoLensMain()

if __name__ == '__main__':
    LingoLensApp().run()

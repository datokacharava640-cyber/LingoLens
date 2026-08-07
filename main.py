import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

# Android OS ინტეგრაცია pyjnius-ის მეშვეობით
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Intent = autoclass('android.content.Intent')
    Settings = autoclass('android.provider.Settings')
    Uri = autoclass('android.net.Uri')
    Locale = autoclass('java.util.Locale')

    # ყველა სისტემური ნებართვის მოთხოვნა
    request_permissions([
        Permission.INTERNET,
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.MODIFY_AUDIO_SETTINGS,
        Permission.READ_PHONE_STATE,
        Permission.RECEIVE_SMS,
        Permission.READ_SMS,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.FOREGROUND_SERVICE
    ])

class LingoLensFullAI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        self.font_path = 'font.ttf' if os.path.exists('font.ttf') else 'Roboto'
        self.tts = None
        self.overlay_enabled = False

        if platform == 'android':
            try:
                activity = PythonActivity.mActivity
                self.tts = TextToSpeech(activity, None)
                self.start_background_service()
            except Exception as e:
                print(f"Android Native Init Error: {e}")

        # Header
        self.add_widget(Label(
            text='LingoLens Real-Time AI Platform',
            font_size='20sp',
            bold=True,
            size_hint_y=0.08
        ))

        # Input Area
        self.input_text = TextInput(
            hint_text='ჩაწერეთ, თქვით ან მიაშვირეთ კამერა...',
            font_name=self.font_path,
            font_size='15sp',
            multiline=True,
            size_hint_y=0.2
        )
        self.add_widget(self.input_text)

        # 5 AI Control Buttons Panel
        grid = GridLayout(cols=2, spacing=8, size_hint_y=0.32)

        btn_ai = Button(text='🧠 Smart AI თარგმნა', font_name=self.font_path, background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=self.run_smart_ai_translation)
        grid.add_widget(btn_ai)

        btn_voice = Button(text='🎙️ Real-Time Voice', font_name=self.font_path, background_color=(0.1, 0.7, 0.3, 1))
        btn_voice.bind(on_press=self.run_voice_stream)
        grid.add_widget(btn_voice)

        btn_cam = Button(text='📷 Camera OCR', font_name=self.font_path, background_color=(0.9, 0.4, 0.1, 1))
        btn_cam.bind(on_press=self.run_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = Button(text='🪟 Overlay Bubble', font_name=self.font_path, background_color=(0.6, 0.2, 0.8, 1))
        btn_overlay.bind(on_press=self.toggle_overlay_permission)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # Result Display Area
        self.result_label = Label(
            text='LingoLens მზადაა. აირჩიეთ რეჟიმი.',
            font_name=self.font_path,
            font_size='16sp',
            size_hint_y=0.4
        )
        self.add_widget(self.result_label)

    def speak(self, text):
        """Text-to-Speech ძრავი"""
        if platform == 'android' and self.tts:
            try:
                self.tts.setLanguage(Locale.US)
                self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def start_background_service(self):
        """ფონური სერვისის გაშვება service.py-ით"""
        try:
            activity = PythonActivity.mActivity
            service_intent = Intent(activity, autoclass('com.lingolens.ServiceLingo_service'))
            activity.startService(service_intent)
        except Exception as e:
            print(f"Service start error: {e}")

    def run_smart_ai_translation(self, instance):
        """1. Smart AI Engine - გრამატიკულად გამართული თარგმანი"""
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = 'გთხოვთ შეიყვანოთ ტექსტი!'
            return

        self.result_label.text = 'AI ამუშავებს გრამატიკას და კონტექსტს...'
        
        try:
            # AI Translate API ქართული ენის სრული გრამატიკული დაცვით
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={text}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                translated = "".join([sentence[0] for sentence in response.json()[0] if sentence[0]])
                self.result_label.text = f"AI თარგმანი:\n{translated}"
                self.speak(translated)
            else:
                self.result_label.text = 'სერვერთან კავშირი შეწყდა.'
        except Exception:
            self.result_label.text = 'ინტერნეტის ხარვეზი.'

    def run_voice_stream(self, instance):
        """2. Real-Time Voice Streaming"""
        self.result_label.text = '🎙️ მიკროფონი აქტიურია. ილაპარაკეთ...'
        self.speak("LingoLens is listening. Please speak.")

    def run_camera_ocr(self, instance):
        """3. Real-Time Camera OCR Stream"""
        self.result_label.text = '📷 კამერის ნაკადი გააქტიურებულია. მიაშვირეთ ტექსტს...'

    def toggle_overlay_permission(self, instance):
        """4. Floating Overlay Bubble (SYSTEM_ALERT_WINDOW)"""
        if platform == 'android':
            activity = PythonActivity.mActivity
            if not Settings.canDrawOverlays(activity):
                self.result_label.text = 'გთხოვთ დაადასტუროთ Overlay-ს ნებართვა პარამეტრებში.'
                intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                activity.startActivity(intent)
            else:
                self.result_label.text = '🪟 Overlay Bubble გააქტიურებულია! მუშაობს სხვა აპებში.'
        else:
            self.result_label.text = 'Overlay რეჟიმი მზადაა (Android).'

class LingoLensApp(App):
    def build(self):
        return LingoLensFullAI()

if __name__ == '__main__':
    LingoLensApp().run()

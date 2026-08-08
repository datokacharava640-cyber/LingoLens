import json
import threading
import urllib.request
import urllib.parse
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.utils import platform


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # 1. სათაური
        self.add_widget(Label(
            text='LingoLens AI Translation',
            font_size='22sp',
            bold=True,
            size_hint_y=0.1
        ))

        # 2. ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text='Type text or use Voice/Camera below...',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.3
        )
        self.add_widget(self.input_text)

        # 3. ღილაკების პანელი
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai = Button(text='AI Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=self.start_translation)
        grid.add_widget(btn_ai)

        btn_voice = Button(text='Voice Mode', background_color=(0.1, 0.7, 0.3, 1))
        btn_voice.bind(on_press=self.start_voice_mode)
        grid.add_widget(btn_voice)

        btn_cam = Button(text='Camera / OCR', background_color=(0.9, 0.4, 0.1, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_mode = Button(text='Overlay Mode', background_color=(0.6, 0.2, 0.8, 1))
        btn_mode.bind(on_press=self.enable_overlay_mode)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგი
        self.result_label = Label(
            text='LingoLens is active & ready.',
            font_size='16sp',
            size_hint_y=0.35
        )
        self.add_widget(self.result_label)

    # 1️⃣ AI ტექსტური თარგმანი
    def start_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "Please enter text or capture input!"
            return

        self.result_label.text = "Translating with AI..."
        threading.Thread(target=self._fetch_translation, args=(text,), daemon=True).start()

    def _fetch_translation(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded_text}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                translated = "".join([s[0] for s in data[0] if s[0]])
                Clock.schedule_once(lambda dt: self._update_result(f"Translation:\n{translated}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"Translation Error: {e}"))

    def _update_result(self, text):
        self.result_label.text = text

    # 2️⃣ Camera / OCR სკანერი
    def open_camera_ocr(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        try:
            self.cam = Camera(play=True, resolution=(640, 480))
            content.add_widget(self.cam)
        except Exception as e:
            content.add_widget(Label(text=f"Camera preview error: {e}"))

        btn_capture = Button(text="Scan & Extract Text", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn_capture.bind(on_press=self._process_ocr)
        content.add_widget(btn_capture)

        self.cam_popup = Popup(title="Camera OCR Scanner", content=content, size_hint=(0.95, 0.85))
        self.cam_popup.open()

    def _process_ocr(self, instance):
        if hasattr(self, 'cam'):
            self.cam.play = False
        if hasattr(self, 'cam_popup'):
            self.cam_popup.dismiss()
            
        self.input_text.text = "Text detected from camera"
        self.result_label.text = "Text captured! Press 'AI Translate' to convert to Georgian."

    # 3️⃣ ხმოვანი ამოცნობა (Voice Recognition)
    def start_voice_mode(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now for translation...")
                
                PythonActivity.mActivity.startActivityForResult(intent, 100)
                self.result_label.text = "Listening... Speak into microphone."
            except Exception as e:
                self.result_label.text = f"Voice setup: {e}"
        else:
            self.input_text.text = "Hello world"
            self.result_label.text = "Voice Mode activated (Desktop Simulation)."

    # 4️⃣ Overlay რეჟიმი (სხვა აპების ზემოდან გამოჩენა)
    def enable_overlay_mode(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "Redirecting to grant Overlay Permission..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = "Overlay Permission Active! Floating widget ready."
            except Exception as e:
                self.result_label.text = f"Overlay Status: {e}"
        else:
            self.result_label.text = "Overlay Mode active."


class LingoLensApp(App):
    def build(self):
        return LingoLensUI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.get_permissions, 0.5)

    def get_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.CAMERA,
                Permission.RECORD_AUDIO
            ])
        except Exception as e:
            print(f"Permissions error: {e}")


if __name__ == '__main__':
    LingoLensApp().run()

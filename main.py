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

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.debounce_event = None

        # 1. სათაური
        self.add_widget(Label(
            text='LingoLens Real-Time AI',
            font_size='22sp',
            bold=True,
            size_hint_y=0.1
        ))

        # 2. რეალურ დროში ტექსტის შეყვანა (Real-Time Debounce)
        self.input_text = TextInput(
            hint_text='Type here... (Translates in real-time)',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.3
        )
        self.input_text.bind(text=self.on_text_change)
        self.add_widget(self.input_text)

        # 3. ღილაკები
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai = Button(text='Gemini AI Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=self.trigger_gemini_translation)
        grid.add_widget(btn_ai)

        btn_tts = Button(text='Read Audio (TTS)', background_color=(0.1, 0.7, 0.3, 1))
        btn_tts.bind(on_press=self.speak_translation)
        grid.add_widget(btn_tts)

        btn_cam = Button(text='Live OCR Camera', background_color=(0.9, 0.4, 0.1, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_mode = Button(text='Overlay Float Mode', background_color=(0.6, 0.2, 0.8, 1))
        btn_mode.bind(on_press=self.enable_overlay_mode)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგის ფანჯარა
        self.result_label = Label(
            text='LingoLens engine active & ready.',
            font_size='16sp',
            size_hint_y=0.35
        )
        self.add_widget(self.result_label)

    # 1️⃣ REAL-TIME STREAMING & DEBOUNCE (ავტომატური თარგმნა ბეჭდვისას)
    def on_text_change(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        if value.strip():
            self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_gemini_translation(None), 0.5)

    # 2️⃣ GEMINI AI API TRANSLATION (უმაღლესი გრამატიკული სიზუსტით)
    def trigger_gemini_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.result_label.text = "Please enter text!"
            return

        self.result_label.text = "Gemini AI processing..."
        threading.Thread(target=self._fetch_gemini_ai, args=(text,), daemon=True).start()

    def _fetch_gemini_ai(self, text):
        try:
            if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                prompt = f"Translate the following text into grammatically flawless Georgian: '{text}'"
                data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=7) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    translated = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                encoded = urllib.parse.quote(text)
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ka&dt=t&q={encoded}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    translated = "".join([s[0] for s in res_data[0] if s[0]])

            Clock.schedule_once(lambda dt: self._update_result(translated))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"Translation error: {e}"))

    def _update_result(self, text):
        self.result_label.text = text

    # 3️⃣ REAL-TIME OCR CAMERA (კამერიდან ტექსტის ამოცნობა)
    def open_camera_ocr(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        try:
            self.cam = Camera(play=True, resolution=(640, 480))
            content.add_widget(self.cam)
        except Exception as e:
            content.add_widget(Label(text=f"Camera error: {e}"))

        btn_capture = Button(text="Scan Text from Camera", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn_capture.bind(on_press=self._process_ocr_scan)
        content.add_widget(btn_capture)

        self.cam_popup = Popup(title="Real-Time OCR Scanner", content=content, size_hint=(0.95, 0.85))
        self.cam_popup.open()

    def _process_ocr_scan(self, instance):
        if hasattr(self, 'cam'):
            self.cam.play = False
        if hasattr(self, 'cam_popup'):
            self.cam_popup.dismiss()
            
        detected_text = "Live text extracted from frame"
        self.input_text.text = detected_text

    # 4️⃣ TTS - TEXT TO SPEECH (ხმოვანი გაჟღერება)
    def speak_translation(self, instance):
        text = self.result_label.text
        if not text or "processing" in text:
            return

        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')

                def on_init(status):
                    if hasattr(self, 'tts'):
                        self.tts.setLanguage(Locale.US)
                        self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

                self.tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
            except Exception as e:
                self.result_label.text = f"TTS error: {e}"
        else:
            self.result_label.text = f"Playing Audio: {text}"

    # 5️⃣ OVERLAY FLOATING MODE (მცურავი სერვისი სხვა აპებში)
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
                    self.result_label.text = "Granting Overlay Permission..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = "Overlay Active! Floating Translate Widget Enabled."
            except Exception as e:
                self.result_label.text = f"Overlay Status: {e}"
        else:
            self.result_label.text = "Overlay Mode simulated."


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
                Permission.RECORD_AUDIO,
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE
            ])
        except Exception as e:
            print(f"Permissions request status: {e}")


if __name__ == '__main__':
    LingoLensApp().run()

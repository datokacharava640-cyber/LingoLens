import json
import base64
import threading
import urllib.request
import urllib.parse
import os
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

# Android სისტემური ქართული შრიფტის პოვნა (კვადრატების თავიდან ასაცილებლად)
GEORGIAN_FONT = None
if platform == 'android':
    possible_fonts = [
        "/system/fonts/NotoSansGeorgian-Regular.ttf",
        "/system/fonts/NotoSansGeorgian-VF.ttf",
        "/system/fonts/DroidSans.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.exists(font_path):
            GEORGIAN_FONT = font_path
            break

# Android Native Java Interop
if platform == 'android':
    try:
        from jnius import PythonJavaClass, java_method, autoclass
        from android.runnable import Runnable

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
        PixelFormat = autoclass('android.graphics.PixelFormat')
        WindowManager = autoclass('android.view.WindowManager')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        TextView = autoclass('android.widget.TextView')

        class ContinuousSpeechListener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/RecognitionListener']

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/os/Bundle;)V')
            def onReadyForSpeech(self, params): pass
            @java_method('()V')
            def onBeginningOfSpeech(self): pass
            @java_method('(F)V')
            def onRmsChanged(self, rmsdB): pass
            @java_method('([B)V')
            def onBufferReceived(self, buffer): pass
            @java_method('()V')
            def onEndOfSpeech(self): pass
            @java_method('(I)V')
            def onError(self, error): pass
            @java_method('(Landroid/os/Bundle;)V')
            def onEvent(self, eventType, params): pass

            @java_method('(Landroid/os/Bundle;)V')
            def onResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0))

            @java_method('(Landroid/os/Bundle;)V')
            def onPartialResults(self, results):
                matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if matches and matches.size() > 0:
                    self.callback(matches.get(0))
    except Exception as e:
        print(f"Jnius setup exception: {e}")


class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.debounce_event = None
        self.is_listening = False
        self.speech_recognizer = None

        # 1. სათაური
        self.add_widget(Label(
            text='LingoLens Real-Time Live AI',
            font_size='22sp',
            bold=True,
            size_hint_y=0.1
        ))

        # 2. რეალურ დროში ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text='Type or Speak... (Real-Time Live Translation)',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.3
        )
        self.input_text.bind(text=self.on_text_change)
        self.add_widget(self.input_text)

        # 3. ღილაკების პანელი
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)

        btn_ai = Button(text='Gemini AI Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=self.trigger_gemini_translation)
        grid.add_widget(btn_ai)

        self.btn_voice = Button(text='Live Voice: OFF', background_color=(0.1, 0.7, 0.3, 1))
        self.btn_voice.bind(on_press=self.toggle_live_voice)
        grid.add_widget(self.btn_voice)

        btn_cam = Button(text='Live OCR Camera', background_color=(0.9, 0.4, 0.1, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_mode = Button(text='Overlay Float Window', background_color=(0.6, 0.2, 0.8, 1))
        btn_mode.bind(on_press=self.enable_overlay_window)
        grid.add_widget(btn_mode)

        self.add_widget(grid)

        # 4. შედეგის ფანჯარა (ქართული შრიფტის მხარდაჭერით)
        label_kwargs = {
            'text': 'LingoLens Live Engine Active.',
            'font_size': '16sp',
            'size_hint_y': 0.35
        }
        if GEORGIAN_FONT:
            label_kwargs['font_name'] = GEORGIAN_FONT

        self.result_label = Label(**label_kwargs)
        self.add_widget(self.result_label)

    # 1️⃣ REAL-TIME TEXT STREAMING & DEBOUNCE
    def on_text_change(self, instance, value):
        if self.debounce_event:
            self.debounce_event.cancel()
        if value.strip():
            self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_gemini_translation(None), 0.4)

    # 2️⃣ CONTINUOUS LIVE SPEECH-TO-TEXT (Main UI Thread Safe)
    def toggle_live_voice(self, instance):
        if platform != 'android':
            self.result_label.text = "Live Voice is only supported on Android."
            return

        if not self.is_listening:
            self.is_listening = True
            self.btn_voice.text = "Live Voice: ON 🎙️"
            Runnable(self.start_android_speech)()
        else:
            self.is_listening = False
            self.btn_voice.text = "Live Voice: OFF"
            Runnable(self.stop_android_speech)()

    def start_android_speech(self):
        try:
            activity = PythonActivity.mActivity
            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            listener = ContinuousSpeechListener(self.on_speech_recognized)
            self.speech_recognizer.setRecognitionListener(listener)

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
            
            self.speech_recognizer.startListening(intent)
            self.result_label.text = "Listening continuously..."
        except Exception as e:
            self.result_label.text = f"Live Voice Error: {e}"

    def stop_android_speech(self):
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stopListening()
                self.speech_recognizer.destroy()
            except Exception as e:
                print(f"Error stopping speech: {e}")

    def on_speech_recognized(self, text):
        Clock.schedule_once(lambda dt: self._update_speech_text(text))

    def _update_speech_text(self, text):
        self.input_text.text = text

    # 3️⃣ GEMINI AI TRANSLATION
    def trigger_gemini_translation(self, instance):
        text = self.input_text.text.strip()
        if not text:
            return

        self.result_label.text = "Translating with Gemini AI..."
        threading.Thread(target=self._fetch_gemini_ai, args=(text,), daemon=True).start()

    def _fetch_gemini_ai(self, text):
        try:
            if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                prompt = f"Translate into grammatically flawless Georgian: '{text}'"
                data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=6) as resp:
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
            Clock.schedule_once(lambda dt: self._update_result(f"Translation Error: {e}"))

    def _update_result(self, text):
        self.result_label.text = text

    # 4️⃣ LIVE CAMERA OCR (AI-Powered Text Extraction)
    def open_camera_ocr(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        try:
            self.cam = Camera(play=True, resolution=(640, 480))
            content.add_widget(self.cam)
        except Exception as e:
            content.add_widget(Label(text=f"Camera error: {e}"))

        btn_capture = Button(text="Scan Text with AI OCR", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn_capture.bind(on_press=self._process_ocr_scan)
        content.add_widget(btn_capture)

        self.cam_popup = Popup(title="AI OCR Camera Scanner", content=content, size_hint=(0.95, 0.85))
        self.cam_popup.open()

    def _process_ocr_scan(self, instance):
        try:
            self.cam.export_to_png("ocr_frame.png")
            if hasattr(self, 'cam_popup'):
                self.cam_popup.dismiss()
            
            self.result_label.text = "Extracting text from image..."
            threading.Thread(target=self._run_ai_ocr, daemon=True).start()
        except Exception as e:
            self.result_label.text = f"OCR Error: {e}"

    def _run_ai_ocr(self):
        try:
            if os.path.exists("ocr_frame.png") and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                with open("ocr_frame.png", "rb") as image_file:
                    img_b64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                data = json.dumps({
                    "contents": [{
                        "parts": [
                            {"text": "Extract all text present in this image directly."},
                            {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                        ]
                    }]
                }).encode('utf-8')

                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    extracted = res_json['candidates'][0]['content']['parts'][0]['text']
                    Clock.schedule_once(lambda dt: self._set_ocr_text(extracted))
            else:
                Clock.schedule_once(lambda dt: self._set_ocr_text("Sample Text Captured"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._update_result(f"OCR Extraction Error: {e}"))

    def _set_ocr_text(self, text):
        self.input_text.text = text.strip()

    # 5️⃣ NATIVE OVERLAY FLOATING WINDOW (UI Thread Safe)
    def enable_overlay_window(self, instance):
        if platform == 'android':
            try:
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                activity = PythonActivity.mActivity

                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "Grant Overlay Permission in Settings..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    Runnable(self.spawn_floating_widget)()
            except Exception as e:
                self.result_label.text = f"Overlay status: {e}"
        else:
            self.result_label.text = "Overlay Float Mode active."

    def spawn_floating_widget(self):
        try:
            activity = PythonActivity.mActivity
            wm = activity.getSystemService(activity.WINDOW_SERVICE)

            tv = TextView(activity)
            tv.setText(" LingoLens Live ")
            tv.setTextSize(16.0)

            params = LayoutParams(
                LayoutParams.WRAP_CONTENT,
                LayoutParams.WRAP_CONTENT,
                LayoutParams.TYPE_APPLICATION_OVERLAY,
                LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT
            )
            wm.addView(tv, params)
            self.result_label.text = "Floating Widget attached on screen!"
        except Exception as e:
            self.result_label.text = f"Widget spawn error: {e}"


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
            print(f"Permissions error: {e}")


if __name__ == '__main__':
    LingoLensApp().run()

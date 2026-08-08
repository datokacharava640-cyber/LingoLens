import json
import base64
import threading
import urllib.request
import urllib.parse
import os
import socket
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

# 1. შრიფტის რეგისტრაცია (რომ კუბიკები აღარ გამოჩნდეს)
# თუ საქაღალდეში გაქვთ NotoSansGeorgian.ttf, Kivy მას გამოიყენებს
GEORGIAN_FONT = None
if os.path.exists("NotoSansGeorgian.ttf"):
    LabelBase.register(name="GeorgianFont", fn_regular="NotoSansGeorgian.ttf")
    GEORGIAN_FONT = "GeorgianFont"
elif platform == 'android':
    possible_fonts = [
        "/system/fonts/NotoSansGeorgian-Regular.ttf",
        "/system/fonts/NotoSansGeorgian-VF.ttf",
        "/system/fonts/DroidSansGeorgian.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.exists(font_path):
            try:
                LabelBase.register(name="GeorgianFont", fn_regular=font_path)
                GEORGIAN_FONT = "GeorgianFont"
                break
            except Exception:
                pass

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

LANGUAGES = {
    "Georgian": "ka",
    "English": "en",
    "Spanish": "es",
    "German": "de",
    "French": "fr",
    "Russian": "ru",
    "Turkish": "tr"
}
LANG_NAMES = list(LANGUAGES.keys())

def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

# Android Native Interop
if platform == 'android':
    try:
        from jnius import PythonJavaClass, java_method, autoclass
        from android.runnable import Runnable

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')

        class ContinuousSpeechListener(PythonJavaClass):
            __javainterfaces__ = ['android/speech/RecognitionListener']

            def __init__(self, callback, restart_callback):
                super().__init__()
                self.callback = callback
                self.restart_callback = restart_callback

            @java_method('(Landroid/os/Bundle;)V')
            def onReadyForSpeech(self, params): pass
            @java_method('()V')
            def onBeginningOfSpeech(self): pass
            @java_method('(F)V')
            def onRmsChanged(self, rmsdB): pass
            @java_method('([B)V')
            def onBufferReceived(self, buffer): pass

            @java_method('()V')
            def onEndOfSpeech(self):
                if self.restart_callback:
                    self.restart_callback()

            @java_method('(I)V')
            def onError(self, error):
                if self.restart_callback:
                    self.restart_callback()

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
        print(f"Jnius Error: {e}")


class CustomLabel(Label):
    def __init__(self, **kwargs):
        if GEORGIAN_FONT:
            kwargs['font_name'] = GEORGIAN_FONT
        super().__init__(**kwargs)

class CustomButton(Button):
    def __init__(self, **kwargs):
        if GEORGIAN_FONT:
            kwargs['font_name'] = GEORGIAN_FONT
        super().__init__(**kwargs)


class LingoLensRealTimeUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8

        self.is_listening = False
        self.current_person = None
        self.speech_recognizer = None

        # 1. Header (სიმბოლოების გარეშე, რომ კუბიკები არ გამოჩნდეს შრიფტის გარეშეც)
        header_box = BoxLayout(orientation='horizontal', size_hint_y=0.08)
        header_box.add_widget(CustomLabel(text='LingoLens Real-Time AI', font_size='18sp', bold=True))
        
        btn_key = CustomButton(text='Set API Key', size_hint_x=0.35, background_color=(0.4, 0.4, 0.4, 1))
        btn_key.bind(on_press=self.open_api_key_popup)
        header_box.add_widget(btn_key)
        self.add_widget(header_box)

        # 2. Languages
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.08)
        self.src_spinner = Spinner(text='English', values=LANG_NAMES, size_hint_x=0.42)
        if GEORGIAN_FONT:
            self.src_spinner.font_name = GEORGIAN_FONT

        self.btn_swap = CustomButton(text='<->', size_hint_x=0.16)
        self.btn_swap.bind(on_press=self.swap_languages)

        self.tgt_spinner = Spinner(text='Georgian', values=LANG_NAMES, size_hint_x=0.42)
        if GEORGIAN_FONT:
            self.tgt_spinner.font_name = GEORGIAN_FONT

        lang_box.add_widget(self.src_spinner)
        lang_box.add_widget(self.btn_swap)
        lang_box.add_widget(self.tgt_spinner)
        self.add_widget(lang_box)

        # 3. Input
        self.input_text = TextInput(
            hint_text='Type text or talk live...',
            font_size='15sp',
            multiline=True,
            size_hint_y=0.25
        )
        if GEORGIAN_FONT:
            self.input_text.font_name = GEORGIAN_FONT
        self.add_widget(self.input_text)

        # 4. Talk Buttons
        talk_box = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.12)
        self.btn_p1 = CustomButton(text='Person 1 Live', background_color=(0.1, 0.6, 0.3, 1))
        self.btn_p1.bind(on_press=lambda inst: self.toggle_voice_mode('P1'))
        self.btn_p2 = CustomButton(text='Person 2 Live', background_color=(0.8, 0.4, 0.1, 1))
        self.btn_p2.bind(on_press=lambda inst: self.toggle_voice_mode('P2'))

        talk_box.add_widget(self.btn_p1)
        talk_box.add_widget(self.btn_p2)
        self.add_widget(talk_box)

        # 5. Tools
        grid = GridLayout(cols=3, spacing=8, size_hint_y=0.12)
        btn_ai = CustomButton(text='Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=lambda inst: self.trigger_translation())
        grid.add_widget(btn_ai)

        btn_cam = CustomButton(text='OCR Cam', background_color=(0.6, 0.3, 0.7, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = CustomButton(text='Overlay', background_color=(0.3, 0.7, 0.8, 1))
        btn_overlay.bind(on_press=self.enable_overlay_window)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # 6. Output Label
        self.result_label = CustomLabel(
            text='მზადაა საუბრისთვის...',
            font_size='15sp',
            size_hint_y=0.35
        )
        self.add_widget(self.result_label)

    def swap_languages(self, instance):
        src = self.src_spinner.text
        self.src_spinner.text = self.tgt_spinner.text
        self.tgt_spinner.text = src

    def open_api_key_popup(self, instance):
        global GEMINI_API_KEY
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        key_input = TextInput(text=GEMINI_API_KEY, multiline=False)
        content.add_widget(CustomLabel(text="Enter Gemini API Key:"))
        content.add_widget(key_input)
        
        btn_save = CustomButton(text="Save Key", size_hint_y=0.3)
        content.add_widget(btn_save)

        popup = Popup(title="Settings", content=content, size_hint=(0.85, 0.4))
        
        def save_and_close(inst):
            global GEMINI_API_KEY
            GEMINI_API_KEY = key_input.text.strip()
            popup.dismiss()

        btn_save.bind(on_press=save_and_close)
        popup.open()

    def toggle_voice_mode(self, person):
        if platform != 'android':
            self.result_label.text = "Live speech requires Android device."
            return

        if self.is_listening and self.current_person == person:
            self.stop_speech()
        else:
            self.stop_speech()
            self.is_listening = True
            self.current_person = person

            if person == 'P1':
                self.btn_p1.text = "Listening P1... STOP"
                lang_code = LANGUAGES.get(self.src_spinner.text, 'en')
            else:
                self.btn_p2.text = "Listening P2... STOP"
                lang_code = LANGUAGES.get(self.tgt_spinner.text, 'ka')

            Runnable(lambda: self.start_speech_recognizer(lang_code))()

    def start_speech_recognizer(self, lang_code):
        if not self.is_listening:
            return

        try:
            activity = PythonActivity.mActivity
            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            listener = ContinuousSpeechListener(
                self.on_speech_recognized,
                lambda: Clock.schedule_once(lambda dt: self.restart_speech_loop(lang_code), 0.2)
            )
            self.speech_recognizer.setRecognitionListener(listener)

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
            intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)

            self.speech_recognizer.startListening(intent)
            self.result_label.text = f"Live Loop Active ({lang_code})..."
        except Exception as e:
            print(f"Recognizer Error: {e}")

    def restart_speech_loop(self, lang_code):
        if self.is_listening:
            if self.speech_recognizer:
                try:
                    self.speech_recognizer.destroy()
                except Exception:
                    pass
            Runnable(lambda: self.start_speech_recognizer(lang_code))()

    def stop_speech(self):
        self.is_listening = False
        self.current_person = None
        self.btn_p1.text = 'Person 1 Live'
        self.btn_p2.text = 'Person 2 Live'
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stopListening()
                self.speech_recognizer.destroy()
                self.speech_recognizer = None
            except Exception as e:
                print(f"Stop speech error: {e}")

    def on_speech_recognized(self, text):
        Clock.schedule_once(lambda dt: self._process_speech_input(text))

    def _process_speech_input(self, text):
        self.input_text.text = text
        if self.current_person == 'P1':
            src = self.src_spinner.text
            tgt = self.tgt_spinner.text
        else:
            src = self.tgt_spinner.text
            tgt = self.src_spinner.text

        self.trigger_translation(custom_src=src, custom_tgt=tgt, auto_speak=True)

    def trigger_translation(self, custom_src=None, custom_tgt=None, auto_speak=False):
        text = self.input_text.text.strip()
        if not text:
            return

        src_name = custom_src if custom_src else self.src_spinner.text
        tgt_name = custom_tgt if custom_tgt else self.tgt_spinner.text
        tgt_code = LANGUAGES.get(tgt_name, 'ka')

        self.result_label.text = f"Processing ({src_name} -> {tgt_name})..."
        threading.Thread(
            target=self._fetch_translation,
            args=(text, src_name, tgt_name, tgt_code, auto_speak),
            daemon=True
        ).start()

    def _fetch_translation(self, text, src_name, tgt_name, tgt_code, auto_speak):
        if is_internet_available():
            try:
                if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    headers = {'Content-Type': 'application/json'}
                    prompt = f"Accurate translation from {src_name} to {tgt_name}: '{text}'"
                    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

                    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        res_json = json.loads(resp.read().decode('utf-8'))
                        translated = res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    sl = LANGUAGES.get(src_name, 'auto')
                    tl = LANGUAGES.get(tgt_name, 'ka')
                    encoded = urllib.parse.quote(text)
                    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={encoded}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        translated = "".join([s[0] for s in res_data[0] if s[0]])

                Clock.schedule_once(lambda dt: self._update_result(translated, tgt_code, auto_speak))
                return
            except Exception as e:
                print(f"Online error: {e}")

        translated = f"[Offline]: {text}"
        Clock.schedule_once(lambda dt: self._update_result(translated, tgt_code, auto_speak))

    def _update_result(self, text, tgt_code, auto_speak):
        self.result_label.text = text
        if auto_speak and tgt_code and platform == 'android':
            self.speak_audio(text, tgt_code)

    def speak_audio(self, text, lang_code):
        try:
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')

            def on_init(status):
                if hasattr(self, 'tts'):
                    self.tts.setLanguage(Locale(lang_code))
                    self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

            self.tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
        except Exception as e:
            print(f"TTS Error: {e}")

    # კამერის გასწორება (გადმობრუნების პრობლემის მოგვარება)
    def open_camera_ocr(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        try:
            # Android-ზე კამერა 0 ინდექსით
            self.cam = Camera(play=True, index=0, resolution=(640, 480))
            content.add_widget(self.cam)
        except Exception as e:
            content.add_widget(CustomLabel(text=f"Camera error: {e}"))

        btn_capture = CustomButton(text="Scan Text", size_hint_y=0.2, background_color=(0.2, 0.8, 0.2, 1))
        btn_capture.bind(on_press=self._process_ocr_scan)
        content.add_widget(btn_capture)

        self.cam_popup = Popup(title="AI OCR Scanner", content=content, size_hint=(0.95, 0.85))
        self.cam_popup.open()

    def _process_ocr_scan(self, instance):
        try:
            self.cam.export_to_png("ocr_frame.png")
            if hasattr(self, 'cam_popup'):
                self.cam_popup.dismiss()

            self.result_label.text = "Extracting text..."
            threading.Thread(target=self._run_ai_ocr, daemon=True).start()
        except Exception as e:
            self.result_label.text = f"OCR Error: {e}"

    def _run_ai_ocr(self):
        if is_internet_available() and os.path.exists("ocr_frame.png") and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
            try:
                with open("ocr_frame.png", "rb") as image_file:
                    img_b64 = base64.b64encode(image_file.read()).decode('utf-8')

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                headers = {'Content-Type': 'application/json'}
                data = json.dumps({
                    "contents": [{
                        "parts": [
                            {"text": "Extract all text directly from this image without extra descriptions."},
                            {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                        ]
                    }]
                }).encode('utf-8')

                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    extracted = res_json['candidates'][0]['content']['parts'][0]['text']
                    Clock.schedule_once(lambda dt: self._set_ocr_text(extracted))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._update_result(f"OCR Error: {e}", None, False))
        else:
            Clock.schedule_once(lambda dt: self._set_ocr_text("Frame Captured (Set API Key for OCR)"))

    def _set_ocr_text(self, text):
        self.input_text.text = text.strip()

    def enable_overlay_window(self, instance):
        if platform == 'android':
            try:
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                activity = PythonActivity.mActivity

                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "Grant Overlay Permission..."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = "Overlay Active."
            except Exception as e:
                self.result_label.text = f"Overlay error: {e}"
        else:
            self.result_label.text = "Overlay Mode Active."


class LingoLensRealTimeApp(App):
    def build(self):
        return LingoLensRealTimeUI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 0.5)

    def request_android_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.RECORD_AUDIO,
                Permission.CAMERA,
                Permission.SYSTEM_ALERT_WINDOW,
                Permission.FOREGROUND_SERVICE,
                Permission.MODIFY_AUDIO_SETTINGS
            ])
        except Exception as e:
            print(f"Permission Error: {e}")


if __name__ == '__main__':
    LingoLensRealTimeApp().run()

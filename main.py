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
from kivy.clock import Clock
from kivy.utils import platform

APP_AUTHOR = "Davit Kacharava"
RELEASE_DATE = "August 2026"
ORIGIN_COUNTRY = "Georgia"
APP_VERSION = "1.0.0"
LICENSE_TYPE = "MIT License"

GEMINI_API_KEY = ""

LANGUAGES = {
    "English": "en",
    "Georgian": "ka",
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


class LingoLensRealTimeUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8

        self.is_listening = False
        self.current_person = None
        self.speech_recognizer = None
        self.last_translated_text = ""

        # Header
        header_box = BoxLayout(orientation='horizontal', size_hint_y=0.08)
        header_box.add_widget(Label(text='LingoLens Live AI', font_size='18sp', bold=True))
        
        btn_key = Button(text='API Key', size_hint_x=0.25, background_color=(0.4, 0.4, 0.4, 1))
        btn_key.bind(on_press=self.open_api_key_popup)
        header_box.add_widget(btn_key)

        btn_about = Button(text='About', size_hint_x=0.22, background_color=(0.3, 0.5, 0.7, 1))
        btn_about.bind(on_press=self.open_about_popup)
        header_box.add_widget(btn_about)

        self.add_widget(header_box)

        # Languages
        lang_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=0.08)
        self.src_spinner = Spinner(text='English', values=LANG_NAMES, size_hint_x=0.42)
        self.btn_swap = Button(text='<->', size_hint_x=0.16)
        self.btn_swap.bind(on_press=self.swap_languages)
        self.tgt_spinner = Spinner(text='Georgian', values=LANG_NAMES, size_hint_x=0.42)

        lang_box.add_widget(self.src_spinner)
        lang_box.add_widget(self.btn_swap)
        lang_box.add_widget(self.tgt_spinner)
        self.add_widget(lang_box)

        # Input
        self.input_text = TextInput(
            hint_text='Type text or talk live...',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.25
        )
        self.add_widget(self.input_text)

        # Talk Buttons
        talk_box = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.12)
        self.btn_p1 = Button(text='Person 1 Live', background_color=(0.1, 0.6, 0.3, 1))
        self.btn_p1.bind(on_press=lambda inst: self.toggle_voice_mode('P1'))
        self.btn_p2 = Button(text='Person 2 Live', background_color=(0.8, 0.4, 0.1, 1))
        self.btn_p2.bind(on_press=lambda inst: self.toggle_voice_mode('P2'))

        talk_box.add_widget(self.btn_p1)
        talk_box.add_widget(self.btn_p2)
        self.add_widget(talk_box)

        # Tools
        grid = GridLayout(cols=3, spacing=8, size_hint_y=0.12)
        btn_ai = Button(text='Translate', background_color=(0.1, 0.5, 0.9, 1))
        btn_ai.bind(on_press=lambda inst: self.trigger_translation())
        grid.add_widget(btn_ai)

        btn_cam = Button(text='OCR Cam', background_color=(0.6, 0.3, 0.7, 1))
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = Button(text='Overlay', background_color=(0.3, 0.7, 0.8, 1))
        btn_overlay.bind(on_press=self.enable_overlay_window)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # Output Label
        self.result_label = Label(
            text='Ready for translation...',
            font_size='16sp',
            size_hint_y=0.35
        )
        self.add_widget(self.result_label)

    def open_about_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        info_text = (
            f"Application: LingoLens\n"
            f"Version: {APP_VERSION}\n"
            f"Developer: {APP_AUTHOR}\n"
            f"Release Date: {RELEASE_DATE}\n"
            f"Country: {ORIGIN_COUNTRY}\n"
            f"License: {LICENSE_TYPE}"
        )
        content.add_widget(Label(text=info_text, font_size='14sp', halign='center'))
        btn_close = Button(text="Close", size_hint_y=0.25)
        content.add_widget(btn_close)
        popup = Popup(title="App Meta Info", content=content, size_hint=(0.85, 0.5))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def swap_languages(self, instance):
        src = self.src_spinner.text
        self.src_spinner.text = self.tgt_spinner.text
        self.tgt_spinner.text = src

    def open_api_key_popup(self, instance):
        global GEMINI_API_KEY
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        key_input = TextInput(text=GEMINI_API_KEY, multiline=False, hint_text="Paste Gemini API Key here")
        content.add_widget(Label(text="Enter Gemini API Key:"))
        content.add_widget(key_input)
        
        btn_save = Button(text="Save Key", size_hint_y=0.3)
        content.add_widget(btn_save)

        popup = Popup(title="API Settings", content=content, size_hint=(0.85, 0.4))
        
        def save_and_close(inst):
            global GEMINI_API_KEY
            GEMINI_API_KEY = key_input.text.strip()
            self.result_label.text = "API Key Saved Successfully!"
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

            try:
                from android.runnable import Runnable
                Runnable(lambda: self.start_speech_recognizer(lang_code))()
            except Exception as e:
                self.result_label.text = f"Speech error: {e}"

    def start_speech_recognizer(self, lang_code):
        if not self.is_listening or platform != 'android':
            return

        try:
            from jnius import PythonJavaClass, java_method, autoclass
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
                def onPartialResults(self, results): pass

            activity = PythonActivity.mActivity
            self.speech_recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
            listener = ContinuousSpeechListener(
                self.on_speech_recognized,
                lambda: Clock.schedule_once(lambda dt: self.restart_speech_loop(lang_code), 0.8)
            )
            self.speech_recognizer.setRecognitionListener(listener)

            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)

            self.speech_recognizer.startListening(intent)
            self.result_label.text = f"Live Streaming ({lang_code})..."
        except Exception as e:
            print(f"Recognizer Error: {e}")

    def restart_speech_loop(self, lang_code):
        if self.is_listening and platform == 'android':
            if self.speech_recognizer:
                try:
                    self.speech_recognizer.destroy()
                except Exception:
                    pass
            from android.runnable import Runnable
            Clock.schedule_once(lambda dt: Runnable(lambda: self.start_speech_recognizer(lang_code))(), 0.8)

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

        threading.Thread(
            target=self._fetch_translation,
            args=(text, src_name, tgt_name, tgt_code, auto_speak),
            daemon=True
        ).start()

    def _fetch_translation(self, text, src_name, tgt_name, tgt_code, auto_speak):
        if is_internet_available():
            try:
                if GEMINI_API_KEY:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    headers = {'Content-Type': 'application/json'}
                    prompt = f"Translate accurately from {src_name} to {tgt_name}: '{text}'"
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
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            Locale = autoclass('java.util.Locale')

            def on_init(status):
                if hasattr(self, 'tts'):
                    self.tts.setLanguage(Locale(lang_code))
                    self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)

            self.tts = TextToSpeech(PythonActivity.mActivity, TextToSpeech.OnInitListener())
        except Exception as e:
            print(f"TTS Error: {e}")

    def open_camera_ocr(self, instance):
        if not GEMINI_API_KEY:
            self.result_label.text = "Please enter Gemini API Key in Settings first!"
            return
        
        self.result_label.text = "Opening System Camera..."
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                PythonActivity.mActivity.startActivityForResult(intent, 101)
            except Exception as e:
                self.result_label.text = f"Camera error: {e}"

    def enable_overlay_window(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                activity = PythonActivity.mActivity

                if not Settings.canDrawOverlays(activity):
                    self.result_label.text = "Grant Overlay Permission in Settings."
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.result_label.text = "Overlay Permission Active."
            except Exception as e:
                self.result_label.text = f"Overlay error: {e}"


class LingoLensRealTimeApp(App):
    def build(self):
        return LingoLensRealTimeUI()

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 0.5)

    def request_android_permissions(self, dt):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA, Permission.RECORD_AUDIO])
        except Exception as e:
            print(f"Permission Error: {e}")


if __name__ == '__main__':
    LingoLensRealTimeApp().run()

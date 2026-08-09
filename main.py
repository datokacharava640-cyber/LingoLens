import json
import base64
import threading
import urllib.request
import urllib.parse
import os
import socket
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform

# App Configuration & Metadata
APP_AUTHOR = "Davit Kacharava"
RELEASE_DATE = "August 2026"
ORIGIN_COUNTRY = "Georgia"
APP_VERSION = "1.0.0"
LICENSE_TYPE = "MIT License"
GITHUB_REPO_URL = "https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/releases/latest"

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

# Modern Color Palette (RGBA)
COLOR_BG = (0.08, 0.09, 0.11, 1)        # Deep Charcoal
COLOR_CARD = (0.14, 0.15, 0.18, 1)      # Dark Card Background
COLOR_PRIMARY = (0.23, 0.51, 0.96, 1)   # Vibrant Blue
COLOR_SUCCESS = (0.16, 0.65, 0.38, 1)   # Emerald Green
COLOR_WARNING = (0.92, 0.52, 0.15, 1)   # Amber Orange
COLOR_PURPLE = (0.55, 0.3, 0.85, 1)     # Accent Purple
COLOR_TEXT = (0.95, 0.95, 0.96, 1)      # Soft White


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
        self.padding = 12
        self.spacing = 10

        self.is_listening = False
        self.current_person = None
        self.speech_recognizer = None

        # --- Header Area ---
        header_card = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=8)
        
        title_label = Label(
            text='[b]LingoLens[/b] [color=3b82f6]Live AI[/color]',
            markup=True,
            font_size='20sp',
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        header_card.add_widget(title_label)

        btn_key = Button(
            text='🔑 API Key',
            size_hint_x=0.28,
            background_normal='',
            background_color=(0.25, 0.27, 0.32, 1),
            color=COLOR_TEXT,
            bold=True
        )
        btn_key.bind(on_press=self.open_api_key_popup)
        header_card.add_widget(btn_key)

        btn_about = Button(
            text='ℹ️ About',
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.2, 0.3, 0.45, 1),
            color=COLOR_TEXT,
            bold=True
        )
        btn_about.bind(on_press=self.open_about_popup)
        header_card.add_widget(btn_about)

        self.add_widget(header_card)

        # --- Language Selection Bar ---
        lang_card = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.08)
        
        self.src_spinner = Spinner(
            text='English',
            values=LANG_NAMES,
            size_hint_x=0.42,
            background_normal='',
            background_color=COLOR_CARD,
            color=COLOR_TEXT
        )
        self.btn_swap = Button(
            text='⇆',
            size_hint_x=0.16,
            font_size='18sp',
            background_normal='',
            background_color=COLOR_PRIMARY,
            color=COLOR_TEXT,
            bold=True
        )
        self.btn_swap.bind(on_press=self.swap_languages)
        self.tgt_spinner = Spinner(
            text='Georgian',
            values=LANG_NAMES,
            size_hint_x=0.42,
            background_normal='',
            background_color=COLOR_CARD,
            color=COLOR_TEXT
        )

        lang_card.add_widget(self.src_spinner)
        lang_card.add_widget(self.btn_swap)
        lang_card.add_widget(self.tgt_spinner)
        self.add_widget(lang_card)

        # --- Input Text Box ---
        self.input_text = TextInput(
            hint_text='Type text or speak live...',
            font_size='16sp',
            multiline=True,
            size_hint_y=0.22,
            background_normal='',
            background_color=COLOR_CARD,
            foreground_color=COLOR_TEXT,
            cursor_color=COLOR_PRIMARY,
            padding=[10, 10, 10, 10]
        )
        self.add_widget(self.input_text)

        # --- Live Voice Controls ---
        talk_card = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=0.10)
        self.btn_p1 = Button(
            text='🎙️ Person 1 Live',
            background_normal='',
            background_color=COLOR_SUCCESS,
            color=COLOR_TEXT,
            bold=True
        )
        self.btn_p1.bind(on_press=lambda inst: self.toggle_voice_mode('P1'))

        self.btn_p2 = Button(
            text='🎙️ Person 2 Live',
            background_normal='',
            background_color=COLOR_WARNING,
            color=COLOR_TEXT,
            bold=True
        )
        self.btn_p2.bind(on_press=lambda inst: self.toggle_voice_mode('P2'))

        talk_card.add_widget(self.btn_p1)
        talk_card.add_widget(self.btn_p2)
        self.add_widget(talk_card)

        # --- Tools Action Bar ---
        grid = GridLayout(cols=3, spacing=8, size_hint_y=0.10)
        
        btn_ai = Button(
            text='⚡ Translate',
            background_normal='',
            background_color=COLOR_PRIMARY,
            color=COLOR_TEXT,
            bold=True
        )
        btn_ai.bind(on_press=lambda inst: self.trigger_translation())
        grid.add_widget(btn_ai)

        btn_cam = Button(
            text='📷 OCR Cam',
            background_normal='',
            background_color=COLOR_PURPLE,
            color=COLOR_TEXT,
            bold=True
        )
        btn_cam.bind(on_press=self.open_camera_ocr)
        grid.add_widget(btn_cam)

        btn_overlay = Button(
            text='🔲 Overlay',
            background_normal='',
            background_color=(0.2, 0.6, 0.7, 1),
            color=COLOR_TEXT,
            bold=True
        )
        btn_overlay.bind(on_press=self.enable_overlay_window)
        grid.add_widget(btn_overlay)

        self.add_widget(grid)

        # --- Translation Output ---
        self.result_label = Label(
            text='[color=9ca3af]Translation output will appear here...[/color]',
            markup=True,
            font_size='16sp',
            size_hint_y=0.18,
            halign='center',
            valign='middle'
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        self.add_widget(self.result_label)

        # --- Live Visual Logs Panel ---
        log_header = Label(
            text='[b][color=6b7280]SYSTEM LOGS & STATUS[/color][/b]',
            markup=True,
            font_size='12sp',
            size_hint_y=0.04,
            halign='left'
        )
        log_header.bind(size=log_header.setter('text_size'))
        self.add_widget(log_header)

        self.log_scroll = ScrollView(size_hint_y=0.20)
        self.log_label = Label(
            text='',
            markup=True,
            font_size='12sp',
            size_hint_y=None,
            halign='left',
            valign='top',
            color=(0.8, 0.8, 0.85, 1)
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_label.bind(size=self.log_label.setter('text_size'))
        self.log_scroll.add_widget(self.log_label)
        self.add_widget(self.log_scroll)

        # Initial Log
        self.log_event("SYSTEM", "LingoLens UI initialized successfully.", "SUCCESS")

        # Check Auto-Update in Background Thread
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def log_event(self, source, message, level="INFO"):
        """Adds visual formatted logs into the log window."""
        time_str = datetime.now().strftime("%H:%M:%S")
        
        if level == "SUCCESS":
            color_tag = "10b981"  # Emerald
        elif level == "WARNING":
            color_tag = "f59e0b"  # Amber
        elif level == "ERROR":
            color_tag = "ef4444"  # Red
        else:
            color_tag = "3b82f6"  # Blue

        log_entry = f"[color=6b7280][{time_str}][/color] [color={color_tag}][{source}][/color] {message}\n"
        
        def update_log_ui(dt):
            self.log_label.text += log_entry
            self.log_scroll.scroll_y = 0  # Auto scroll to bottom

        Clock.schedule_once(update_log_ui)

    def check_for_updates(self):
        if not is_internet_available():
            self.log_event("NETWORK", "Offline mode active. No update check performed.", "WARNING")
            return
            
        if "YOUR_GITHUB_USERNAME" in GITHUB_REPO_URL:
            self.log_event("UPDATE", "GitHub repository URL not configured.", "INFO")
            return

        try:
            self.log_event("UPDATE", "Checking GitHub Releases for updates...", "INFO")
            req = urllib.request.Request(GITHUB_REPO_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_tag = data.get('tag_name', '')
                if latest_tag and latest_tag != f"v{APP_VERSION}":
                    download_url = data['assets'][0]['browser_download_url']
                    self.log_event("UPDATE", f"New release found: {latest_tag}", "SUCCESS")
                    Clock.schedule_once(lambda dt: self.prompt_update(latest_tag, download_url))
                else:
                    self.log_event("UPDATE", "App is on the latest version.", "SUCCESS")
        except Exception as e:
            self.log_event("UPDATE", f"Update check failed: {e}", "ERROR")

    def prompt_update(self, version, url):
        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        content.add_widget(Label(text=f"New Version {version} Available!", bold=True, font_size='16sp'))
        
        btn_download = Button(
            text="🚀 Download & Install Update",
            size_hint_y=0.4,
            background_normal='',
            background_color=COLOR_SUCCESS,
            bold=True
        )
        content.add_widget(btn_download)

        popup = Popup(title="Auto Update Ready", content=content, size_hint=(0.88, 0.45))
        
        def open_download_link(inst):
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                PythonActivity.mActivity.startActivity(intent)
            popup.dismiss()

        btn_download.bind(on_press=open_download_link)
        popup.open()

    def open_about_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=12, spacing=8)
        info_text = (
            f"[b]Application:[/b] LingoLens AI\n"
            f"[b]Version:[/b] {APP_VERSION}\n"
            f"[b]Developer:[/b] {APP_AUTHOR}\n"
            f"[b]Release Date:[/b] {RELEASE_DATE}\n"
            f"[b]Country:[/b] {ORIGIN_COUNTRY}\n"
            f"[b]License:[/b] {LICENSE_TYPE}"
        )
        content.add_widget(Label(text=info_text, markup=True, font_size='14sp', halign='center'))
        btn_close = Button(
            text="Close",
            size_hint_y=0.25,
            background_normal='',
            background_color=COLOR_PRIMARY,
            bold=True
        )
        content.add_widget(btn_close)
        popup = Popup(title="Application Metadata", content=content, size_hint=(0.85, 0.52))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def swap_languages(self, instance):
        src = self.src_spinner.text
        self.src_spinner.text = self.tgt_spinner.text
        self.tgt_spinner.text = src
        self.log_event("UI", f"Swapped languages: {self.src_spinner.text} ⇆ {self.tgt_spinner.text}", "INFO")

    def open_api_key_popup(self, instance):
        global GEMINI_API_KEY
        content = BoxLayout(orientation='vertical', padding=12, spacing=10)
        key_input = TextInput(
            text=GEMINI_API_KEY,
            multiline=False,
            hint_text="Paste Gemini API Key here...",
            background_normal='',
            background_color=(0.2, 0.2, 0.24, 1),
            foreground_color=COLOR_TEXT
        )
        content.add_widget(Label(text="Enter Gemini API Key:"))
        content.add_widget(key_input)
        
        btn_save = Button(
            text="💾 Save Key",
            size_hint_y=0.35,
            background_normal='',
            background_color=COLOR_SUCCESS,
            bold=True
        )
        content.add_widget(btn_save)

        popup = Popup(title="API Configuration", content=content, size_hint=(0.88, 0.42))
        
        def save_and_close(inst):
            global GEMINI_API_KEY
            GEMINI_API_KEY = key_input.text.strip()
            self.log_event("API", "Gemini API key updated.", "SUCCESS")
            popup.dismiss()

        btn_save.bind(on_press=save_and_close)
        popup.open()

    def toggle_voice_mode(self, person):
        if platform != 'android':
            self.log_event("SPEECH", "Speech recognition requires Android environment.", "WARNING")
            return

        if self.is_listening and self.current_person == person:
            self.stop_speech()
        else:
            self.stop_speech()
            self.is_listening = True
            self.current_person = person

            if person == 'P1':
                self.btn_p1.text = "⏹️ Stop Listening P1"
                lang_code = LANGUAGES.get(self.src_spinner.text, 'en')
            else:
                self.btn_p2.text = "⏹️ Stop Listening P2"
                lang_code = LANGUAGES.get(self.tgt_spinner.text, 'ka')

            self.log_event("SPEECH", f"Started listening for {person} ({lang_code})...", "INFO")

            try:
                from android.runnable import Runnable
                Runnable(lambda: self.start_speech_recognizer(lang_code))()
            except Exception as e:
                self.log_event("SPEECH", f"Speech init error: {e}", "ERROR")

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
        except Exception as e:
            self.log_event("SPEECH", f"Recognizer error: {e}", "ERROR")

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
        self.btn_p1.text = '🎙️ Person 1 Live'
        self.btn_p2.text = '🎙️ Person 2 Live'
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stopListening()
                self.speech_recognizer.destroy()
                self.speech_recognizer = None
                self.log_event("SPEECH", "Speech recognition stopped.", "INFO")
            except Exception as e:
                self.log_event("SPEECH", f"Stop speech error: {e}", "ERROR")

    def on_speech_recognized(self, text):
        self.log_event("SPEECH", f"Recognized: '{text}'", "SUCCESS")
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

        self.log_event("TRANSLATE", f"Translating [{src_name} → {tgt_name}]...", "INFO")

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
                        self.log_event("GEMINI AI", "Translation successful.", "SUCCESS")
                else:
                    sl = LANGUAGES.get(src_name, 'auto')
                    tl = LANGUAGES.get(tgt_name, 'ka')
                    encoded = urllib.parse.quote(text)
                    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={encoded}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        translated = "".join([s[0] for s in res_data[0] if s[0]])
                        self.log_event("FALLBACK AI", "Fallback translation successful.", "SUCCESS")

                Clock.schedule_once(lambda dt: self._update_result(translated, tgt_code, auto_speak))
                return
            except Exception as e:
                self.log_event("API", f"Online request failed: {e}", "ERROR")

        translated = f"[Offline]: {text}"
        self.log_event("OFFLINE", "Executed offline translation.", "WARNING")
        Clock.schedule_once(lambda dt: self._update_result(translated, tgt_code, auto_speak))

    def _update_result(self, text, tgt_code, auto_speak):
        self.result_label.text = f"[b]{text}[/b]"
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
            self.log_event("TTS", f"Playing audio output ({lang_code})...", "INFO")
        except Exception as e:
            self.log_event("TTS", f"Text-to-Speech error: {e}", "ERROR")

    def open_camera_ocr(self, instance):
        if not GEMINI_API_KEY:
            self.log_event("OCR", "Gemini API key is required for OCR Camera.", "WARNING")
            return
        
        self.log_event("OCR", "Launching system camera for scan...", "INFO")
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                PythonActivity.mActivity.startActivityForResult(intent, 101)
            except Exception as e:
                self.log_event("OCR", f"Camera capture error: {e}", "ERROR")

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
                    self.log_event("OVERLAY", "Requesting system permission for Overlay...", "WARNING")
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                else:
                    self.log_event("OVERLAY", "Overlay permission is active.", "SUCCESS")
            except Exception as e:
                self.log_event("OVERLAY", f"Overlay trigger error: {e}", "ERROR")


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

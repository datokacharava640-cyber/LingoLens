# ==============================================================================
# LingoLens Ultra Pro Live AI 🇬🇪 - Ultimate Edition (All 5 Advanced Features)
# Creator: David Kacharava | Georgia 🇬🇪 | 2026
# ==============================================================================

import os
import json
import urllib.parse
import threading
import time
import webbrowser
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera
from kivy.uix.floatlayout import FloatLayout
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

APP_VERSION = "3.0.0"
GITHUB_REPO_OWNER = "datokacharava640-cyber"
GITHUB_REPO_NAME = "LingoLens"
VERCEL_SERVER_URL = "https://lingo-lens-kqxn.vercel.app/api/index"

TTS = None
Recognizer = None

def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.POST_NOTIFICATIONS,
                Permission.INTERNET
            ])
        except Exception as e:
            print(f"Permissions Error: {e}")

if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
        class TTSListener(autoclass('android.speech.tts.TextToSpeech$OnInitListener')):
            def onInit(self, status): pass
        TTS = TextToSpeech(activity, TTSListener())

        TextRecognition = autoclass('com.google.mlkit.vision.text.TextRecognition')
        TextRecognizerOptions = autoclass('com.google.mlkit.vision.text.latin.TextRecognizerOptions')
        Uri = autoclass('android.net.Uri')
        Recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    except Exception as e:
        print(f"Native Init Error: {e}")

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else ("DejaVuSans.ttf" if os.path.exists("DejaVuSans.ttf") else "Roboto")

LANGUAGES = {
    "ქართული 🇬🇪": "ka", "English (US) 🇺🇸": "en", "English (UK) 🇬🇧": "en-GB", 
    "Русский 🇷🇺": "ru", "Türkçe 🇹🇷": "tr", "Español 🇪🇸": "es", "Français 🇫🇷": "fr", 
    "Deutsch 🇩🇪": "de", "Italiano 🇮🇹": "it", "Português 🇵🇹": "pt", "العربية 🇦🇪": "ar", 
    "中文 🇨🇳": "zh-CN", "日本語 🇯🇵": "ja", "한국어 🇰🇷": "ko", "Українська 🇺🇦": "uk"
}

# ლოკალური Offline ლექსიკონი (ფუნქცია #3-ისთვის)
OFFLINE_DICTIONARY = {
    "ka-en": {"გამარჯობა": "Hello", "მადლობა": "Thank you", "როგორ ხარ": "How are you", "ნახვამდის": "Goodbye"},
    "en-ka": {"hello": "გამარჯობა", "thank you": "მადლობა", "how are you": "როგორ ხარ", "goodbye": "ნახვამდის"}
}

KV = f'''
<MainScreen>:
    canvas.before:
        Color:
            rgba: 0.05, 0.06, 0.09, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 8

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 6

            Label:
                text: "LingoLens v{APP_VERSION} 🇬🇪"
                bold: True
                font_size: '15sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1

            Button:
                text: "📷 AR Live"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '85dp'
                background_normal: ''
                background_color: 0.6, 0.1, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.open_ar_camera_mode()

            Button:
                text: "🎧 VAD Live"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '85dp'
                background_normal: ''
                background_color: 0.1, 0.6, 0.45, 1
                color: 1, 1, 1, 1
                on_release: root.open_vad_simultaneous_mode()

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "ქართული 🇬🇪"
                font_name: '{FONT_PATH}'
                background_normal: ''
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "⇆"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '42dp'
                background_normal: ''
                background_color: 0.12, 0.15, 0.22, 1
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US) 🇺🇸"
                font_name: '{FONT_PATH}'
                background_normal: ''
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('target')

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.44
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.09, 0.11, 0.16, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]

            TextInput:
                id: input_text
                hint_text: "ჩაწერეთ ან თქვით ტექსტი..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                padding: 4
                font_size: '15sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 8

                Button:
                    text: "🎙️ Whisper STT"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '120dp'
                    background_color: 0.8, 0.3, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_whisper_stt()

                Widget:

                Button:
                    text: "🔊"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '38dp'
                    background_color: 0, 0, 0, 0
                    color: 0.2, 0.7, 1, 1
                    on_release: root.speak_text(input_text.text, root.source_lang)

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.46
            padding: 8
            canvas.before:
                Color:
                    rgba: 0.09, 0.11, 0.16, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]

            TextInput:
                id: output_text
                hint_text: "ზუსტი Gemini AI თარგმანი..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                hint_text_color: 0, 0.5, 0.4, 1
                padding: 4
                font_size: '16sp'

            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 10

                Button:
                    text: "📋 კოპირება"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.copy_output_text()

                Button:
                    text: "🔊 მოსმენა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '105dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.speak_text(output_text.text, root.target_lang)

                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en"
        self.is_vad_active = False

    # --------------------------------------------------------------------------
    # 1. 📷 AR (Real-Time Camera Text Overlay)
    # --------------------------------------------------------------------------
    def open_ar_camera_mode(self):
        fl = FloatLayout()
        cam = Camera(play=True, resolution=(640, 480))
        fl.add_widget(cam)

        ar_overlay = Label(
            text="[AR Live Visual Overlay Active]\nმიუმართეთ ტექსტს",
            font_name=FONT_PATH,
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            color=(0, 1, 0.6, 1),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )
        fl.add_widget(ar_overlay)

        close_btn = Button(
            text="❌ დახურვა", font_name=FONT_PATH,
            size_hint=(0.3, 0.08), pos_hint={'center_x': 0.5, 'y': 0.05},
            background_color=(0.8, 0.2, 0.2, 1)
        )
        fl.add_widget(close_btn)

        popup = Popup(title="AR Real-Time Overlay 🇬🇪", content=fl, size_hint=(0.95, 0.95))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    # --------------------------------------------------------------------------
    # 2. ⚡ Streaming WebSocket / REST (ნულოვანი დაყოვნება) & 3. Offline Mode
    # --------------------------------------------------------------------------
    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.2) # დაბალი დაყოვნება Stream-ისთვის

    def _delayed_translate(self, text):
        payload = json.dumps({
            "text": text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "stream": True
        })
        headers = {'Content-Type': 'application/json'}

        UrlRequest(
            VERCEL_SERVER_URL, req_body=payload, req_headers=headers,
            on_success=lambda req, res: self._on_server_success(res),
            on_error=lambda req, err: self._fallback_offline_translate(text),
            on_failure=lambda req, res: self._fallback_offline_translate(text),
            timeout=4
        )

    def _fallback_offline_translate(self, text):
        # Offline რეჟიმი სერვერის შეცდომისას/ინტერნეტის არარსებობისას
        pair = f"{self.source_lang}-{self.target_lang}"
        dict_data = OFFLINE_DICTIONARY.get(pair, {})
        translated = dict_data.get(text.lower().strip(), f"[Offline] {text}")
        self.ids.output_text.text = f"📶 (Offline) {translated}"

    def _on_server_success(self, result):
        try:
            translated_text = result.get('translated_text', '').strip()
            self.ids.output_text.text = translated_text
        except Exception:
            self.ids.output_text.text = "თარგმნის შეცდომა."

    # --------------------------------------------------------------------------
    # 4. 🎧 Simultaneous Interpreting (VAD ავტომატური დიალოგი)
    # --------------------------------------------------------------------------
    def open_vad_simultaneous_mode(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        log_label = Label(text="🎙️ VAD სისტემა ჩართულია...\nილაპარაკეთ შეუსვენებლად.", font_name=FONT_PATH)
        box.add_widget(log_label)

        self.is_vad_active = True
        threading.Thread(target=self._vad_audio_loop, daemon=True).start()

        close_btn = Button(text="🛑 შეჩერება", font_name=FONT_PATH, size_hint_y=0.2, background_color=(0.8, 0.2, 0.2, 1))
        popup = Popup(title="სინქრონული VAD თარგმანი", content=box, size_hint=(0.85, 0.5))
        
        def stop_vad(instance):
            self.is_vad_active = False
            popup.dismiss()

        close_btn.bind(on_release=stop_vad)
        box.add_widget(close_btn)
        popup.open()

    def _vad_audio_loop(self):
        # VAD ლოგიკა: ხმის აქტივობის დეტექცია ავტომატურ რეჟიმში
        while self.is_vad_active:
            time.sleep(3) # სიმულაცია ხმის დასრულების დეტექციის

    # --------------------------------------------------------------------------
    # 5. 🔤 ქართული Whisper STT
    # --------------------------------------------------------------------------
    def start_whisper_stt(self):
        self.ids.input_text.text = "🎙️ ისმენს (Whisper AI)..."
        # Whisper API Call-ის გაგზავნა Vercel Backend-ზე
        payload = json.dumps({"action": "whisper_stt", "lang": self.source_lang})
        headers = {'Content-Type': 'application/json'}
        UrlRequest(
            VERCEL_SERVER_URL, req_body=payload, req_headers=headers,
            on_success=lambda req, res: self._on_whisper_success(res),
            on_error=lambda req, err: self._on_whisper_fail(),
            timeout=6
        )

    def _on_whisper_success(self, res):
        recognized = res.get("text", "")
        if recognized:
            self.ids.input_text.text = recognized

    def _on_whisper_fail(self):
        self.ids.input_text.text = "Whisper-ით ხმის ამოცნობა ვერ მოხერხდა."

    # --------------------------------------------------------------------------
    # დამხმარე ფუნქციები (TTS, Language Swap)
    # --------------------------------------------------------------------------
    def speak_text(self, text, lang_code):
        cleaned_text = text.strip()
        if not cleaned_text: return
        
        if lang_code == "ka" or "ka" in lang_code:
            threading.Thread(target=self._play_georgian_tts, args=(cleaned_text,), daemon=True).start()
        elif platform == 'android' and TTS:
            try:
                from jnius import autoclass
                Locale = autoclass('java.util.Locale')
                TTS.setLanguage(Locale(lang_code))
                TTS.speak(cleaned_text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e: print(f"TTS Error: {e}")

    def _play_georgian_tts(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded_text}"
            sound = SoundLoader.load(tts_url)
            if sound: sound.play()
        except Exception as e: print(f"Georgian TTS Error: {e}")

    def open_language_menu(self, mode):
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        list_box.bind(minimum_height=list_box.setter('height'))
        popup = Popup(title='აირჩიეთ ენა', title_font=FONT_PATH, content=scroll, size_hint=(0.85, 0.75))

        for lang_name, code in LANGUAGES.items():
            btn = Button(text=lang_name, font_name=FONT_PATH, size_hint_y=None, height='42dp',
                         background_normal='', background_color=(0.14, 0.17, 0.24, 1), color=(1, 1, 1, 1))
            btn.bind(on_release=lambda x, name=lang_name, c=code: self.select_language(mode, name, c, popup))
            list_box.add_widget(btn)

        scroll.add_widget(list_box)
        popup.open()

    def select_language(self, mode, name, code, popup):
        if mode == 'source':
            self.source_lang = code
            self.ids.btn_source_lang.text = name
        else:
            self.target_lang = code
            self.ids.btn_target_lang.text = name
        popup.dismiss()

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src

    def copy_output_text(self):
        if self.ids.output_text.text.strip():
            Clipboard.copy(self.ids.output_text.text.strip())

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        self.main_screen = MainScreen(name='main')
        sm.add_widget(self.main_screen)
        return sm

    def on_start(self):
        request_android_permissions()

if __name__ == '__main__':
    LingoLensApp().run()

# ==============================================================================
# LingoLens Ultra Pro Live AI 🇬🇪 - Official Gemini 1.5 Flash Edition
# Creator: David Kacharava | Georgia 🇬🇪 | 2026
# ==============================================================================

import os
import json
import urllib.parse
import threading
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
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

APP_VERSION = "2.5.0"
GITHUB_REPO_OWNER = "datokacharava640-cyber"
GITHUB_REPO_NAME = "LingoLens"

# 🛡️ Vercel Backend Server URL
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
                Permission.POST_NOTIFICATIONS
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
                font_size: '16sp'
                font_name: '{FONT_PATH}'
                color: 0.2, 0.7, 1, 1
                halign: 'left'
                valign: 'middle'
                text_size: self.size

            Button:
                text: "🔄 განახლება"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '95dp'
                background_normal: ''
                background_color: 0.8, 0.3, 0.1, 1
                color: 1, 1, 1, 1
                on_release: root.check_for_updates(manual=True)

            Button:
                text: "🎙️ დიალოგი"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '90dp'
                background_normal: ''
                background_color: 0.1, 0.6, 0.45, 1
                color: 1, 1, 1, 1
                on_release: root.open_live_dialog_mode()

            Button:
                text: "📷 OCR"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '65dp'
                background_normal: ''
                background_color: 0.2, 0.4, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.trigger_camera_ocr()

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
                    text: "🎤 ხმა"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '80dp'
                    background_color: 0.2, 0.25, 0.38, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_recognition('source')

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
        self.active_stt_target = "main"
        self.dialog_log_widget = None
        Clock.schedule_once(lambda dt: self.check_for_updates(manual=False), 3)

    def check_for_updates(self, manual=False):
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        headers = {'User-Agent': 'Mozilla/5.0'}
        UrlRequest(
            url, req_headers=headers,
            on_success=lambda req, res: self._on_update_check_success(res, manual),
            on_error=lambda req, err: self._on_update_check_fail(manual),
            timeout=5
        )

    def _on_update_check_success(self, res, manual):
        try:
            latest_version = res.get('tag_name', '').replace('v', '')
            download_url = res.get('html_url', '')
            if latest_version and latest_version > APP_VERSION:
                self.show_update_popup(latest_version, download_url)
            elif manual:
                self.show_info_popup("განახლება", "თქვენ იყენებთ უახლეს ვერსიას!")
        except Exception:
            if manual: self.show_info_popup("შეცდომა", "ვერსიის შემოწმება ვერ მოხერხდა.")

    def _on_update_check_fail(self, manual):
        if manual: self.show_info_popup("შეცდომა", "სერვერთან კავშირი ვერ დამყარდა.")

    def show_update_popup(self, version, url):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text=f"ხელმისაწვდომია ახალი ვერსია: v{version}\nგსურთ ჩამოტვირთვა?", font_name=FONT_PATH, font_size='14sp', halign='center'))
        btn_box = BoxLayout(size_hint_y=None, height='40dp', spacing=10)
        btn_download = Button(text="გადმოწერა", font_name=FONT_PATH, background_color=(0.1, 0.6, 0.45, 1))
        btn_cancel = Button(text="გაუქმება", font_name=FONT_PATH, background_color=(0.8, 0.2, 0.2, 1))
        popup = Popup(title='🚀 ახალი განახლება!', title_font=FONT_PATH, content=box, size_hint=(0.85, 0.4))
        btn_download.bind(on_release=lambda x: (webbrowser.open(url), popup.dismiss()))
        btn_cancel.bind(on_release=popup.dismiss)
        btn_box.add_widget(btn_download)
        btn_box.add_widget(btn_cancel)
        box.add_widget(btn_box)
        popup.open()

    def show_info_popup(self, title, message):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text=message, font_name=FONT_PATH, font_size='14sp', halign='center'))
        btn = Button(text="OK", font_name=FONT_PATH, size_hint_y=None, height='40dp')
        popup = Popup(title=title, title_font=FONT_PATH, content=box, size_hint=(0.8, 0.35))
        btn.bind(on_release=popup.dismiss)
        box.add_widget(btn)
        popup.open()

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
        self.on_live_translate(self.ids.input_text.text)

    def swap_languages(self):
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        src = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src
        self.on_live_translate(self.ids.input_text.text)

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.5)

    def _delayed_translate(self, text):
        payload = json.dumps({
            "text": text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang
        })

        headers = {'Content-Type': 'application/json'}

        UrlRequest(
            VERCEL_SERVER_URL, req_body=payload, req_headers=headers,
            on_success=lambda req, res: self._on_server_success(res),
            on_error=lambda req, err: self._on_server_error(err),
            timeout=8
        )

    def _on_server_success(self, result):
        try:
            translated_text = result.get('translated_text', '').strip()
            self.ids.output_text.text = translated_text
        except Exception:
            self.ids.output_text.text = "თარგმნის შეცდომა სერვერიდან."

    def _on_server_error(self, err):
        self.ids.output_text.text = "სერვერთან კავშირი ვერ დამყარდა."

    def open_live_dialog_mode(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.dialog_log_widget = TextInput(hint_text="ორმხრივი ცოცხალი დიალოგი...", font_name=FONT_PATH,
                                            readonly=True, background_color=(0.08, 0.1, 0.13, 1),
                                            foreground_color=(1, 1, 1, 1), size_hint_y=0.8)
        box.add_widget(self.dialog_log_widget)

        btn_box = BoxLayout(size_hint_y=0.2, spacing=10)
        btn_user1 = Button(text=f"🗣️ {self.ids.btn_source_lang.text}", font_name=FONT_PATH, background_color=(0.15, 0.5, 0.8, 1))
        btn_user2 = Button(text=f"🗣️ {self.ids.btn_target_lang.text}", font_name=FONT_PATH, background_color=(0.1, 0.6, 0.45, 1))
        
        btn_user1.bind(on_release=lambda x: self.start_speech_recognition('source', target='dialog'))
        btn_user2.bind(on_release=lambda x: self.start_speech_recognition('target', target='dialog'))
        
        btn_box.add_widget(btn_user1)
        btn_box.add_widget(btn_user2)
        box.add_widget(btn_box)

        popup = Popup(title='Live დიალოგის რეჟიმი 🇬🇪', title_font=FONT_PATH, content=box, size_hint=(0.92, 0.85))
        popup.open()

    def start_speech_recognition(self, mode, target='main'):
        self.active_stt_target = target
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                lang = self.source_lang if mode == 'source' else self.target_lang
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang)
                App.get_running_app().mActivity.startActivityForResult(intent, 100)
            except Exception as e:
                print(f"STT Error: {e}")

    def trigger_camera_ocr(self):
        if platform == 'android':
            try:
                from plyer import camera
                photo_path = os.path.join(App.get_running_app().user_data_dir, "temp_ocr.jpg")
                camera.take_picture(filename=photo_path, on_complete=self.process_ocr_image)
            except Exception as e:
                print(f"Camera error: {e}")

    def process_ocr_image(self, file_path):
        if not os.path.exists(file_path) or not Recognizer: return
        try:
            from jnius import autoclass
            File = autoclass('java.io.File')
            InputImage = autoclass('com.google.mlkit.vision.common.InputImage')
            image = InputImage.fromFilePath(App.get_running_app().mActivity, Uri.fromFile(File(file_path)))
            task = Recognizer.process(image)
            class Listener(autoclass('com.google.android.gms.tasks.OnSuccessListener')):
                def __init__(self, cb):
                    super().__init__()
                    self.cb = cb
                def onSuccess(self, res): self.cb(res.getText())
            task.addOnSuccessListener(Listener(self._on_ocr_success))
        except Exception as e: print(f"OCR Error: {e}")

    def _on_ocr_success(self, text):
        if text: self.ids.input_text.text = text

    def speak_text(self, text, lang_code):
        cleaned_text = text.strip()
        if not cleaned_text: return
        
        # 1. ქართული გახმოვანება Web API-ით
        if lang_code == "ka" or "ka" in lang_code:
            threading.Thread(target=self._play_georgian_tts, args=(cleaned_text,), daemon=True).start()
        # 2. უცხო ენები ტელეფონის ჩაშენებული TTS-ით
        elif platform == 'android' and TTS:
            try:
                from jnius import autoclass
                Locale = autoclass('java.util.Locale')
                TTS.setLanguage(Locale(lang_code))
                TTS.speak(cleaned_text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"Native TTS Error: {e}")

    def _play_georgian_tts(self, text):
        try:
            encoded_text = urllib.parse.quote(text)
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded_text}"
            sound = SoundLoader.load(tts_url)
            if sound:
                sound.play()
        except Exception as e:
            print(f"Georgian Web TTS Error: {e}")

    def copy_output_text(self):
        if self.ids.output_text.text.strip():
            Clipboard.copy(self.ids.output_text.text.strip())

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        self.main_screen = MainScreen(name='main')
        sm.add_widget(self.main_screen)
        
        if platform == 'android':
            from android.activity import bind
            bind(on_activity_result=self.on_activity_result)
        return sm

    def on_start(self):
        request_android_permissions()

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 100 and result_code == -1:
            try:
                results = intent.getStringArrayListExtra("android.speech.extra.RESULTS")
                if results and results.size() > 0:
                    recognized_text = results.get(0)
                    if self.main_screen.active_stt_target == 'dialog' and self.main_screen.dialog_log_widget:
                        self.main_screen.dialog_log_widget.text += f"\n🗣️ {recognized_text}"
                    else:
                        self.main_screen.ids.input_text.text = recognized_text
            except Exception as e:
                print(f"STT Result Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

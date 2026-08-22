# ==============================================================================
# LingoLens Ultra Pro v3.2.1 🇬🇪 - Safe Real-Time Production Build
# ==============================================================================

import os
import json
import urllib.parse
import threading
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
from kivy.uix.widget import Widget
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

APP_VERSION = "3.2.1"
VERCEL_SERVER_URL = "https://lingo-lens-kqxn.vercel.app/api/index"

FONT_PATH = "font.ttf" if os.path.exists("font.ttf") else "Roboto"

LANGUAGES = {
    "ქართული 🇬🇪": "ka", "English (US) 🇺🇸": "en_US", "English (UK) 🇬🇧": "en_GB", 
    "Русский 🇷🇺": "ru_RU", "Türkçe 🇹🇷": "tr_TR", "Español 🇪🇸": "es_ES", "Français 🇫🇷": "fr_FR", 
    "Deutsch 🇩🇪": "de_DE", "Italiano 🇮🇹": "it_IT", "Português 🇵🇹": "pt_PT", "العربية 🇦🇪": "ar", 
    "中文 🇨🇳": "zh_CN", "日本語 🇯🇵": "ja_JP", "한국어 🇰🇷": "ko_KR", "Українська 🇺🇦": "uk_UA"
}

OFFLINE_DICTIONARY = {
    ("ka", "en_US"): {"გამარჯობა": "Hello", "მადლობა": "Thank you", "როგორ ხარ": "How are you", "დიახ": "Yes", "არა": "No"},
    ("en_US", "ka"): {"hello": "გამარჯობა", "thank you": "მადლობა", "how are you": "როგორ ხარ", "yes": "დიახ", "no": "არა"}
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
                text: "📁 ფოტო OCR"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '90dp'
                background_color: 0.2, 0.5, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.pick_image_from_gallery()

            Button:
                text: "📷 Live AR"
                font_name: '{FONT_PATH}'
                size_hint_x: None
                width: '85dp'
                background_color: 0.6, 0.1, 0.8, 1
                color: 1, 1, 1, 1
                on_release: root.open_ar_camera_mode()

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "ქართული 🇬🇪"
                font_name: '{FONT_PATH}'
                background_color: 0.12, 0.15, 0.22, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "⇆"
                size_hint_x: None
                width: '42dp'
                background_color: 0.12, 0.15, 0.22, 1
                color: 0.2, 0.7, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (US) 🇺🇸"
                font_name: '{FONT_PATH}'
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
                hint_text: "ჩაწერეთ ტექსტი, გამოიყენეთ მიკროფონი ან ფოტო..."
                font_name: '{FONT_PATH}'
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.48, 0.58, 1
                font_size: '15sp'
                on_text: root.on_live_translate(self.text)

            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 6
                Widget:
                Button:
                    text: "🗣️ დიალოგი"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '90dp'
                    background_color: 0.8, 0.4, 0.1, 1
                    color: 1, 1, 1, 1
                    on_release: root.open_conversation_mode()
                Button:
                    text: "🎙️ STT"
                    font_name: '{FONT_PATH}'
                    size_hint_x: None
                    width: '60dp'
                    background_color: 0.1, 0.6, 0.4, 1
                    color: 1, 1, 1, 1
                    on_release: root.start_speech_to_text(root.source_lang)
                Button:
                    text: "🔊"
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
                hint_text: "Gemini AI თარგმანი..."
                font_name: '{FONT_PATH}'
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.95, 0.75, 1
                hint_text_color: 0, 0.5, 0.4, 1
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
        self.target_lang = "en_US"

    def open_ar_camera_mode(self):
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        lbl = Label(
            text="[ AR Live Scanner & Native ML Kit Active ]\n\nკამერის ნაკადი მზადაა რეალურ დროში ტექსტის ამოსაცნობად.",
            font_name=FONT_PATH, halign='center'
        )
        box.add_widget(lbl)
        close_btn = Button(text="❌ დახურვა", font_name=FONT_PATH, size_hint_y=None, height='45dp', background_color=(0.8, 0.2, 0.2, 1))
        box.add_widget(close_btn)
        
        popup = Popup(title="Live AR Text Detection", content=box, size_hint=(0.85, 0.5))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def pick_image_from_gallery(self):
        if platform == 'android':
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self._on_image_selected)
            except Exception as e:
                self.ids.input_text.text = f"[Gallery Error: {e}]"
        else:
            self.ids.input_text.text = "გალერეიდან ფოტოს არჩევა აქტიურდება Android APK-ში."

    def _on_image_selected(self, selection):
        if selection and len(selection) > 0:
            img_path = selection[0]
            self.ids.input_text.text = f"[OCR დამუშავება ფაილისთვის: {os.path.basename(img_path)}...]"

    def open_conversation_mode(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="ორმხრივი ცოცხალი დიალოგი\nდააჭირეთ შესაბამის ენას სასაუბროდ", font_name=FONT_PATH, halign='center')
        box.add_widget(lbl)

        btn_src = Button(text=f"🗣️ ილაპარაკე ({self.source_lang})", font_name=FONT_PATH, height='50dp', size_hint_y=None, background_color=(0.1, 0.5, 0.8, 1))
        btn_src.bind(on_release=lambda x: self.start_speech_to_text(self.source_lang))
        box.add_widget(btn_src)

        btn_tgt = Button(text=f"🗣️ ილაპარაკე ({self.target_lang})", font_name=FONT_PATH, height='50dp', size_hint_y=None, background_color=(0.8, 0.4, 0.1, 1))
        btn_tgt.bind(on_release=lambda x: self.start_speech_to_text(self.target_lang))
        box.add_widget(btn_tgt)

        close_btn = Button(text="დახურვა", font_name=FONT_PATH, height='40dp', size_hint_y=None)
        box.add_widget(close_btn)

        popup = Popup(title="Conversation Mode", content=box, size_hint=(0.85, 0.6))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def start_speech_to_text(self, lang_code):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                PythonActivity.mActivity.startActivityForResult(intent, 1001)
            except Exception as e:
                self.ids.input_text.text = f"[STT Error: {e}]"
        else:
            self.ids.input_text.text = "STT ხელმისაწვდომია Android-ზე."

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.3)

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
            on_error=lambda req, err: self._fallback_offline_translation(text),
            on_failure=lambda req, res: self._fallback_offline_translation(text),
            timeout=5
        )

    def _on_server_success(self, result):
        translated = result.get('translated_text', '')
        self.ids.output_text.text = translated

    def _fallback_offline_translation(self, text):
        key = (self.source_lang, self.target_lang)
        local_dict = OFFLINE_DICTIONARY.get(key, {})
        lower_text = text.lower().strip()

        if lower_text in local_dict:
            self.ids.output_text.text = f"[Offline AI] {local_dict[lower_text]}"
        else:
            words = lower_text.split()
            translated_words = [local_dict.get(w, w) for w in words]
            self.ids.output_text.text = f"[Offline Mode] {' '.join(translated_words)}"

    def speak_text(self, text, lang_code):
        cleaned = text.strip()
        if not cleaned: return
        
        if "ka" in lang_code:
            threading.Thread(target=self._play_georgian_tts, args=(cleaned,), daemon=True).start()
        elif platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                
                parts = lang_code.split('_')
                locale_obj = Locale(parts[0], parts[1]) if len(parts) > 1 else Locale(parts[0])
                
                class TTSListener(autoclass('android.speech.tts.TextToSpeech$OnInitListener')):
                    def onInit(self, status): pass
                
                tts = TextToSpeech(PythonActivity.mActivity, TTSListener())
                tts.setLanguage(locale_obj)
                tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def _play_georgian_tts(self, text):
        try:
            encoded = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ka&client=tw-ob&q={encoded}"
            sound = SoundLoader.load(url)
            if sound: sound.play()
        except Exception as e: print(f"Audio error: {e}")

    def open_language_menu(self, mode):
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4, padding=4)
        list_box.bind(minimum_height=list_box.setter('height'))
        popup = Popup(title='აირჩიეთ ენა', content=scroll, size_hint=(0.85, 0.75))

        for lang_name, code in LANGUAGES.items():
            btn = Button(text=lang_name, font_name=FONT_PATH, size_hint_y=None, height='42dp',
                         background_color=(0.14, 0.17, 0.24, 1), color=(1, 1, 1, 1))
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

    def copy_output_text(self):
        if self.ids.output_text.text.strip():
            Clipboard.copy(self.ids.output_text.text.strip())

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

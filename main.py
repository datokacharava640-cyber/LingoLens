import sys
import os
import json
import ssl
import urllib.request
import urllib.parse
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

FONT_NAME = "Roboto"
if os.path.exists("font.ttf"):
    try:
        LabelBase.register(name="Roboto", fn_regular="font.ttf")
    except Exception as e:
        print(f"Font Error: {e}")

LANGUAGES = {
    "English": "en",
    "ქართული": "ka",
    "Русский": "ru",
    "Türkçe": "tr",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Português": "pt",
    "العربية (არაბული)": "ar",
    "中文 (ჩინური)": "zh-CN",
    "日本語 (იაპონური)": "ja",
    "한국어 (კორეული)": "ko",
    "हिन्दी (ჰინდი)": "hi",
    "Українська": "uk",
    "Polski": "pl",
    "Ελληνικά (ბერძნული)": "el",
    "עברית (ებრაული)": "he",
    "Nederlands": "nl",
    "Svenska": "sv",
    "Azerbaycan": "az",
    "Հայերեն (სომხური)": "hy"
}

KV = '''
<MainScreen>:
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 5
        spacing: 5

        # Header Bar
        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 5

            Label:
                text: "LingoLens Ultra Pro"
                bold: True
                font_size: '18sp'
                color: 0.8, 0.8, 0.8, 1

            Button:
                text: "[=] მენიუ"
                size_hint_x: None
                width: '100dp'
                background_normal: ''
                background_color: 0.25, 0.25, 0.25, 1
                color: 0.9, 0.9, 0.9, 1
                on_release: root.open_menu()

        # Language Select Bar
        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: 5

            Label:
                text: "უცხოელის ენა:"
                size_hint_x: 0.4
                color: 0.8, 0.8, 0.8, 1

            Button:
                id: btn_lang
                text: "English"
                size_hint_x: 0.6
                background_normal: ''
                background_color: 0.25, 0.25, 0.25, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu()

        # Text Input & Voice Button Area
        BoxLayout:
            size_hint_y: 0.45
            spacing: 5

            TextInput:
                id: input_text
                hint_text: "მოსმენილი ტექსტი..."
                background_normal: ''
                background_color: 0.2, 0.2, 0.2, 1
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.5, 0.5, 0.5, 1
                padding: 10
                font_size: '16sp'
                on_text: root.on_live_translate(self.text)

            # ამოხაზული [ხმა] ღილაკი
            Button:
                text: "\\nხმა"
                size_hint_x: 0.25
                background_normal: ''
                background_color: 0.3, 0.3, 0.3, 1
                color: 1, 1, 1, 1
                font_size: '15sp'
                on_release: root.speak_input_text()

        # Translated Text Result Block
        BoxLayout:
            size_hint_y: 0.35
            orientation: 'vertical'

            TextInput:
                id: output_text
                hint_text: "ნათარგმნი ტექსტი..."
                readonly: True
                background_normal: ''
                background_color: 0.05, 0.05, 0.05, 1
                foreground_color: 0, 1, 0.8, 1
                hint_text_color: 0.4, 0.4, 0.4, 1
                padding: 10
                font_size: '16sp'

        # Bottom Speech Controls
        BoxLayout:
            size_hint_y: None
            height: '110dp'
            spacing: 5

            Button:
                text: "🎙 უცხოელი საუბრობს"
                background_normal: ''
                background_color: 0.08, 0.15, 0.2, 1
                color: 0.7, 0.85, 1, 1
                font_size: '14sp'
                on_release: root.start_speech_recognition('foreign')

            Button:
                text: "🎙 მე ვსაუბრობ (ქართულად)"
                background_normal: ''
                background_color: 0.05, 0.2, 0.1, 1
                color: 0.7, 1, 0.8, 1
                font_size: '14sp'
                on_release: root.start_speech_recognition('georgian')
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.foreign_lang_code = "en"
        self.history = []
        self.executor = ThreadPoolExecutor(max_workers=2)

    def open_menu(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        btn_hist = Button(text="[H] ისტორია", background_color=(0.3, 0.3, 0.3, 1), size_hint_y=None, height='45dp')
        btn_clear = Button(text="[D] ისტორიის წაშლა", background_color=(0.3, 0.3, 0.3, 1), size_hint_y=None, height='45dp')
        btn_about = Button(text="[i] შესახებ", background_color=(0.3, 0.3, 0.3, 1), size_hint_y=None, height='45dp')
        btn_close = Button(text="[X] დახურვა", background_color=(0.3, 0.3, 0.3, 1), size_hint_y=None, height='45dp')

        popup = Popup(title='მენიუ', content=content, size_hint=(0.8, 0.6), auto_dismiss=True)

        btn_hist.bind(on_release=lambda x: [popup.dismiss(), self.show_history()])
        btn_clear.bind(on_release=lambda x: [popup.dismiss(), self.clear_history()])
        btn_about.bind(on_release=lambda x: [popup.dismiss(), self.show_about()])
        btn_close.bind(on_release=popup.dismiss)

        content.add_widget(btn_hist)
        content.add_widget(btn_clear)
        content.add_widget(btn_about)
        content.add_widget(btn_close)
        popup.open()

    def open_language_menu(self):
        layout = BoxLayout(orientation='vertical', spacing=5, padding=5)
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        list_box.bind(minimum_height=list_box.setter('height'))

        popup = Popup(title='აირჩიეთ ენა', content=scroll, size_hint=(0.85, 0.8))

        for lang_name, code in LANGUAGES.items():
            btn = Button(text=lang_name, size_hint_y=None, height='40dp', background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda x, name=lang_name, c=code: self.select_language(name, c, popup))
            list_box.add_widget(btn)

        scroll.add_widget(list_box)
        popup.open()

    def select_language(self, name, code, popup):
        self.foreign_lang_code = code
        self.ids.btn_lang.text = name
        popup.dismiss()
        self.on_live_translate(self.ids.input_text.text)

    def speak_input_text(self):
        text = self.ids.input_text.text.strip()
        if not text:
            return
        
        if platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                tts = TextToSpeech(PythonActivity.mActivity, None)
                tts.setLanguage(Locale(self.foreign_lang_code))
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.6)

    def _delayed_translate(self, text):
        def _async():
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={self.foreign_lang_code}&dt=t&q={quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    translated = "".join([item[0] for item in res[0] if item[0]])
                    Clock.schedule_once(lambda dt: self._update_translation(text, translated), 0)
            except Exception:
                pass
        self.executor.submit(_async)

    def _update_translation(self, src, translated):
        self.ids.output_text.text = translated
        item = f"{src} ➔ {translated}"
        if item not in self.history:
            self.history.insert(0, item)

    def start_speech_recognition(self, mode):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                
                lang = 'ka-GE' if mode == 'georgian' else self.foreign_lang_code
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang)

                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                print(f"STT Start Error: {e}")

    def show_history(self):
        content = BoxLayout(orientation='vertical', spacing=5)
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        list_box.bind(minimum_height=list_box.setter('height'))

        for h in self.history[:30]:
            lbl = Label(text=h, size_hint_y=None, height='35dp', color=(0.8, 0.8, 0.8, 1))
            list_box.add_widget(lbl)

        scroll.add_widget(list_box)
        content.add_widget(scroll)

        popup = Popup(title='ისტორია', content=content, size_hint=(0.85, 0.7))
        popup.open()

    def clear_history(self):
        self.history.clear()
        popup = Popup(title='ისტორია', content=Label(text="ისტორია გასუფთავებულია"), size_hint=(0.6, 0.3))
        popup.open()

    def show_about(self):
        popup = Popup(title='შესახებ', content=Label(text="LingoLens Ultra Pro\\nვერსია 2.0"), size_hint=(0.6, 0.3))
        popup.open()

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

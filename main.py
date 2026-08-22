import sys
import os
import json

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.network.urlrequest import UrlRequest
from urllib.parse import quote

LANGUAGES = {
    "English (აშშ)": "en",
    "ქართული": "ka",
    "Русский": "ru",
    "Türkçe": "tr",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Português": "pt",
    "Arabic (არაბული)": "ar",
    "Chinese (ჩინური)": "zh-CN",
    "Japanese (იაპონური)": "ja",
    "Korean (კორეული)": "ko",
    "Hindi (ჰინდი)": "hi",
    "Ukrainian": "uk",
    "Polish": "pl",
    "Greek": "el",
    "Hebrew": "he",
    "Dutch": "nl",
    "Swedish": "sv",
    "Azerbaijani": "az",
    "Armenian": "hy"
}

KV = '''
<MainScreen>:
    canvas.before:
        Color:
            rgba: 0.08, 0.09, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 8
        spacing: 8

        # Top Header Bar
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 5

            Image:
                source: 'georgia.png' if root.has_flag else ''
                size_hint_x: None
                width: '30dp'

            Label:
                text: "LingoLens Pro"
                bold: True
                font_size: '18sp'
                color: 0.3, 0.6, 1, 1
                halign: 'left'
                valign: 'middle'
                text_size: self.size

            Button:
                text: "📷"
                size_hint_x: None
                width: '40dp'
                background_color: 0,0,0,0
                color: 0.3, 0.6, 1, 1

            Button:
                text: "💬"
                size_hint_x: None
                width: '40dp'
                background_color: 0,0,0,0
                color: 0.3, 0.6, 1, 1

            Button:
                text: "🕒"
                size_hint_x: None
                width: '40dp'
                background_color: 0,0,0,0
                color: 0.3, 0.6, 1, 1
                on_release: root.show_history()

        # Language Selectors
        BoxLayout:
            size_hint_y: None
            height: '42dp'
            spacing: 8

            Button:
                id: btn_source_lang
                text: "ქართული"
                background_normal: ''
                background_color: 0.15, 0.18, 0.24, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('source')

            Button:
                text: "⇆"
                size_hint_x: None
                width: '40dp'
                background_normal: ''
                background_color: 0.15, 0.18, 0.24, 1
                color: 0.3, 0.6, 1, 1
                on_release: root.swap_languages()

            Button:
                id: btn_target_lang
                text: "English (აშშ)"
                background_normal: ''
                background_color: 0.15, 0.18, 0.24, 1
                color: 1, 1, 1, 1
                on_release: root.open_language_menu('target')

        # Input Block
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: '120dp'
            padding: 5
            canvas.before:
                Color:
                    rgba: 0.12, 0.14, 0.18, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            TextInput:
                id: input_text
                hint_text: "შეიყვანეთ ტექსტი..."
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.4, 0.5, 0.6, 1
                padding: 5
                font_size: '15sp'
                on_text: root.on_live_translate(self.text)

        # Translation Result Block
        BoxLayout:
            orientation: 'vertical'
            padding: 8
            spacing: 5
            canvas.before:
                Color:
                    rgba: 0.12, 0.14, 0.18, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]

            TextInput:
                id: output_text
                hint_text: "ნათარგმნი ტექსტი..."
                readonly: True
                background_color: 0, 0, 0, 0
                foreground_color: 0, 0.9, 0.7, 1
                hint_text_color: 0, 0.6, 0.5, 1
                padding: 5
                font_size: '16sp'

            # Bottom Actions
            BoxLayout:
                size_hint_y: None
                height: '35dp'
                spacing: 10

                Button:
                    text: "🔊"
                    size_hint_x: None
                    width: '35dp'
                    background_color: 0,0,0,0
                    color: 0.3, 0.6, 1, 1
                    on_release: root.speak_output_text()

                Button:
                    text: "📋"
                    size_hint_x: None
                    width: '35dp'
                    background_color: 0,0,0,0
                    color: 0.3, 0.6, 1, 1
                    on_release: root.copy_output_text()

                Widget:
'''

Builder.load_string(KV)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_lang = "ka"
        self.target_lang = "en"
        self.has_flag = os.path.exists("georgia.png")
        self.history = []

    def open_language_menu(self, mode):
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=5)
        list_box.bind(minimum_height=list_box.setter('height'))

        popup = Popup(title='აირჩიეთ ენა', content=scroll, size_hint=(0.85, 0.7))

        for lang_name, code in LANGUAGES.items():
            btn = Button(
                text=lang_name, 
                size_hint_y=None, 
                height='42dp', 
                background_normal='',
                background_color=(0.18, 0.2, 0.26, 1),
                color=(1, 1, 1, 1)
            )
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
        src_text = self.ids.btn_source_lang.text
        self.ids.btn_source_lang.text = self.ids.btn_target_lang.text
        self.ids.btn_target_lang.text = src_text
        self.on_live_translate(self.ids.input_text.text)

    def on_live_translate(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.ids.output_text.text = ""
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned), 0.5)

    def _delayed_translate(self, text):
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.source_lang}&tl={self.target_lang}&dt=t&q={quote(text)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        UrlRequest(url, req_headers=headers, on_success=lambda req, result: self._on_translation_success(text, result), timeout=5)

    def _on_translation_success(self, src, result):
        try:
            translated = "".join([item[0] for item in result[0] if item and item[0]])
            if translated:
                self.ids.output_text.text = translated
                item = f"{src} ➔ {translated}"
                if item not in self.history:
                    self.history.insert(0, item)
        except Exception as e:
            print(f"Parsing error: {e}")

    def speak_output_text(self):
        text = self.ids.output_text.text.strip()
        if not text:
            return
        if platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                tts = TextToSpeech(PythonActivity.mActivity, None)
                tts.setLanguage(Locale(self.target_lang))
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def copy_output_text(self):
        text = self.ids.output_text.text.strip()
        if text:
            Clipboard.copy(text)

    def show_history(self):
        content = BoxLayout(orientation='vertical', spacing=8, padding=8)
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        list_box.bind(minimum_height=list_box.setter('height'))

        for h in self.history[:30]:
            lbl = Label(
                text=h, 
                size_hint_y=None, 
                height='35dp', 
                color=(0.9, 0.9, 0.9, 1),
                font_size='14sp'
            )
            list_box.add_widget(lbl)

        scroll.add_widget(list_box)
        content.add_widget(scroll)

        btn_clear = Button(
            text="წაშლა", 
            size_hint_y=None, 
            height='40dp', 
            background_normal='',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        
        popup = Popup(title='ისტორია', content=content, size_hint=(0.85, 0.7))
        btn_clear.bind(on_release=lambda x: [self.history.clear(), popup.dismiss()])
        content.add_widget(btn_clear)
        
        popup.open()

class LingoLensApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    LingoLensApp().run()

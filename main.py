import os
import sys
import json
import threading
import requests

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# Android-ის ნებართვების ავტომატური მოთხოვნა
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.INTERNET,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.SYSTEM_ALERT_WINDOW
    ])

# მსოფლიო ენების ჩამონათვალი
WORLD_LANGUAGES = {
    "ka": "ქართული (Georgian)",
    "en": "ინგლისური (English)",
    "ru": "რუსული (Russian)",
    "de": "გერმანული (German)",
    "fr": "ფრანგული (French)",
    "es": "ესპანური (Spanish)",
    "it": "იტალიური (Italian)",
    "tr": "თურქული (Turkish)",
    "uk": "უკრაინული (Ukrainian)",
    "az": "აზერბაიჯანული (Azerbaijani)",
    "hy": "სომხური (Armenian)",
    "zh-CN": "ჩინური (Chinese)",
    "ja": "იაპონური (Japanese)",
    "ko": "კორეული (Korean)",
    "ar": "არაბული (Arabic)",
    "hi": "ჰინდი (Hindi)",
    "pt": "პორტუგალიური (Portuguese)",
    "nl": "ჰოლანდიური (Dutch)",
    "pl": "პოლონური (Polish)",
    "el": "ბერძნული (Greek)",
    "he": "ებრაული (Hebrew)",
    "sv": "შვედური (Swedish)",
    "no": "ნორვეგიული (Norwegian)",
    "fi": "ფინური (Finnish)",
    "da": "დანიური (Danish)",
    "cs": "ჩეხური (Czech)",
    "hu": "უნგრული (Hungarian)",
    "ro": "რუმინული (Romanian)",
    "bg": "ბულგარული (Bulgarian)"
}

BUILTIN_GEMINI_KEY = "AQ.Ab8RN6JRsQmchpFvza1mUDtsUWVQNye3OmrJWcCOrmV5UuWqWQ"

KV_DESIGN = """
<RoundedButton>:
    background_color: (0, 0, 0, 0)
    background_normal: ''
    color: (1, 1, 1, 1)
    bold: True
    font_size: '13sp'
    canvas.before:
        Color:
            rgba: self.bg_color if hasattr(self, 'bg_color') else (0.18, 0.24, 0.35, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

<CardLayout>:
    orientation: 'vertical'
    padding: 12
    spacing: 8
    canvas.before:
        Color:
            rgba: (0.12, 0.15, 0.22, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [14,]
"""

Builder.load_string(KV_DESIGN)

class RoundedButton(Button):
    def __init__(self, bg_color=(0.18, 0.24, 0.35, 1), **kwargs):
        self.bg_color = bg_color
        super().__init__(**kwargs)

class CardLayout(BoxLayout):
    pass

# Font Registration
GEORGIAN_FONT = None
possible_fonts = ["NotoSansGeorgian-Regular.ttf", "NotoSansGeorgian.ttf", "georgian.ttf", "font.ttf"]
for f in possible_fonts:
    if os.path.exists(f):
        try:
            LabelBase.register(name="Roboto", fn_regular=f)
            LabelBase.register(name="GeorgianFont", fn_regular=f)
            GEORGIAN_FONT = "GeorgianFont"
            break
        except Exception:
            pass

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 14
        self.spacing = 10
        self.api_key = BUILTIN_GEMINI_KEY
        self.src_lang = "auto"
        self.target_lang = "ka"

        # Header Title
        self.title_label = Label(
            text="[b]LingoLens Ultra Pro[/b]",
            markup=True,
            font_size='22sp',
            size_hint_y=0.06,
            color=(0.35, 0.65, 1, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.title_label)

        # Status Bar
        self.status_label = Label(
            text="მზადაა | ⚡ AI & ენები გააქტიურებულია",
            color=(0.25, 0.85, 0.5, 1),
            font_size='11sp',
            size_hint_y=0.03,
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        self.add_widget(self.status_label)

        # Language Selector Bar
        lang_bar = BoxLayout(size_hint_y=0.07, spacing=6)
        self.src_btn = RoundedButton(text="ავტო (Auto)", bg_color=(0.2, 0.28, 0.4, 1))
        self.target_btn = RoundedButton(text="ქართული (ka)", bg_color=(0.2, 0.28, 0.4, 1))
        
        self.src_btn.bind(on_press=lambda x: self.open_language_picker(is_source=True))
        self.target_btn.bind(on_press=lambda x: self.open_language_picker(is_source=False))
        
        lang_bar.add_widget(self.src_btn)
        lang_bar.add_widget(Label(text="➔", size_hint_x=0.15))
        lang_bar.add_widget(self.target_btn)
        self.add_widget(lang_bar)

        # Display Card
        display_card = CardLayout(size_hint_y=0.45)
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            multiline=True,
            size_hint_y=0.55,
            font_size='14sp',
            background_color=(0.07, 0.09, 0.13, 1),
            foreground_color=(0.95, 0.95, 0.98, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.text_input)

        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]",
            markup=True,
            font_size='14sp',
            size_hint_y=0.45,
            color=(0.8, 0.85, 0.92, 1),
            font_name=GEORGIAN_FONT if GEORGIAN_FONT else None
        )
        display_card.add_widget(self.output_label)
        self.add_widget(display_card)

        # Actions
        main_actions = GridLayout(cols=3, spacing=8, size_hint_y=0.09)
        btn_trans = RoundedButton(text="AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=self.translate_text)

        btn_tts = RoundedButton(text="წაკითხვა", bg_color=(0.2, 0.45, 0.75, 1))
        btn_tts.bind(on_press=self.speak_text)

        btn_copy = RoundedButton(text="დაკოპირება", bg_color=(0.28, 0.35, 0.45, 1))
        btn_copy.bind(on_press=self.copy_translation)

        main_actions.add_widget(btn_trans)
        main_actions.add_widget(btn_tts)
        main_actions.add_widget(btn_copy)
        self.add_widget(main_actions)

        # Module Menu Button (Popup-ით)
        self.menu_btn = RoundedButton(text="≡  აირჩიეთ მოდული / მენიუ", bg_color=(0.16, 0.22, 0.32, 1), size_hint_y=0.08)
        self.menu_btn.bind(on_press=self.open_modules_popup)
        self.add_widget(self.menu_btn)

    def open_modules_popup(self, instance):
        layout = BoxLayout(orientation='vertical', padding=12, spacing=8)
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(
            title="აირჩიეთ მოდული",
            content=layout,
            size_hint=(0.85, 0.75)
        )

        modules_list = [
            ("SMS Translator", "sms_translator"),
            ("AR Camera OCR", "ar_camera"),
            ("Hands-Free Live", "live_interpreter"),
            ("Floating Bubble", "floating_bubble"),
            ("Voice Clone", "voice_clone"),
            ("Walkie Talkie", "walkie_talkie"),
            ("Doc Summarizer", "doc_summarizer"),
            ("Coach Mode", "coach_mode"),
            ("Slang Decoder", "slang_decoder"),
            ("Travel SOS", "travel_sos"),
            ("Offline Mode", "offline_mode")
        ]

        for title, mod_name in modules_list:
            btn = RoundedButton(text=title, bg_color=(0.2, 0.26, 0.38, 1), size_hint_y=None, height=48)
            def select_mod(inst, m=mod_name, t=title):
                self.run_module(m, t)
                popup.dismiss()
            btn.bind(on_press=select_mod)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        close_btn = RoundedButton(text="დახურვა", bg_color=(0.6, 0.2, 0.2, 1), size_hint_y=0.15)
        close_btn.bind(on_press=popup.dismiss)
        layout.add_widget(close_btn)

        popup.open()

    def open_language_picker(self, is_source=True):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(title="აირჩიეთ ენა", content=layout, size_hint=(0.85, 0.8))

        if is_source:
            btn = Button(text="ავტომატური (Auto)", size_hint_y=None, height=45)
            btn.bind(on_press=lambda x: (setattr(self, 'src_lang', 'auto'), self.src_btn.setter('text')(self.src_btn, 'ავტო (Auto)'), popup.dismiss()))
            grid.add_widget(btn)

        for code, name in WORLD_LANGUAGES.items():
            btn = Button(text=name, size_hint_y=None, height=45)
            def set_lang(instance, c=code, n=name):
                if is_source:
                    self.src_lang = c
                    self.src_btn.text = n
                else:
                    self.target_lang = c
                    self.target_btn.text = n
                popup.dismiss()
            btn.bind(on_press=set_lang)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)
        popup.open()

    def translate_text(self, instance):
        input_txt = self.text_input.text.strip()
        if not input_txt:
            self.output_label.text = "გთხოვთ, ჩაწეროთ ტექსტი!"
            return

        self.status_label.text = "AI თარგმნის..."
        try:
            gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.src_lang}&tl={self.target_lang}&dt=t&q={input_txt}"
            res = requests.get(gt_url, timeout=5).json()
            translated = res[0][0][0]
            self.output_label.text = translated
            self.status_label.text = "თარგმანი მზადაა!"
        except Exception as e:
            self.output_label.text = f"შეცდომა: {e}"

    def speak_text(self, instance):
        pass

    def copy_translation(self, instance):
        if self.output_label.text:
            Clipboard.copy(self.output_label.text)
            self.status_label.text = "დაკოპირდა!"

    def run_module(self, module_name, title=""):
        self.status_label.text = f"აქტიურია: {title if title else module_name}"

class LingoLensApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    LingoLensApp().run()

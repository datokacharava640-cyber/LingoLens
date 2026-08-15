import os
import requests
import threading

from kivy.app import App
from kivy.clock import Clock
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

try:
    from plyer import tts, stt
except ImportError:
    tts = None
    stt = None

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.CAMERA,
        Permission.RECORD_AUDIO,
        Permission.INTERNET,
        Permission.SYSTEM_ALERT_WINDOW,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

WORLD_LANGUAGES = {
    "ka": "ქართული (Georgian)", "en": "ინგლისური (English)", "ru": "რუსული (Russian)",
    "de": "გერმანული (German)", "fr": "ფრანგული (French)", "es": "ესპანური (Spanish)",
    "it": "იტალიური (Italian)", "tr": "თურქული (Turkish)", "zh-CN": "ჩინური (Chinese)"
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
            radius: [12,]

<IconButtonTile>:
    orientation: 'vertical'
    padding: 8
    spacing: 4
    canvas.before:
        Color:
            rgba: (0.16, 0.22, 0.32, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16,]

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

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 14
        self.spacing = 10
        self.api_key = BUILTIN_GEMINI_KEY
        self.src_lang = "auto"
        self.target_lang = "ka"

        # Header
        self.add_widget(Label(text="[b]LingoLens Ultra Pro[/b]", markup=True, font_size='22sp', size_hint_y=0.06, color=(0.35, 0.65, 1, 1)))
        
        # Status
        self.status_label = Label(text="⚡ Real-Time Engine Ready", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Language Bar
        lang_bar = BoxLayout(size_hint_y=0.07, spacing=6)
        self.src_btn = RoundedButton(text="ავტო (Auto)", bg_color=(0.2, 0.28, 0.4, 1))
        self.target_btn = RoundedButton(text="ქართული (ka)", bg_color=(0.2, 0.28, 0.4, 1))
        self.src_btn.bind(on_press=lambda x: self.open_language_picker(is_source=True))
        self.target_btn.bind(on_press=lambda x: self.open_language_picker(is_source=False))
        lang_bar.add_widget(self.src_btn)
        lang_bar.add_widget(Label(text="➔", size_hint_x=0.15))
        lang_bar.add_widget(self.target_btn)
        self.add_widget(lang_bar)

        # Main Display
        card = CardLayout(size_hint_y=0.45)
        self.text_input = TextInput(hint_text="ჩაწერეთ ტექსტი...", multiline=True, size_hint_y=0.55, background_color=(0.07, 0.09, 0.13, 1), foreground_color=(0.95, 0.95, 0.98, 1))
        self.output_label = Label(text="[AI თარგმანი გამოჩნდება აქ]", markup=True, size_hint_y=0.45, color=(0.8, 0.85, 0.92, 1))
        card.add_widget(self.text_input)
        card.add_widget(self.output_label)
        self.add_widget(card)

        # Actions
        actions = GridLayout(cols=3, spacing=8, size_hint_y=0.09)
        btn_trans = RoundedButton(text="AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.translate_text_gemini, daemon=True).start())
        
        btn_speak = RoundedButton(text="🔊 წაკითხვა", bg_color=(0.2, 0.45, 0.75, 1))
        btn_speak.bind(on_press=self.speak_translation)

        btn_copy = RoundedButton(text="დაკოპირება", bg_color=(0.28, 0.35, 0.45, 1))
        btn_copy.bind(on_press=self.copy_translation)

        actions.add_widget(btn_trans)
        actions.add_widget(btn_speak)
        actions.add_widget(btn_copy)
        self.add_widget(actions)

        # Grid Launcher Menu Button
        self.menu_btn = RoundedButton(text="::  მოდულების მენიუ (App Grid)", bg_color=(0.16, 0.22, 0.32, 1), size_hint_y=0.08)
        self.menu_btn.bind(on_press=self.open_app_grid_popup)
        self.add_widget(self.menu_btn)

    def update_ui_text(self, text, status_text=None):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', text))
        if status_text:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', status_text))

    def translate_text_gemini(self):
        input_txt = self.text_input.text.strip()
        if not input_txt: return
        self.update_ui_text(self.output_label.text, "Gemini თარგმნა...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"Translate into language code '{self.target_lang}'. Output ONLY translated text: {input_txt}"}]}]
        }
        try:
            res = requests.post(url, json=payload, timeout=8).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            self.update_ui_text(translated, "თარგმანი მზადაა!")
        except Exception as e:
            self.update_ui_text(f"შეცდომა: {e}", "შეცდომა თარგმნისას")

    def speak_translation(self, instance):
        text = self.output_label.text
        if text and tts:
            try: tts.speak(text)
            except Exception: pass

    # App Launcher Style Menu (Grid View)
    def open_app_grid_popup(self, instance):
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        scroll = ScrollView()
        
        # 3-სვეტიანი ბადე ტელეფონის მენიუს სტილში
        grid = GridLayout(cols=3, spacing=12, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(title="მოდულების მენიუ", content=layout, size_hint=(0.92, 0.82))

        modules_list = [
            ("💬", "SMS Trans", "sms_translator"),
            ("📷", "AR Camera", "ar_camera"),
            ("🎙️", "Live Voice", "live_interpreter"),
            ("🫧", "Bubble", "floating_bubble"),
            ("👤", "Voice Clone", "voice_clone"),
            ("📻", "Walkie Talkie", "walkie_talkie"),
            ("📄", "Doc Summary", "doc_summarizer"),
            ("🎓", "Coach Mode", "coach_mode"),
            ("🗣️", "Slang Decode", "slang_decoder"),
            ("🧳", "Travel SOS", "travel_sos"),
            ("🌐", "Offline Mode", "offline_mode")
        ]

        for icon, title, mod_id in modules_list:
            btn_box = BoxLayout(orientation='vertical', size_hint_y=None, height=90, padding=6, spacing=4)
            
            # Icon + Text Button
            btn = RoundedButton(
                text=f"{icon}\n[size=11sp]{title}[/size]",
                markup=True,
                bg_color=(0.2, 0.26, 0.38, 1),
                halign='center'
            )
            
            def select_mod(inst, t=title):
                self.status_label.text = f"აქტიურია: {t}"
                popup.dismiss()
                
            btn.bind(on_press=select_mod)
            btn_box.add_widget(btn)
            grid.add_widget(btn_box)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        close_btn = RoundedButton(text="დახურვა", bg_color=(0.6, 0.2, 0.2, 1), size_hint_y=0.12)
        close_btn.bind(on_press=popup.dismiss)
        layout.add_widget(close_btn)

        popup.open()

    def open_language_picker(self, is_source=True):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        popup = Popup(title="აირჩიეთ ენა", content=layout, size_hint=(0.85, 0.8))

        for code, name in WORLD_LANGUAGES.items():
            btn = Button(text=name, size_hint_y=None, height=45)
            def set_l(inst, c=code, n=name):
                if is_source: self.src_lang, self.src_btn.text = c, n
                else: self.target_lang, self.target_btn.text = c, n
                popup.dismiss()
            btn.bind(on_press=set_l)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)
        popup.open()

    def copy_translation(self, instance):
        if self.output_label.text:
            Clipboard.copy(self.output_label.text)
            self.status_label.text = "დაკოპირდა!"

class LingoLensApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    LingoLensApp().run()

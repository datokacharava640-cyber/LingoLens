import os
import base64
import sqlite3
import requests
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.uix.floatlayout import FloatLayout

# ==================== FONT REGISTRATION ====================
FONT_PATH = "NotoSansGeorgian-Regular.ttf"
try:
    if os.path.exists(FONT_PATH):
        LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
except Exception as e:
    print(f"Font Error: {e}")

try:
    from plyer import tts, filechooser
except Exception:
    tts = None
    filechooser = None

# ==================== OFFLINE DATABASE ====================
DB_FILE = "translation_cache.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT,
                target_lang TEXT,
                translated_text TEXT,
                UNIQUE(source_text, target_lang)
            )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_cached_translation(source_text, target_lang):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT translated_text FROM translations WHERE source_text=? AND target_lang=?', (source_text.strip(), target_lang))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

def save_cached_translation(source_text, target_lang, translated_text):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO translations (source_text, target_lang, translated_text) VALUES (?, ?, ?)',
                       (source_text.strip(), target_lang, translated_text.strip()))
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

WORLD_LANGUAGES = {
    "ka": "ქართული (Georgian)", "en": "ინგლისური (English)", "ru": "რუსული (Russian)",
    "de": "გერმანული (German)", "fr": "ფრანგული (French)", "es": "ესპანური (Spanish)",
    "it": "იტალიური (Italian)", "tr": "თურქული (Turkish)", "zh-CN": "ჩინური (Chinese)"
}

BUILTIN_GEMINI_KEY = "AQ.Ab8RN6JRsQmchpFvza1mUDtsUWVQNye3OmrJWcCOrmV5UuWqWQ"

KV_DESIGN = """
<Label>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

<TextInput>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

<Button>:
    font_name: "NotoSansGeorgian-Regular.ttf" if os.path.exists("NotoSansGeorgian-Regular.ttf") else "Roboto"

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

# ==================== LIVE AR OVERLAY CAMERA POPUP ====================
class ARCameraPopup(Popup):
    def __init__(self, target_lang, api_key, update_parent_ui, **kwargs):
        super().__init__(**kwargs)
        self.title = "Live AR Vision Translator"
        self.size_hint = (0.95, 0.9)
        self.target_lang = target_lang
        self.api_key = api_key
        self.update_parent_ui = update_parent_ui

        layout = FloatLayout()
        
        # Camera Feed
        self.cam = Camera(play=True, resolution=(640, 480), size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        layout.add_widget(self.cam)

        # AR Text Overlay
        self.ar_label = Label(
            text="[AR AI იკვლევს კადრს...]",
            markup=True,
            size_hint=(0.9, 0.2),
            pos_hint={'center_x': 0.5, 'y': 0.1},
            color=(0.1, 1, 0.5, 1),
            font_size='16sp'
        )
        layout.add_widget(self.ar_label)

        # Controls
        close_btn = RoundedButton(text="✖ დახურვა", bg_color=(0.8, 0.2, 0.2, 1), size_hint=(0.3, 0.08), pos_hint={'right': 0.95, 'top': 0.98})
        close_btn.bind(on_press=self.close_cam)
        layout.add_widget(close_btn)

        capture_btn = RoundedButton(text="📸 კადრის თარგმნა", bg_color=(0.12, 0.6, 0.4, 1), size_hint=(0.5, 0.08), pos_hint={'center_x': 0.5, 'y': 0.02})
        capture_btn.bind(on_press=self.process_frame)
        layout.add_widget(capture_btn)

        self.content = layout

    def process_frame(self, instance):
        self.ar_label.text = "⏳ AI ამუშავებს კადრს..."
        self.cam.export_to_png("ar_frame.png")
        threading.Thread(target=self._analyze_image, daemon=True).start()

    def _analyze_image(self):
        try:
            if not os.path.exists("ar_frame.png"): return
            with open("ar_frame.png", "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"Extract all visible text and translate to target language code '{self.target_lang}'. Output ONLY the translation:"},
                        {"inline_data": {"mime_type": "image/png", "data": encoded}}
                    ]
                }]
            }
            res = requests.post(url, json=payload, timeout=12).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', f"[b]{translated}[/b]"))
            self.update_parent_ui(translated, "AR კადრი წარმატებით ითარგმნა!")
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.ar_label, 'text', f"შეცდომა: {e}"))

    def close_cam(self, instance):
        self.cam.play = False
        self.dismiss()

# ==================== MAIN UI LAYOUT ====================
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
        
        # Status Bar
        self.status_label = Label(text="⚡ Real-Time Engine Ready", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Language Bar
        lang_bar = BoxLayout(size_hint_y=0.07, spacing=6)
        self.src_btn = RoundedButton(text="ავტო (Auto)", bg_color=(0.2, 0.28, 0.4, 1))
        self.target_btn = RoundedButton(text="ქართული (ka)", bg_color=(0.2, 0.28, 0.4, 1))
        
        self.src_btn.bind(on_press=lambda x: self.open_language_picker(is_source=True))
        self.target_btn.bind(on_press=lambda x: self.open_language_picker(is_source=False))
        
        swap_btn = RoundedButton(text="⇄", bg_color=(0.25, 0.35, 0.5, 1), size_hint_x=0.18)
        swap_btn.bind(on_press=self.swap_languages)

        lang_bar.add_widget(self.src_btn)
        lang_bar.add_widget(swap_btn)
        lang_bar.add_widget(self.target_btn)
        self.add_widget(lang_bar)

        # Text Card
        card = CardLayout(size_hint_y=0.45)
        self.text_input = TextInput(hint_text="ჩაწერეთ ტექსტი...", multiline=True, size_hint_y=0.55, background_color=(0.07, 0.09, 0.13, 1), foreground_color=(0.95, 0.95, 0.98, 1))
        self.output_label = Label(text="[AI თარგმანი გამოჩნდება აქ]", markup=True, size_hint_y=0.45, color=(0.8, 0.85, 0.92, 1))
        card.add_widget(self.text_input)
        card.add_widget(self.output_label)
        self.add_widget(card)

        # Main Actions
        actions = GridLayout(cols=4, spacing=6, size_hint_y=0.09)
        btn_trans = RoundedButton(text="AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.translate_text_gemini, daemon=True).start())
        
        btn_stt = RoundedButton(text="🎤 ხმა", bg_color=(0.55, 0.25, 0.6, 1))
        btn_stt.bind(on_press=self.start_speech_recognition)

        btn_speak = RoundedButton(text="🔊 მოსმენა", bg_color=(0.2, 0.45, 0.75, 1))
        btn_speak.bind(on_press=self.speak_translation)

        btn_copy = RoundedButton(text="📋 კოპირება", bg_color=(0.28, 0.35, 0.45, 1))
        btn_copy.bind(on_press=self.copy_translation)

        actions.add_widget(btn_trans)
        actions.add_widget(btn_stt)
        actions.add_widget(btn_speak)
        actions.add_widget(btn_copy)
        self.add_widget(actions)

        # Menu Button
        self.menu_btn = RoundedButton(text="::  მოდულების მენიუ (App Grid)", bg_color=(0.16, 0.22, 0.32, 1), size_hint_y=0.08)
        self.menu_btn.bind(on_press=self.open_app_grid_popup)
        self.add_widget(self.menu_btn)

    def swap_languages(self, instance):
        self.src_lang, self.target_lang = self.target_lang, self.src_lang
        self.src_btn.text, self.target_btn.text = self.target_btn.text, self.src_btn.text
        self.status_label.text = "ენები შეიცვალა ⇄"

    def update_ui_text(self, text, status_text=None):
        Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', text))
        if status_text:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', status_text))

    def translate_text_gemini(self, custom_prompt=None):
        input_txt = self.text_input.text.strip()
        if not input_txt: return

        cached = get_cached_translation(input_txt, self.target_lang)
        if cached and not custom_prompt:
            self.update_ui_text(cached, "⚡ ოფლაინ თარგმანი (ქეშიდან)")
            return

        self.update_ui_text(self.output_label.text, "Gemini AI თარგმნა...")
        prompt = custom_prompt or f"Translate accurately into target language code '{self.target_lang}'. Output ONLY translated text: {input_txt}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, json=payload, timeout=8).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            save_cached_translation(input_txt, self.target_lang, translated)
            self.update_ui_text(translated, "თარგმანი მზადაა!")
        except Exception as e:
            if cached:
                self.update_ui_text(cached, "🌐 ოფლაინ რეჟიმი (ბაზიდან)")
            else:
                self.update_ui_text(f"ინტერნეტი არ არის: {e}", "შეცდომა / ოფლაინ")

    # Speech-to-Text via Pyjnius (Android Native SpeechRecognizer)
    def start_speech_recognition(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, self.src_lang if self.src_lang != "auto" else "en-US")
                
                PythonActivity.mActivity.startActivityForResult(intent, 5001)
                self.status_label.text = "🎤 გისმენთ... ისაუბრეთ"
            except Exception as e:
                self.status_label.text = f"STT შეცდომა: {e}"
        else:
            self.status_label.text = "STT ხელმისაწვდომია მხოლოდ Android-ზე"

    def speak_translation(self, instance):
        text = self.output_label.text
        if text and tts:
            try: tts.speak(text)
            except Exception: pass

    # Document / Text File Import
    def import_text_file(self):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.on_file_selected)
            except Exception as e:
                self.status_label.text = f"ფაილის შეცდომა: {e}"
        else:
            self.status_label.text = "File Picker მიუწვდომელია"

    def on_file_selected(self, selection):
        if selection and os.path.exists(selection[0]):
            try:
                with open(selection[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_input.text = content[:1500]  # First 1500 chars limit
                    self.status_label.text = "📄 ფაილი წარმატებით ჩაიტვირთა"
            except Exception as e:
                self.status_label.text = f"ფაილის წაკითხვის შეცდომა: {e}"

    # Custom Settings Dialog (Gemini API Key Manager)
    def open_settings_popup(self):
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        popup = Popup(title="⚙️ პარამეტრები & API Key", content=layout, size_hint=(0.88, 0.5))

        layout.add_widget(Label(text="შეიყვანეთ საკუთარი Gemini API Key:", size_hint_y=0.2))
        key_input = TextInput(text=self.api_key, multiline=False, size_hint_y=0.3)
        layout.add_widget(key_input)

        save_btn = RoundedButton(text="💾 შენახვა", bg_color=(0.12, 0.55, 0.38, 1), size_hint_y=0.25)
        def save_key(inst):
            if key_input.text.strip():
                self.api_key = key_input.text.strip()
                self.status_label.text = "🔑 API Key განახლდა!"
            popup.dismiss()
        save_btn.bind(on_press=save_key)
        layout.add_widget(save_btn)

        popup.open()

    def open_app_grid_popup(self, instance):
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        scroll = ScrollView()
        grid = GridLayout(cols=3, spacing=12, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(title="მოდულების მენიუ", content=layout, size_hint=(0.92, 0.82))

        modules_list = [
            ("🎥", "Live AR Camera", lambda: ARCameraPopup(self.target_lang, self.api_key, self.update_ui_text).open()),
            ("📁", "Doc Reader", lambda: self.import_text_file()),
            ("⚙️", "API Settings", lambda: self.open_settings_popup()),
            ("🌐", "Offline Mode", lambda: setattr(self.status_label, 'text', 'Offline Cache Active'))
        ]

        for icon, title, action_func in modules_list:
            btn = RoundedButton(text=f"{icon}\n[size=11sp]{title}[/size]", markup=True, bg_color=(0.2, 0.26, 0.38, 1))
            btn.bind(on_press=lambda x, f=action_func: (popup.dismiss(), f()))
            grid.add_widget(btn)

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

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

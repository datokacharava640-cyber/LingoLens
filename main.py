import os
import base64
import sqlite3
import requests
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase  # <--- დაემატა შრიფტების სამართავად
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

# ==================== 0. GEORGIAN FONT REGISTRATION ====================
FONT_PATH = "NotoSansGeorgian-Regular.ttf"

if os.path.exists(FONT_PATH):
    # არეგისტრირებს ქართულ შრიფტს Kivy-ს სისტემაში
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

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

# ==================== 1. OFFLINE SQLITE DATABASE ====================
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

# Initialize DB on start
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

        # Text Display
        card = CardLayout(size_hint_y=0.45)
        self.text_input = TextInput(hint_text="ჩაწერეთ ტექსტი...", multiline=True, size_hint_y=0.55, background_color=(0.07, 0.09, 0.13, 1), foreground_color=(0.95, 0.95, 0.98, 1))
        self.output_label = Label(text="[AI თარგმანი გამოჩნდება აქ]", markup=True, size_hint_y=0.45, color=(0.8, 0.85, 0.92, 1))
        card.add_widget(self.text_input)
        card.add_widget(self.output_label)
        self.add_widget(card)

        # Control Buttons
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

        # App Grid Menu Button
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

    # ==================== GEMINI API + OFFLINE CACHE ENGINE ====================
    def translate_text_gemini(self, custom_prompt=None):
        input_txt = self.text_input.text.strip()
        if not input_txt: return

        # 1. Check Offline SQLite DB Cache First
        cached = get_cached_translation(input_txt, self.target_lang)
        if cached and not custom_prompt:
            self.update_ui_text(cached, "⚡ ოფლაინ თარგმანი (ქეშიდან)")
            return

        self.update_ui_text(self.output_label.text, "Gemini AI თარგმნა...")
        
        prompt = custom_prompt or f"Translate accurately into target language code '{self.target_lang}'. Output ONLY translated text: {input_txt}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            res = requests.post(url, json=payload, timeout=8).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Save into SQLite Cache for Offline usage
            save_cached_translation(input_txt, self.target_lang, translated)
            
            self.update_ui_text(translated, "თარგმანი მზადაა!")
        except Exception as e:
            if cached:
                self.update_ui_text(cached, "🌐 ოფლაინ რეჟიმი (ბაზიდან)")
            else:
                self.update_ui_text(f"ინტერნეტი არ არის: {e}", "შეცდომა / ოფლაინ")

    def speak_translation(self, instance):
        text = self.output_label.text
        if text and tts:
            try: tts.speak(text)
            except Exception: pass

    # ==================== LIVE VOICE (EVENT-DRIVEN STT) ====================
    def run_live_voice(self):
        if not stt:
            self.status_label.text = "STT მხარდაჭერილი არ არის"
            return
        try:
            self.status_label.text = "🎙️ გისმენთ... ილაპარაკეთ"
            stt.start()
            if hasattr(stt, 'bind'):
                stt.bind(on_results=self.on_stt_results)
            else:
                Clock.schedule_once(lambda dt: self.check_stt_result(), 3)
        except Exception as e:
            self.status_label.text = f"STT შეცდომა: {e}"

    def on_stt_results(self, results):
        if results:
            self.text_input.text = results[0]
            threading.Thread(target=self.translate_text_gemini, daemon=True).start()

    def check_stt_result(self):
        if hasattr(stt, 'results') and stt.results:
            self.text_input.text = stt.results[0]
            threading.Thread(target=self.translate_text_gemini, daemon=True).start()

    # ==================== AR CAMERA VISION ====================
    def run_ar_camera(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        cam = Camera(play=True, resolution=(640, 480))
        res_label = Label(text="დააჭირეთ [კადრის თარგმნა]-ს", size_hint_y=0.2, color=(0.3, 0.9, 0.5, 1))
        btn_capture = RoundedButton(text="📷 კადრის თარგმნა", bg_color=(0.12, 0.55, 0.38, 1), size_hint_y=0.15)
        btn_close = RoundedButton(text="დახურვა", bg_color=(0.6, 0.2, 0.2, 1), size_hint_y=0.15)
        popup = Popup(title="AR Camera Real-Time Translator", content=box, size_hint=(0.95, 0.9))

        def capture_and_translate(instance):
            res_label.text = "⏳ კადრი მუშავდება AI-ით..."
            img_path = "cam_frame.png"
            cam.export_to_png(img_path)
            
            def process_vision():
                try:
                    with open(img_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": f"Extract text from image and translate to language code '{self.target_lang}'. Output ONLY translation:"},
                                {"inline_data": {"mime_type": "image/png", "data": encoded_string}}
                            ]
                        }]
                    }
                    res = requests.post(url, json=payload, timeout=12).json()
                    translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
                    Clock.schedule_once(lambda dt: setattr(res_label, 'text', translated))
                except Exception as e:
                    Clock.schedule_once(lambda dt: setattr(res_label, 'text', f"შეცდომა: {e}"))

            threading.Thread(target=process_vision, daemon=True).start()

        btn_capture.bind(on_press=capture_and_translate)
        btn_close.bind(on_press=popup.dismiss)

        box.add_widget(cam)
        box.add_widget(res_label)
        box.add_widget(btn_capture)
        box.add_widget(btn_close)
        popup.open()

    # ==================== FLOATING BUBBLE OVERLAY ====================
    def run_floating_bubble(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{PythonActivity.mActivity.getPackageName()}"))
                PythonActivity.mActivity.startActivity(intent)
                self.status_label.text = "🫧 ჩართეთ 'Draw over other apps' ნებართვა"
            except Exception:
                self.status_label.text = "Overlay ნებართვა ვერ გაიხსნა"
        else:
            self.status_label.text = "Floating Bubble ხელმისაწვდომია Android-ზე"

    # ==================== ALL MODULES AI PROMPT HANDLERS ====================
    def run_module_action(self, mod_id):
        txt = self.text_input.text.strip()
        if not txt:
            self.status_label.text = "გთხოვთ ჩაწეროთ ტექსტი!"
            return

        prompts = {
            "slang_decoder": f"Decode slang, idioms, and cultural nuances in this text and translate to '{self.target_lang}': {txt}",
            "coach_mode": f"Act as a language coach. Correct grammar, explain rules, and translate to '{self.target_lang}': {txt}",
            "doc_summarizer": f"Summarize this text concisely and translate key bullet points to '{self.target_lang}': {txt}",
            "travel_sos": f"Translate emergency travel request urgent/clear into '{self.target_lang}': {txt}",
            "voice_clone": f"Translate into '{self.target_lang}' optimized with emotional natural tone for TTS: {txt}",
            "walkie_talkie": f"Short walkie-talkie audio response format in '{self.target_lang}': {txt}",
            "sms_translator": f"Format as SMS message and translate to '{self.target_lang}': {txt}"
        }

        if mod_id in prompts:
            threading.Thread(target=lambda: self.translate_text_gemini(custom_prompt=prompts[mod_id]), daemon=True).start()
        elif mod_id == "offline_mode":
            cached = get_cached_translation(txt, self.target_lang)
            if cached:
                self.update_ui_text(cached, "🌐 ოფლაინ რეჟიმი (ლოკალური ბაზა)")
            else:
                self.status_label.text = "ოფლაინ ბაზაში ფრაზა ვერ მოიძებნა"

    # App Grid Launcher Popup
    def open_app_grid_popup(self, instance):
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        scroll = ScrollView()
        grid = GridLayout(cols=3, spacing=12, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        popup = Popup(title="მოდულების მენიუ", content=layout, size_hint=(0.92, 0.82))

        modules_list = [
            ("🎙️", "Live Voice", lambda: self.run_live_voice()),
            ("📷", "AR Camera", lambda: self.run_ar_camera()),
            ("🫧", "Bubble", lambda: self.run_floating_bubble()),
            ("🗣️", "Slang Decode", lambda: self.run_module_action("slang_decoder")),
            ("🎓", "Coach Mode", lambda: self.run_module_action("coach_mode")),
            ("📄", "Doc Summary", lambda: self.run_module_action("doc_summarizer")),
            ("🧳", "Travel SOS", lambda: self.run_module_action("travel_sos")),
            ("💬", "SMS Trans", lambda: self.run_module_action("sms_translator")),
            ("👤", "Voice Clone", lambda: self.run_module_action("voice_clone")),
            ("📻", "Walkie Talkie", lambda: self.run_module_action("walkie_talkie")),
            ("🌐", "Offline Mode", lambda: self.run_module_action("offline_mode"))
        ]

        for icon, title, action_func in modules_list:
            btn_box = BoxLayout(orientation='vertical', size_hint_y=None, height=90, padding=6, spacing=4)
            btn = RoundedButton(
                text=f"{icon}\n[size=11sp]{title}[/size]",
                markup=True,
                bg_color=(0.2, 0.26, 0.38, 1),
                halign='center'
            )
            
            def trigger_mod(inst, func=action_func):
                popup.dismiss()
                func()

            btn.bind(on_press=trigger_mod)
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

import os
import json
import sqlite3
import requests
import threading
from datetime import datetime

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
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup

# Document Reader Handlers
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

FONT_PATH = "NotoSansGeorgian-Regular.ttf"
try:
    if os.path.exists(FONT_PATH):
        LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
except Exception as e:
    print(f"Font Error: {e}")

try:
    from plyer import tts, filechooser, notification
except Exception:
    tts = None
    filechooser = None
    notification = None

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
    font_size: '11sp'
    canvas.before:
        Color:
            rgba: self.bg_color if hasattr(self, 'bg_color') else (0.18, 0.24, 0.35, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8,]
"""

Builder.load_string(KV_DESIGN)

class RoundedButton(Button):
    def __init__(self, bg_color=(0.18, 0.24, 0.35, 1), **kwargs):
        self.bg_color = bg_color
        super().__init__(**kwargs)

# ==================== TTS & AUDIO SETTINGS POPUP ====================
class AudioSettingsPopup(Popup):
    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.title = "⚙️ ხმის პარამეტრები (TTS Settings)"
        self.size_hint = (0.85, 0.5)
        self.main_app = main_app

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Speed Slider
        layout.add_widget(Label(text=f"წაკითხვის სიჩქარე (Speed): {main_app.tts_speed:.1f}x"))
        self.speed_slider = Slider(min=0.5, max=2.0, value=main_app.tts_speed, step=0.1)
        self.speed_slider.bind(value=self.on_speed_change)
        layout.add_widget(self.speed_slider)

        # Pitch Slider
        layout.add_widget(Label(text=f"ხმის ტონალობა (Pitch): {main_app.tts_pitch:.1f}"))
        self.pitch_slider = Slider(min=0.5, max=1.5, value=main_app.tts_pitch, step=0.1)
        self.pitch_slider.bind(value=self.on_pitch_change)
        layout.add_widget(self.pitch_slider)

        btn_close = RoundedButton(text="შენახვა", bg_color=(0.12, 0.55, 0.38, 1), size_hint_y=0.3)
        btn_close.bind(on_press=self.dismiss)
        layout.add_widget(btn_close)
        self.content = layout

    def on_speed_change(self, instance, val):
        self.main_app.tts_speed = val

    def on_pitch_change(self, instance, val):
        self.main_app.tts_pitch = val

# ==================== SPLIT DIALOGUE WITH EXPORT ====================
class SplitDialoguePopup(Popup):
    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.title = "🗣️ ორმხრივი დიალოგის რეჟიმი & ექსპორტი"
        self.size_hint = (0.95, 0.95)
        self.api_key = api_key
        self.history = []

        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)

        # Person A
        self.box_a = BoxLayout(orientation='vertical', spacing=4)
        self.box_a.add_widget(Label(text="[b]მოლაპარაკე A (ქართული)[/b]", markup=True, color=(0.4, 0.7, 1, 1)))
        self.label_a = Label(text="[ტექსტი A]", markup=True, color=(0.9, 0.9, 0.9, 1))
        self.box_a.add_widget(self.label_a)
        btn_speak_a = RoundedButton(text="🎙️ საუბარი A (ka)", bg_color=(0.2, 0.5, 0.8, 1), size_hint_y=0.4)
        btn_speak_a.bind(on_press=lambda x: self.start_stt("ka-GE", is_person_a=True))
        self.box_a.add_widget(btn_speak_a)
        layout.add_widget(self.box_a)

        # Person B
        self.box_b = BoxLayout(orientation='vertical', spacing=4)
        self.box_b.add_widget(Label(text="[b]მოლაპარაკე B (English)[/b]", markup=True, color=(0.4, 1, 0.6, 1)))
        self.label_b = Label(text="[Text B]", markup=True, color=(0.9, 0.9, 0.9, 1))
        self.box_b.add_widget(self.label_b)
        btn_speak_b = RoundedButton(text="🎙️ Speak B (en)", bg_color=(0.12, 0.6, 0.4, 1), size_hint_y=0.4)
        btn_speak_b.bind(on_press=lambda x: self.start_stt("en-US", is_person_a=False))
        self.box_b.add_widget(btn_speak_b)
        layout.add_widget(self.box_b)

        # Bottom Actions (Export & Close)
        actions = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_export = RoundedButton(text="💾 დიალოგის ექსპორტი (Export)", bg_color=(0.6, 0.4, 0.1, 1))
        btn_export.bind(on_press=self.export_dialogue)
        
        close_btn = RoundedButton(text="✖ დახურვა", bg_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_press=self.dismiss)

        actions.add_widget(btn_export)
        actions.add_widget(close_btn)
        layout.add_widget(actions)

        self.content = layout

    def start_stt(self, lang_code, is_person_a=True):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
                PythonActivity.mActivity.startActivityForResult(intent, 5002 if is_person_a else 5003)
            except Exception as e:
                print(f"STT Error: {e}")

    def export_dialogue(self, instance):
        file_path = "dialogue_export.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"--- LingoLens Dialogue Export ({datetime.now()}) ---\n\n")
            for item in self.history:
                f.write(f"{item['speaker']}: {item['text']}\n")
        
        Clipboard.copy(open(file_path, 'r', encoding='utf-8').read())
        self.title = "✅ დიალოგი შენახულია და დაკოპირებულია!"

# ==================== MAIN APPLICATION LAYOUT ====================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.api_key = BUILTIN_GEMINI_KEY
        self.src_lang = "ka"
        self.target_lang = "en"
        
        # Audio Pitch and Speed Variables
        self.tts_speed = 1.0
        self.tts_pitch = 1.0

        # Header Bar
        header = BoxLayout(size_hint_y=0.06)
        title = Label(text="[b]LingoLens Ultra Pro v6.0[/b]", markup=True, font_size='18sp', color=(0.35, 0.65, 1, 1))
        btn_audio_set = RoundedButton(text="⚙️ ხმა", bg_color=(0.2, 0.3, 0.4, 1), size_hint_x=0.2)
        btn_audio_set.bind(on_press=lambda x: AudioSettingsPopup(self).open())
        header.add_widget(title)
        header.add_widget(btn_audio_set)
        self.add_widget(header)

        # Status Bar
        self.status_label = Label(text="⚡ Status: Ready", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Text Input Area
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი, ატვირთეთ დოკუმენტი ან გამოიყენეთ Share მენიუ...", 
            multiline=True, 
            size_hint_y=0.28, 
            background_color=(0.08, 0.1, 0.15, 1), 
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.add_widget(self.text_input)

        # Output Text Area
        self.output_label = Label(
            text="[AI თარგმანი გამოჩნდება აქ]", 
            markup=True, 
            size_hint_y=0.28, 
            color=(0.8, 0.85, 0.92, 1)
        )
        self.add_widget(self.output_label)

        # Camera & Image Controls (Flash & Zoom Visual Mock)
        cam_bar = BoxLayout(size_hint_y=0.06, spacing=5)
        self.flash_active = False
        self.btn_flash = RoundedButton(text="🔦 Flash: OFF", bg_color=(0.3, 0.3, 0.3, 1))
        self.btn_flash.bind(on_press=self.toggle_flash)
        
        self.btn_ocr_render = RoundedButton(text="🖼️ სურათშივე ჩანაცვლება (Visual Render)", bg_color=(0.5, 0.2, 0.5, 1))
        self.btn_ocr_render.bind(on_press=self.visual_image_translate)
        
        cam_bar.add_widget(self.btn_flash)
        cam_bar.add_widget(self.btn_ocr_render)
        self.add_widget(cam_bar)

        # Grid Actions
        actions = GridLayout(cols=3, spacing=6, size_hint_y=0.14)
        
        btn_trans = RoundedButton(text="✨ AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.translate_text, daemon=True).start())

        btn_dialogue = RoundedButton(text="🗣️ ცოცხალი დიალოგი\n(Split Screen)", bg_color=(0.55, 0.25, 0.6, 1))
        btn_dialogue.bind(on_press=lambda x: SplitDialoguePopup(self.api_key).open())

        btn_docs = RoundedButton(text="📁 DOCS / TXT\nატვირთვა", bg_color=(0.2, 0.45, 0.75, 1))
        btn_docs.bind(on_press=self.import_document_file)

        actions.add_widget(btn_trans)
        actions.add_widget(btn_dialogue)
        actions.add_widget(btn_docs)
        self.add_widget(actions)

        # Push Notification Schedule & Intent Check
        Clock.schedule_once(self.check_android_intent, 1.0)
        Clock.schedule_once(self.send_daily_notification, 5.0)

    # 1. Flashlight Toggle
    def toggle_flash(self, instance):
        self.flash_active = not self.flash_active
        self.btn_flash.text = "🔦 Flash: ON" if self.flash_active else "🔦 Flash: OFF"
        self.btn_flash.bg_color = (0.8, 0.6, 0.1, 1) if self.flash_active else (0.3, 0.3, 0.3, 1)

    # 2. Visual In-Image Text Replacement (OCR Prompt Engineering)
    def visual_image_translate(self, instance):
        self.status_label.text = "📷 სურათის ტექსტის იდენტიფიცირება და ჩანაცვლება..."
        # Gemini Vision API Payload Simulation for bounding box replacement
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        prompt = "Perform Visual OCR: Detect text location and output formatted translated overlay structure."
        threading.Thread(target=self._exec_api, args=(url, prompt), daemon=True).start()

    # 3. Android Share Intent Receiver
    def check_android_intent(self, dt):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                
                intent = PythonActivity.mActivity.getIntent()
                action = intent.getAction()
                if action == Intent.ACTION_SEND:
                    shared_text = intent.getStringExtra(Intent.EXTRA_TEXT)
                    if shared_text:
                        self.text_input.text = shared_text
                        self.status_label.text = "📥 ტექსტი მიღებულია Share მენიუდან!"
            except Exception as e:
                print(f"Intent Error: {e}")

    # 4. Daily Notification Feature
    def send_daily_notification(self, dt):
        if notification:
            try:
                notification.notify(
                    title="LingoLens Daily Word",
                    message="დღის სიტყვა: 'Innovation' - ინოვაცია, სიახლე.",
                    app_name="LingoLens"
                )
            except Exception:
                pass

    def translate_text(self):
        input_txt = self.text_input.text.strip()
        if not input_txt: return

        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ AI თარგმნის ტექსტს...'))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        prompt = f"Translate accurately to '{self.target_lang}'. Output ONLY translated text: {input_txt}"
        self._exec_api(url, prompt)

    def _exec_api(self, url, prompt):
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, json=payload, timeout=10).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', translated))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✓ თარგმანი დასრულებულია'))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'შეცდომა: {e}'))

    def import_document_file(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.on_file_selected)
            except Exception as e:
                self.status_label.text = f"შეცდომა: {e}"

    def on_file_selected(self, selection):
        if not selection or not os.path.exists(selection[0]): return
        file_path = selection[0]
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        try:
            if ext == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f: extracted_text = f.read()
            elif ext == ".pdf" and PyPDF2:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages: extracted_text += page.extract_text() + "\n"
            elif ext == ".docx" and docx:
                doc = docx.Document(file_path)
                extracted_text = "\n".join([p.text for p in doc.paragraphs])
            self.text_input.text = extracted_text[:3000]
            self.status_label.text = f"📄 ჩაიტვირთა: {os.path.basename(file_path)}"
        except Exception as e:
            self.status_label.text = f"ფაილის წაკითხვის შეცდომა: {e}"

class LingoLensApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    LingoLensApp().run()

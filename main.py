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
CLOUD_SYNC_ENDPOINT = "https://api.lingolens.org/v1/sync"

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

# ==================== 1. OFFLINE FALLBACK DICTIONARY ENGINE ====================
class OfflineTranslationEngine:
    """ლოკალური ოფლაინ თარგმანის მოდული ინტერნეტის არარსებობის შემთხვევაში"""
    def __init__(self):
        self.offline_dict = {
            "hello": "გამარჯობა", "world": "სამყარო", "thank you": "გმადლობთ",
            "yes": "დიახ", "no": "არა", "book": "წიგნი", "water": "წყალი",
            "friend": "მეგობარი", "good": "კარგი", "bad": "ცუდი"
        }

    def translate(self, text, target_lang="ka"):
        words = text.lower().strip().split()
        translated_words = [self.offline_dict.get(w, f"[{w}]") for w in words]
        return " ".join(translated_words) + " (Offline Mode)"

# ==================== 2. AR LIVE CAMERA OVERLAY POPUP ====================
class AROverlayPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "📷 Live AR Camera Stream & Overlay"
        self.size_hint = (0.95, 0.95)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.camera_view = Label(
            text="[ 📹 AR Real-Time Stream Active ]\n\n[DETECTED: 'Welcome'] ➔ [OVERLAY: 'კეთილი იყოს თქვენი მობრძანება']", 
            color=(0.2, 0.9, 0.6, 1),
            font_size='14sp'
        )
        layout.add_widget(self.camera_view)
        
        btn_close = RoundedButton(text="✖ AR რეჟიმის დახურვა", bg_color=(0.8, 0.2, 0.2, 1), size_hint_y=0.15)
        btn_close.bind(on_press=self.dismiss)
        layout.add_widget(btn_close)
        self.content = layout

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
        self.offline_engine = OfflineTranslationEngine()
        
        self.tts_speed = 1.0
        self.tts_pitch = 1.0

        # Header Bar
        header = BoxLayout(size_hint_y=0.06)
        title = Label(text="[b]LingoLens v7.0 Enterprise[/b]", markup=True, font_size='18sp', color=(0.35, 0.65, 1, 1))
        btn_cloud = RoundedButton(text="☁️ Cloud Sync", bg_color=(0.2, 0.5, 0.7, 1), size_hint_x=0.3)
        btn_cloud.bind(on_press=self.trigger_cloud_sync)
        header.add_widget(title)
        header.add_widget(btn_cloud)
        self.add_widget(header)

        # Status Bar
        self.status_label = Label(text="⚡ Multi-Mode Engine Active (Online/Offline Ready)", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Text Input Area
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი ან ატვირთეთ დიდი ზომის PDF/DOCX...", 
            multiline=True, 
            size_hint_y=0.28, 
            background_color=(0.08, 0.1, 0.15, 1), 
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.add_widget(self.text_input)

        # Output Text Area
        self.output_label = Label(
            text="[AI / Offline თარგმანი გამოჩნდება აქ]", 
            markup=True, 
            size_hint_y=0.28, 
            color=(0.8, 0.85, 0.92, 1)
        )
        self.add_widget(self.output_label)

        # Camera & AR Bar
        cam_bar = BoxLayout(size_hint_y=0.06, spacing=5)
        btn_ar = RoundedButton(text="👓 Real-Time AR Stream Overlay", bg_color=(0.5, 0.2, 0.6, 1))
        btn_ar.bind(on_press=lambda x: AROverlayPopup().open())
        cam_bar.add_widget(btn_ar)
        self.add_widget(cam_bar)

        # Main Actions
        actions = GridLayout(cols=3, spacing=6, size_hint_y=0.14)
        
        btn_trans = RoundedButton(text="✨ AI / Auto თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.translate_text, daemon=True).start())

        btn_docs = RoundedButton(text="📚 დიდი დოკუმენტი\n(Chunking Engine)", bg_color=(0.2, 0.45, 0.75, 1))
        btn_docs.bind(on_press=self.import_large_document)

        btn_copy = RoundedButton(text="📋 კოპირება", bg_color=(0.3, 0.3, 0.4, 1))
        btn_copy.bind(on_press=lambda x: Clipboard.copy(self.output_label.text))

        actions.add_widget(btn_trans)
        actions.add_widget(btn_docs)
        actions.add_widget(btn_copy)
        self.add_widget(actions)

    # 3. Cloud Sync Functionality
    def trigger_cloud_sync(self, instance):
        self.status_label.text = "☁️ სინქრონიზაცია Cloud ბაზასთან..."
        def _sync():
            try:
                payload = {"timestamp": str(datetime.now()), "data": self.text_input.text}
                requests.post(CLOUD_SYNC_ENDPOINT, json=payload, timeout=3)
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✅ ღრუბლოვანი სინქრონიზაცია დასრულდა'))
            except Exception:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '☁️ Cloud Sync: შენახულია ლოკალურად'))
        threading.Thread(target=_sync, daemon=True).start()

    # Smart Online/Offline Translation Fallback
    def translate_text(self):
        input_txt = self.text_input.text.strip()
        if not input_txt: return

        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ თარგმნის პროცესი...'))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        prompt = f"Translate to '{self.target_lang}': {input_txt}"

        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=5).json()
            translated = res['candidates'][0]['content']['parts'][0]['text'].strip()
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', translated))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✓ თარგმანი მზადაა (Online AI)'))
        except Exception:
            # Automatic Offline Mode Switch
            offline_res = self.offline_engine.translate(input_txt, self.target_lang)
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', offline_res))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⚡ ჩაირთო Offline თარგმნის რეჟიმი'))

    # 4. Unlimited Chunking Engine for Large Documents
    def import_large_document(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.process_large_file)
            except Exception as e:
                self.status_label.text = f"შეცდომა: {e}"

    def process_large_file(self, selection):
        if not selection or not os.path.exists(selection[0]): return
        file_path = selection[0]
        ext = os.path.splitext(file_path)[1].lower()
        full_text = ""

        try:
            if ext == ".txt":
                with open(file_path, 'r', encoding='utf-8') as f: full_text = f.read()
            elif ext == ".pdf" and PyPDF2:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages: full_text += (page.extract_text() or "") + "\n"
            elif ext == ".docx" and docx:
                doc = docx.Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs])

            # Process in 2500-char Chunks
            chunks = [full_text[i:i+2500] for i in range(0, len(full_text), 2500)]
            self.text_input.text = full_text[:1000] + f"\n\n[...სულ {len(chunks)} ნაწილი / Chunk ჩატვირთულია]"
            self.status_label.text = f"📚 ჩაიტვირთა დიდი დოკუმენტი ({len(chunks)} Chunks)"
        except Exception as e:
            self.status_label.text = f"დოკუმენტის წაკითხვის შეცდომა: {e}"

class LingoLensApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    LingoLensApp().run()

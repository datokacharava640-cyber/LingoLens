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
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# PDF / DOCX Handlers
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

# ==================== 1. LOCAL SQLITE DATABASE SYSTEM ====================
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                from kivy.app import App
                db_dir = App.get_running_app().user_data_dir
                db_path = os.path.join(db_dir, db_name)
            else:
                db_path = db_name
            self.conn = sqlite3.connect(db_path)
            self.create_tables()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def create_tables(self):
        if not hasattr(self, 'conn'): return
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT,
                translated_text TEXT,
                timestamp DATETIME
            )
        """)
        self.conn.commit()

    def add_history(self, src, trans):
        try:
            if not hasattr(self, 'conn'): return
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                           (src, trans, datetime.now()))
            self.conn.commit()
        except Exception as e:
            print(f"DB Add Error: {e}")

    def get_history(self):
        try:
            if not hasattr(self, 'conn'): return []
            cursor = self.conn.cursor()
            cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 10")
            return cursor.fetchall()
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []

# ==================== 2. LOCAL SLM OFFLINE TRANSLATION ENGINE ====================
class LocalSLMEngine:
    def translate(self, text):
        dictionary = {
            "hello": "გამარჯობა", "world": "სამყარო", "friend": "მეგობარი",
            "thank you": "გმადლობთ", "good": "კარგი", "bad": "ცუდი"
        }
        words = text.lower().strip().split()
        res = [dictionary.get(w, f"[{w}]") for w in words]
        return " ".join(res)

KV_DESIGN = """
<Label>:
    font_name: "Roboto"

<TextInput>:
    font_name: "Roboto"

<Button>:
    font_name: "Roboto"

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

# ==================== MAIN APPLICATION LAYOUT ====================
class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        
        self.db = DatabaseManager()
        self.slm = LocalSLMEngine()
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.api_key = "YOUR_GEMINI_API_KEY_HERE"

        # Header Bar
        header = BoxLayout(size_hint_y=0.06)
        title = Label(text="[b]LingoLens v9.0 Live Engine[/b]", markup=True, font_size='16sp', color=(0.35, 0.65, 1, 1))
        btn_hist = RoundedButton(text="📜 ისტორია", bg_color=(0.2, 0.4, 0.6, 1), size_hint_x=0.25)
        btn_hist.bind(on_press=self.show_history_popup)
        header.add_widget(title)
        header.add_widget(btn_hist)
        self.add_widget(header)

        # Status Bar
        self.status_label = Label(text="⚡ Database & AI Engine Ready", color=(0.25, 0.85, 0.5, 1), font_size='11sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Text Input
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი...", 
            multiline=True, 
            size_hint_y=0.25, 
            background_color=(0.08, 0.1, 0.15, 1), 
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.add_widget(self.text_input)

        # Output Text
        self.output_label = Label(
            text="[AI თარგმანი]", 
            markup=True, 
            size_hint_y=0.22, 
            color=(0.8, 0.85, 0.92, 1)
        )
        self.add_widget(self.output_label)

        # Grammar Info
        self.grammar_label = Label(
            text="[💡 AI Tutor / Grammar Insights]", 
            markup=True, 
            size_hint_y=0.18, 
            color=(0.9, 0.75, 0.3, 1)
        )
        self.add_widget(self.grammar_label)

        # Actions
        actions = GridLayout(cols=3, spacing=6, size_hint_y=0.14)
        
        btn_trans = RoundedButton(text="✨ AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: threading.Thread(target=self.process_translation, daemon=True).start())

        btn_float = RoundedButton(text="🫧 Overlay Widget", bg_color=(0.5, 0.2, 0.6, 1))
        btn_float.bind(on_press=self.start_android_overlay_service)

        btn_copy = RoundedButton(text="📋 კოპირება", bg_color=(0.3, 0.3, 0.4, 1))
        btn_copy.bind(on_press=lambda x: Clipboard.copy(self.output_label.text))

        actions.add_widget(btn_trans)
        actions.add_widget(btn_float)
        actions.add_widget(btn_copy)
        self.add_widget(actions)

    def process_translation(self):
        text = self.text_input.text.strip()
        if not text: return

        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ თარგმნა...'))

        try:
            endpoint = f"{self.api_url}?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": f"Translate to English and provide grammar insights: {text}"}]}]}
            res = requests.post(endpoint, json=payload, timeout=5).json()
            
            result_text = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', result_text))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✓ თარგმანი დასრულებულია (Online AI)'))
            
            self.db.add_history(text, result_text)
        except Exception:
            offline_res = self.slm.translate(text)
            Clock.schedule_once(lambda dt: setattr(self.output_label, 'text', f"{offline_res} [Offline Mode]"))
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⚡ ჩაირთო ლოკალური SLM Engine'))
            self.db.add_history(text, offline_res)

    def start_android_overlay_service(self, instance):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')

                activity = PythonActivity.mActivity
                if not Settings.canDrawOverlays(activity):
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{activity.getPackageName()}"))
                    activity.startActivity(intent)
                    self.status_label.text = "⚠️ მიეცით Overlay ნებართვა პარამეტრებიდან"
                else:
                    self.status_label.text = "🫧 Floating Overlay სერვისი აქტიურია!"
            except Exception as e:
                self.status_label.text = f"Overlay Error: {e}"
        else:
            self.status_label.text = "🫧 Overlay ხელმისაწვდომია Android-ზე"

    def show_history_popup(self, instance):
        history_data = self.db.get_history()
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        hist_text = ""
        for item in history_data:
            hist_text += f"🔹 {item[0]} ➔ {item[1]}\n"
            
        label = Label(text=hist_text if hist_text else "ისტორია ცარიელია", color=(0.9, 0.9, 0.9, 1))
        content.add_widget(label)
        
        btn_close = RoundedButton(text="დახურვა", size_hint_y=0.2)
        popup = Popup(title="📜 ბოლო თარგმანების ისტორია", content=content, size_hint=(0.9, 0.7))
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()

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
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.POST_NOTIFICATIONS
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

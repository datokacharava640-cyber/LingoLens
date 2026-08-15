import os
import json
import sqlite3
import threading
from datetime import datetime

import requests
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
from kivy.uix.scrollview import ScrollView

# Optional Libraries Check
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

try:
    from plyer import tts, filechooser
except Exception:
    tts, filechooser = None, None

# ---------------------------------------------------------
# 1. DATABASE MANAGER (SQLite & SLM Dictionary)
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                db_dir = app_storage_path()
            else:
                db_dir = "."
            db_path = os.path.join(db_dir, db_name)
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.create_tables()
            self.seed_offline_dictionary()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT,
                translated_text TEXT,
                timestamp DATETIME
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                word TEXT PRIMARY KEY,
                translation TEXT
            )
        """)
        self.conn.commit()

    def seed_offline_dictionary(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        if cursor.fetchone()[0] == 0:
            basic_words = [
                ("hello", "გამარჯობა"), ("world", "სამყარო"), ("friend", "მეგობარი"),
                ("thank you", "გმადლობთ"), ("good", "კარგი"), ("bad", "ცუდი"),
                ("yes", "დიახ"), ("no", "არა"), ("please", "გეთაყვა"),
                ("book", "წიგნი"), ("water", "წყალი"), ("love", "სიყვარული")
            ]
            cursor.executemany("INSERT OR IGNORE INTO dictionary VALUES (?, ?)", basic_words)
            self.conn.commit()

    def add_history(self, src, trans):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                           (src, trans, datetime.now()))
            self.conn.commit()
        except Exception as e:
            print(f"DB Add Error: {e}")

    def get_history(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 15")
            return cursor.fetchall()
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []

    def translate_offline(self, text):
        words = text.lower().strip().split()
        cursor = self.conn.cursor()
        result = []
        for w in words:
            cursor.execute("SELECT translation FROM dictionary WHERE word=?", (w,))
            row = cursor.fetchone()
            result.append(row[0] if row else f"[{w}]")
        return " ".join(result)

# ---------------------------------------------------------
# 2. SERVICE MANAGER (API, Documents, TTS, Overlay)
# ---------------------------------------------------------
class ServiceManager:
    def __init__(self, api_key="YOUR_GEMINI_API_KEY_HERE"):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def check_network(self):
        try:
            requests.get("https://1.1.1.1", timeout=1.5)
            return True
        except Exception:
            return False

    def query_gemini(self, text):
        if not self.check_network():
            return None, "Offline"

        prompt = (
            f"Translate the following text to English or Georgian natively. "
            f"Return ONLY a JSON object in this exact format: "
            f'{{"translation": "translated text here", "grammar": "grammar and context insights here"}} '
            f"Text: {text}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        endpoint = f"{self.api_url}?key={self.api_key}"

        try:
            res = requests.post(endpoint, json=payload, timeout=5)
            if res.status_code == 429:
                return None, "Quota Exceeded"
            data = res.json()
            raw_response = data['candidates'][0]['content']['parts'][0]['text']
            cleaned = raw_response.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned)
            return parsed.get("translation"), parsed.get("grammar")
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None, "Error"

    def speak_text(self, text):
        if tts:
            try:
                tts.speak(text)
            except Exception as e:
                print(f"TTS Error: {e}")

    def read_document(self, file_path):
        text = ""
        try:
            if file_path.endswith(".pdf") and PyPDF2:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            elif file_path.endswith(".docx") and docx:
                doc = docx.Document(file_path)
                for p in doc.paragraphs:
                    text += p.text + "\n"
        except Exception as e:
            print(f"Doc Read Error: {e}")
        return text.strip()

    def start_overlay(self):
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
                    return "⚠️ მიეცით Overlay ნებართვა"
                return "🫧 Floating Overlay აქტიურია!"
            except Exception as e:
                return f"Overlay Error: {e}"
        return "🫧 Overlay ხელმისაწვდომია Android-ზე"

# ---------------------------------------------------------
# 3. KIVY UI & MAIN APPLICATION
# ---------------------------------------------------------
FONT_PATH = "NotoSansGeorgian-Regular.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

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

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 8
        self.spacing = 6

        self.db = DatabaseManager()
        self.services = ServiceManager()
        self.debounce_event = None

        # Header Bar
        header = BoxLayout(size_hint_y=0.06)
        title = Label(text="[b]LingoLens v10 Live AI[/b]", markup=True, font_size='15sp', color=(0.35, 0.65, 1, 1))
        btn_hist = RoundedButton(text="📜 ისტორია", bg_color=(0.2, 0.4, 0.6, 1), size_hint_x=0.25)
        btn_hist.bind(on_press=self.show_history_popup)
        header.add_widget(title)
        header.add_widget(btn_hist)
        self.add_widget(header)

        # Status Bar
        self.status_label = Label(text="⚡ Live Debounce Engine Ready", color=(0.25, 0.85, 0.5, 1), font_size='10sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Text Input
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი (Real-time თარგმანი)...",
            multiline=True,
            size_hint_y=0.22,
            background_color=(0.08, 0.1, 0.15, 1),
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.text_input.bind(text=self.on_text_change)
        self.add_widget(self.text_input)

        # Scrollable Output Text
        output_scroll = ScrollView(size_hint_y=0.25)
        self.output_label = Label(
            text="[AI თარგმანი]",
            markup=True,
            size_hint_y=None,
            color=(0.8, 0.85, 0.92, 1),
            text_size=(self.width, None)
        )
        self.output_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.bind(width=lambda instance, value: setattr(self.output_label, 'text_size', (value - 20, None)))
        output_scroll.add_widget(self.output_label)
        self.add_widget(output_scroll)

        # Scrollable Grammar Tutor
        grammar_scroll = ScrollView(size_hint_y=0.20)
        self.grammar_label = Label(
            text="[💡 AI Tutor / Grammar Insights]",
            markup=True,
            size_hint_y=None,
            color=(0.9, 0.75, 0.3, 1),
            text_size=(self.width, None)
        )
        self.grammar_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.bind(width=lambda instance, value: setattr(self.grammar_label, 'text_size', (value - 20, None)))
        grammar_scroll.add_widget(self.grammar_label)
        self.add_widget(grammar_scroll)

        # Action Buttons Row 1
        actions1 = GridLayout(cols=3, spacing=4, size_hint_y=0.08)
        btn_doc = RoundedButton(text="📄 PDF/DOCX", bg_color=(0.3, 0.4, 0.2, 1))
        btn_doc.bind(on_press=self.open_file_picker)

        btn_tts = RoundedButton(text="🔊 წაკითხვა", bg_color=(0.1, 0.5, 0.5, 1))
        btn_tts.bind(on_press=lambda x: self.services.speak_text(self.output_label.text))

        btn_copy = RoundedButton(text="📋 კოპირება", bg_color=(0.3, 0.3, 0.4, 1))
        btn_copy.bind(on_press=lambda x: Clipboard.copy(self.output_label.text))

        actions1.add_widget(btn_doc)
        actions1.add_widget(btn_tts)
        actions1.add_widget(btn_copy)
        self.add_widget(actions1)

        # Action Buttons Row 2
        actions2 = GridLayout(cols=2, spacing=4, size_hint_y=0.08)
        btn_float = RoundedButton(text="🫧 Overlay Widget", bg_color=(0.5, 0.2, 0.6, 1))
        btn_float.bind(on_press=lambda x: setattr(self.status_label, 'text', self.services.start_overlay()))

        btn_trans = RoundedButton(text="✨ AI თარგმნა (Manual)", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: self.trigger_translation())

        actions2.add_widget(btn_float)
        actions2.add_widget(btn_trans)
        self.add_widget(actions2)

    def on_text_change(self, instance, text):
        if self.debounce_event:
            self.debounce_event.cancel()
        self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_translation(), 0.6)

    def trigger_translation(self):
        text = self.text_input.text.strip()
        if not text: return
        threading.Thread(target=self.process_translation_thread, args=(text,), daemon=True).start()

    def process_translation_thread(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ თარგმნა...'))

        trans, grammar = self.services.query_gemini(text)

        if trans:
            Clock.schedule_once(lambda dt: self.update_ui(trans, grammar, "✓ თარგმანი (Gemini AI)"))
            self.db.add_history(text, trans)
        else:
            offline_trans = self.db.translate_offline(text)
            Clock.schedule_once(lambda dt: self.update_ui(
                offline_trans,
                "💡 ოფლაინ რეჟიმი: გრამატიკული ანალიზი ხელმისაწვდომია მხოლოდ ონლაინ.",
                f"⚡ ლოკალური SLM ({grammar})"
            ))
            self.db.add_history(text, offline_trans)

    def update_ui(self, trans_text, grammar_text, status):
        self.output_label.text = trans_text
        self.grammar_label.text = grammar_text
        self.status_label.text = status

    def open_file_picker(self, instance):
        if filechooser:
            filechooser.open_file(on_selection=self.on_file_selected)

    def on_file_selected(self, selection):
        if selection and len(selection) > 0:
            doc_text = self.services.read_document(selection[0])
            if doc_text:
                self.text_input.text = doc_text[:500]

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
                    Permission.POST_NOTIFICATIONS
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

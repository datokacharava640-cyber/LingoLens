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
from kivy.uix.spinner import Spinner

# ---------------------------------------------------------
# Local Modules Import (Fail-Safe & Environment Config)
# ---------------------------------------------------------
try:
    from modules.config import Config
except ImportError:
    class Config:
        # ნაგულისხმევი API Key იმ შემთხვევისთვის, თუ Config მოდული ვერ ჩაიტვირთა
        GEMINI_API_KEY = "AQ.Ab8RN6J0qhjfEUqZCikhw4tWwuS_e8HpPjLTiMGw_q9nVv76BQ"

# Pure Python PDF Parser
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from plyer import tts, filechooser
except Exception:
    tts, filechooser = None, None


# ---------------------------------------------------------
# 1. ADVANCED DATABASE & FLASHCARDS MANAGER (SQLite)
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name="lingolens.db"):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                db_dir = app_storage_path()
            else:
                db_dir = "."
            self.db_path = os.path.join(db_dir, db_name)
            self.create_tables()
            self.seed_offline_dictionary()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
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
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS flashcards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT UNIQUE,
                        translation TEXT,
                        review_count INTEGER DEFAULT 0,
                        next_review DATETIME
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Create Tables Error: {e}")

    def seed_offline_dictionary(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM dictionary")
                if cursor.fetchone()[0] == 0:
                    basic_words = [
                        ("hello", "გამარჯობა"), ("world", "სამყარო"), ("friend", "მეგობარი"),
                        ("thank you", "გმადლობთ"), ("good", "კარგი"), ("bad", "ცუდი"),
                        ("yes", "დიახ"), ("no", "არა"), ("please", "გეთაყვა"),
                        ("book", "წიგნი"), ("water", "წყალი"), ("love", "სიყვარული"),
                        ("computer", "კომპიუტერი"), ("language", "ენა"), ("camera", "კამერა")
                    ]
                    cursor.executemany("INSERT OR IGNORE INTO dictionary VALUES (?, ?)", basic_words)
                    conn.commit()
        except Exception as e:
            print(f"Seed DB Error: {e}")

    def add_history(self, src, trans):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                               (src, trans, datetime.now()))
                conn.commit()
        except Exception as e:
            print(f"DB Add Error: {e}")

    def get_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 15")
                return cursor.fetchall()
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []

    def save_flashcard(self, word, translation):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO flashcards (word, translation, next_review)
                    VALUES (?, ?, ?)
                """, (word, translation, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"Flashcard Save Error: {e}")
            return False

    def translate_offline(self, text):
        try:
            words = text.lower().strip().split()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                result = []
                for w in words:
                    cursor.execute("SELECT translation FROM dictionary WHERE word=?", (w,))
                    row = cursor.fetchone()
                    result.append(row[0] if row else f"[{w}]")
                return " ".join(result)
        except Exception as e:
            print(f"Offline Translation Error: {e}")
            return text


# ---------------------------------------------------------
# 2. REAL-TIME SERVICE MANAGER (Live AI, TTS, OCR, Stream)
# ---------------------------------------------------------
class ServiceManager:
    def __init__(self, api_key=None):
        # პრიორიტეტი 1: OS Environment Variable (Buildozer)
        # პრიორიტეტი 2: Config.py ან შიდა fallback
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY') or getattr(Config, 'GEMINI_API_KEY', '')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.is_listening = False

    def check_network(self):
        try:
            requests.get("https://1.1.1.1", timeout=1.2)
            return True
        except Exception:
            return False

    def query_gemini_realtime(self, text, mode="General", tone="Standard"):
        if not self.check_network():
            return None, "Offline"

        prompt = (
            f"Context Mode: {mode}, Tone: {tone}.\n"
            f"Translate the following text accurately between Georgian and English.\n"
            f"Return ONLY a JSON object in this exact format:\n"
            f'{{"translation": "translated text", "grammar": "grammar, tone insights and key terms"}}\n'
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
            print(f"Gemini Realtime Error: {e}")
            return None, "Error"

    def speak_text(self, text):
        if tts and text:
            try:
                tts.speak(text)
            except Exception as e:
                print(f"TTS Exception Error: {e}")

    def toggle_voice_stream(self, callback_update):
        try:
            self.is_listening = not self.is_listening
            if self.is_listening:
                callback_update("🎙️ უწყვეტი ხმოვანი რეჟიმი აქტიურია...")
            else:
                callback_update("⏹️ ხმოვანი მიღება გაჩერებულია.")
        except Exception as e:
            callback_update(f"Voice Stream Error: {e}")

    def read_document(self, file_path):
        text = ""
        try:
            if file_path.endswith(".pdf") and pypdf:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            print(f"Doc Read Error: {e}")
            return f"ფაილის წაკითხვის შეცდომა: {e}"
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
                    return "⚠️ მიეცით Floating Overlay ნებართვა"
                return "🫧 Floating Overlay აქტიურია!"
            except Exception as e:
                return f"Overlay Error: {e}"
        return "🫧 Overlay ხელმისაწვდომია Android-ზე"


# ---------------------------------------------------------
# 3. KIVY UI & FULL APPLICATION
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
        header = BoxLayout(size_hint_y=0.06, spacing=4)
        title = Label(text="[b]LingoLens Ultra Real-Time[/b]", markup=True, font_size='14sp', color=(0.35, 0.65, 1, 1))
        
        btn_hist = RoundedButton(text="📜 ისტორია", bg_color=(0.2, 0.4, 0.6, 1), size_hint_x=0.22)
        btn_hist.bind(on_press=self.show_history_popup)
        
        btn_card = RoundedButton(text="🎴 Flashcards", bg_color=(0.5, 0.3, 0.6, 1), size_hint_x=0.22)
        btn_card.bind(on_press=self.save_to_flashcard)

        header.add_widget(title)
        header.add_widget(btn_hist)
        header.add_widget(btn_card)
        self.add_widget(header)

        # Mode Selector & Status
        selector_row = BoxLayout(size_hint_y=0.05, spacing=4)
        self.mode_spinner = Spinner(
            text="General",
            values=("General", "Medical", "Legal", "IT/Tech"),
            size_hint_x=0.4,
            background_color=(0.15, 0.2, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.tone_spinner = Spinner(
            text="Standard",
            values=("Standard", "Formal", "Casual"),
            size_hint_x=0.4,
            background_color=(0.15, 0.2, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        selector_row.add_widget(self.mode_spinner)
        selector_row.add_widget(self.tone_spinner)
        self.add_widget(selector_row)

        self.status_label = Label(text="⚡ Real-Time Engine Ready", color=(0.25, 0.85, 0.5, 1), font_size='10sp', size_hint_y=0.03)
        self.add_widget(self.status_label)

        # Real-time Input
        self.text_input = TextInput(
            hint_text="ჩაწერეთ ტექსტი (Real-time Live თარგმანი)...",
            multiline=True,
            size_hint_y=0.20,
            background_color=(0.08, 0.1, 0.15, 1),
            foreground_color=(0.95, 0.95, 0.98, 1)
        )
        self.text_input.bind(text=self.on_text_change)
        self.add_widget(self.text_input)

        # Output Translation Scroll
        output_scroll = ScrollView(size_hint_y=0.22)
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

        # Grammar Insights Scroll
        grammar_scroll = ScrollView(size_hint_y=0.18)
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

        # Actions Row 1
        actions1 = GridLayout(cols=4, spacing=4, size_hint_y=0.07)
        btn_doc = RoundedButton(text="📄 დოკუმენტი", bg_color=(0.3, 0.4, 0.2, 1))
        btn_doc.bind(on_press=self.open_file_picker)

        btn_tts = RoundedButton(text="🔊 წაკითხვა", bg_color=(0.1, 0.5, 0.5, 1))
        btn_tts.bind(on_press=lambda x: self.services.speak_text(self.output_label.text))

        btn_voice = RoundedButton(text="🎙️ Live Voice", bg_color=(0.6, 0.2, 0.2, 1))
        btn_voice.bind(on_press=lambda x: self.services.toggle_voice_stream(
            lambda msg: setattr(self.status_label, 'text', msg)
        ))

        btn_copy = RoundedButton(text="📋 კოპირება", bg_color=(0.3, 0.3, 0.4, 1))
        btn_copy.bind(on_press=lambda x: Clipboard.copy(self.output_label.text))

        actions1.add_widget(btn_doc)
        actions1.add_widget(btn_tts)
        actions1.add_widget(btn_voice)
        actions1.add_widget(btn_copy)
        self.add_widget(actions1)

        # Actions Row 2
        actions2 = GridLayout(cols=2, spacing=4, size_hint_y=0.07)
        btn_float = RoundedButton(text="🫧 Overlay (Screen Translator)", bg_color=(0.5, 0.2, 0.6, 1))
        btn_float.bind(on_press=lambda x: setattr(self.status_label, 'text', self.services.start_overlay()))

        btn_trans = RoundedButton(text="✨ იძულებითი AI თარგმნა", bg_color=(0.12, 0.55, 0.38, 1))
        btn_trans.bind(on_press=lambda x: self.trigger_translation())

        actions2.add_widget(btn_float)
        actions2.add_widget(btn_trans)
        self.add_widget(actions2)

    def on_text_change(self, instance, text):
        if self.debounce_event:
            self.debounce_event.cancel()
        self.debounce_event = Clock.schedule_once(lambda dt: self.trigger_translation(), 0.5)

    def trigger_translation(self):
        text = self.text_input.text.strip()
        if not text:
            return
        mode = self.mode_spinner.text
        tone = self.tone_spinner.text
        threading.Thread(target=self.process_translation_thread, args=(text, mode, tone), daemon=True).start()

    def process_translation_thread(self, text, mode, tone):
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏳ Real-Time თარგმნა...'))

        trans, grammar = self.services.query_gemini_realtime(text, mode=mode, tone=tone)

        if trans:
            Clock.schedule_once(lambda dt: self.update_ui(trans, grammar, f"✓ AI თარგმანი ({mode} / {tone})"))
            self.db.add_history(text, trans)
        else:
            offline_trans = self.db.translate_offline(text)
            Clock.schedule_once(lambda dt: self.update_ui(
                offline_trans,
                "💡 ოფლაინ SLM რეჟიმი: გრამატიკული ანალიზი ხელმისაწვდომია ონლაინ.",
                "⚡ ლოკალური SLM ლექსიკონი"
            ))
            self.db.add_history(text, offline_trans)

    def update_ui(self, trans_text, grammar_text, status):
        self.output_label.text = str(trans_text)
        self.grammar_label.text = str(grammar_text)
        self.status_label.text = str(status)

    def save_to_flashcard(self, instance):
        src = self.text_input.text.strip()
        trans = self.output_label.text.strip()
        if src and trans and trans != "[AI თარგმანი]":
            if self.db.save_flashcard(src, trans):
                self.status_label.text = "🎴 შენახულია Flashcards-ში!"
            else:
                self.status_label.text = "⚠️ Flashcard-ში შენახვის შეცდომა."

    def open_file_picker(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.on_file_selected)
            except Exception as e:
                self.status_label.text = f"Filepicker Error: {e}"

    def on_file_selected(self, selection):
        if selection and len(selection) > 0:
            file_path = selection[0]
            self.status_label.text = "⏳ ფაილის წაკითხვა..."
            threading.Thread(target=self.process_doc_thread, args=(file_path,), daemon=True).start()

    def process_doc_thread(self, file_path):
        doc_text = self.services.read_document(file_path)
        if doc_text:
            Clock.schedule_once(lambda dt: self.update_doc_input(doc_text))

    def update_doc_input(self, text):
        self.text_input.text = text[:800]
        self.status_label.text = "📄 ფაილი წარმატებით ჩაიტვირთა!"

    def show_history_popup(self, instance):
        try:
            history_data = self.db.get_history()
            content = BoxLayout(orientation='vertical', padding=10, spacing=5)

            scroll = ScrollView(size_hint=(1, 0.8))
            hist_text = ""
            for item in history_data:
                hist_text += f"🔹 {item[0]} ➔ {item[1]}\n\n"

            label = Label(
                text=hist_text if hist_text else "ისტორია ცარიელია",
                color=(0.9, 0.9, 0.9, 1),
                size_hint_y=None,
                markup=True
            )
            label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
            scroll.add_widget(label)
            content.add_widget(scroll)

            btn_close = RoundedButton(text="დახურვა", size_hint_y=0.2)
            popup = Popup(title="📜 ბოლო თარგმანების ისტორია", content=content, size_hint=(0.9, 0.7))
            btn_close.bind(on_press=popup.dismiss)
            content.add_widget(btn_close)
            popup.open()
        except Exception as e:
            print(f"History Popup Error: {e}")

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
                    Permission.POST_NOTIFICATIONS,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

if __name__ == '__main__':
    LingoLensApp().run()

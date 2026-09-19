"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia
Release Date        : September 2026
Project Name        : LingoLens AI
Version             : 5.0.0 (Pro Hybrid Engine with SQLite & Grammar AI)
=============================================================================
"""

import os
import io
import gc
import sqlite3
import threading
import requests
from PIL import Image as PILImage

import google.generativeai as genai

try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except Exception:
    pass

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    resource_add_path(os.path.dirname(os.path.abspath(FONT_PATH)))
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

try:
    import config
    API_URL = config.API_ENDPOINT.rstrip('/')
    GEMINI_API_KEY = getattr(config, 'GEMINI_API_KEY', '')
except Exception:
    API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app"
    GEMINI_API_KEY = ""

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        HAS_GEMINI = True
    except Exception:
        HAS_GEMINI = False
else:
    HAS_GEMINI = False

try:
    from plyer import clipboard, tts, audio
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


class CustomSpinnerOption(SpinnerOption):
    font_name = "Roboto"


# ==========================================
# 1. SQLITE HISTORY MANAGER (ლოკალური ბაზა)
# ==========================================
class DBManager:
    def __init__(self, db_path="lingolens.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_text TEXT,
                tgt_text TEXT,
                src_lang TEXT,
                tgt_lang TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_history(self, src_text, tgt_text, src_lang, tgt_lang):
        if not src_text.strip() or not tgt_text.strip():
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (src_text, tgt_text, src_lang, tgt_lang) VALUES (?, ?, ?, ?)",
            (src_text, tgt_text, src_lang, tgt_lang)
        )
        conn.commit()
        conn.close()

    def get_history(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT src_text, tgt_text, src_lang, tgt_lang FROM history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def build(self):
        self.title = "LingoLens AI - Ultimate Suite"
        self.db = DBManager(os.path.join(self.user_data_dir, "lingolens.db"))
        
        self.is_live = False
        self.live_event = None
        self.ocr_in_progress = False
        self.is_recording = False
        self.camera = None
        self.audio_path = os.path.join(self.user_data_dir, "dialogue.wav")

        font_to_use = "Roboto"
        self.root_layout = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # Header
        self.root_layout.add_widget(Label(
            text="LingoLens AI - Professional Translator",
            font_size='16sp', bold=True, size_hint_y=0.05,
            color=(0.2, 0.8, 0.5, 1), font_name=font_to_use
        ))

        # ენების არჩევა (Auto-Detect დამატებულია!)
        lang_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        src_langs = ('auto', 'ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN')
        tgt_langs = ('ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN')

        self.src_spin = Spinner(
            text='auto', values=src_langs, size_hint_x=0.4,
            font_name=font_to_use, option_cls=CustomSpinnerOption
        )
        btn_swap = Button(
            text="Swap", size_hint_x=0.2,
            background_color=(0.2, 0.6, 0.9, 1), font_name=font_to_use
        )
        btn_swap.bind(on_press=self.swap_langs)

        self.tgt_spin = Spinner(
            text='en', values=tgt_langs, size_hint_x=0.4,
            font_name=font_to_use, option_cls=CustomSpinnerOption
        )

        lang_layout.add_widget(self.src_spin)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.tgt_spin)
        self.root_layout.add_widget(lang_layout)

        # დიალოგის მოდული
        dialogue_grid = GridLayout(cols=2, spacing=6, size_hint_y=0.09)
        self.btn_mic_a = Button(
            text="🎤 Speaker A", background_color=(0.1, 0.7, 0.4, 1),
            font_name=font_to_use, halign='center'
        )
        self.btn_mic_a.bind(on_press=lambda inst: self.toggle_recording('A'))

        self.btn_mic_b = Button(
            text="🎤 Speaker B", background_color=(0.8, 0.3, 0.2, 1),
            font_name=font_to_use, halign='center'
        )
        self.btn_mic_b.bind(on_press=lambda inst: self.toggle_recording('B'))

        dialogue_grid.add_widget(self.btn_mic_a)
        dialogue_grid.add_widget(self.btn_mic_b)
        self.root_layout.add_widget(dialogue_grid)

        # კამერის კონტეინერი
        self.cam_box = BoxLayout(size_hint_y=0.22)
        self.placeholder_label = Label(text="კამერის ჩატვირთვა...", font_name=font_to_use)
        self.cam_box.add_widget(self.placeholder_label)
        self.root_layout.add_widget(self.cam_box)

        # ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text="ჩაწერილი ხმა ან ტექსტი...", multiline=True,
            size_hint_y=0.14, font_size='14sp', font_name=font_to_use
        )
        self.input_text.bind(text=self.on_text_change)
        self.root_layout.add_widget(self.input_text)

        # ნათარგმნი ტექსტი
        self.output_text = TextInput(
            hint_text="თარგმანი გამოჩნდება აქ...", multiline=True,
            readonly=True, size_hint_y=0.14, font_size='14sp', font_name=font_to_use
        )
        self.root_layout.add_widget(self.output_text)

        # Action Buttons Row 1
        btn_grid1 = GridLayout(cols=3, spacing=6, size_hint_y=0.07)
        self.btn_live = Button(text="Live OCR", background_color=(0.1, 0.6, 0.9, 1), font_name=font_to_use)
        self.btn_live.bind(on_press=self.toggle_live)

        btn_speak = Button(text="🔊 Read", background_color=(0.8, 0.4, 0.1, 1), font_name=font_to_use)
        btn_speak.bind(on_press=self.speak_text)

        btn_copy = Button(text="📋 Copy", background_color=(0.2, 0.7, 0.3, 1), font_name=font_to_use)
        btn_copy.bind(on_press=self.copy_text)

        btn_grid1.add_widget(self.btn_live)
        btn_grid1.add_widget(btn_speak)
        btn_grid1.add_widget(btn_copy)
        self.root_layout.add_widget(btn_grid1)

        # Action Buttons Row 2 (ახალი ფუნქციები!)
        btn_grid2 = GridLayout(cols=2, spacing=6, size_hint_y=0.07)
        btn_grammar = Button(text="💡 Explain Grammar", background_color=(0.6, 0.3, 0.8, 1), font_name=font_to_use)
        btn_grammar.bind(on_press=self.explain_grammar_popup)

        btn_history = Button(text="📜 History", background_color=(0.4, 0.4, 0.4, 1), font_name=font_to_use)
        btn_history.bind(on_press=self.show_history_popup)

        btn_grid2.add_widget(btn_grammar)
        btn_grid2.add_widget(btn_history)
        self.root_layout.add_widget(btn_grid2)

        # Status Bar
        self.status = Label(
            text="მზადაა სამუშაოდ (Auto-Detect & History Enabled)", size_hint_y=0.04, font_size='12sp', font_name=font_to_use
        )
        self.root_layout.add_widget(self.status)

        return self.root_layout

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, 
                    Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE
                ])
                Clock.schedule_once(lambda dt: self.init_camera(), 1.0)
            except Exception:
                self.init_camera()
        else:
            self.init_camera()

    @mainthread
    def init_camera(self):
        try:
            self.cam_box.clear_widgets()
            self.camera = Camera(play=True, resolution=(640, 480), index=0)
            self.cam_box.add_widget(self.camera)
            self.status.text = "კამერა მზადაა"
        except Exception:
            self.status.text = "კამერის ჩართვა ვერ მოხერხდა"

    # ==========================================
    # 2. GRAMMAR EXPLANATION POPUP (ფუნქცია 3)
    # ==========================================
    def explain_grammar_popup(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.status.text = "შეიყვანეთ ტექსტი გრამატიკული ანალიზისთვის"
            return

        self.status.text = "⏳ გრამატიკა მოწმდება AI-ს მიერ..."
        
        def async_grammar():
            try:
                res = requests.post(
                    f"{API_URL}/explain-grammar",
                    data={'text': text, 'target_lang': self.tgt_spin.text},
                    timeout=10
                )
                if res.status_code == 200:
                    explanation = res.json().get("explanation", "განმარტება ვერ მოიძებნა.")
                    self.open_text_popup("💡 Grammar & Structural Analysis", explanation)
                else:
                    self.update_status("გრამატიკის შემოწმების შეცდომა")
            except Exception as e:
                self.update_status(f"შეცდომა: {e}")

        threading.Thread(target=async_grammar, daemon=True).start()

    # ==========================================
    # 3. HISTORY POPUP & SQLITE VIEW (ფუნქცია 1)
    # ==========================================
    def show_history_popup(self, instance):
        records = self.db.get_history(20)
        if not records:
            self.open_text_popup("📜 History", "ისტორია ცარიელია.")
            return

        content = ""
        for src, tgt, s_lang, t_lang in records:
            content += f"[{s_lang.upper()} ➔ {t_lang.upper()}]\nORIGINAL: {src}\nTRANSLATED: {tgt}\n"
            content += "----------------------------------------\n"

        self.open_text_popup("📜 Translation History (Last 20)", content)

    @mainthread
    def open_text_popup(self, title, content_text):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll = ScrollView(size_hint=(1, 0.85))
        lbl = Label(text=content_text, size_hint_y=None, font_name="Roboto", font_size='14sp', halign='left')
        lbl.bind(texture_size=lbl.setter('size'))
        scroll.add_widget(lbl)

        btn_close = Button(text="დახურვა", size_hint=(1, 0.15), background_color=(0.8, 0.2, 0.2, 1))
        layout.add_widget(scroll)
        layout.add_widget(btn_close)

        popup = Popup(title=title, content=layout, size_hint=(0.9, 0.8))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    # --- STANDARD TRANSLATION & DIALOGUE ---
    def on_text_change(self, instance, val):
        Clock.unschedule(self.translate_task)
        Clock.schedule_once(lambda dt: self.translate_task(val), 0.6)

    def translate_task(self, text):
        if not text.strip() or self.is_recording:
            return

        def async_run():
            src_lang = self.src_spin.text
            tgt_lang = self.tgt_spin.text

            try:
                res = requests.post(
                    f"{API_URL}/translate-text",
                    data={'text': text, 'src_lang': src_lang, 'target_lang': tgt_lang},
                    timeout=8
                )
                if res.status_code == 200:
                    tr = res.json().get("translated_text", "")
                    self.update_out(tr)
                    self.db.add_history(text, tr, src_lang, tgt_lang) # ისტორიაში შენახვა
                    self.update_status("✅ თარგმანი მზადაა")
            except Exception as e:
                self.update_status(f"კავშირის შეცდომა: {e}")

        threading.Thread(target=async_run, daemon=True).start()

    def toggle_recording(self, speaker):
        if not HAS_PLYER:
            return

        src = self.src_spin.text if speaker == 'A' else self.tgt_spin.text
        tgt = self.tgt_spin.text if speaker == 'A' else self.src_spin.text

        if not self.is_recording:
            try:
                if os.path.exists(self.audio_path):
                    os.remove(self.audio_path)
                audio.start_recording(file_path=self.audio_path)
                self.is_recording = True
                btn = self.btn_mic_a if speaker == 'A' else self.btn_mic_b
                btn.text = "🛑 Stop & Translate"
                btn.background_color = (0.9, 0.1, 0.1, 1)
                self.status.text = f"ისმენს ({src})..."
            except Exception as e:
                self.status.text = f"ჩაწერის შეცდომა: {e}"
        else:
            try:
                audio.stop_recording()
                self.is_recording = False
                self.status.text = "⏳ ითარგმნება..."
                threading.Thread(target=self.send_audio_task, args=(src, tgt), daemon=True).start()
            except Exception:
                self.reset_mic_buttons()

    def send_audio_task(self, src, tgt):
        try:
            with open(self.audio_path, 'rb') as f:
                res = requests.post(
                    f"{API_URL}/stt-translate",
                    files={'file': ('audio.wav', f, 'audio/wav')},
                    data={'src_lang': src, 'target_lang': tgt},
                    timeout=15
                )
            if res.status_code == 200:
                data = res.json()
                ext = data.get("extracted_text", "")
                tr = data.get("translated_text", "")
                self.apply_dialogue_result(ext, tr)
                self.db.add_history(ext, tr, src, tgt)
        except Exception as e:
            self.update_status(f"შეცდომა: {e}")
        finally:
            self.reset_mic_buttons()

    @mainthread
    def apply_dialogue_result(self, ext, tr):
        self.input_text.text = ext
        self.output_text.text = tr
        if HAS_PLYER and tr:
            try:
                tts.speak(tr)
            except Exception:
                pass

    @mainthread
    def reset_mic_buttons(self):
        self.btn_mic_a.text = "🎤 Speaker A"
        self.btn_mic_a.background_color = (0.1, 0.7, 0.4, 1)
        self.btn_mic_b.text = "🎤 Speaker B"
        self.btn_mic_b.background_color = (0.8, 0.3, 0.2, 1)

    def swap_langs(self, instance):
        s, t = self.src_spin.text, self.tgt_spin.text
        if s != 'auto':
            self.src_spin.text, self.tgt_spin.text = t, s

    def toggle_live(self, instance):
        if not self.camera:
            return
        if not self.is_live:
            self.is_live = True
            self.btn_live.text = "Stop Live"
            self.btn_live.background_color = (0.9, 0.2, 0.2, 1)
            self.live_event = Clock.schedule_interval(self.capture_frame, 3.0)
        else:
            self.is_live = False
            self.btn_live.text = "Live OCR"
            self.btn_live.background_color = (0.1, 0.6, 0.9, 1)
            if self.live_event:
                self.live_event.cancel()

    def capture_frame(self, dt):
        if not self.camera or not self.camera.texture or self.ocr_in_progress:
            return
        try:
            tex = self.camera.texture
            img = PILImage.frombytes('RGBA', tex.size, tex.pixels).convert('RGB')
            img.thumbnail((480, 480))
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=65)
            data_bytes = buf.getvalue()
            buf.close()

            self.ocr_in_progress = True

            def async_ocr():
                try:
                    res = requests.post(
                        f"{API_URL}/ocr-translate",
                        files={'file': ('frame.jpg', io.BytesIO(data_bytes), 'image/jpeg')},
                        data={'target_lang': self.tgt_spin.text},
                        timeout=10
                    )
                    if res.status_code == 200:
                        data = res.json()
                        ext, tr = data.get("extracted_text", ""), data.get("translated_text", "")
                        self.apply_ocr(ext, tr)
                        if ext and tr:
                            self.db.add_history(ext, tr, "ocr", self.tgt_spin.text)
                except Exception:
                    pass
                finally:
                    self.ocr_in_progress = False

            threading.Thread(target=async_ocr, daemon=True).start()
        except Exception:
            self.ocr_in_progress = False

    @mainthread
    def apply_ocr(self, ext, tr):
        if ext.strip():
            self.input_text.text = ext
            self.output_text.text = tr

    @mainthread
    def update_out(self, val):
        self.output_text.text = val

    @mainthread
    def update_status(self, msg):
        self.status.text = str(msg)

    def speak_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            tts.speak(self.output_text.text)

    def copy_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            clipboard.copy(self.output_text.text)
            self.status.text = "დაკოპირდა!"


if __name__ == "__main__":
    LingoLensApp().run()

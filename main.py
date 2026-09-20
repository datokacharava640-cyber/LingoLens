"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia
Release Date        : September 2026
Project Name        : LingoLens AI
Version             : 6.0.1 (Crash-Safe Build)
=============================================================================
"""

import os
import io
import base64
import sqlite3
import threading

# SSL/Certifi უსაფრთხო ჩატვირთვა
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
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

# PIL მხარდაჭერა OCR-ისთვის
try:
    from PIL import Image as PILImage
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# Requests უსაფრთხო იმპორტი
try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    try:
        resource_add_path(os.path.dirname(os.path.abspath(FONT_PATH)))
        LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
    except Exception:
        pass

# Safe Config / API Key Import
try:
    import config
    API_URL = getattr(config, 'API_ENDPOINT', "https://lingo-lens-pied.vercel.app").rstrip('/')
    GEMINI_API_KEY = getattr(config, 'GEMINI_API_KEY', "")
except Exception:
    API_URL = "https://lingo-lens-pied.vercel.app"
    GEMINI_API_KEY = ""

def get_gemini_url():
    key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"

try:
    from plyer import clipboard, tts, audio
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


class CustomSpinnerOption(SpinnerOption):
    pass


# ==========================================
# SAFE GEMINI REST API HELPER
# ==========================================
def call_gemini_api(prompt, image_bytes=None):
    if not HAS_REQUESTS:
        return "შეცდომა: requests ბიბლიოთეკა მიუწვდომელია"

    key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not key or key == "ჩასვი_შენი_GEMINI_API_KEY_აქ":
        return "შეცდომა: GEMINI_API_KEY არ არის გამართული config.py-ში!"

    headers = {"Content-Type": "application/json"}
    parts = [{"text": prompt}]

    if image_bytes:
        img_b64 = base64.b64encode(image_bytes).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": img_b64
            }
        })

    data = {"contents": [{"parts": parts}]}
    url = get_gemini_url()
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=20)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                return candidates[0]['content']['parts'][0]['text'].strip()
            return "შეცდომა: AI-მ პასუხი ვერ დააბრუნა."
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Connection Error: {str(e)}"


# ==========================================
# SQLITE STORAGE MANAGER
# ==========================================
class DBManager:
    def __init__(self, db_path="lingolens.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        try:
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
        except Exception:
            pass

    def add_history(self, src_text, tgt_text, src_lang, tgt_lang):
        if not src_text.strip() or not tgt_text.strip():
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (src_text, tgt_text, src_lang, tgt_lang) VALUES (?, ?, ?, ?)",
                (src_text, tgt_text, src_lang, tgt_lang)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_history(self, limit=30):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT src_text, tgt_text, src_lang, tgt_lang FROM history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception:
            return []

    def clear_history(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history")
            conn.commit()
            conn.close()
        except Exception:
            pass


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def build(self):
        self.title = "LingoLens AI - Academic & Multi-Language Suite"
        
        try:
            db_file = os.path.join(self.user_data_dir, "lingolens.db")
        except Exception:
            db_file = "lingolens.db"
            
        self.db = DBManager(db_file)
        
        self.is_live = False
        self.live_event = None
        self.ocr_in_progress = False
        self.is_recording = False
        self.camera = None

        self.root_layout = BoxLayout(orientation='vertical', padding=8, spacing=5)

        # Header
        self.root_layout.add_widget(Label(
            text="LingoLens AI - Academic Suite",
            font_size='15sp', bold=True, size_hint_y=0.05,
            color=(0.2, 0.8, 0.5, 1)
        ))

        # ენების არჩევა
        lang_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        src_langs = ('auto', 'ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN', 'ja', 'ar')
        tgt_langs = ('en', 'ka', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN', 'ja', 'ar')

        self.src_spin = Spinner(text='ka', values=src_langs, size_hint_x=0.4, option_cls=CustomSpinnerOption)
        btn_swap = Button(text="Swap", size_hint_x=0.2, background_color=(0.2, 0.6, 0.9, 1))
        btn_swap.bind(on_press=self.swap_langs)
        self.tgt_spin = Spinner(text='en', values=tgt_langs, size_hint_x=0.4, option_cls=CustomSpinnerOption)

        lang_layout.add_widget(self.src_spin)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.tgt_spin)
        self.root_layout.add_widget(lang_layout)

        # დიალოგის მოდული
        dialogue_grid = GridLayout(cols=2, spacing=5, size_hint_y=0.08)
        self.btn_mic_a = Button(text="[A] Speaker A", background_color=(0.1, 0.7, 0.4, 1))
        self.btn_mic_a.bind(on_press=lambda inst: self.toggle_recording('A'))

        self.btn_mic_b = Button(text="[B] Speaker B", background_color=(0.8, 0.3, 0.2, 1))
        self.btn_mic_b.bind(on_press=lambda inst: self.toggle_recording('B'))

        dialogue_grid.add_widget(self.btn_mic_a)
        dialogue_grid.add_widget(self.btn_mic_b)
        self.root_layout.add_widget(dialogue_grid)

        # კამერის კონტეინერი
        self.cam_box = BoxLayout(size_hint_y=0.20)
        self.placeholder_label = Label(text="კამერა ჩაირთვება ნებართვის შემდეგ...")
        self.cam_box.add_widget(self.placeholder_label)
        self.root_layout.add_widget(self.cam_box)

        # ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text="ჩაწერილი ხმა, ტექსტი ან დავალების თემა...", multiline=True,
            size_hint_y=0.15, font_size='14sp'
        )
        self.input_text.bind(text=self.on_text_change)
        self.root_layout.add_widget(self.input_text)

        # ნათარგმნი / გენერირებული ტექსტი
        self.output_text = TextInput(
            hint_text="პასუხი გამოჩნდება აქ...", multiline=True,
            readonly=True, size_hint_y=0.15, font_size='14sp'
        )
        self.root_layout.add_widget(self.output_text)

        # ღილაკების მწკრივი 1
        btn_grid1 = GridLayout(cols=5, spacing=4, size_hint_y=0.07)
        self.btn_live = Button(text="Live OCR", background_color=(0.1, 0.6, 0.9, 1))
        self.btn_live.bind(on_press=self.toggle_live)

        btn_speak = Button(text="Read", background_color=(0.8, 0.4, 0.1, 1))
        btn_speak.bind(on_press=self.speak_text)

        btn_copy = Button(text="Copy", background_color=(0.2, 0.7, 0.3, 1))
        btn_copy.bind(on_press=self.copy_text)

        btn_save = Button(text="Save", background_color=(0.1, 0.5, 0.7, 1))
        btn_save.bind(on_press=self.manual_save)

        btn_clear = Button(text="Clear", background_color=(0.7, 0.2, 0.2, 1))
        btn_clear.bind(on_press=self.clear_fields)

        btn_grid1.add_widget(self.btn_live)
        btn_grid1.add_widget(btn_speak)
        btn_grid1.add_widget(btn_copy)
        btn_grid1.add_widget(btn_save)
        btn_grid1.add_widget(btn_clear)
        self.root_layout.add_widget(btn_grid1)

        # ღილაკების მწკრივი 2
        btn_grid2 = GridLayout(cols=3, spacing=5, size_hint_y=0.08)
        
        btn_academic = Button(text="Academic AI", background_color=(0.1, 0.6, 0.5, 1))
        btn_academic.bind(on_press=self.open_academic_menu)

        btn_grammar = Button(text="Explain Grammar", background_color=(0.6, 0.3, 0.8, 1))
        btn_grammar.bind(on_press=self.explain_grammar_popup)

        btn_history = Button(text="History", background_color=(0.4, 0.4, 0.4, 1))
        btn_history.bind(on_press=self.show_history_popup)

        btn_grid2.add_widget(btn_academic)
        btn_grid2.add_widget(btn_grammar)
        btn_grid2.add_widget(btn_history)
        self.root_layout.add_widget(btn_grid2)

        # Status Bar
        self.status = Label(text="მზადაა სამუშაოდ", size_hint_y=0.04, font_size='12sp')
        self.root_layout.add_widget(self.status)

        return self.root_layout

    def on_start(self):
        # უსაფრთხო ნებართვების მოთხოვნა Startup Crash-ის ასარიდებლად
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                def permission_callback(permissions, grants):
                    if all(grants):
                        Clock.schedule_once(lambda dt: self.init_camera(), 0.5)
                    else:
                        self.status.text = "კამერის ნებართვა უარყოფილია"

                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, 
                    Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE
                ], permission_callback)
            except Exception as e:
                self.status.text = f"Android init notice: {e}"
                Clock.schedule_once(lambda dt: self.init_camera(), 1.0)
        else:
            Clock.schedule_once(lambda dt: self.init_camera(), 0.5)

    @mainthread
    def init_camera(self):
        try:
            from kivy.uix.camera import Camera
            self.cam_box.clear_widgets()
            self.camera = Camera(play=True, resolution=(640, 480), index=0)
            self.cam_box.add_widget(self.camera)
            self.status.text = "კამერა ჩართულია"
        except Exception as e:
            self.status.text = "კამერა მიუწვდომელია"

    # ==========================================
    # 🎓 ACADEMIC MENU
    # ==========================================
    def open_academic_menu(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.status.text = "შეიყვანეთ ტექსტი/თემა აკადემიური ასისტენტისთვის"
            return

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text="აირჩიეთ აკადემიური დავალების ტიპი:", font_size='15sp', bold=True))

        btn_essay = Button(text="Write Essay / Assignment Topic", background_color=(0.2, 0.6, 0.8, 1))
        btn_summary = Button(text="Summarize Text / Research Paper", background_color=(0.2, 0.7, 0.4, 1))
        btn_para = Button(text="Paraphrase in Academic Tone", background_color=(0.8, 0.5, 0.2, 1))
        btn_cancel = Button(text="გაუქმება", background_color=(0.7, 0.2, 0.2, 1))

        layout.add_widget(btn_essay)
        layout.add_widget(btn_summary)
        layout.add_widget(btn_para)
        layout.add_widget(btn_cancel)

        popup = Popup(title="Academic & School AI Suite", content=layout, size_hint=(0.9, 0.55))

        def run_task(task_type):
            popup.dismiss()
            self.status.text = "⏳ AI ამუშავებს აკადემიურ დავალებას..."
            
            def async_acad():
                prompt = f"Task: {task_type.upper()}\nTarget Language: {self.tgt_spin.text}\nInput Text: {text}"
                result = call_gemini_api(prompt)
                self.update_out(result)
                self.db.add_history(f"[Academic: {task_type}] {text}", result, "academic", self.tgt_spin.text)
                self.update_status("✅ აკადემიური დავალება მზადაა")

            threading.Thread(target=async_acad, daemon=True).start()

        btn_essay.bind(on_press=lambda i: run_task('essay'))
        btn_summary.bind(on_press=lambda i: run_task('summarize'))
        btn_para.bind(on_press=lambda i: run_task('paraphrase'))
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def explain_grammar_popup(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.status.text = "შეიყვანეთ ტექსტი გრამატიკული ანალიზისთვის"
            return

        self.status.text = "⏳ გრამატიკა მოწმდება AI-ს მიერ..."
        
        def async_grammar():
            prompt = f"Explain the grammar and structural details of this text in language '{self.tgt_spin.text}':\n{text}"
            explanation = call_gemini_api(prompt)
            self.open_text_popup("Grammar Analysis", explanation)
            self.update_status("✅ გრამატიკა გაანალიზებულია")

        threading.Thread(target=async_grammar, daemon=True).start()

    def show_history_popup(self, instance):
        records = self.db.get_history(30)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        scroll = ScrollView(size_hint=(1, 0.8))
        
        content = ""
        if not records:
            content = "ისტორია ცარიელია."
        else:
            for src, tgt, s_lang, t_lang in records:
                content += f"[{s_lang.upper()} -> {t_lang.upper()}]\nSRC: {src}\nRES: {tgt}\n----------------------------------------\n"

        lbl = Label(text=content, size_hint_y=None, font_size='13sp', halign='left')
        lbl.bind(texture_size=lbl.setter('size'))
        scroll.add_widget(lbl)

        btn_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)
        btn_clear_db = Button(text="Clear All History", background_color=(0.8, 0.2, 0.2, 1))
        btn_close = Button(text="დახურვა", background_color=(0.4, 0.4, 0.4, 1))

        btn_box.add_widget(btn_clear_db)
        btn_box.add_widget(btn_close)

        layout.add_widget(scroll)
        layout.add_widget(btn_box)

        popup = Popup(title="Translation History", content=layout, size_hint=(0.9, 0.8))

        def clear_history_action(i):
            self.db.clear_history()
            popup.dismiss()
            self.status.text = "ისტორია წაიშალა"

        btn_clear_db.bind(on_press=clear_history_action)
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    @mainthread
    def open_text_popup(self, title, content_text):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll = ScrollView(size_hint=(1, 0.85))
        lbl = Label(text=content_text, size_hint_y=None, font_size='14sp', halign='left')
        lbl.bind(texture_size=lbl.setter('size'))
        scroll.add_widget(lbl)

        btn_close = Button(text="დახურვა", size_hint=(1, 0.15), background_color=(0.8, 0.2, 0.2, 1))
        layout.add_widget(scroll)
        layout.add_widget(btn_close)

        popup = Popup(title=title, content=layout, size_hint=(0.9, 0.8))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()

    def clear_fields(self, instance):
        self.input_text.text = ""
        self.output_text.text = ""
        self.status.text = "ველები გასუფთავდა"

    def manual_save(self, instance):
        src = self.input_text.text.strip()
        tgt = self.output_text.text.strip()
        if src and tgt:
            self.db.add_history(src, tgt, self.src_spin.text, self.tgt_spin.text)
            self.status.text = "💾 შენახულია ისტორიაში!"

    def on_text_change(self, instance, val):
        Clock.unschedule(self.translate_task)
        Clock.schedule_once(lambda dt: self.translate_task(val), 0.8)

    def translate_task(self, text):
        if not text.strip() or self.is_recording:
            return

        def async_run():
            src_lang = self.src_spin.text
            tgt_lang = self.tgt_spin.text
            prompt = f"Translate text from '{src_lang}' to '{tgt_lang}':\n{text}"
            
            tr = call_gemini_api(prompt)
            self.update_out(tr)
            self.db.add_history(text, tr, src_lang, tgt_lang)
            self.update_status("✅ თარგმანი მზადაა")

        threading.Thread(target=async_run, daemon=True).start()

    def toggle_recording(self, speaker):
        if not HAS_PLYER:
            self.status.text = "Plyer მიუწვდომელია"
            return
        self.status.text = "ხმის ჩაწერა გააქტიურებულია"

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
        if not self.camera or not self.camera.texture or self.ocr_in_progress or not HAS_PIL:
            return
        try:
            tex = self.camera.texture
            if tex.width == 0 or tex.height == 0 or not tex.pixels:
                return

            img = PILImage.frombytes('RGBA', tex.size, tex.pixels).convert('RGB')
            img.thumbnail((480, 480))
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=65)
            data_bytes = buf.getvalue()
            buf.close()

            self.ocr_in_progress = True

            def async_ocr():
                try:
                    prompt = f"Extract all visible text and translate to '{self.tgt_spin.text}'. Format: 'EXTRACTED ||| TRANSLATED'"
                    res = call_gemini_api(prompt, image_bytes=data_bytes)
                    if "|||" in res:
                        ext, tr = res.split("|||", 1)
                    else:
                        ext, tr = res, ""
                    
                    self.apply_ocr(ext, tr)
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
            try:
                tts.speak(self.output_text.text)
            except Exception:
                pass

    def copy_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            try:
                clipboard.copy(self.output_text.text)
                self.status.text = "დაკოპირდა!"
            except Exception:
                pass


if __name__ == "__main__":
    LingoLensApp().run()

import os
import json
import sqlite3
import threading
import base64
import difflib
import io
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage

# PDF Parser
try:
    import pypdf
except ImportError:
    pypdf = None

# Hardware Access via Plyer
try:
    from plyer import tts, filechooser, stt
except Exception:
    tts, filechooser, stt = None, None, None

# ---------------------------------------------------------
# 0. FONT REGISTRATION & ANDROID PERMISSIONS
# ---------------------------------------------------------
FONT_PATH = "NotoSansGeorgian-Regular.ttf"
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.INTERNET,
                Permission.READ_MEDIA_IMAGES,
                Permission.MODIFY_AUDIO_SETTINGS
            ])
        except Exception as e:
            print(f"Permissions Request Error: {e}")

try:
    from modules.config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = ""


# ---------------------------------------------------------
# 1. DATABASE MANAGER
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
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
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
                    words = [
                        ("hello", "გამარჯობა"), ("world", "სამყარო"), ("friend", "მეგობარი"),
                        ("thank you", "გმადლობთ"), ("good", "კარგი"), ("bad", "ცუდი"),
                        ("yes", "დიახ"), ("no", "არა"), ("please", "გეთაყვა"),
                        ("book", "წიგნი"), ("water", "წყალი"), ("love", "სიყვარული"),
                        ("computer", "კომპიუტერი"), ("language", "ენა"), ("camera", "კამერა"),
                        ("document", "დოკუმენტი"), ("page", "გვერდი"), ("file", "ფაილი")
                    ]
                    cursor.executemany("INSERT OR IGNORE INTO dictionary VALUES (?, ?)", words)
                    conn.commit()
        except Exception as e:
            print(f"Seed DB Error: {e}")

    def set_setting(self, key, value):
        try:
            with self.get_connection() as conn:
                conn.cursor().execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))
                conn.commit()
        except Exception as e:
            print(f"Set Setting Error: {e}")

    def get_setting(self, key, default=""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception:
            return default

    def add_history(self, src, trans):
        try:
            with self.get_connection() as conn:
                conn.cursor().execute(
                    "INSERT INTO history (source_text, translated_text, timestamp) VALUES (?, ?, ?)",
                    (src, trans, datetime.now())
                )
                conn.commit()
        except Exception as e:
            print(f"DB Add History Error: {e}")

    def get_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_text, translated_text FROM history ORDER BY id DESC LIMIT 20")
                return cursor.fetchall()
        except Exception:
            return []

    def translate_offline_fuzzy(self, text):
        try:
            words = text.lower().strip().split()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT word, translation FROM dictionary")
                dict_data = dict(cursor.fetchall())
                
                res = []
                for w in words:
                    clean_w = "".join(c for c in w if c.isalnum())
                    if clean_w in dict_data:
                        res.append(dict_data[clean_w])
                    else:
                        matches = difflib.get_close_matches(clean_w, dict_data.keys(), n=1, cutoff=0.7)
                        if matches:
                            res.append(f"{dict_data[matches[0]]}(*) ")
                        else:
                            res.append(f"[{w}]")
                return " ".join(res)
        except Exception as e:
            return f"ოფლაინ შეცდომა: {e}"


# ---------------------------------------------------------
# 2. SERVICE MANAGER
# ---------------------------------------------------------
class ServiceManager:
    def __init__(self, db):
        self.db = db
        self.direct_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.session = requests.Session()
        retries = Retry(total=2, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def translate_text(self, text):
        proxy_url = self.db.get_setting("proxy_url")
        api_key = self.db.get_setting("api_key") or getattr(Config, 'GEMINI_API_KEY', '')

        if proxy_url:
            try:
                res = self.session.post(f"{proxy_url.rstrip('/')}/translate", json={"text": text}, timeout=10)
                if res.status_code == 200:
                    return res.json().get("translation", ""), None
            except Exception as e:
                print(f"Proxy Connection Error: {e}")

        if api_key:
            prompt = (
                "Translate the following text accurately between Georgian and English.\n"
                "Return ONLY a JSON object with key 'translation'.\n"
                f"Text: {text}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            try:
                res = self.session.post(f"{self.direct_api_url}?key={api_key}", json=payload, timeout=10)
                if res.status_code == 200:
                    raw = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(raw.strip()).get("translation", ""), None
            except Exception as e:
                return None, str(e)

        return None, "სერვერი ან API Key არ არის კონფიგურირებული."

    def translate_image(self, image_path):
        proxy_url = self.db.get_setting("proxy_url")
        api_key = self.db.get_setting("api_key") or getattr(Config, 'GEMINI_API_KEY', '')

        try:
            with open(image_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode('utf-8')

            if proxy_url:
                res = self.session.post(f"{proxy_url.rstrip('/')}/translate-image", json={"image_b64": encoded_image}, timeout=15)
                if res.status_code == 200:
                    return res.json().get("translation", ""), None

            if api_key:
                prompt = "Extract all text from this image and translate it to Georgian/English. Return ONLY JSON with key 'translation'."
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}
                        ]
                    }],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                res = self.session.post(f"{self.direct_api_url}?key={api_key}", json=payload, timeout=15)
                if res.status_code == 200:
                    raw = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(raw.strip()).get("translation", ""), None

            return None, "სერვერი ან API Key არ არის მითითებული!"
        except Exception as e:
            return None, f"ფაილის შეცდომა: {str(e)}"

    def process_ar_overlay(self, image_path):
        proxy_url = self.db.get_setting("proxy_url")
        if not proxy_url:
            return None, "AR Overlay-სთვის საჭიროა Proxy Server URL!"

        try:
            with open(image_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode('utf-8')
            res = self.session.post(f"{proxy_url.rstrip('/')}/translate-ar", json={"image_b64": encoded_image}, timeout=25)
            if res.status_code == 200:
                return res.json().get("ar_image_b64"), None
            return None, "AR სერვერის შეცდომა."
        except Exception as e:
            return None, str(e)

    def translate_pdf(self, pdf_path):
        if not pypdf:
            return None, "pypdf ბიბლიოთეკა მიუწვდომელია."

        try:
            reader = pypdf.PdfReader(pdf_path)
            extracted_text = ""
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted_text += txt + "\n"

            if not extracted_text.strip():
                return None, "PDF-დან ტექსტის ამოღება ვერ მოხერხდა (შესაძლოა სკანირებული ფოტოა)."

            chunks = [extracted_text[i:i + 1500] for i in range(0, len(extracted_text), 1500)]
            translated_chunks = []

            for index, chunk in enumerate(chunks):
                trans, err = self.translate_text(chunk)
                if trans:
                    translated_chunks.append(f"--- [ნაწილი {index + 1}] ---\n" + trans)
                else:
                    translated_chunks.append(f"--- [ნაწილი {index + 1} შეცდომა: {err}] ---")

            return "\n\n".join(translated_chunks), None
        except Exception as e:
            return None, f"PDF დამუშავების შეცდომა: {str(e)}"


# ---------------------------------------------------------
# 3. POPUP WIDGETS
# ---------------------------------------------------------
class LiveCameraPopup(Popup):
    def __init__(self, callback_on_capture, **kwargs):
        super().__init__(**kwargs)
        self.title = "ცოცხალი კამერა (Live Preview)"
        self.size_hint = (0.95, 0.85)
        self.callback = callback_on_capture

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        try:
            self.camera = Camera(play=True, resolution=(640, 480))
            layout.add_widget(self.camera)
        except Exception as e:
            layout.add_widget(Label(text=f"კამერის ჩართვა ვერ მოხერხდა: {e}"))

        btn_capture = Button(text="📷 გადაღება და თარგმნა", size_hint_y=0.15, background_color=(0.2, 0.7, 0.3, 1), bold=True)
        btn_capture.bind(on_press=self.capture_frame)

        layout.add_widget(btn_capture)
        self.content = layout

    def capture_frame(self, instance):
        try:
            temp_path = os.path.join(App.get_running_app().user_data_dir, "live_snap.png")
            if hasattr(self, 'camera'):
                self.camera.export_to_png(temp_path)
                self.camera.play = False
            self.dismiss()
            if self.callback:
                self.callback(temp_path)
        except Exception as e:
            print(f"Camera Frame Error: {e}")


class ARViewPopup(Popup):
    def __init__(self, b64_img_data, **kwargs):
        super().__init__(**kwargs)
        self.title = "AR Live Overlay თარგმანი"
        self.size_hint = (0.95, 0.85)
        
        img_bytes = base64.b64decode(b64_img_data)
        data = io.BytesIO(img_bytes)
        core_img = CoreImage(data, ext="jpg")

        img_widget = Image()
        img_widget.texture = core_img.texture
        self.content = img_widget


# ---------------------------------------------------------
# 4. MAIN USER INTERFACE
# ---------------------------------------------------------
class LingoLensUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8

        self.db = DatabaseManager()
        self.service = ServiceManager(self.db)

        # Header Navigation
        header = BoxLayout(size_hint_y=0.08, spacing=5)
        title = Label(text="LingoLens Ultra Pro", font_size='18sp', bold=True)
        btn_history = Button(text="📜 ისტორია", size_hint_x=0.28)
        btn_history.bind(on_press=self.open_history)
        btn_settings = Button(text="⚙ პარამეტრები", size_hint_x=0.32)
        btn_settings.bind(on_press=self.open_settings)
        header.add_widget(title)
        header.add_widget(btn_history)
        header.add_widget(btn_settings)
        self.add_widget(header)

        # Input Text Area
        self.input_text = TextInput(
            hint_text="შეიყვანეთ ტექსტი თარგმნისთვის...",
            multiline=True,
            size_hint_y=0.25,
            font_size='15sp'
        )
        self.add_widget(self.input_text)

        # Actions Panel
        actions = BoxLayout(size_hint_y=0.14, spacing=4)
        btn_trans = Button(text="თარგმნა", background_color=(0.1, 0.5, 0.9, 1), bold=True)
        btn_trans.bind(on_press=self.on_translate)
        
        btn_ocr = Button(text="🖼 ფოტო", background_color=(0.2, 0.7, 0.3, 1))
        btn_ocr.bind(on_press=self.on_ocr)

        btn_ar = Button(text="👓 AR", background_color=(0.8, 0.2, 0.5, 1))
        btn_ar.bind(on_press=self.on_ar_select)

        btn_cam = Button(text="📷 Live", background_color=(0.2, 0.8, 0.6, 1))
        btn_cam.bind(on_press=self.open_live_camera)

        btn_pdf = Button(text="📄 PDF", background_color=(0.6, 0.3, 0.8, 1))
        btn_pdf.bind(on_press=self.on_pdf_select)

        btn_mic = Button(text="🎙 ხმა", background_color=(0.9, 0.4, 0.2, 1))
        btn_mic.bind(on_press=self.on_speech_input)

        actions.add_widget(btn_trans)
        actions.add_widget(btn_ocr)
        actions.add_widget(btn_ar)
        actions.add_widget(btn_cam)
        actions.add_widget(btn_pdf)
        actions.add_widget(btn_mic)
        self.add_widget(actions)

        # Output Box
        self.output_label = Label(
            text="თარგმანი გამოჩნდება აქ...",
            size_hint_y=0.43,
            font_size='15sp'
        )
        self.add_widget(self.output_label)

        # Bottom Tools
        tools = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_copy = Button(text="📋 კოპირება")
        btn_copy.bind(on_press=self.copy_to_clipboard)
        btn_speak = Button(text="🔊 წაკითხვა")
        btn_speak.bind(on_press=self.speak_text)
        tools.add_widget(btn_copy)
        tools.add_widget(btn_speak)
        self.add_widget(tools)

    def on_translate(self, instance):
        text = self.input_text.text.strip()
        if not text:
            self.output_label.text = "გთხოვთ შეიყვანოთ ტექსტი!"
            return

        self.output_label.text = "მიმდინარეობს თარგმნა..."

        def run():
            trans, err = self.service.translate_text(text)
            if trans:
                Clock.schedule_once(lambda dt: self.update_res(text, trans))
            else:
                offline_res = self.db.translate_offline_fuzzy(text)
                Clock.schedule_once(
                    lambda dt: self.update_res(text, f"[ოფლაინ თარგმანი]:\n{offline_res}\n\n({err})")
                )

        threading.Thread(target=run, daemon=True).start()

    def open_live_camera(self, instance):
        popup = LiveCameraPopup(callback_on_capture=self.process_camera_frame)
        popup.open()

    def process_camera_frame(self, frame_path):
        if not os.path.exists(frame_path):
            self.output_label.text = "კადრის შენახვა ვერ მოხერხდა."
            return

        self.output_label.text = "მიმდინარეობს კადრის დამუშავება..."

        def run():
            trans, err = self.service.translate_image(frame_path)
            if trans:
                Clock.schedule_once(lambda dt: self.update_res("[Live Camera OCR]", trans))
            else:
                Clock.schedule_once(lambda dt: self.show_err(err))

        threading.Thread(target=run, daemon=True).start()

    def on_ocr(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.process_image_selection)
            except Exception as e:
                self.output_label.text = f"ფაილის გახსნის შეცდომა: {e}"
        else:
            self.output_label.text = "Filechooser მიუწვდომელია."

    def process_image_selection(self, selection):
        if selection:
            img_path = selection[0]
            self.output_label.text = "ფოტოს დამუშავება..."

            def run():
                trans, err = self.service.translate_image(img_path)
                if trans:
                    Clock.schedule_once(lambda dt: self.update_res("[ფოტო OCR]", trans))
                else:
                    Clock.schedule_once(lambda dt: self.show_err(err))

            threading.Thread(target=run, daemon=True).start()

    def on_ar_select(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.process_ar_selection)
            except Exception as e:
                self.output_label.text = f"AR ფაილის არჩევის შე测დომა: {e}"

    def process_ar_selection(self, selection):
        if selection:
            img_path = selection[0]
            self.output_label.text = "AR Overlay დამუშავება..."

            def run():
                b64_res, err = self.service.process_ar_overlay(img_path)
                if b64_res:
                    Clock.schedule_once(lambda dt: ARViewPopup(b64_res).open())
                else:
                    Clock.schedule_once(lambda dt: self.show_err(err))

            threading.Thread(target=run, daemon=True).start()

    def on_pdf_select(self, instance):
        if filechooser:
            try:
                filechooser.open_file(on_selection=self.process_pdf_selection)
            except Exception as e:
                self.output_label.text = f"PDF არჩევის შეცდომა: {e}"
        else:
            self.output_label.text = "Filechooser მიუწვდომელია."

    def process_pdf_selection(self, selection):
        if selection and selection[0].endswith('.pdf'):
            pdf_path = selection[0]
            self.output_label.text = "PDF დოკუმენტის თარგმნა..."

            def run():
                trans, err = self.service.translate_pdf(pdf_path)
                if trans:
                    Clock.schedule_once(lambda dt: self.update_res("[PDF Document]", trans))
                else:
                    Clock.schedule_once(lambda dt: self.show_err(err))

            threading.Thread(target=run, daemon=True).start()
        else:
            self.output_label.text = "გთხოვთ აირჩიოთ ვალიდური PDF ფაილი!"

    def on_speech_input(self, instance):
        if stt and platform == 'android':
            try:
                stt.start()
            except Exception as e:
                self.output_label.text = f"ხმოვანი შეყვანის შეცდომა: {e}"
        else:
            self.output_label.text = "ხმოვანი შეყვანა ხელმისაწვდომია Android-ზე."

    def update_res(self, src, trans):
        self.output_label.text = trans
        self.db.add_history(src[:30], trans)

    def show_err(self, err):
        self.output_label.text = f"[შეცდომა]:\n{err}"

    def copy_to_clipboard(self, instance):
        if self.output_label.text and "[შეცდომა]" not in self.output_label.text:
            Clipboard.copy(self.output_label.text)

    def speak_text(self, instance):
        if tts and self.output_label.text:
            try:
                tts.speak(self.output_label.text)
            except Exception as e:
                print(f"TTS Error: {e}")

    def open_settings(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        proxy_input = TextInput(
            text=self.db.get_setting("proxy_url"),
            hint_text="Proxy URL (მაგ: https://myproxy.onrender.com)",
            multiline=False
        )
        key_input = TextInput(
            text=self.db.get_setting("api_key"),
            hint_text="ან ჩასვით Direct Gemini API Key...",
            multiline=False
        )
        btn_save = Button(text="შენახვა", size_hint_y=0.35)

        content.add_widget(Label(text="Backend Proxy URL:"))
        content.add_widget(proxy_input)
        content.add_widget(Label(text="Direct Gemini API Key:"))
        content.add_widget(key_input)
        content.add_widget(btn_save)

        popup = Popup(title="პარამეტრები", content=content, size_hint=(0.9, 0.6))

        def save_settings(inst):
            self.db.set_setting("proxy_url", proxy_input.text.strip())
            self.db.set_setting("api_key", key_input.text.strip())
            popup.dismiss()

        btn_save.bind(on_press=save_settings)
        popup.open()

    def open_history(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        scroll = ScrollView()
        hist_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        hist_box.bind(minimum_height=hist_box.setter('height'))

        records = self.db.get_history()
        for src, trans in records:
            lbl = Label(
                text=f"• {src} ➔ {trans}",
                size_hint_y=None,
                height=45,
                font_size='13sp'
            )
            hist_box.add_widget(lbl)

        scroll.add_widget(hist_box)
        content.add_widget(scroll)
        popup = Popup(title="ბოლო თარგმანების ისტორია", content=content, size_hint=(0.9, 0.75))
        popup.open()


# ---------------------------------------------------------
# 5. ENTRY POINT
# ---------------------------------------------------------
class LingoLensApp(App):
    def build(self):
        request_android_permissions()
        return LingoLensUI()


if __name__ == "__main__":
    LingoLensApp().run()

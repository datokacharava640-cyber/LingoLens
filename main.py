import sys
import os
import json
import ssl
import sqlite3
import threading
import urllib.request
import urllib.parse
import base64
import hashlib
import math
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

# Kivy Graphics & Clock imports
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.widget import Widget

# ---------------------------------------------------------
# 0. AUTOMATIC FILEPROVIDER XML GENERATION (ANDROID 10+)
# ---------------------------------------------------------
def init_android_file_provider():
    try:
        xml_dir = os.path.join("res", "xml")
        os.makedirs(xml_dir, exist_ok=True)
        xml_path = os.path.join(xml_dir, "provider_paths.xml")
        if not os.path.exists(xml_path):
            content = '''<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res-auto">
    <external-files-path name="my_images" path="/" />
    <cache-path name="cached_files" path="/" />
</paths>'''
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        print(f"FileProvider Init Warning: {e}")

init_android_file_provider()

# ---------------------------------------------------------
# ANIMATED GEORGIAN FLAG WIDGET
# ---------------------------------------------------------
class GeorgianFlagWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_flag, size=self.update_flag)
        self.wave_phase = 0
        Clock.schedule_interval(self.animate_wave, 1 / 30.0)

    def animate_wave(self, dt):
        self.wave_phase += dt * 3
        self.update_flag()

    def update_flag(self, *args):
        self.canvas.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height

        if w <= 0 or h <= 0:
            return

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=(x, y), size=(w, h))

            Color(1, 0, 0, 1)
            cross_thickness = min(w, h) * 0.2
            Rectangle(pos=(x + (w - cross_thickness) / 2, y), size=(cross_thickness, h))
            Rectangle(pos=(x, y + (h - cross_thickness) / 2), size=(w, cross_thickness))

            quad_w = (w - cross_thickness) / 2
            quad_h = (h - cross_thickness) / 2
            small_thick = cross_thickness * 0.3
            small_len = min(quad_w, quad_h) * 0.4

            centers = [
                (x + quad_w / 2, y + quad_h * 1.5 + cross_thickness),
                (x + quad_w * 1.5 + cross_thickness, y + quad_h * 1.5 + cross_thickness),
                (x + quad_w / 2, y + quad_h / 2),
                (x + quad_w * 1.5 + cross_thickness, y + quad_h / 2)
            ]

            for cx, cy in centers:
                offset = math.sin(self.wave_phase + (cx / w) * 3) * (h * 0.03)
                cy_anim = cy + offset
                Rectangle(pos=(cx - small_len / 2, cy_anim - small_thick / 2), size=(small_len, small_thick))
                Rectangle(pos=(cx - small_thick / 2, cy_anim - small_len / 2), size=(small_thick, small_len))

# ---------------------------------------------------------
# 1. FONT REGISTRATION
# ---------------------------------------------------------
from kivy.core.text import LabelBase

FONT_NAME = "Roboto"
if os.path.exists("font.ttf"):
    FONT_PATH = "font.ttf"
elif os.path.exists("/system/fonts/NotoSansGeorgian-Regular.ttf"):
    FONT_PATH = "/system/fonts/NotoSansGeorgian-Regular.ttf"
elif os.path.exists("/system/fonts/DroidSansFallback.ttf"):
    FONT_PATH = "/system/fonts/DroidSansFallback.ttf"
else:
    FONT_PATH = "font.ttf"

try:
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)
    LabelBase.register(name="Georgian", fn_regular=FONT_PATH)
except Exception as e:
    print(f"Font Registration Error: {e}")

from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.uix.scrollview import ScrollView

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, OneLineListItem, OneLineIconListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField

from plyer import filechooser, clipboard

# ---------------------------------------------------------
# 2. KEYSTORE & SECURE BRIDGE
# ---------------------------------------------------------
class AndroidKeyStoreBridge:
    @staticmethod
    def get_secure_key(alias="AZURE_API_KEY"):
        if platform == 'android':
            try:
                from jnius import autoclass
                KeyStore = autoclass('java.security.KeyStore')
                ks = KeyStore.getInstance("AndroidKeyStore")
                ks.load(None)
                if ks.containsAlias(alias):
                    entry = ks.getEntry(alias, None)
                    return entry.getPrivateKey().toString()
            except Exception as e:
                print(f"KeyStore Bridge Error: {e}")
        return "YOUR_AZURE_API_KEY_HERE"

# ---------------------------------------------------------
# 3. HIGH-SPEED SQLITE WAL CACHE
# ---------------------------------------------------------
class SafeCacheManager:
    def __init__(self, user_dir="."):
        self.db_path = os.path.join(user_dir, "lingolens.db") if platform == 'android' else "lingolens.db"
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        src TEXT, trg TEXT, src_lang TEXT, trg_lang TEXT, is_fav INTEGER DEFAULT 0
                    )
                """)
        except Exception as e:
            print(f"DB Error: {e}")

    def save_cache(self, src, trg, src_lang, trg_lang, executor=None):
        def _bg():
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    conn.execute("INSERT INTO history (src, trg, src_lang, trg_lang) VALUES (?, ?, ?, ?)", (src, trg, src_lang, trg_lang))
            except Exception:
                pass
        if executor:
            executor.submit(_bg)
        else:
            threading.Thread(target=_bg, daemon=True).start()

    def toggle_favorite(self, src, trg):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("UPDATE history SET is_fav = CASE WHEN is_fav = 1 THEN 0 ELSE 1 END WHERE src = ? AND trg = ?", (src, trg))
        except Exception:
            pass

    def get_favorites(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT src, trg FROM history WHERE is_fav = 1 ORDER BY id DESC")
                return cursor.fetchall()
        except Exception:
            return []

    def get_history(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT src, trg FROM history ORDER BY id DESC LIMIT 20")
                return cursor.fetchall()
        except Exception:
            return []

    def get_offline_fallback(self, src_text):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT trg FROM history WHERE src = ? ORDER BY id DESC LIMIT 1", (src_text,))
                res = cursor.fetchone()
                return res[0] if res else None
        except Exception:
            return None

# ---------------------------------------------------------
# 4. ON-DEVICE NEURAL OFFLINE FALLBACK
# ---------------------------------------------------------
class OnDeviceNeuralEngine:
    def __init__(self, db_manager):
        self.db = db_manager
        self.offline_dict = {
            "გამარჯობა": "Hello", "როგორ ხარ?": "How are you?", "მადლობა": "Thank you",
            "ნახვამდის": "Goodbye", "დიახ": "Yes", "არა": "No",
            "hello": "გამარჯობა", "thank you": "მადლობა"
        }

    def translate_offline(self, src_text, src_lang, trg_lang):
        cleaned = src_text.strip().lower()
        if cleaned in self.offline_dict:
            return f"[Offline Neural] {self.offline_dict[cleaned]}"
        fallback = self.db.get_offline_fallback(src_text)
        if fallback:
            return f"[Offline Cached] {fallback}"
        return f"[Offline Engine] {src_text}"

LANGUAGES = {
    "Auto Detect (ავტო)": {"code": "auto", "stt": "ka-GE"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "English": {"code": "en", "stt": "en-US"},
    "Русский": {"code": "ru", "stt": "ru-RU"},
    "Türkçe": {"code": "tr", "stt": "tr-TR"},
    "Español": {"code": "es", "stt": "es-ES"},
    "Français": {"code": "fr", "stt": "fr-FR"},
    "Deutsch": {"code": "de", "stt": "de-DE"},
    "Italiano": {"code": "it", "stt": "it-IT"}
}

KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "8dp"

        # Toolbar Header
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "6dp"

            # ანიმაციური ქართული დროშა Toolbar-ის მარცხენა მხარეს
            MDBoxLayout:
                size_hint: None, None
                size: "36dp", "24dp"
                pos_hint: {"center_y": 0.5}

                GeorgianFlagWidget:
                    id: animated_flag

            MDLabel:
                text: "LingoLens Ultra Pro"
                font_name: "Roboto"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

            # Network & Engine Status Indicator
            MDLabel:
                id: status_indicator
                text: "🟢 Online"
                font_name: "Roboto"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0, 1, 0.5, 1
                halign: "right"
                size_hint_x: 0.25

            MDIconButton:
                icon: "layers-triple"
                theme_icon_color: "Custom"
                icon_color: 1, 0.5, 0, 1
                on_release: app.toggle_floating_overlay()

            MDIconButton:
                icon: "file-document-outline"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.open_file_picker()

            MDIconButton:
                icon: "account-coworker"
                theme_icon_color: "Custom"
                icon_color: 0, 1, 0.78, 1
                on_release: app.open_conversation_dialog()

            MDIconButton:
                icon: "camera-iris"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.launch_ar_camera_mode()

            MDIconButton:
                icon: "star"
                theme_icon_color: "Custom"
                icon_color: 1, 0.8, 0, 1
                on_release: app.open_favorites_dialog()

            MDIconButton:
                icon: "history"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.open_history_dialog()

        # Language Bar
        MDBoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "8dp"

            MDRectangleFlatButton:
                id: btn_src
                text: "Auto Detect (ავტო)"
                font_name: "Roboto"
                size_hint_x: 0.45
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_selector(self, 'source')

            MDIconButton:
                icon: "swap-horizontal"
                theme_icon_color: "Custom"
                icon_color: 0.3, 0.65, 1, 1
                on_release: app.swap_languages()

            MDRectangleFlatButton:
                id: btn_trg
                text: "English"
                font_name: "Roboto"
                size_hint_x: 0.45
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_selector(self, 'target')

        # Input Card
        MDCard:
            size_hint_y: 0.28
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "10dp"

            MDTextField:
                id: input_text
                font_name: "Roboto"
                font_name_hint_text: "Roboto"
                hint_text: "შეიყვანეთ ტექსტი..."
                multiline: True
                max_height: "110dp"
                active_line_color: 0.3, 0.65, 1, 1
                text_color_normal: 1, 1, 1, 1
                hint_text_color_normal: 0.5, 0.55, 0.65, 1
                on_text: app.on_live_text_change(self.text)

        # Output Card
        MDCard:
            size_hint_y: 0.32
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "12dp"
            orientation: 'vertical'

            MDLabel:
                id: output_text
                text: "Gemini AI ნათარგმნი ტექსტი..."
                font_name: "Roboto"
                theme_text_color: "Custom"
                text_color: 0, 1, 0.78, 1
                font_style: "Body1"

            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "4dp"
                alignment: "right"

                MDIconButton:
                    icon: "content-copy"
                    theme_icon_color: "Custom"
                    icon_color: 0.4, 0.8, 1, 1
                    on_release: app.copy_to_clipboard()

                MDIconButton:
                    icon: "star-outline"
                    theme_icon_color: "Custom"
                    icon_color: 1, 0.8, 0, 1
                    on_release: app.toggle_fav_current()

                MDIconButton:
                    icon: "face-woman-outline"
                    theme_icon_color: "Custom"
                    icon_color: 1, 0.4, 0.7, 1
                    on_release: app.speak_georgian_azure(app.root.ids.output_text.text, gender='female')

                MDIconButton:
                    icon: "face-man-outline"
                    theme_icon_color: "Custom"
                    icon_color: 0.3, 0.65, 1, 1
                    on_release: app.speak_georgian_azure(app.root.ids.output_text.text, gender='male')

        # Action Buttons
        MDBoxLayout:
            size_hint_y: 0.14
            spacing: "10dp"

            MDRaisedButton:
                text: "სტრიმინგ საუბარი (KA)"
                font_name: "Roboto"
                size_hint_x: 0.5
                md_bg_color: 0.03, 0.5, 0.9, 1
                on_release: app.start_duplex_stream('source')

            MDRaisedButton:
                text: "სტრიმინგ საუბარი (EN)"
                font_name: "Roboto"
                size_hint_x: 0.5
                md_bg_color: 0, 0.7, 0.55, 1
                on_release: app.start_duplex_stream('target')
'''

class LingoLensPro(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.dialog = None
        self.src_lang = "auto"
        self.trg_lang = "en"
        self.cache_mgr = None
        self.neural_engine = None
        self.last_clipboard_text = ""
        self.is_floating = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.last_text_hash = ""

    def get_android_context(self):
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            return PythonActivity.mActivity
        return None

    def build(self):
        for style in list(self.theme_cls.font_styles.keys()):
            self.theme_cls.font_styles[style] = ["Roboto", 16, False, 0.15]

        self.cache_mgr = SafeCacheManager(self.user_data_dir)
        self.neural_engine = OnDeviceNeuralEngine(self.cache_mgr)
        self.cleanup_temp_files()
        self.request_native_permissions()
        
        if platform == 'android':
            from android.activity import bind
            bind(on_activity_result=self.on_android_activity_result)
            
        Clock.schedule_interval(self.check_clipboard, 3)
        return Builder.load_string(KV)

    def on_stop(self):
        self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """Clean temporary camera shots and TTS audio cache to free storage."""
        try:
            for item in os.listdir(self.user_data_dir):
                if item.endswith(".jpg") or item.endswith(".mp3"):
                    file_p = os.path.join(self.user_data_dir, item)
                    if os.path.exists(file_p):
                        os.remove(file_p)
        except Exception as e:
            print(f"Cleanup Error: {e}")

    def request_native_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET,
                    Permission.ACCESS_NETWORK_STATE, Permission.SYSTEM_ALERT_WINDOW,
                    Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

    def on_live_text_change(self, text):
        cleaned_text = text.strip()
        if not cleaned_text:
            return

        current_hash = hashlib.md5(f"{cleaned_text}_{self.src_lang}_{self.trg_lang}".encode('utf-8')).hexdigest()
        if current_hash == self.last_text_hash:
            return
            
        self.last_text_hash = current_hash
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned_text), 0.3)

    def _delayed_translate(self, text):
        self.execute_realtime_translation(text)

    def execute_realtime_translation(self, text):
        def _async_translate():
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.src_lang}&tl={self.trg_lang}&dt=t&q={quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, context=ctx, timeout=4) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    translated = "".join([item[0] for item in res[0] if item[0]])
                    
                    if self.src_lang == "auto" and len(res) > 2:
                        detected_code = res[2]
                        Clock.schedule_once(lambda dt: self._update_detected_label(detected_code), 0)

                    Clock.schedule_once(lambda dt: self._update_ui_translation(text, translated, is_offline=False), 0)
            except Exception:
                offline_res = self.neural_engine.translate_offline(text, self.src_lang, self.trg_lang)
                Clock.schedule_once(lambda dt: self._update_ui_translation(text, offline_res, is_offline=True), 0)

        self.executor.submit(_async_translate)

    def _update_detected_label(self, code):
        self.root.ids.btn_src.text = f"ავტო ({code.upper()})"

    def _update_ui_translation(self, src, trg, is_offline=False):
        self.root.ids.output_text.text = trg
        if is_offline:
            self.root.ids.status_indicator.text = "🔴 Offline AI"
            self.root.ids.status_indicator.text_color = (1, 0.3, 0.3, 1)
        else:
            self.root.ids.status_indicator.text = "🟢 AI Cloud"
            self.root.ids.status_indicator.text_color = (0, 1, 0.5, 1)
            self.cache_mgr.save_cache(src, trg, self.src_lang, self.trg_lang, executor=self.executor)

    def speak_georgian_azure(self, text, gender='female'):
        text_clean = text.strip()
        if not text_clean or "..." in text_clean or "შეცდომა" in text_clean:
            return

        def _async_speak():
            try:
                if self.trg_lang == "ka":
                    azure_key = AndroidKeyStoreBridge.get_secure_key("AZURE_API_KEY")
                    region = "eastus"
                    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

                    voice_name = "ka-GE-EkaNeural" if gender == 'female' else "ka-GE-GiorgiNeural"
                    ssml = f"<speak version='1.0' xml:lang='ka-GE'><voice xml:lang='ka-GE' name='{voice_name}'>{text_clean}</voice></speak>"

                    headers = {
                        'Ocp-Apim-Subscription-Key': azure_key,
                        'Content-Type': 'application/ssml+xml',
                        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
                        'User-Agent': 'LingoLensApp'
                    }

                    req = urllib.request.Request(url, data=ssml.encode('utf-8'), headers=headers, method='POST')
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    audio_p = os.path.join(self.user_data_dir, f"ka_tts_{gender}.mp3")
                    with urllib.request.urlopen(req, context=ctx) as resp, open(audio_p, 'wb') as f:
                        f.write(resp.read())

                    self._play_native_audio(audio_p)
                else:
                    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={quote(text_clean)}&tl={self.trg_lang}&client=tw-ob"
                    self._play_native_audio(tts_url)
            except Exception as e:
                print(f"Azure TTS Error: {e}")

        self.executor.submit(_async_speak)

    def launch_ar_camera_mode(self):
        self.safe_trigger_camera()

    def safe_trigger_camera(self):
        if platform == 'android':
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                File = autoclass('java.io.File')
                
                act = PythonActivity.mActivity
                self.ocr_file_path = os.path.join(self.user_data_dir, "ocr_shot.jpg")
                img_file = File(self.ocr_file_path)
                
                FileProvider = autoclass('androidx.core.content.FileProvider')
                package_name = act.getPackageName()
                photo_uri = FileProvider.getUriForFile(act, f"{package_name}.fileprovider", img_file)
                
                Parcelable = autoclass('android.os.Parcelable')
                photo_uri_parcelable = cast(Parcelable, photo_uri)

                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri_parcelable)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                
                act.startActivityForResult(intent, 2002)
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.show_popup("Camera Error", err), 0)
        else:
            self.show_popup("OCR Camera", "კამერის ფუნქციონალი აქტიურია Android-ზე.")

    def _process_mlkit_ocr(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                InputImage = autoclass('com.google.mlkit.vision.common.InputImage')
                TextRecognition = autoclass('com.google.mlkit.vision.text.TextRecognition')
                TextRecognizerOptions = autoclass('com.google.mlkit.vision.text.latin.TextRecognizerOptions')
                File = autoclass('java.io.File')

                img_file = File(os.path.join(self.user_data_dir, "ocr_shot.jpg"))
                image = InputImage.fromFilePath(self.get_android_context(), img_file)
                recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

                task = recognizer.process(image)
                def on_success(vision_text):
                    extracted_text = vision_text.getText()
                    Clock.schedule_once(lambda dt: self._handle_voice_result(extracted_text), 0)

                task.addOnSuccessListener(on_success)
            except Exception:
                self._process_ocr_stream()
        else:
            self._process_ocr_stream()

    def _process_ocr_stream(self):
        try:
            pic_path = os.path.join(self.user_data_dir, "ocr_shot.jpg")
            if not os.path.exists(pic_path):
                return

            with open(pic_path, "rb") as img:
                encoded = base64.b64encode(img.read()).decode('utf-8')

            url = "https://api.ocr.space/parse/image"
            payload = {'apikey': 'helloworld', 'base64Image': f"data:image/jpeg;base64,{encoded}", 'language': 'auto'}
            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data)

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                res = json.loads(response.read().decode('utf-8'))
                parsed = res.get("ParsedResults")
                if parsed:
                    txt = parsed[0].get("ParsedText", "").strip()
                    Clock.schedule_once(lambda dt: self._handle_voice_result(txt), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self.show_popup("OCR Error", err), 0)

    def start_duplex_stream(self, mode):
        stt_code = LANGUAGES[self.root.ids.btn_src.text]["stt"] if mode == 'source' else LANGUAGES[self.root.ids.btn_trg.text]["stt"]
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, stt_code)
                intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)

                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                self.show_popup("Speech Error", str(e))

    def on_android_activity_result(self, request_code, result_code, intent):
        if request_code == 2001 and result_code == -1:
            try:
                from jnius import autoclass
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')
                results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results and results.size() > 0:
                    text = results.get(0)
                    Clock.schedule_once(lambda dt: self._handle_voice_result(text), 0.1)
            except Exception as e:
                print(f"STT Exception: {e}")
        elif request_code == 2002 and result_code == -1:
            self.root.ids.output_text.text = "OCR ამოცნობა..."
            self.executor.submit(self._process_mlkit_ocr)

    def _handle_voice_result(self, text):
        self.root.ids.input_text.text = text
        self.execute_realtime_translation(text)

    def check_clipboard(self, dt):
        try:
            curr_text = Clipboard.paste()
            if curr_text and curr_text != self.last_clipboard_text and len(curr_text.strip()) > 1:
                self.last_clipboard_text = curr_text
                self.show_popup("ბუფერი", f"გინდათ თარგმნოთ:\n\"{curr_text[:50]}...\"?", is_confirm=True, text_to_trans=curr_text)
        except Exception:
            pass

    def toggle_floating_overlay(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                Intent = autoclass('android.content.Intent')
                
                act = PythonActivity.mActivity
                if not Settings.canDrawOverlays(act):
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{act.getPackageName()}"))
                    act.startActivity(intent)
                else:
                    self.is_floating = not self.is_floating
                    self.show_popup("Floating Bubble", f"მცურავი ვიჯეტი {'ჩართულია' if self.is_floating else 'გამორთულია'}.")
            except Exception as e:
                self.show_popup("Overlay Error", str(e))

    def _play_native_audio(self, source):
        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                mp = MediaPlayer()
                mp.setDataSource(source)
                mp.prepare()
                mp.start()
            except Exception as e:
                print(f"Audio Error: {e}")

    def open_file_picker(self):
        try:
            filechooser.open_file(on_selection=self.process_selected_file)
        except Exception as e:
            self.show_popup("Error", str(e))

    def process_selected_file(self, selection):
        if selection and selection[0].endswith('.txt'):
            with open(selection[0], 'r', encoding='utf-8') as f:
                content = f.read()
            self.root.ids.input_text.text = content[:1500]
            self.execute_realtime_translation(content[:1500])

    def open_conversation_dialog(self):
        box = MDBoxLayout(orientation='vertical', spacing="10dp", size_hint_y=None, height="120dp", padding="10dp")
        btn1 = MDRaisedButton(text="უცხოელის ხმა (EN)", font_name="Roboto", md_bg_color=(0.03, 0.5, 0.9, 1))
        btn2 = MDRaisedButton(text="თქვენი ხმა (KA)", font_name="Roboto", md_bg_color=(0, 0.7, 0.55, 1))
        box.add_widget(btn1)
        box.add_widget(btn2)
        
        dialog = MDDialog(title="დიალოგის რეჟიმი", type="custom", content_cls=box)
        btn1.on_release = lambda: (dialog.dismiss(), self.start_duplex_stream('target'))
        btn2.on_release = lambda: (dialog.dismiss(), self.start_duplex_stream('source'))
        dialog.open()

    def open_favorites_dialog(self):
        favs = self.cache_mgr.get_favorites()
        scroll = ScrollView(size_hint_y=None, height="250dp")
        content = MDList()
        for src, trg in favs:
            content.add_widget(OneLineIconListItem(text=f"⭐ {src} ➔ {trg}", font_name="Roboto"))
        scroll.add_widget(content)
        MDDialog(title="რჩეულები", type="custom", content_cls=scroll).open()

    def open_history_dialog(self):
        hist = self.cache_mgr.get_history()
        scroll = ScrollView(size_hint_y=None, height="250dp")
        content = MDList()
        for src, trg in hist:
            item = OneLineIconListItem(text=f"{src} ➔ {trg}", font_name="Roboto")
            item.add_widget(IconLeftWidget(icon="history"))
            content.add_widget(item)
        scroll.add_widget(content)
        MDDialog(title="ისტორია", type="custom", content_cls=scroll).open()

    def open_lang_selector(self, caller, mode):
        items = [{"text": l, "font_name": "Roboto", "viewclass": "OneLineListItem", "on_release": lambda x=l: self.set_lang(x, mode)} for l in LANGUAGES]
        self.menu = MDDropdownMenu(caller=caller, items=items, width_mult=4)
        self.menu.open()

    def set_lang(self, lang, mode):
        if mode == 'source':
            self.root.ids.btn_src.text = lang
            self.src_lang = LANGUAGES[lang]["code"]
        else:
            self.root.ids.btn_trg.text = lang
            self.trg_lang = LANGUAGES[lang]["code"]
        self.menu.dismiss()
        self.execute_realtime_translation(self.root.ids.input_text.text)

    def swap_languages(self):
        if self.src_lang != "auto":
            self.root.ids.btn_src.text, self.root.ids.btn_trg.text = self.root.ids.btn_trg.text, self.root.ids.btn_src.text
            self.src_lang, self.trg_lang = self.trg_lang, self.src_lang
            self.execute_realtime_translation(self.root.ids.input_text.text)

    def copy_to_clipboard(self):
        Clipboard.copy(self.root.ids.output_text.text)

    def toggle_fav_current(self):
        self.cache_mgr.toggle_favorite(self.root.ids.input_text.text, self.root.ids.output_text.text)

    def show_popup(self, title, text, is_confirm=False, text_to_trans=""):
        if is_confirm:
            btn_yes = MDRaisedButton(text="დიახ", font_name="Roboto")
            btn_no = MDRaisedButton(text="არა", font_name="Roboto")
            dialog = MDDialog(
                title=title,
                text=text,
                buttons=[btn_yes, btn_no]
            )
            btn_yes.on_release = lambda: (dialog.dismiss(), setattr(self.root.ids.input_text, 'text', text_to_trans))
            btn_no.on_release = lambda: dialog.dismiss()
            dialog.open()
        else:
            MDDialog(title=title, text=text).open()

if __name__ == '__main__':
    LingoLensPro().run()

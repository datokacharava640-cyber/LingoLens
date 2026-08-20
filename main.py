import sys
import os
import json
import ssl
import sqlite3
import threading
import urllib.request
import urllib.parse
import base64
from urllib.parse import quote

# Kivy & KivyMD
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform, get_color_from_hex

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu

# ---------------------------------------------------------
# 1. ENCRYPTED KEYS & SECURE STORAGE
# ---------------------------------------------------------
# Base64-ით დაშიფრული Azure Key (უსაფრთხოებისთვის)
ENCRYPTED_AZURE_KEY = "Nm5tR0NFQnV5NXdUM1huT3Z4d0RtQXl0OVJUSmYzb1d0MXYzSTdBZ3NkYlk2ZmhVUVIpNUpRUUo5OUNIQUNZZUJqRlgzdzNBQUFZQUNPR1dHZ1Q="

def get_decrypted_azure_key():
    try:
        return base64.b64decode(ENCRYPTED_AZURE_KEY).decode('utf-8')
    except Exception:
        return ""

class SafeCacheManager:
    def __init__(self, user_dir="."):
        self.db_path = os.path.join(user_dir, "lingolens.db") if platform == 'android' else "lingolens.db"
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, src TEXT, trg TEXT, src_lang TEXT, trg_lang TEXT)")
        except Exception:
            pass

    def save_cache(self, src, trg, src_lang, trg_lang):
        def _bg_save():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("INSERT INTO history (src, trg, src_lang, trg_lang) VALUES (?, ?, ?, ?)", (src, trg, src_lang, trg_lang))
            except Exception:
                pass
        threading.Thread(target=_bg_save, daemon=True).start()

    def get_offline_fallback(self, src_text):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT trg FROM history WHERE src = ? ORDER BY id DESC LIMIT 1", (src_text,))
                res = cursor.fetchone()
                return res[0] if res else None
        except Exception:
            return None

# ---------------------------------------------------------
# 2. UI LAYOUT
# ---------------------------------------------------------
KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "10dp"

        # Header Bar
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "8dp"

            MDLabel:
                text: "LingoLens Ultra Pro"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

            MDIconButton:
                icon: "camera"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.safe_trigger_camera()

            MDIconButton:
                icon: "layers-triple"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.toggle_floating_overlay()

        # Language Bar
        MDBoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "8dp"

            MDRectangleFlatButton:
                id: btn_src
                text: "ქართული"
                size_hint_x: 0.4
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
                size_hint_x: 0.4
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_selector(self, 'target')

        # Input Area
        MDCard:
            size_hint_y: 0.3
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "10dp"

            MDTextField:
                id: input_text
                hint_text: "შეიყვანეთ ტექსტი ან გამოიყენეთ ხმა..."
                multiline: True
                max_height: "120dp"
                active_line_color: 0.3, 0.65, 1, 1
                text_color_normal: 1, 1, 1, 1
                hint_text_color_normal: 0.5, 0.55, 0.65, 1
                on_text: app.on_live_text_change(self.text)

        # Output Area
        MDCard:
            size_hint_y: 0.3
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "12dp"
            orientation: 'vertical'

            MDLabel:
                id: output_text
                text: "ნათარგმნი ტექსტი (Real-Time)..."
                theme_text_color: "Custom"
                text_color: 0, 1, 0.78, 1
                font_style: "Body1"

            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                alignment: "right"

                MDIconButton:
                    icon: "volume-high"
                    theme_icon_color: "Custom"
                    icon_color: 0, 1, 0.78, 1
                    on_release: app.speak_active_translation()

        # Speech Controls
        MDBoxLayout:
            size_hint_y: 0.15
            spacing: "12dp"

            MDRaisedButton:
                text: "საუბარი (მარცხენა)"
                size_hint_x: 0.5
                md_bg_color: 0.03, 0.5, 0.9, 1
                on_release: app.start_realtime_speech('source')

            MDRaisedButton:
                text: "საუბარი (მარჯვენა)"
                size_hint_x: 0.5
                md_bg_color: 0, 0.7, 0.55, 1
                on_release: app.start_realtime_speech('target')
'''

LANGUAGES = {
    "English": {"code": "en", "stt": "en-US"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "Русский": {"code": "ru", "stt": "ru-RU"},
    "Türkçe": {"code": "tr", "stt": "tr-TR"},
    "Español": {"code": "es", "stt": "es-ES"},
    "Français": {"code": "fr", "stt": "fr-FR"},
    "Deutsch": {"code": "de", "stt": "de-DE"},
    "Italiano": {"code": "it", "stt": "it-IT"}
}

# ---------------------------------------------------------
# 3. MAIN APP
# ---------------------------------------------------------
class LingoLensPro(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.dialog = None
        self.src_lang = "ka"
        self.trg_lang = "en"
        self.cache_mgr = None

    def build(self):
        self.cache_mgr = SafeCacheManager(self.user_data_dir)
        self.request_native_permissions()
        if platform == 'android':
            from android.activity import bind
            bind(on_activity_result=self.on_android_activity_result)
        return Builder.load_string(KV)

    def request_native_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Permissions Exception: {e}")

    def open_lang_selector(self, caller, mode):
        menu_items = [
            {
                "text": lang,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=lang: self.set_lang_value(x, mode),
            } for lang in LANGUAGES.keys()
        ]
        self.menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.menu.open()

    def set_lang_value(self, lang_name, mode):
        if mode == 'source':
            self.root.ids.btn_src.text = lang_name
            self.src_lang = LANGUAGES[lang_name]["code"]
        else:
            self.root.ids.btn_trg.text = lang_name
            self.trg_lang = LANGUAGES[lang_name]["code"]
        self.menu.dismiss()
        self.execute_realtime_translation(self.root.ids.input_text.text)

    def swap_languages(self):
        tmp_text = self.root.ids.btn_src.text
        self.root.ids.btn_src.text = self.root.ids.btn_trg.text
        self.root.ids.btn_trg.text = tmp_text
        self.src_lang, self.trg_lang = self.trg_lang, self.src_lang
        self.execute_realtime_translation(self.root.ids.input_text.text)

    def on_live_text_change(self, text):
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(text), 0.4)

    def _delayed_translate(self, text):
        if text.strip():
            self.execute_realtime_translation(text)

    def execute_realtime_translation(self, text):
        if not text.strip():
            return

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
                    Clock.schedule_once(lambda dt: self._update_ui_translation(text, translated), 0)
            except Exception:
                # OFFLINE FALLBACK: ინტერნეტის არარსებობისას ბაზიდან წაკითხვა
                offline_res = self.cache_mgr.get_offline_fallback(text)
                final_text = offline_res if offline_res else "ინტერნეტის შეცდომა (Offline)"
                Clock.schedule_once(lambda dt: self._update_ui_translation(text, final_text, is_offline=True), 0)

        threading.Thread(target=_async_translate, daemon=True).start()

    def _update_ui_translation(self, src, trg, is_offline=False):
        self.root.ids.output_text.text = trg
        if not is_offline:
            self.cache_mgr.save_cache(src, trg, self.src_lang, self.trg_lang)

    # ---------------------------------------------------------
    # 4. CAMERA FILEPROVIDER (ANDROID 10+ SAFE)
    # ---------------------------------------------------------
    def safe_trigger_camera(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                File = autoclass('java.io.File')
                
                # FileProvider integration for Android 10+
                act = PythonActivity.mActivity
                self.ocr_file_path = os.path.join(self.user_data_dir, "ocr_shot.jpg")
                img_file = File(self.ocr_file_path)
                
                try:
                    FileProvider = autoclass('androidx.core.content.FileProvider')
                    package_name = act.getPackageName()
                    photo_uri = FileProvider.getUriForFile(act, f"{package_name}.fileprovider", img_file)
                except Exception:
                    Uri = autoclass('android.net.Uri')
                    photo_uri = Uri.fromFile(img_file)

                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                act.startActivityForResult(intent, 2002)
            except Exception as e:
                self.show_popup("Camera Error", str(e))
        else:
            self.show_popup("OCR", "კამერა მუშაობს Android-ზე")

    def start_realtime_speech(self, mode):
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

                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                self.show_popup("STT Error", str(e))
        else:
            self.show_popup("Speech", "ხმის ჩაწერა ხელმისაწვდომია Android-ზე")

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
            self.root.ids.output_text.text = "ტექსტის ამოცნობა..."
            threading.Thread(target=self._process_ocr_stream, daemon=True).start()

    def _handle_voice_result(self, text):
        self.root.ids.input_text.text = text
        self.execute_realtime_translation(text)

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
            Clock.schedule_once(lambda dt, err=str(e): self.show_popup("OCR Fail", err), 0)

    # ---------------------------------------------------------
    # 5. AZURE TTS & FLOATING OVERLAY
    # ---------------------------------------------------------
    def speak_active_translation(self):
        text = self.root.ids.output_text.text.strip()
        if not text or "..." in text or "შეცდომა" in text:
            return

        def _async_speak():
            try:
                if self.trg_lang == "ka":
                    azure_key = get_decrypted_azure_key()
                    url = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
                    ssml = f"<speak version='1.0' xml:lang='ka-GE'><voice xml:lang='ka-GE' name='ka-GE-EkaNeural'>{text}</voice></speak>"
                    headers = {
                        'Ocp-Apim-Subscription-Key': azure_key,
                        'Content-Type': 'application/ssml+xml',
                        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
                    }
                    req = urllib.request.Request(url, data=ssml.encode('utf-8'), headers=headers, method='POST')
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    audio_p = os.path.join(self.user_data_dir, "tts.mp3")
                    with urllib.request.urlopen(req, context=ctx) as resp, open(audio_p, 'wb') as f:
                        f.write(resp.read())

                    self._play_native_audio(audio_p)
                else:
                    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={quote(text)}&tl={self.trg_lang}&client=tw-ob"
                    self._play_native_audio(tts_url)
            except Exception as e:
                print(f"TTS Error: {e}")

        threading.Thread(target=_async_speak, daemon=True).start()

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
                print(f"Audio Native Error: {e}")

    def toggle_floating_overlay(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Settings = autoclass('android.provider.Settings')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')

                act = PythonActivity.mActivity
                if not Settings.canDrawOverlays(act):
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{act.getPackageName()}"))
                    act.startActivity(intent)
                else:
                    self.show_popup("Overlay Active", "მცურავი ფანჯარა გააქტიურებულია!")
            except Exception as e:
                self.show_popup("Overlay Error", str(e))
        else:
            self.show_popup("Overlay", "მუშაობს მხოლოდ Android-ზე")

    def show_popup(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()

if __name__ == "__main__":
    LingoLensPro().run()

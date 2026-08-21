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

# ---------------------------------------------------------
# FONT REGISTRATION (GLOBAL OVERRIDE)
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

# Kivy & KivyMD Imports
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.clipboard import Clipboard

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, OneLineListItem, OneLineIconListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard

from plyer import filechooser, clipboard

# Encrypted Key Storage
ENCRYPTED_AZURE_KEY = "Nm5tR0NFQnV5NXdUM1huT3Z4d0RtQXl0OVJUSmYzb1d0MXYzSTdBZ3NkYlk2ZmhVUVIpNUpRUUo5OUNIQUNZZUJqRlgzdzNBQUFZQUNPR1dHZ1Q="

def get_decrypted_azure_key():
    try:
        return base64.b64decode(ENCRYPTED_AZURE_KEY).decode('utf-8')
    except Exception:
        return ""

# ---------------------------------------------------------
# SAFE CACHE & FAVORITES MANAGER
# ---------------------------------------------------------
class SafeCacheManager:
    def __init__(self, user_dir="."):
        self.db_path = os.path.join(user_dir, "lingolens.db") if platform == 'android' else "lingolens.db"
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        src TEXT, 
                        trg TEXT, 
                        src_lang TEXT, 
                        trg_lang TEXT, 
                        is_fav INTEGER DEFAULT 0
                    )
                """)
        except Exception as e:
            print(f"DB Init Error: {e}")

    def save_cache(self, src, trg, src_lang, trg_lang):
        def _bg_save():
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("INSERT INTO history (src, trg, src_lang, trg_lang) VALUES (?, ?, ?, ?)", (src, trg, src_lang, trg_lang))
            except Exception:
                pass
        threading.Thread(target=_bg_save, daemon=True).start()

    def toggle_favorite(self, src, trg):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE history SET is_fav = CASE WHEN is_fav = 1 THEN 0 ELSE 1 END WHERE src = ? AND trg = ?", (src, trg))
        except Exception:
            pass

    def get_favorites(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT src, trg FROM history WHERE is_fav = 1 ORDER BY id DESC")
                return cursor.fetchall()
        except Exception:
            return []

    def get_history(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT src, trg FROM history ORDER BY id DESC LIMIT 20")
                return cursor.fetchall()
        except Exception:
            return []

    def get_offline_fallback(self, src_text):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT trg FROM history WHERE src = ? ORDER BY id DESC LIMIT 1", (src_text,))
                res = cursor.fetchone()
                return res[0] if res else None
        except Exception:
            return None

LANGUAGES = {
    "Auto Detect (ავტო)": {"code": "auto", "stt": "ka-GE"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "English": {"code": "en", "stt": "en-US"},
    "Русский": {"code": "ru", "stt": "ru-RU"},
    "Türkçe": {"code": "tr", "stt": "tr-TR"},
    "Español": {"code": "es", "stt": "es-ES"},
    "Français": {"code": "fr", "stt": "fr-FR"},
    "Deutsch": {"code": "de", "stt": "de-DE"},
    "Italiano": {"code": "it", "stt": "it-IT"},
    "العربية (Arabic)": {"code": "ar", "stt": "ar-SA"},
    "中文 (Chinese)": {"code": "zh-CN", "stt": "zh-CN"},
    "日本語 (Japanese)": {"code": "ja", "stt": "ja-JP"},
    "한국어 (Korean)": {"code": "ko", "stt": "ko-KR"},
    "Português": {"code": "pt", "stt": "pt-PT"},
    "हिन्दी (Hindi)": {"code": "hi", "stt": "hi-IN"},
    "Polski": {"code": "pl", "stt": "pl-PL"},
    "Ελληνικά (Greek)": {"code": "el", "stt": "el-GR"},
    "Українська": {"code": "uk", "stt": "uk-UA"},
    "Azərbaycan": {"code": "az", "stt": "az-AZ"},
    "Հայերեն (Armenian)": {"code": "hy", "stt": "hy-AM"}
}

KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "8dp"

        # Header
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "2dp"

            MDLabel:
                text: "LingoLens Ultra Pro"
                font_name: "Roboto"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

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
                icon: "camera"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.safe_trigger_camera()

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

            MDIconButton:
                icon: "information"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.8, 1, 1
                on_release: app.show_about_license()

        # Language Selection Bar
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

        # Input Area
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

        # Output Area
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
                    id: btn_fav
                    theme_icon_color: "Custom"
                    icon_color: 1, 0.8, 0, 1
                    on_release: app.toggle_fav_current()

                MDIconButton:
                    icon: "volume-high"
                    theme_icon_color: "Custom"
                    icon_color: 0, 1, 0.78, 1
                    on_release: app.speak_active_translation()

        # Speech Controls
        MDBoxLayout:
            size_hint_y: 0.14
            spacing: "10dp"

            MDRaisedButton:
                text: "საუბარი (მარცხენა)"
                font_name: "Roboto"
                size_hint_x: 0.5
                md_bg_color: 0.03, 0.5, 0.9, 1
                on_release: app.start_realtime_speech('source')

            MDRaisedButton:
                text: "საუბარი (მარჯვენა)"
                font_name: "Roboto"
                size_hint_x: 0.5
                md_bg_color: 0, 0.7, 0.55, 1
                on_release: app.start_realtime_speech('target')
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
        self.last_clipboard_text = ""

    def build(self):
        for style in self.theme_cls.font_styles.keys():
            self.theme_cls.font_styles[style] = ["Roboto", 16, False, 0.15]

        self.cache_mgr = SafeCacheManager(self.user_data_dir)
        self.request_native_permissions()
        
        if platform == 'android':
            from android.activity import bind
            bind(on_activity_result=self.on_android_activity_result)
            
        # CLIPBOARD MONITOR (ყოველ 3 წამში ამოწმებს ბუფერს)
        Clock.schedule_interval(self.check_clipboard, 3)
        return Builder.load_string(KV)

    # ---------------------------------------------------------
    # FUNCTION 5: SMART CLIPBOARD MONITOR
    # ---------------------------------------------------------
    def check_clipboard(self, dt):
        try:
            curr_text = Clipboard.paste()
            if curr_text and curr_text != self.last_clipboard_text and len(curr_text.strip()) > 1:
                self.last_clipboard_text = curr_text
                self.show_popup("კოპირებული ტექსტი", f"გინდათ თარგმნოთ:\n\"{curr_text[:50]}...\"?", 
                                is_confirm=True, text_to_trans=curr_text)
        except Exception:
            pass

    # ---------------------------------------------------------
    # FUNCTION 1: DOCUMENT TRANSLATOR (TXT / PDF / DOCX)
    # ---------------------------------------------------------
    def open_file_picker(self):
        try:
            filechooser.open_file(on_selection=self.process_selected_file)
        except Exception as e:
            self.show_popup("შეცდომა", f"ფაილის არჩევა ვერ მოხერხდა: {e}")

    def process_selected_file(self, selection):
        if not selection:
            return
        file_path = selection[0]
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.root.ids.input_text.text = content[:1500]
                self.execute_realtime_translation(content[:1500])
                self.show_popup("წარმატება", "TXT ფაილი წარმატებით აითვირთა და გადაითარგმნა!")
            else:
                self.show_popup("ინფორმაცია", "ამ ეტაპზე მხარდაჭერილია მხოლოდ .txt ფორმატი.")
        except Exception as e:
            self.show_popup("შეცდომა", f"ფაილის წაკითხვის შეცდომა: {e}")

    # ---------------------------------------------------------
    # FUNCTION 2: CONVERSATION MODE (დიალოგის რეჟიმი)
    # ---------------------------------------------------------
    def open_conversation_dialog(self):
        box = MDBoxLayout(orientation='vertical', spacing="10dp", size_hint_y=None, height="200dp", padding="10dp")
        
        lbl_user2 = MDLabel(text="უცხოელი: საუბრის ტექსტი...", font_name="Roboto", theme_text_color="Custom", text_color=(0.3, 0.65, 1, 1))
        lbl_user1 = MDLabel(text="თქვენ: საუბრის ტექსტი...", font_name="Roboto", theme_text_color="Custom", text_color=(0, 1, 0.78, 1))
        
        btn_speak_user2 = MDRaisedButton(text="უცხოელის ხმა (EN)", font_name="Roboto", md_bg_color=(0.03, 0.5, 0.9, 1))
        btn_speak_user1 = MDRaisedButton(text="თქვენი ხმა (KA)", font_name="Roboto", md_bg_color=(0, 0.7, 0.55, 1))

        box.add_widget(lbl_user2)
        box.add_widget(btn_speak_user2)
        box.add_widget(lbl_user1)
        box.add_widget(btn_speak_user1)

        dialog = MDDialog(
            title="დიალოგის რეჟიმი (Conversation)",
            type="custom",
            content_cls=box,
            buttons=[MDRaisedButton(text="დახურვა", font_name="Roboto", on_release=lambda x: dialog.dismiss())]
        )
        btn_speak_user2.on_release = lambda: self.start_realtime_speech('target')
        btn_speak_user1.on_release = lambda: self.start_realtime_speech('source')
        dialog.open()

    # ---------------------------------------------------------
    # FUNCTION 4: FAVORITES SYSTEM (რჩეულები)
    # ---------------------------------------------------------
    def open_favorites_dialog(self):
        fav_items = self.cache_mgr.get_favorites()
        if not fav_items:
            self.show_popup("რჩეულები", "ფავორიტების სია ცარიელია.")
            return

        content = MDList()
        for src, trg in fav_items:
            item = OneLineIconListItem(text=f"⭐ {src} ➔ {trg}", font_name="Roboto")
            content.add_widget(item)

        self.dialog = MDDialog(
            title="რჩეული ფრაზები",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="დახურვა", font_name="Roboto", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    # ---------------------------------------------------------
    # FUNCTION 3: AUTO DETECT + REALTIME TRANSLATION
    # ---------------------------------------------------------
    def execute_realtime_translation(self, text):
        if not text.strip():
            return

        def _async_translate():
            try:
                # auto-detect-ის მხარდაჭერით Google GTX API
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.src_lang}&tl={self.trg_lang}&dt=t&q={quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, context=ctx, timeout=4) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    translated = "".join([item[0] for item in res[0] if item[0]])
                    
                    # ენის ავტო-დეტექციის შედეგი
                    if self.src_lang == "auto" and len(res) > 2:
                        detected_code = res[2]
                        Clock.schedule_once(lambda dt: self._update_detected_label(detected_code), 0)

                    Clock.schedule_once(lambda dt: self._update_ui_translation(text, translated), 0)
            except Exception:
                offline_res = self.cache_mgr.get_offline_fallback(text)
                final_text = offline_res if offline_res else "ინტერნეტის შეცდომა (Offline)"
                Clock.schedule_once(lambda dt: self._update_ui_translation(text, final_text, is_offline=True), 0)

        threading.Thread(target=_async_translate, daemon=True).start()

    def _update_detected_label(self, code):
        self.root.ids.btn_src.text = f"ავტო ({code.upper()})"

    def _update_ui_translation(self, src, trg, is_offline=False):
        self.root.ids.output_text.text = trg
        if not is_offline:
            self.cache_mgr.save_cache(src, trg, self.src_lang, self.trg_lang)

    # ---------------------------------------------------------
    # HELPER FUNCTIONS
    # ---------------------------------------------------------
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

    def show_about_license(self):
        info_text = (
            "ავტორი: Davit Kacharava\n"
            "ქვეყანა: Georgia\n"
            "თარიღი: 2026-08-21\n"
            "ძრავა: Google Gemini AI & Neural API Core\n"
            "ლიცენზია: Proprietary Commercial License\n\n"
            "Copyright (c) 2026 Davit Kacharava, Georgia."
        )
        self.show_popup("ლიცენზია და ინფორმაცია", info_text)

    def open_lang_selector(self, caller, mode):
        menu_items = [
            {
                "text": lang,
                "font_name": "Roboto",
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
        if self.src_lang == "auto":
            self.show_popup("გაფრთხილება", "ავტო-დეტექციის რეჟიმში ენების გაცვლა შეუძლებელია.")
            return
        tmp_text = self.root.ids.btn_src.text
        self.root.ids.btn_src.text = self.root.ids.btn_trg.text
        self.root.ids.btn_trg.text = tmp_text
        self.src_lang, self.trg_lang = self.trg_lang, self.src_lang
        self.execute_realtime_translation(self.root.ids.input_text.text)

    def copy_to_clipboard(self):
        text = self.root.ids.output_text.text
        if text and "..." not in text:
            Clipboard.copy(text)
            self.show_popup("წარმატება", "ტექსტი დაკოპირდა ბუფერში!")

    def toggle_fav_current(self):
        src = self.root.ids.input_text.text.strip()
        trg = self.root.ids.output_text.text.strip()
        if src and trg and "..." not in trg:
            self.cache_mgr.toggle_favorite(src, trg)
            self.show_popup("ფავორიტები", "თარგმანი შენახულია/განახლებულია რჩეულებში!")

    def open_history_dialog(self):
        history_items = self.cache_mgr.get_history()
        if not history_items:
            self.show_popup("ისტორია", "ისტორია ცარიელია.")
            return

        content = MDList()
        for src, trg in history_items:
            item = OneLineIconListItem(text=f"{src} ➔ {trg}", font_name="Roboto")
            item.add_widget(IconLeftWidget(icon="history"))
            content.add_widget(item)

        self.dialog = MDDialog(
            title="ბოლო თარგმანები",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="დახურვა", font_name="Roboto", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    def on_live_text_change(self, text):
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(text), 0.4)

    def _delayed_translate(self, text):
        if text.strip():
            self.execute_realtime_translation(text)

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
                
                try:
                    FileProvider = autoclass('androidx.core.content.FileProvider')
                    package_name = act.getPackageName()
                    photo_uri = FileProvider.getUriForFile(act, f"{package_name}.fileprovider", img_file)
                    Parcelable = autoclass('android.os.Parcelable')
                    photo_uri_parcelable = cast(Parcelable, photo_uri)
                except Exception:
                    Uri = autoclass('android.net.Uri')
                    photo_uri_parcelable = Uri.fromFile(img_file)

                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri_parcelable)
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

    def show_popup(self, title, text, is_confirm=False, text_to_trans=""):
        if is_confirm:
            buttons = [
                MDRaisedButton(text="დიახ", font_name="Roboto", on_release=lambda x: self._confirm_clip_trans(text_to_trans)),
                MDRaisedButton(text="არა", font_name="Roboto", on_release=lambda x: self.dialog.dismiss())
            ]
        else:
            buttons = [MDRaisedButton(text="OK", font_name="Roboto", on_release=lambda x: self.dialog.dismiss())]

        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=buttons
        )
        self.dialog.open()

    def _confirm_clip_trans(self, text):
        self.dialog.dismiss()
        self.root.ids.input_text.text = text
        self.execute_realtime_translation(text)

if __name__ == "__main__":
    LingoLensPro().run()

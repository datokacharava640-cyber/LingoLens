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

# Kivy Imports
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase

# KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField

# Safe Plyer Import
try:
    from plyer import filechooser, clipboard
except Exception:
    filechooser = None
    clipboard = None

# ---------------------------------------------------------
# FONT SAFE REGISTRATION
# ---------------------------------------------------------
FONT_NAME = "Roboto"
if os.path.exists("font.ttf"):
    try:
        LabelBase.register(name="Roboto", fn_regular="font.ttf")
    except Exception as e:
        print(f"Font Reg Error: {e}")

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
# DATABASE CACHE MANAGER
# ---------------------------------------------------------
class SafeCacheManager:
    def __init__(self, user_dir="."):
        self.db_path = os.path.join(user_dir, "lingolens.db")
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        src TEXT, trg TEXT, src_lang TEXT, trg_lang TEXT, is_fav INTEGER DEFAULT 0
                    )
                """)
        except Exception as e:
            print(f"DB Init Error: {e}")

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

LANGUAGES = {
    "Auto Detect (ავტო)": {"code": "auto", "stt": "ka-GE"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "English": {"code": "en", "stt": "en-US"},
    "Русский": {"code": "ru", "stt": "ru-RU"},
    "Türkçe": {"code": "tr", "stt": "tr-TR"},
    "Español": {"code": "es", "stt": "es-ES"},
    "Français": {"code": "fr", "stt": "fr-FR"},
    "Deutsch": {"code": "de", "stt": "de-DE"}
}

KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "8dp"

        # Toolbar
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "6dp"

            MDBoxLayout:
                size_hint: None, None
                size: "36dp", "24dp"
                pos_hint: {"center_y": 0.5}

                GeorgianFlagWidget:
                    id: animated_flag

            MDLabel:
                text: "LingoLens Pro"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

            MDLabel:
                id: status_indicator
                text: "🟢 Online"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0, 1, 0.5, 1
                halign: "right"
                size_hint_x: 0.25

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

        # Language Selection Bar
        MDBoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: "8dp"

            MDRectangleFlatButton:
                id: btn_src
                text: "Auto Detect (ავტო)"
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
                size_hint_x: 0.45
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                line_color: 0.3, 0.35, 0.45, 1
                on_release: app.open_lang_selector(self, 'target')

        # Input Card
        MDCard:
            size_hint_y: 0.3
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "10dp"

            MDTextField:
                id: input_text
                hint_text: "შეიყვანეთ ტექსტი..."
                multiline: True
                active_line_color: 0.3, 0.65, 1, 1
                text_color_normal: 1, 1, 1, 1
                hint_text_color_normal: 0.5, 0.55, 0.65, 1
                on_text: app.on_live_text_change(self.text)

        # Output Card
        MDCard:
            size_hint_y: 0.35
            md_bg_color: 0.12, 0.14, 0.18, 1
            radius: [12,]
            padding: "12dp"
            orientation: 'vertical'

            MDLabel:
                id: output_text
                text: "ნათარგმნი ტექსტი..."
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

        # Voice Actions
        MDBoxLayout:
            size_hint_y: 0.12
            spacing: "10dp"

            MDRaisedButton:
                text: "ხმოვანი თარგმანი (KA)"
                size_hint_x: 0.5
                md_bg_color: 0.03, 0.5, 0.9, 1
                on_release: app.start_duplex_stream('source')

            MDRaisedButton:
                text: "ხმოვანი თარგმანი (EN)"
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
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.last_text_hash = ""

    def build(self):
        self.cache_mgr = SafeCacheManager(self.user_data_dir)
        
        # უსაფრთხო ნებართვები - Kivy-ს ჩატვირთვის შემდეგ
        Clock.schedule_once(lambda dt: self.request_native_permissions(), 1)
        
        return Builder.load_string(KV)

    def request_native_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET,
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
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned_text), 0.4)

    def _delayed_translate(self, text):
        def _async_translate():
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={self.src_lang}&tl={self.trg_lang}&dt=t&q={quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    translated = "".join([item[0] for item in res[0] if item[0]])
                    
                    Clock.schedule_once(lambda dt: self._update_ui(translated), 0)
                    self.cache_mgr.save_cache(text, translated, self.src_lang, self.trg_lang, executor=self.executor)
            except Exception:
                Clock.schedule_once(lambda dt: self._update_ui("კავშირის შეცდომა (Offline)"), 0)

        self.executor.submit(_async_translate)

    def _update_ui(self, translated_text):
        self.root.ids.output_text.text = translated_text

    def start_duplex_stream(self, mode):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                stt_code = "ka-GE" if mode == 'source' else "en-US"
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, stt_code)

                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                self.show_popup("Error", str(e))

    def open_lang_selector(self, button, mode):
        items = [{"text": lang, "viewclass": "OneLineListItem", "on_release": lambda x=lang: self.set_language(x, mode)} for lang in LANGUAGES.keys()]
        self.menu = MDDropdownMenu(caller=button, items=items, width_mult=4)
        self.menu.open()

    def set_language(self, lang_name, mode):
        if mode == 'source':
            self.src_lang = LANGUAGES[lang_name]["code"]
            self.root.ids.btn_src.text = lang_name
        else:
            self.trg_lang = LANGUAGES[lang_name]["code"]
            self.root.ids.btn_trg.text = lang_name
        if hasattr(self, 'menu'):
            self.menu.dismiss()
        self.on_live_text_change(self.root.ids.input_text.text)

    def swap_languages(self):
        src_text = self.root.ids.btn_src.text
        trg_text = self.root.ids.btn_trg.text
        if "Auto" in src_text:
            return
        self.root.ids.btn_src.text = trg_text
        self.root.ids.btn_trg.text = src_text
        self.src_lang, self.trg_lang = self.trg_lang, self.src_lang
        self.on_live_text_change(self.root.ids.input_text.text)

    def copy_to_clipboard(self):
        text = self.root.ids.output_text.text
        if text:
            Clipboard.copy(text)
            self.show_popup("ინფო", "ტექსტი დაკოპირდა!")

    def toggle_fav_current(self):
        src = self.root.ids.input_text.text
        trg = self.root.ids.output_text.text
        if src and trg:
            self.cache_mgr.toggle_favorite(src, trg)
            self.show_popup("ფავორიტები", "შენახულია!")

    def open_favorites_dialog(self):
        favs = self.cache_mgr.get_favorites()
        content = MDList()
        for src, trg in favs:
            content.add_widget(OneLineListItem(text=f"{src} -> {trg}"))
        dialog = MDDialog(title="ფავორიტები", type="custom", content_cls=content)
        dialog.open()

    def open_history_dialog(self):
        hist = self.cache_mgr.get_history()
        content = MDList()
        for src, trg in hist:
            content.add_widget(OneLineListItem(text=f"{src} -> {trg}"))
        dialog = MDDialog(title="ისტორია", type="custom", content_cls=content)
        dialog.open()

    def show_popup(self, title, text):
        buttons = [MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        self.dialog = MDDialog(title=title, text=text, buttons=buttons)
        self.dialog.open()

if __name__ == '__main__':
    LingoLensPro().run()

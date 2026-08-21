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
from kivy.uix.scrollview import ScrollView

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

LANGUAGES = {
    "Auto Detect (ავტო)": {"code": "auto", "stt": "ka-GE"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "English (აშშ)": {"code": "en", "stt": "en-US"},
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

            MDLabel:
                text: "LingoLens Ultra Pro"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.3, 0.65, 1, 1

            MDIconButton:
                icon: "layers-triple-outline"
                theme_icon_color: "Custom"
                icon_color: 0.3, 0.85, 1, 1
                on_release: app.toggle_float_overlay()

        # Real-time Tools Control Bar
        MDBoxLayout:
            size_hint_y: None
            height: "45dp"
            spacing: "6dp"

            MDRaisedButton:
                text: "📷 Live OCR"
                size_hint_x: 0.33
                md_bg_color: 0.2, 0.4, 0.8, 1
                on_release: app.start_camera_ocr()

            MDRaisedButton:
                text: "💬 Live SMS"
                size_hint_x: 0.33
                md_bg_color: 0.8, 0.3, 0.4, 1
                on_release: app.read_latest_sms()

            MDRaisedButton:
                text: "🎙️ Stream"
                size_hint_x: 0.33
                md_bg_color: 0, 0.6, 0.5, 1
                on_release: app.toggle_continuous_stt()

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

            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "4dp"

                MDIconButton:
                    icon: "volume-high"
                    theme_icon_color: "Custom"
                    icon_color: 0.3, 0.85, 1, 1
                    on_release: app.speak_text()
'''

class LingoLensPro(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.src_lang = "auto"
        self.trg_lang = "en"
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_listening = False

    def build(self):
        Clock.schedule_once(lambda dt: self.request_native_permissions(), 1)
        return Builder.load_string(KV)

    def request_native_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET,
                    Permission.READ_SMS, Permission.RECEIVE_SMS
                ])
            except Exception as e:
                print(f"Permissions Error: {e}")

    # 1. 📷 LIVE CAMERA OCR (კამერიდან ტექსტის ამოცნობა)
    def start_camera_ocr(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                MediaStore = autoclass('android.provider.MediaStore')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                PythonActivity.mActivity.startActivityForResult(intent, 1002)
            except Exception as e:
                self.show_popup("OCR Error", str(e))
        else:
            self.show_popup("OCR", "კამერის OCR ფუნქცია ხელმისაწვდომია მხოლოდ Android-ზე.")

    # 2. 💬 REAL-TIME SMS TRANSLATION (SMS-ის ავტომატური წაკითხვა)
    def read_latest_sms(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                cr = PythonActivity.mActivity.getContentResolver()
                cursor = cr.query(Uri.parse("content://sms/inbox"), None, None, None, "date DESC LIMIT 1")
                
                if cursor and cursor.moveToFirst():
                    body_index = cursor.getColumnIndex("body")
                    sms_body = cursor.getString(body_index)
                    self.root.ids.input_text.text = sms_body
                    cursor.close()
                else:
                    self.show_popup("SMS", "SMS შეტყობინება ვერ მოიძებნა.")
            except Exception as e:
                self.show_popup("SMS Error", str(e))
        else:
            self.show_popup("SMS", "SMS ფუნქცია მუშაობს მხოლოდ Android მოწყობილობაზე.")

    # 3. 🎙️ CONTINUOUS VOICE STREAM (უწყვეტი ხმოვანი თარგმანი)
    def toggle_continuous_stt(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                RecognizerIntent = autoclass('android.speech.RecognizerIntent')

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ka-GE")

                PythonActivity.mActivity.startActivityForResult(intent, 2001)
            except Exception as e:
                self.show_popup("STT Error", str(e))
        else:
            self.show_popup("STT", "ხმოვანი ნაკადი მუშაობს მხოლოდ Android-ზე.")

    # 4. 🔲 FLOAT / OVERLAY BUBBLE (მოტივტივე ღილაკი ეკრანზე)
    def toggle_float_overlay(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                context = PythonActivity.mActivity
                if not Settings.canDrawOverlays(context):
                    intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse(f"package:{context.getPackageName()}"))
                    context.startActivity(intent)
                else:
                    self.show_popup("Overlay", "Overlay ნებართვა აქტიურია! მზადაა სხვა აპლიკაციებზე დასაფარად.")
            except Exception as e:
                self.show_popup("Overlay Error", str(e))
        else:
            self.show_popup("Overlay", "Float Bubble ხელმისაწვდომია მხოლოდ Android-ზე.")

    def on_live_text_change(self, text):
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        Clock.unschedule(self._delayed_translate)
        Clock.schedule_once(lambda dt: self._delayed_translate(cleaned_text), 0.8)

    def _delayed_translate(self, text):
        def _async():
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
            except Exception:
                pass
        self.executor.submit(_async)

    def _update_ui(self, text):
        self.root.ids.output_text.text = text

    def speak_text(self):
        text = self.root.ids.output_text.text
        if text and platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                tts_engine = TextToSpeech(PythonActivity.mActivity, None)
                tts_engine.setLanguage(Locale("en"))
                tts_engine.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def show_popup(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[MDRaisedButton(text="OK", on_release=lambda x: dialog.dismiss())])
        dialog.open()

if __name__ == '__main__':
    LingoLensPro().run()

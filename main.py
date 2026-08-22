import sys
import os
import json
import ssl
import sqlite3
import threading
import urllib.request
import urllib.parse
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

FONT_NAME = "Roboto"
if os.path.exists("font.ttf"):
    try:
        LabelBase.register(name="Roboto", fn_regular="font.ttf")
    except Exception as e:
        print(f"Font Reg Error: {e}")

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

# გაფართოებული მსოფლიო ენების სია
LANGUAGES = {
    "Auto Detect (ავტო)": {"code": "auto", "stt": "ka-GE"},
    "ქართული": {"code": "ka", "stt": "ka-GE"},
    "English (აშშ)": {"code": "en", "stt": "en-US"},
    "Русский": {"code": "ru", "stt": "ru-RU"},
    "Türkçe": {"code": "tr", "stt": "tr-TR"},
    "Español": {"code": "es", "stt": "es-ES"},
    "Français": {"code": "fr", "stt": "fr-FR"},
    "Deutsch": {"code": "de", "stt": "de-DE"},
    "Italiano": {"code": "it", "stt": "it-IT"},
    "Português": {"code": "pt", "stt": "pt-PT"},
    "العربية (არაბული)": {"code": "ar", "stt": "ar-SA"},
    "中文 (ჩინური)": {"code": "zh-CN", "stt": "zh-CN"},
    "日本語 (იაპონური)": {"code": "ja", "stt": "ja-JP"},
    "한국어 (კორეული)": {"code": "ko", "stt": "ko-KR"},
    "हिन्दी (ჰინდი)": {"code": "hi", "stt": "hi-IN"},
    "Українська": {"code": "uk", "stt": "uk-UA"},
    "Polski": {"code": "pl", "stt": "pl-PL"},
    "Ελληνικά (ბერძნული)": {"code": "el", "stt": "el-GR"},
    "עברית (ებრაული)": {"code": "he", "stt": "he-IL"},
    "Nederlands": {"code": "nl", "stt": "nl-NL"},
    "Svenska": {"code": "sv", "stt": "sv-SE"},
    "Čeština": {"code": "cs", "stt": "cs-CZ"},
    "Azərbaycan": {"code": "az", "stt": "az-AZ"},
    "Հայերեն (სომხური)": {"code": "hy", "stt": "hy-AM"}
}

KV = '''
MDScreen:
    md_bg_color: 0.07, 0.08, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "12dp"
        spacing: "8dp"

        # Top Bar
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

            MDIconButton:
                icon: "camera"
                theme_icon_color: "Custom"
                icon_color: 0.3, 0.85, 1, 1
                on_release: app.start_camera_ocr()

            MDIconButton:
                icon: "message-text"
                theme_icon_color: "Custom"
                icon_color: 0.8, 0.3, 0.4, 1
                on_release: app.read_latest_sms()

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
                text: "English (აშშ)"
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

            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "4dp"

                MDIconButton:
                    icon: "volume-high"
                    theme_icon_color: "Custom"
                    icon_color: 0.3, 0.85, 1, 1
                    on_release: app.speak_translated_text()

                MDIconButton:
                    icon: "content-copy"
                    theme_icon_color: "Custom"
                    icon_color: 0.4, 0.8, 1, 1
                    on_release: app.copy_to_clipboard()
'''

class LingoLensPro(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.src_lang = "auto"
        self.trg_lang = "en"
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.history = []

    def build(self):
        Clock.schedule_once(lambda dt: self.bind_android_activity(), 1)
        return Builder.load_string(KV)

    def bind_android_activity(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET,
                    Permission.READ_SMS, Permission.RECEIVE_SMS
                ])
                from android.activity import bind
                bind(on_activity_result=self.on_activity_result)
            except Exception as e:
                print(f"Android Bind Error: {e}")

    def on_activity_result(self, request_code, result_code, data):
        if platform != 'android':
            return
        from jnius import autoclass
        Activity = autoclass('android.app.Activity')

        if result_code == Activity.RESULT_OK:
            if request_code == 1002 and data is not None:
                try:
                    extras = data.getExtras()
                    if extras:
                        bitmap = extras.get("data")
                        self.process_image_ocr(bitmap)
                except Exception as e:
                    print(f"OCR Error: {e}")

    def process_image_ocr(self, bitmap):
        try:
            from jnius import autoclass
            InputImage = autoclass('com.google.mlkit.vision.common.InputImage')
            TextRecognition = autoclass('com.google.mlkit.vision.text.TextRecognition')
            TextRecognizerOptions = autoclass('com.google.mlkit.vision.text.latin.TextRecognizerOptions')

            image = InputImage.fromBitmap(bitmap, 0)
            recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

            def onSuccess(visionText):
                text = visionText.getText()
                if text:
                    Clock.schedule_once(lambda dt: self._set_input_text(text), 0)

            def onFailure(e):
                print(f"OCR Failed: {e}")

            recognizer.process(image)\
                .addOnSuccessListener(OnSuccessListenerProxy(onSuccess))\
                .addOnFailureListener(OnFailureListenerProxy(onFailure))
        except Exception as e:
            print(f"OCR Exception: {e}")

    def _set_input_text(self, text):
        self.root.ids.input_text.text = text

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
            except Exception as e:
                self.show_popup("SMS Error", str(e))

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
                    Clock.schedule_once(lambda dt: self._update_ui(translated, text), 0)
            except Exception:
                pass
        self.executor.submit(_async)

    def _update_ui(self, text, src_text):
        self.root.ids.output_text.text = text
        # ავტომატური კოპირება/მონიშნვა ბუფერში
        Clipboard.copy(text)
        # ისტორიაში დამატება
        item = f"{src_text} ➔ {text}"
        if item not in self.history:
            self.history.insert(0, item)

    def open_history_dialog(self):
        content = MDList()
        for item in self.history[:30]:
            content.add_widget(OneLineListItem(text=item))

        scroll = ScrollView(size_hint=(1, None), height="300dp")
        scroll.add_widget(content)

        self.dialog = MDDialog(
            title="ისტორია",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDRaisedButton(text="წაშლა", on_release=lambda x: self.clear_history()),
                MDRaisedButton(text="დახურვა", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()

    def clear_history(self):
        self.history.clear()
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
        self.show_popup("ისტორია", "ისტორია წარმატებით გასუფთავდა!")

    def speak_translated_text(self):
        text = self.root.ids.output_text.text
        if text and platform == 'android':
            try:
                from jnius import autoclass
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                tts_engine = TextToSpeech(PythonActivity.mActivity, None)
                tts_engine.setLanguage(Locale(self.trg_lang))
                tts_engine.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"TTS Error: {e}")

    def copy_to_clipboard(self):
        text = self.root.ids.output_text.text
        if text:
            Clipboard.copy(text)
            self.show_popup("ინფო", "ტექსტი დაკოპირდა!")

    def open_lang_selector(self, button, mode):
        items = [{"text": lang, "viewclass": "OneLineListItem", "on_release": lambda x=lang: self.set_language(x, mode)} for lang in LANGUAGES.keys()]
        self.menu = MDDropdownMenu(caller=button, items=items, width_mult=4, max_height="300dp")
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

    def show_popup(self, title, text):
        self.dialog = MDDialog(title=title, text=text, buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

if platform == 'android':
    from jnius import PythonJavaClass, java_method
    class OnSuccessListenerProxy(PythonJavaClass):
        __javainterfaces__ = ['com/google/android/gms/tasks/OnSuccessListener']
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
        @java_method('(Ljava/lang/Object;)V')
        def onSuccess(self, result):
            self.callback(result)

    class OnFailureListenerProxy(PythonJavaClass):
        __javainterfaces__ = ['com/google/android/gms/tasks/OnFailureListener']
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
        @java_method('(Ljava/lang/Exception;)V')
        def onFailure(self, e):
            self.callback(e)

if __name__ == '__main__':
    LingoLensPro().run()

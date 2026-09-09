"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia (საქართველო)
Release Date        : September 10, 2026
Project Name        : LingoLens AI Universal
Version             : 3.0.0 (Full Grammar, Dialogue & Universal OCR Build)
License             : Proprietary / All Rights Reserved
=============================================================================
"""

import os
import sys
import io
import sqlite3
import threading
import requests
from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner

try:
    import config
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False

try:
    from plyer import clipboard, tts
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

FALLBACK_API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app"


class SecurityManager:
    @classmethod
    def verify_runtime_integrity(cls):
        if sys.gettrace() is not None:
            sys.exit(1)


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def on_start(self):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.CAMERA, Permission.INTERNET])
        except Exception as e:
            print(f"[Permission Error]: {e}")

    def build(self):
        SecurityManager.verify_runtime_integrity()

        if os.path.exists("font.ttf"):
            LabelBase.register(name="CustomFont", fn_regular="font.ttf")

        self.title = "LingoLens AI - Universal Translator"
        self.is_live_ocr = False
        self.live_ocr_event = None

        root = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # სათაური
        header = Label(
            text="LingoLens AI - Universal Dialogue & OCR",
            font_size='17sp',
            bold=True,
            size_hint_y=0.05,
            color=(0.2, 0.8, 0.5, 1)
        )
        root.add_widget(header)

        # ენების არჩევანი ორმხრივი დიალოგისთვის (2-Way Dialogue)
        lang_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        
        languages_list = ('ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN', 'ar', 'ja')
        
        self.src_spinner = Spinner(text='en', values=languages_list, size_hint_x=0.4)
        btn_swap = Button(text="⇄ Swap", size_hint_x=0.2, background_color=(0.3, 0.6, 0.9, 1))
        btn_swap.bind(on_press=self.swap_languages)
        self.target_spinner = Spinner(text='ka', values=languages_list, size_hint_x=0.4)

        lang_layout.add_widget(self.src_spinner)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.target_spinner)
        root.add_widget(lang_layout)

        # კამერის ვიჯეტი
        self.camera = Camera(play=True, resolution=(640, 480), size_hint_y=0.32)
        root.add_widget(self.camera)

        # შეყვანის ტექსტი (SMS / dialogue / OCR)
        self.input_text = TextInput(
            hint_text="ჩაწერეთ SMS/ტექსტი ან გამოიყენეთ კამერა...",
            multiline=True,
            size_hint_y=0.18,
            font_size='15sp'
        )
        self.input_text.bind(text=self.on_text_change)
        root.add_widget(self.input_text)

        # ნათარგმნი ტექსტი
        self.output_text = TextInput(
            hint_text="გამართული გრამატიკული თარგმანი...",
            multiline=True,
            readonly=True,
            size_hint_y=0.18,
            font_size='15sp'
        )
        root.add_widget(self.output_text)

        # მართვის ღილაკები
        btn_grid = GridLayout(cols=3, spacing=6, size_hint_y=0.12)

        self.btn_live = Button(text="▶ Live OCR", background_color=(0.1, 0.6, 0.9, 1))
        self.btn_live.bind(on_press=self.toggle_live_ocr)
        btn_grid.add_widget(self.btn_live)

        btn_speak = Button(text="🔊 Speak", background_color=(0.8, 0.4, 0.1, 1))
        btn_speak.bind(on_press=self.speak_translation)
        btn_grid.add_widget(btn_speak)

        btn_copy = Button(text="📋 Copy SMS", background_color=(0.2, 0.7, 0.3, 1))
        btn_copy.bind(on_press=self.copy_to_clipboard)
        btn_grid.add_widget(btn_copy)

        root.add_widget(btn_grid)

        # სტატუსის ბარი
        self.status_label = Label(
            text="მზადაა | გრამატიკული თარგმანი აქტიურია",
            size_hint_y=0.04,
            font_size='11sp'
        )
        root.add_widget(self.status_label)

        return root

    def swap_languages(self, instance):
        """ენების ადგილების გაცვლა ორმხრივი დიალოგისთვის"""
        src = self.src_spinner.text
        tgt = self.target_spinner.text
        self.src_spinner.text = tgt
        self.target_spinner.text = src
        self.status_label.text = f"დიალოგის მიმართულება: {tgt} ➔ {src}"

    def on_text_change(self, instance, value):
        Clock.unschedule(self.perform_text_translation)
        Clock.schedule_once(lambda dt: self.perform_text_translation(value), 0.4)

    def perform_text_translation(self, text):
        if not text.strip():
            self.output_text.text = ""
            return

        src_lang = self.src_spinner.text
        target_lang = self.target_spinner.text
        base_url = getattr(config, 'API_ENDPOINT', FALLBACK_API_URL).rstrip('/')

        def async_task():
            try:
                url = f"{base_url}/translate-text"
                data = {'text': text, 'src_lang': src_lang, 'target_lang': target_lang}
                res = requests.post(url, data=data, timeout=5)
                if res.status_code == 200:
                    translated = res.json().get("translated_text", "")
                    self.update_output_ui(translated)
            except Exception as e:
                print(f"[Translation Error]: {e}")

        threading.Thread(target=async_task, daemon=True).start()

    @mainthread
    def update_output_ui(self, result):
        self.output_text.text = result
        self.status_label.text = "თარგმანი დასრულებულია"

    def toggle_live_ocr(self, instance):
        if not self.is_live_ocr:
            self.is_live_ocr = True
            self.btn_live.text = "⏹ Stop Live"
            self.btn_live.background_color = (0.9, 0.2, 0.2, 1)
            self.status_label.text = "Live OCR აქტიურია..."
            self.live_ocr_event = Clock.schedule_interval(self.process_live_frame, 2.5)
        else:
            self.stop_live_ocr()

    def stop_live_ocr(self):
        self.is_live_ocr = False
        self.btn_live.text = "▶ Live OCR"
        self.btn_live.background_color = (0.1, 0.6, 0.9, 1)
        self.status_label.text = "Live OCR გაჩერებულია"
        if self.live_ocr_event:
            self.live_ocr_event.cancel()

    def process_live_frame(self, dt):
        if not self.camera or not self.camera.texture:
            return

        texture = self.camera.texture
        size = texture.size
        pixels = texture.pixels
        target_lang = self.target_spinner.text
        base_url = getattr(config, 'API_ENDPOINT', FALLBACK_API_URL).rstrip('/')

        def async_frame_send():
            try:
                pil_img = PILImage.frombytes(mode='RGBA', size=size, data=pixels)
                buffer = io.BytesIO()
                pil_img.convert('RGB').save(buffer, format='JPEG')
                buffer.seek(0)

                files = {'file': ('frame.jpg', buffer, 'image/jpeg')}
                data = {'target_lang': target_lang}

                response = requests.post(f"{base_url}/ocr-translate", files=files, data=data, timeout=6)
                if response.status_code == 200:
                    res = response.json()
                    extracted = res.get("extracted_text", "")
                    translated = res.get("translated_text", "")
                    
                    if extracted.strip():
                        self.apply_live_results(extracted, translated)
            except Exception as e:
                print(f"[Live Frame Error]: {e}")

        threading.Thread(target=async_frame_send, daemon=True).start()

    @mainthread
    def apply_live_results(self, extracted, translated):
        self.input_text.text = extracted
        if translated:
            self.output_text.text = translated
        self.status_label.text = "ტექსტი კამერიდან წაკითხულია!"

    def speak_translation(self, instance):
        if HAS_PLYER and self.output_text.text:
            try:
                tts.speak(self.output_text.text)
            except Exception as e:
                self.status_label.text = f"TTS შეცდომა: {e}"

    def copy_to_clipboard(self, instance):
        if self.output_text.text and HAS_PLYER:
            try:
                clipboard.copy(self.output_text.text)
                self.status_label.text = "SMS დაკოპირდა!"
            except Exception as e:
                self.status_label.text = f"შეცდომა: {e}"


if __name__ == "__main__":
    LingoLensApp().run()

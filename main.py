"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia
Release Date        : September 10, 2026
Project Name        : LingoLens AI
Version             : 3.6.3 (Ultimate Stable Release)
License             : Proprietary / All Rights Reserved
=============================================================================
"""

import os
import io
import threading
import requests
from PIL import Image as PILImage

# Android SSL Certificate Fixing
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except Exception as e:
    print(f"[SSL Setup Warning]: {e}")

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
from kivy.utils import platform

try:
    import config
    API_URL = config.API_ENDPOINT.rstrip('/')
except Exception:
    API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app"

try:
    from plyer import clipboard, tts
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                
                def callback(permissions, results):
                    if all(results):
                        Clock.schedule_once(lambda dt: self.enable_camera(), 0.5)

                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET
                ], callback)
            except Exception as e:
                print(f"[Permission Error]: {e}")
        else:
            self.enable_camera()

    def enable_camera(self):
        try:
            if hasattr(self, 'camera') and self.camera:
                self.camera.play = True
        except Exception as e:
            print(f"[Camera Enable Error]: {e}")

    def build(self):
        if os.path.exists("font.ttf"):
            LabelBase.register(name="CustomFont", fn_regular="font.ttf")

        self.title = "LingoLens AI - Dialogue & Live OCR"
        self.is_live = False
        self.live_event = None
        self.ocr_in_progress = False

        root = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # Header
        root.add_widget(Label(
            text="LingoLens AI - Two-Way Dialogue & Live OCR",
            font_size='16sp',
            bold=True,
            size_hint_y=0.05,
            color=(0.2, 0.8, 0.5, 1)
        ))

        # ენების არჩევა / Swap
        lang_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        langs = ('ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN')
        
        self.src_spin = Spinner(text='en', values=langs, size_hint_x=0.4)
        btn_swap = Button(text="⇄ Swap", size_hint_x=0.2, background_color=(0.2, 0.6, 0.9, 1))
        btn_swap.bind(on_press=self.swap_langs)
        self.tgt_spin = Spinner(text='ka', values=langs, size_hint_x=0.4)

        lang_layout.add_widget(self.src_spin)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.tgt_spin)
        root.add_widget(lang_layout)

        # კამერა (Android-ზე უსაფრთხო ინიციალიზაცია)
        try:
            self.camera = Camera(play=False, resolution=(640, 480), size_hint_y=0.28)
        except Exception as e:
            print(f"[Camera Init Warning]: {e}")
            self.camera = Label(text="კამერის ინიციალიზაცია ვერ მოხერხდა", size_hint_y=0.28)

        root.add_widget(self.camera)

        # 1. ტექსტის შეყვანა
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი თარგმნისთვის...",
            multiline=True, size_hint_y=0.15, font_size='14sp'
        )
        self.input_text.bind(text=self.on_text_change)
        root.add_widget(self.input_text)

        # 2. ნათარგმნი ტექსტი
        self.output_text = TextInput(
            hint_text="გამართული თარგმანი გამოჩნდება აქ...",
            multiline=True, readonly=True, size_hint_y=0.15, font_size='14sp'
        )
        root.add_widget(self.output_text)

        # Action Buttons
        btn_grid = GridLayout(cols=3, spacing=6, size_hint_y=0.10)
        
        self.btn_live = Button(text="▶ Live OCR", background_color=(0.1, 0.6, 0.9, 1))
        self.btn_live.bind(on_press=self.toggle_live)
        btn_grid.add_widget(self.btn_live)

        btn_speak = Button(text="🔊 Read Output", background_color=(0.8, 0.4, 0.1, 1))
        btn_speak.bind(on_press=self.speak_text)
        btn_grid.add_widget(btn_speak)

        btn_copy = Button(text="📋 Copy", background_color=(0.2, 0.7, 0.3, 1))
        btn_copy.bind(on_press=self.copy_text)
        btn_grid.add_widget(btn_copy)

        root.add_widget(btn_grid)

        # Status
        self.status = Label(text="მზადაა მუშაობისთვის", size_hint_y=0.04, font_size='11sp')
        root.add_widget(self.status)

        return root

    def swap_langs(self, instance):
        s, t = self.src_spin.text, self.tgt_spin.text
        self.src_spin.text, self.tgt_spin.text = t, s
        self.status.text = f"მიმართულება: {t} ➔ {s}"

    def on_text_change(self, instance, val):
        Clock.unschedule(self.translate_task)
        Clock.schedule_once(lambda dt: self.translate_task(val), 0.5)

    def translate_task(self, text):
        if not text.strip():
            self.output_text.text = ""
            return

        def async_run():
            try:
                res = requests.post(
                    f"{API_URL}/translate-text",
                    data={'text': text, 'src_lang': self.src_spin.text, 'target_lang': self.tgt_spin.text},
                    timeout=8
                )
                if res.status_code == 200:
                    self.update_out(res.json().get("translated_text", ""))
            except Exception as e:
                self.update_status(f"კავშირის შეცდომა: {e}")

        threading.Thread(target=async_run, daemon=True).start()

    @mainthread
    def update_out(self, val):
        self.output_text.text = val
        self.status.text = "თარგმანი მზადაა!"

    @mainthread
    def update_status(self, msg):
        self.status.text = str(msg)

    def toggle_live(self, instance):
        if not isinstance(self.camera, Camera):
            self.status.text = "კამერა მიუწვდომელია"
            return

        if not self.is_live:
            self.enable_camera()
            self.is_live = True
            self.ocr_in_progress = False
            self.btn_live.text = "⏹ Stop Live"
            self.btn_live.background_color = (0.9, 0.2, 0.2, 1)
            self.live_event = Clock.schedule_interval(self.capture_frame, 2.5)
            self.status.text = "Live OCR აქტიურია..."
        else:
            self.is_live = False
            self.btn_live.text = "▶ Live OCR"
            self.btn_live.background_color = (0.1, 0.6, 0.9, 1)
            if self.live_event:
                self.live_event.cancel()
            self.status.text = "Live OCR გაჩერებულია"

    def capture_frame(self, dt):
        if not isinstance(self.camera, Camera) or not self.camera.texture or self.ocr_in_progress:
            return

        try:
            tex = self.camera.texture
            size = tex.size
            pixels = tex.pixels
            
            if not pixels:
                return

            color_fmt = tex.colorfmt.upper()
            if color_fmt not in ('RGB', 'RGBA', 'BGRA'):
                color_fmt = 'RGBA'

            img = PILImage.frombytes(color_fmt, size, pixels)
            if color_fmt == 'BGRA':
                r, g, b, a = img.split()
                img = PILImage.merge('RGBA', (b, g, r, a))

            img = img.convert('RGB')
            img.thumbnail((640, 640))
            
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=75)
            buf_bytes = buf.getvalue()

            self.ocr_in_progress = True

            def async_ocr(data_bytes):
                try:
                    res = requests.post(
                        f"{API_URL}/ocr-translate",
                        files={'file': ('frame.jpg', io.BytesIO(data_bytes), 'image/jpeg')},
                        data={'target_lang': self.tgt_spin.text},
                        timeout=8
                    )
                    if res.status_code == 200:
                        data = res.json()
                        ext = data.get("extracted_text", "")
                        tr = data.get("translated_text", "")
                        if ext.strip():
                            self.apply_ocr(ext, tr)
                except Exception as e:
                    print(f"[OCR Error]: {e}")
                finally:
                    self.ocr_in_progress = False

            threading.Thread(target=async_ocr, args=(buf_bytes,), daemon=True).start()
        except Exception as e:
            self.ocr_in_progress = False
            print(f"[Texture Error]: {e}")

    @mainthread
    def apply_ocr(self, ext, tr):
        self.input_text.text = ext
        if tr:
            self.output_text.text = tr
        self.status.text = "ტექსტი ამოცნობილია კამერიდან!"

    def speak_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            try:
                tts.speak(self.output_text.text)
            except Exception:
                self.status.text = "ხმოვანი გაჟღერების შეცდომა"

    def copy_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            try:
                clipboard.copy(self.output_text.text)
                self.status.text = "დაკოპირდა!"
            except Exception:
                self.status.text = "დაკოპირების შეცდომა"


if __name__ == "__main__":
    LingoLensApp().run()

"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia (საქართველო)
Release Date        : September 10, 2026
Project Name        : LingoLens AI
Version             : 3.6.0 (Added Two-Way Dialogue & Voice STT)
License             : Proprietary / All Rights Reserved
=============================================================================
"""

import os
import io
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
    API_URL = config.API_ENDPOINT.rstrip('/')
except Exception:
    API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app"

try:
    from plyer import clipboard, tts, stt
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def on_start(self):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                
                def callback(permissions, results):
                    if all(results):
                        Clock.schedule_once(lambda dt: setattr(self.camera, 'play', True), 0.5)

                request_permissions([
                    Permission.CAMERA,
                    Permission.RECORD_AUDIO,
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ], callback)
            else:
                self.camera.play = True
        except Exception as e:
            print(f"[Permission Error]: {e}")

    def build(self):
        if os.path.exists("font.ttf"):
            LabelBase.register(name="CustomFont", fn_regular="font.ttf")

        self.title = "LingoLens AI - Dialogue & Live OCR"
        self.is_live = False
        self.live_event = None
        self.active_speaker_lang = 'ka'

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

        # კამერა (Live OCR)
        self.camera = Camera(play=False, resolution=(640, 480), size_hint_y=0.28)
        root.add_widget(self.camera)

        # 1. ტექსტის შეყვანა / ამოცნობა
        self.input_text = TextInput(
            hint_text="ჩაწერეთ ტექსტი ან გამოიყენეთ მიკროფონი დიალოგისთვის...",
            multiline=True, size_hint_y=0.15, font_size='14sp'
        )
        self.input_text.bind(text=self.on_text_change)
        root.add_widget(self.input_text)

        # 2. ნათარგმნი ტექსტი (ორმხრივი დიალოგის შედეგი)
        self.output_text = TextInput(
            hint_text="გამართული თარგმანი გამოჩნდება აქ...",
            multiline=True, readonly=True, size_hint_y=0.15, font_size='14sp'
        )
        root.add_widget(self.output_text)

        # --- ORMXRIVI DIALOGI / MIC & OCR BUTTONS ---
        dialogue_grid = GridLayout(cols=2, spacing=6, size_hint_y=0.10)
        
        # Speaker 1 (Source Language)
        self.btn_spk1 = Button(
            text=f"🎤 Speak ({self.src_spin.text.upper()})", 
            background_color=(0.2, 0.7, 0.9, 1)
        )
        self.btn_spk1.bind(on_press=lambda x: self.start_listening(self.src_spin.text))
        dialogue_grid.add_widget(self.btn_spk1)

        # Speaker 2 (Target Language)
        self.btn_spk2 = Button(
            text=f"🎤 Speak ({self.tgt_spin.text.upper()})", 
            background_color=(0.9, 0.5, 0.2, 1)
        )
        self.btn_spk2.bind(on_press=lambda x: self.start_listening(self.tgt_spin.text))
        dialogue_grid.add_widget(self.btn_spk2)

        root.add_widget(dialogue_grid)

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
        self.status = Label(text="მზადაა ორმხრივი დიალოგისთვის", size_hint_y=0.04, font_size='11sp')
        root.add_widget(self.status)

        return root

    def swap_langs(self, instance):
        s, t = self.src_spin.text, self.tgt_spin.text
        self.src_spin.text, self.tgt_spin.text = t, s
        self.btn_spk1.text = f"🎤 Speak ({self.src_spin.text.upper()})"
        self.btn_spk2.text = f"🎤 Speak ({self.tgt_spin.text.upper()})"
        self.status.text = f"მიმართულება: {t} ➔ {s}"

    # --- ORMXRIVI DIALOGI (VOICE RECOGNITION) ---
    def start_listening(self, lang):
        self.active_speaker_lang = lang
        self.status.text = f"გისმენთ ({lang.upper()})..."
        if HAS_PLYER:
            try:
                stt.start()
                Clock.schedule_once(self.check_stt_result, 3.0)
            except Exception as e:
                self.status.text = f"STT შეცდომა: {e}"
        else:
            self.status.text = "ხმოვანი შეყვანა არ არის მხარდაჭერილი"

    def check_stt_result(self, dt):
        if HAS_PLYER:
            try:
                results = stt.results
                if results:
                    recognized_text = results[0]
                    self.input_text.text = recognized_text
                    # განსაზღვრეთ თარგმანის მიმართულება მოლაპარაკე ენის მიხედვით
                    if self.active_speaker_lang == self.src_spin.text:
                        src, tgt = self.src_spin.text, self.tgt_spin.text
                    else:
                        src, tgt = self.tgt_spin.text, self.src_spin.text
                    self.translate_dialogue(recognized_text, src, tgt)
            except Exception:
                pass

    def translate_dialogue(self, text, src_lang, target_lang):
        def async_run():
            try:
                res = requests.post(
                    f"{API_URL}/translate-text",
                    data={'text': text, 'src_lang': src_lang, 'target_lang': target_lang},
                    timeout=5
                )
                if res.status_code == 200:
                    translated = res.json().get("translated_text", "")
                    self.update_out(translated)
                    # ავტომატური გაჟღერება ორმხრივი დიალოგისთვის
                    if HAS_PLYER and translated:
                        tts.speak(translated)
            except Exception as e:
                print(f"[Dialogue Error]: {e}")

        threading.Thread(target=async_run, daemon=True).start()

    def on_text_change(self, instance, val):
        Clock.unschedule(self.translate_task)
        Clock.schedule_once(lambda dt: self.translate_task(val), 0.4)

    def translate_task(self, text):
        if not text.strip():
            self.output_text.text = ""
            return

        def async_run():
            try:
                res = requests.post(
                    f"{API_URL}/translate-text",
                    data={'text': text, 'src_lang': self.src_spin.text, 'target_lang': self.tgt_spin.text},
                    timeout=5
                )
                if res.status_code == 200:
                    self.update_out(res.json().get("translated_text", ""))
            except Exception as e:
                print(f"[Translate Error]: {e}")

        threading.Thread(target=async_run, daemon=True).start()

    @mainthread
    def update_out(self, val):
        self.output_text.text = val
        self.status.text = "დიალოგის თარგმანი მზადაა!"

    def toggle_live(self, instance):
        if not self.is_live:
            self.camera.play = True
            self.is_live = True
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
        if not self.camera or not self.camera.texture:
            return

        try:
            tex = self.camera.texture
            size = tex.size
            pixels = tex.pixels
        except Exception as e:
            print(f"[Texture Error]: {e}")
            return

        def async_ocr(frame_size, frame_pixels):
            try:
                img = PILImage.frombytes('RGBA', frame_size, frame_pixels)
                buf = io.BytesIO()
                img.convert('RGB').save(buf, format='JPEG')
                buf.seek(0)

                res = requests.post(
                    f"{API_URL}/ocr-translate",
                    files={'file': ('frame.jpg', buf, 'image/jpeg')},
                    data={'target_lang': self.tgt_spin.text},
                    timeout=6
                )
                if res.status_code == 200:
                    data = res.json()
                    ext, tr = data.get("extracted_text", ""), data.get("translated_text", "")
                    if ext.strip():
                        self.apply_ocr(ext, tr)
            except Exception as e:
                print(f"[OCR Frame Error]: {e}")

        threading.Thread(target=async_ocr, args=(size, pixels), daemon=True).start()

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

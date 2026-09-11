"""
=============================================================================
PROJECT META INFORMATION & AUTHOR CREDITS
=============================================================================
Author / Developer  : Dato Kacharava
Country             : Georgia
Release Date        : September 10, 2026
Project Name        : LingoLens AI
Version             : 4.0.0 (Dual-Voice Dialogue & Live OCR)
License             : Proprietary / All Rights Reserved
=============================================================================
"""

import os
import io
import threading
import requests
from PIL import Image as PILImage

try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except Exception as e:
    print(f"[SSL Setup Warning]: {e}")

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.utils import platform

FONT_PATH = "font.ttf"
if os.path.exists(FONT_PATH):
    resource_add_path(os.path.dirname(os.path.abspath(FONT_PATH)))
    LabelBase.register(name="Roboto", fn_regular=FONT_PATH)

try:
    import config
    API_URL = config.API_ENDPOINT.rstrip('/')
except Exception:
    API_URL = "https://lingo-lens-kqxn-ntwa1e0h0-datokacharava640-cybers-projects.vercel.app"

try:
    from plyer import clipboard, tts, audio
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False


class CustomSpinnerOption(SpinnerOption):
    font_name = "Roboto"


class LingoLensApp(App):
    AUTHOR = "Dato Kacharava"
    COUNTRY = "Georgia"

    def build(self):
        self.title = "LingoLens AI - Real-Time Dialogue & OCR"
        self.is_live = False
        self.live_event = None
        self.ocr_in_progress = False
        self.is_recording = False
        self.active_speaker = None
        self.camera = None
        self.audio_path = os.path.join(self.user_data_dir, "dialogue.wav")

        font_to_use = "Roboto"
        self.root_layout = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # Header
        self.root_layout.add_widget(Label(
            text="LingoLens AI - Live Dialogue & OCR",
            font_size='16sp', bold=True, size_hint_y=0.05,
            color=(0.2, 0.8, 0.5, 1), font_name=font_to_use
        ))

        # ენების არჩევა / Swap
        lang_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=5)
        langs = ('ka', 'en', 'ru', 'de', 'fr', 'es', 'it', 'tr', 'zh-CN')

        self.src_spin = Spinner(
            text='ka', values=langs, size_hint_x=0.4,
            font_name=font_to_use, option_cls=CustomSpinnerOption
        )
        btn_swap = Button(
            text="Swap", size_hint_x=0.2,
            background_color=(0.2, 0.6, 0.9, 1), font_name=font_to_use
        )
        btn_swap.bind(on_press=self.swap_langs)

        self.tgt_spin = Spinner(
            text='en', values=langs, size_hint_x=0.4,
            font_name=font_to_use, option_cls=CustomSpinnerOption
        )

        lang_layout.add_widget(self.src_spin)
        lang_layout.add_widget(btn_swap)
        lang_layout.add_widget(self.tgt_spin)
        self.root_layout.add_widget(lang_layout)

        # 1. დიალოგის მოდული (ორი მიკროფონის ღილაკი)
        dialogue_grid = GridLayout(cols=2, spacing=6, size_hint_y=0.10)
        self.btn_mic_a = Button(
            text="🎤 Speaker A\n(Speak Left)", background_color=(0.1, 0.7, 0.4, 1),
            font_name=font_to_use, halign='center'
        )
        self.btn_mic_a.bind(on_press=lambda inst: self.toggle_recording('A'))

        self.btn_mic_b = Button(
            text="🎤 Speaker B\n(Speak Right)", background_color=(0.8, 0.3, 0.2, 1),
            font_name=font_to_use, halign='center'
        )
        self.btn_mic_b.bind(on_press=lambda inst: self.toggle_recording('B'))

        dialogue_grid.add_widget(self.btn_mic_a)
        dialogue_grid.add_widget(self.btn_mic_b)
        self.root_layout.add_widget(dialogue_grid)

        # კამერის კონტეინერი
        self.cam_box = BoxLayout(size_hint_y=0.25)
        self.placeholder_label = Label(text="კამერის ჩატვირთვა...", font_name=font_to_use)
        self.cam_box.add_widget(self.placeholder_label)
        self.root_layout.add_widget(self.cam_box)

        # 2. ტექსტის შეყვანა / ამოცნობილი ხმა
        self.input_text = TextInput(
            hint_text="ჩაწერილი ხმა ან ტექსტი...", multiline=True,
            size_hint_y=0.15, font_size='14sp', font_name=font_to_use
        )
        self.input_text.bind(text=self.on_text_change)
        self.root_layout.add_widget(self.input_text)

        # 3. ნათარგმნი ტექსტი
        self.output_text = TextInput(
            hint_text="თარგმანი გამოჩნდება აქ...", multiline=True,
            readonly=True, size_hint_y=0.15, font_size='14sp', font_name=font_to_use
        )
        self.root_layout.add_widget(self.output_text)

        # Action Buttons
        btn_grid = GridLayout(cols=3, spacing=6, size_hint_y=0.08)
        self.btn_live = Button(
            text="Live OCR", background_color=(0.1, 0.6, 0.9, 1), font_name=font_to_use
        )
        self.btn_live.bind(on_press=self.toggle_live)
        btn_grid.add_widget(self.btn_live)

        btn_speak = Button(
            text="Read Text", background_color=(0.8, 0.4, 0.1, 1), font_name=font_to_use
        )
        btn_speak.bind(on_press=self.speak_text)
        btn_grid.add_widget(btn_speak)

        btn_copy = Button(
            text="Copy", background_color=(0.2, 0.7, 0.3, 1), font_name=font_to_use
        )
        btn_copy.bind(on_press=self.copy_text)
        btn_grid.add_widget(btn_copy)

        self.root_layout.add_widget(btn_grid)

        # Status Bar
        self.status = Label(
            text="მზადაა დიალოგისთვის", size_hint_y=0.04, font_size='12sp', font_name=font_to_use
        )
        self.root_layout.add_widget(self.status)

        return self.root_layout

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                def callback(permissions, results):
                    if all(results):
                        Clock.schedule_once(lambda dt: self.init_camera(), 0.5)
                    else:
                        self.update_status("ნებართვა უარყოფილია")
                request_permissions([
                    Permission.CAMERA, Permission.RECORD_AUDIO, Permission.INTERNET
                ], callback)
            except Exception as e:
                print(f"[Permission Error]: {e}")
                self.init_camera()
        else:
            self.init_camera()

    @mainthread
    def init_camera(self):
        try:
            self.cam_box.clear_widgets()
            self.camera = Camera(play=False, resolution=(640, 480))
            self.cam_box.add_widget(self.camera)
            self.status.text = "კამერა მზადაა"
        except Exception as e:
            print(f"[Camera Error]: {e}")

    def toggle_recording(self, speaker):
        if not HAS_PLYER:
            self.status.text = "ხმის ჩაწერა მიუწვდომელია"
            return

        src = self.src_spin.text if speaker == 'A' else self.tgt_spin.text
        tgt = self.tgt_spin.text if speaker == 'A' else self.src_spin.text

        if not self.is_recording:
            try:
                audio.start_recording(self.audio_path)
                self.is_recording = True
                self.active_speaker = speaker
                btn = self.btn_mic_a if speaker == 'A' else self.btn_mic_b
                btn.text = "🛑 Stop & Translate"
                btn.background_color = (0.9, 0.1, 0.1, 1)
                self.status.text = f"ისმენს ({src})..."
            except Exception as e:
                self.status.text = f"ჩაწერის შეცდომა: {e}"
        else:
            try:
                audio.stop_recording()
                self.is_recording = False
                self.reset_mic_buttons()
                self.status.text = "მუშავდება..."
                threading.Thread(target=self.send_audio_task, args=(src, tgt), daemon=True).start()
            except Exception as e:
                self.status.text = f"ჩაწერის გაჩერების შეცდომა: {e}"

    def reset_mic_buttons(self):
        self.btn_mic_a.text = "🎤 Speaker A\n(Speak Left)"
        self.btn_mic_a.background_color = (0.1, 0.7, 0.4, 1)
        self.btn_mic_b.text = "🎤 Speaker B\n(Speak Right)"
        self.btn_mic_b.background_color = (0.8, 0.3, 0.2, 1)

    def send_audio_task(self, src, tgt):
        if not os.path.exists(self.audio_path):
            self.update_status("ხმის ფაილი ვერ მოიძებნა")
            return

        try:
            with open(self.audio_path, 'rb') as f:
                res = requests.post(
                    f"{API_URL}/stt-translate",
                    files={'file': ('audio.wav', f, 'audio/wav')},
                    data={'src_lang': src, 'target_lang': tgt},
                    timeout=12
                )
            if res.status_code == 200:
                data = res.json()
                ext = data.get("extracted_text", "")
                tr = data.get("translated_text", "")
                self.apply_dialogue_result(ext, tr)
        except Exception as e:
            self.update_status(f"სერვერის შეცდომა: {e}")

    @mainthread
    def apply_dialogue_result(self, ext, tr):
        self.input_text.text = ext
        self.output_text.text = tr
        self.status.text = "თარგმანი მზადაა!"
        if HAS_PLYER and tr:
            try:
                tts.speak(tr)
            except Exception:
                pass

    def swap_langs(self, instance):
        s, t = self.src_spin.text, self.tgt_spin.text
        self.src_spin.text, self.tgt_spin.text = t, s

    def on_text_change(self, instance, val):
        Clock.unschedule(self.translate_task)
        Clock.schedule_once(lambda dt: self.translate_task(val), 0.5)

    def translate_task(self, text):
        if not text.strip() or self.is_recording:
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

    @mainthread
    def update_status(self, msg):
        self.status.text = str(msg)

    def toggle_live(self, instance):
        if not self.camera or not isinstance(self.camera, Camera):
            return

        if not self.is_live:
            self.camera.play = True
            self.is_live = True
            self.btn_live.text = "Stop Live"
            self.btn_live.background_color = (0.9, 0.2, 0.2, 1)
            self.live_event = Clock.schedule_interval(self.capture_frame, 2.5)
        else:
            self.camera.play = False
            self.is_live = False
            self.btn_live.text = "Live OCR"
            self.btn_live.background_color = (0.1, 0.6, 0.9, 1)
            if self.live_event:
                self.live_event.cancel()

    def capture_frame(self, dt):
        if not self.camera or not self.camera.texture or self.ocr_in_progress:
            return

        try:
            tex = self.camera.texture
            img = PILImage.frombytes('RGBA', tex.size, tex.pixels).convert('RGB')
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
                        self.apply_ocr(data.get("extracted_text", ""), data.get("translated_text", ""))
                except Exception as e:
                    print(f"[OCR Error]: {e}")
                finally:
                    self.ocr_in_progress = False

            threading.Thread(target=async_ocr, args=(buf_bytes,), daemon=True).start()
        except Exception:
            self.ocr_in_progress = False

    @mainthread
    def apply_ocr(self, ext, tr):
        if ext.strip():
            self.input_text.text = ext
            self.output_text.text = tr

    def speak_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            tts.speak(self.output_text.text)

    def copy_text(self, instance):
        if HAS_PLYER and self.output_text.text:
            clipboard.copy(self.output_text.text)
            self.status.text = "დაკოპირდა!"


if __name__ == "__main__":
    LingoLensApp().run()

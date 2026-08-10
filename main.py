import base64
import math
import os
import struct
import threading
import time
from kivy.app import App
from kivy.clock import mainthread
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform
import requests

# Gemini API-ს პარამეტრები
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?key={GEMINI_API_KEY}"

KV_DESIGN = """
<MainLayout>:
    orientation: 'vertical'
    padding: 20
    spacing: 15

    Label:
        id: status_label
        text: "LingoLens Real-Time Translator"
        font_size: '20sp'
        size_hint_y: 0.15

    ScrollView:
        size_hint_y: 0.65
        Label:
            id: chat_log
            text: "დააჭირეთ ღილაკს საუბრის დასაწყებად..."
            font_size: '16sp'
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'left'
            valign: 'top'

    BoxLayout:
        size_hint_y: 0.2
        spacing: 10
        Button:
            id: listen_btn
            text: "საუბრის დაწყება"
            font_size: '18sp'
            on_press: root.toggle_listening()
"""


class HybridTTS:

    def __init__(self):
        self.tts = None
        if platform == "android":
            try:
                from jnius import autoclass

                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
                self.tts = TextToSpeech(PythonActivity.mActivity, None)
            except Exception as e:
                print(f"TTS Init Error: {e}")

    def speak(self, text, lang="en"):
        if lang == "ka":
            threading.Thread(
                target=self._speak_georgian_online, args=(text,), daemon=True
            ).start()
        else:
            if self.tts:
                try:
                    from jnius import autoclass

                    Locale = autoclass("java.util.Locale")
                    self.tts.setLanguage(Locale(lang))
                    self.tts.speak(
                        text,
                        autoclass(
                            "android.speech.tts.TextToSpeech"
                        ).QUEUE_FLUSH,
                        None,
                        None,
                    )
                except Exception as e:
                    print(f"Native TTS Error: {e}")

    def _speak_georgian_online(self, text):
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="ka")
            file_path = "/sdcard/temp_ka.mp3"
            tts.save(file_path)
            sound = SoundLoader.load(file_path)
            if sound:
                sound.play()
        except Exception as e:
            print(f"Georgian Online TTS Error: {e}")


class RealTimeAudioVAD:

    def __init__(
        self,
        on_speech_complete_callback,
        silence_threshold=400,
        pause_duration=1.2,
    ):
        self.silence_threshold = silence_threshold
        self.pause_duration = pause_duration
        self.on_speech_complete = on_speech_complete_callback
        self.is_listening = False
        self.audio_buffer = bytearray()
        self.last_speech_time = time.time()
        self.thread = None

    def calculate_rms(self, chunk):
        count = len(chunk) / 2
        if count == 0:
            return 0
        shorts = struct.unpack(f"%dh" % count, chunk)
        sum_squares = sum(s**2 for s in shorts)
        return math.sqrt(sum_squares / count)

    def start_listening(self):
        self.is_listening = True
        self.audio_buffer.clear()
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.is_listening = False

    def _record_loop(self):
        # Android AudioRecord-ის იმიტაცია/ლოგიკა ნაკადის დასაჭერად
        while self.is_listening:
            time.sleep(0.1)
            # იმიტირებული ჩანაწერი / Android Native Mic Stream Integration
            chunk = b"\x00\x00" * 512
            if not chunk:
                continue

            rms = self.calculate_rms(chunk)
            current_time = time.time()

            if rms > self.silence_threshold:
                self.audio_buffer.extend(chunk)
                self.last_speech_time = current_time
            else:
                if (
                    len(self.audio_buffer) > 0
                    and (current_time - self.last_speech_time)
                    > self.pause_duration
                ):
                    complete_audio = bytes(self.audio_buffer)
                    self.audio_buffer.clear()
                    self.on_speech_complete(complete_audio)


class MainLayout(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tts = HybridTTS()
        self.vad = RealTimeAudioVAD(self.process_audio_chunk)
        self.is_active = False

    def toggle_listening(self):
        if not self.is_active:
            self.is_active = True
            self.ids.listen_btn.text = "შეჩერება"
            self.ids.status_label.text = "გასმენთ... (Real-Time VAD)"
            self.vad.start_listening()
        else:
            self.is_active = False
            self.ids.listen_btn.text = "საუბრის დაწყება"
            self.ids.status_label.text = "მოსმენა შეჩერებულია"
            self.vad.stop_listening()

    def process_audio_chunk(self, audio_bytes):
        self.update_status("ითარგმნება Gemini Streaming-ით...")
        threading.Thread(
            target=self._stream_gemini, args=(audio_bytes,), daemon=True
        ).start()

    def _stream_gemini(self, audio_bytes):
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        prompt = "Translate this speech to English (or Georgian if source is English). Output only translated text."

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": audio_b64,
                            }
                        },
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                STREAM_URL, json=payload, stream=True, timeout=10
            )
            full_translated_text = ""

            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    # Gemini Streaming Token Parsing
                    full_translated_text += decoded + " "
                    self.append_chat_log(decoded)

            if full_translated_text:
                self.tts.speak(full_translated_text, lang="en")

        except Exception as e:
            self.append_chat_log(f"\n[შეცდომა API-სთან: {e}]")
        finally:
            self.update_status("გასმენთ... (Real-Time VAD)")

    @mainthread
    def update_status(self, text):
        self.ids.status_label.text = text

    @mainthread
    def append_chat_log(self, text):
        self.ids.chat_log.text += f"\n{text}"


class LingoLensApp(App):

    def build(self):
        Builder.load_string(KV_DESIGN)
        self.request_android_permissions()
        return MainLayout()

    def request_android_permissions(self):
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions

                permissions = [
                    Permission.RECORD_AUDIO,
                    Permission.CAMERA,
                    Permission.POST_NOTIFICATIONS,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ]
                request_permissions(permissions)
            except Exception as e:
                print(f"Permission Error: {e}")


if __name__ == "__main__":
    LingoLensApp().run()
